import pybullet as p
import pybullet_data
import time
import numpy as np
import json
from protocol import create_protocol_message, read_messages, check_response
from agent import Agent

# === Simulation Setup ===
p.connect(p.GUI)
p.setAdditionalSearchPath(pybullet_data.getDataPath())
p.setGravity(0, 0, -9.8)
planeId = p.loadURDF("plane.urdf")

# Create task objects
num_objects = 3
object_ids = []
task_name_map = {}

for i in range(num_objects):
    pos = np.random.uniform(low=[-2, -2, 0.5], high=[2, 2, 0.5])
    obj_id = p.loadURDF("cube_small.urdf", pos)
    object_ids.append(obj_id)
    task_name_map[obj_id] = f"cube_{i}"

task_pool = object_ids.copy()

agent_starts = {
    "agent1": [0, -1, 0.5],
    "agent2": [0, 1, 0.5],
    "agent3": [-1, 0, 0.5]
}

agent_orientation = p.getQuaternionFromEuler([0, 0, 0])
agents = {}

# Load agents
for name, pos in agent_starts.items():
    uid = p.loadURDF("r2d2.urdf", pos, agent_orientation)
    agents[name] = Agent(name, uid, task_name_map)

# Distribute tasks
for agent in agents.values():
    agent.set_task_pool(task_pool)
    agent.assign_task()
    print(f"[DEBUG] {agent.name} assigned task {agent.task}")

# === Main Coordination Loop ===
priority_start = 1
max_retries = 3
message_queue = []

for attempt in range(max_retries):
    print(f"\n=== Attempt #{attempt} ===")

    # Phase 1: send claims
    for agent_name, agent in agents.items():
        if not agent.success:
            if agent.task is None:
                print(f"[SKIP] {agent_name} has no task to claim.")
                continue
            recipients = [a for a in agents if a != agent_name]
            agent.send_claim(recipients, message_queue)

    time.sleep(0.2)

    # Phase 2: process responses
    for agent in agents.values():
        if not agent.success:
            agent.respond_to_claims(message_queue, agents)

    # Phase 3: check results
    all_success = True
    for agent in agents.values():
        if not agent.success:
            result = check_response(agent.name, agent.task, message_queue, task_name_map, task_pool, agents)
            agent.success = result
            if not result:
                agent.task = None  # Clear failed task to reassign

        if agent.success and agent.task in task_pool:
            task_pool.remove(agent.task)
        elif not agent.success:
            agent.priority += 1
            agent.assign_task(exclude_list=[agent.task] if agent.task else None)
            all_success = False

    if all_success:
        break


# === Execute Simulation ===
def move_towards(agent_id, target_pos, agent_orientation, step_size=0.01):
    pos, _ = p.getBasePositionAndOrientation(agent_id)
    pos = np.array(pos)
    direction = np.array(target_pos) - pos
    norm = np.linalg.norm(direction)
    if norm > step_size:
        direction = direction / norm * step_size
    new_pos = pos + direction
    p.resetBasePositionAndOrientation(agent_id, new_pos.tolist(), agent_orientation)

for agent in agents.values():
    if agent.task is not None:
        pos = p.getBasePositionAndOrientation(agent.task)[0]
        print(f"{agent.name} target object id: {agent.task}, assigned: {task_name_map[agent.task]}")
        agent.target_pos = pos

for _ in range(1000):
    for agent in agents.values():
        if hasattr(agent, 'target_pos'):
            move_towards(agent.id, agent.target_pos, agent_orientation)
    p.stepSimulation()
    time.sleep(1./240)

p.disconnect()
