import sys
sys.path.insert(0, "./dp_repo")

import pybullet as p
import pybullet_data
import time
import numpy as np
from agent import Agent
from protocol import Protocol
from policy import NearestTaskPolicy, DiffusionPolicyStub, DiffusionPolicyWrapperAdapter
from task_conflict_gen import assign_conflicting_tasks
from pathlib import Path

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

policy = NearestTaskPolicy()
# ckpt_path = Path("dp_repo/data/outputs/2025.06.04/20.16.23_train_diffusion_unet_lowdim_pybullet_mcp_lowdim/checkpoints/epoch=0150-test_mean_score=0.098.ckpt").resolve()
# policy = DiffusionPolicyWrapperAdapter(str(ckpt_path))

for name, pos in agent_starts.items():
    uid = p.loadURDF("r2d2.urdf", pos, agent_orientation)
    agents[name] = Agent(name, uid, task_name_map, policy)
    agents[name].reached_goal = False

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

def get_obs_for_agent(agent, task_obj_id):
    agent_pos, _ = p.getBasePositionAndOrientation(agent.id)
    agent_vel, _ = p.getBaseVelocity(agent.id)

    obj_pos, _ = p.getBasePositionAndOrientation(task_obj_id)
    obj_vel, _ = p.getBaseVelocity(task_obj_id)

    agent_cos, agent_sin = 1.0, 0.0

    task_name = agent.task_name_map[task_obj_id]
    obj_idx = int(task_name.split("_")[1])
    one_hot = np.zeros(8)
    one_hot[obj_idx] = 1.0

    obs = np.concatenate([
        agent_pos[:2], agent_vel[:2],
        obj_pos[:2], obj_vel[:2],
        [agent_cos, agent_sin, 0.0, 0.0],
        one_hot
    ])

    return np.stack([obs, obs])

# Move agents toward target
for agent in agents.values():
    agent.update_obs()
    if agent.task is not None:
        pos = p.getBasePositionAndOrientation(agent.task)[0]
        print(f"{agent.name} target object id: {agent.task}, assigned: {task_name_map[agent.task]}")
        agent.target_pos = pos

MAX_STEP_SIZE = 0.01
reach_threshold = 0.1

for _ in range(1000):
    for agent in agents.values():
        if agent.task is None:
            continue

        current_xy = np.array(p.getBasePositionAndOrientation(agent.id)[0][:2])
        target_xy = np.array(p.getBasePositionAndOrientation(agent.task)[0][:2])
        distance = np.linalg.norm(current_xy - target_xy)

        # === Check if close to target ===
        if distance < reach_threshold:
            if not hasattr(agent, 'reached_goal') or not agent.reached_goal:
                print(f"[INFO] {agent.name} is close to the target. Skipping control.")
                agent.reached_goal = True
            continue

        # === Get action ===
        obs_vec = get_obs_for_agent(agent, agent.task).astype(np.float32)

        if isinstance(agent.policy, NearestTaskPolicy):
            actions = agent.policy.predict_action(agent)
            step = actions[0]
            norm = np.linalg.norm(step)
            if norm > MAX_STEP_SIZE:
                step = step / norm * MAX_STEP_SIZE
        else:
            actions = agent.policy.predict_action({'obs': obs_vec})
            predicted_target_xy = actions[0]
            direction = predicted_target_xy - current_xy
            norm = np.linalg.norm(direction)
            step = direction / norm * MAX_STEP_SIZE if norm > MAX_STEP_SIZE else direction

        # === Debug output ===
        # print(f"[DEBUG] {agent.name} obs[:6]: {obs_vec[0][:6]} | action[0]: {actions[0]}")

        # === Update position ===
        new_pos_2d = current_xy + step
        new_pos_3d = [new_pos_2d[0], new_pos_2d[1], p.getBasePositionAndOrientation(agent.id)[0][2]]
        p.resetBasePositionAndOrientation(agent.id, new_pos_3d, agent_orientation)

    p.stepSimulation()
    time.sleep(1. / 240)

p.disconnect()

