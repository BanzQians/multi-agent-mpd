import pybullet as p
import pybullet_data
import time
import numpy as np
from agent import Agent
from protocol import Protocol
from policy import NearestTaskPolicy, DiffusionPolicyStub
from task_conflict_gen import assign_conflicting_tasks

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

# policy = NearestTaskPolicy()
policy = DiffusionPolicyStub()

for name, pos in agent_starts.items():
    uid = p.loadURDF("r2d2.urdf", pos, agent_orientation)
    agents[name] = Agent(name, uid, task_name_map, policy)

# Distribute initial tasks
assign_conflicting_tasks(agents, task_pool, task_name_map, conflict_ratio=0.8)

# === Coordination Loop via Protocol ===
protocol = Protocol(agents, task_name_map, task_pool)

max_retries = 3
for attempt in range(max_retries):
    print(f"\n=== Attempt #{attempt} ===")
    protocol.receive_claims()
    protocol.evaluate_conflicts()
    success = protocol.resolve_outcomes()
    if success:
        print("[SUCCESS] All agents assigned.")
        break

# === Execute Simulation ===
def move_towards(agent_id, target_pos, orientation, step_size=0.01):
    pos, _ = p.getBasePositionAndOrientation(agent_id)
    pos = np.array(pos)
    direction = np.array(target_pos) - pos
    norm = np.linalg.norm(direction)
    if norm > step_size:
        direction = direction / norm * step_size
    new_pos = pos + direction
    p.resetBasePositionAndOrientation(agent_id, new_pos.tolist(), orientation)

# Move agents toward target
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
