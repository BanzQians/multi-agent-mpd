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

# policy = NearestTaskPolicy()
ckpt_path = Path("dp_repo/data/outputs/2025.05.27/16.21.55_train_diffusion_unet_lowdim_pusht_lowdim/checkpoints/epoch=1300-test_mean_score=0.912.ckpt").resolve()
policy = DiffusionPolicyWrapperAdapter(str(ckpt_path))


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

def get_obs_for_agent(agent, task_obj_id):
    # === Get positions and velocities ===
    agent_pos, _ = p.getBasePositionAndOrientation(agent.id)
    agent_vel, _ = p.getBaseVelocity(agent.id)

    obj_pos, _ = p.getBasePositionAndOrientation(task_obj_id)
    obj_vel, _ = p.getBaseVelocity(task_obj_id)

    # === Heading approximation ===
    agent_cos, agent_sin = 1.0, 0.0  # 如果你有朝向可改

    # === One-hot object ID ===
    task_name = agent.task_name_map[task_obj_id]  # e.g. "cube_2"
    obj_idx = int(task_name.split("_")[1])
    one_hot = np.zeros(8)
    one_hot[obj_idx] = 1.0

    # === Compose feature ===
    obs = np.concatenate([
        agent_pos[:2], agent_vel[:2],
        obj_pos[:2], obj_vel[:2],
        [agent_cos, agent_sin, 0.0, 0.0],
        one_hot
    ])  # (20,)
    
    # Repeat to make shape (2, 20)
    return np.stack([obs, obs])


# Move agents toward target
for agent in agents.values():
    agent.update_obs()
    if agent.task is not None:
        pos = p.getBasePositionAndOrientation(agent.task)[0]
        print(f"{agent.name} target object id: {agent.task}, assigned: {task_name_map[agent.task]}")
        agent.target_pos = pos

# for _ in range(1000):
#     for agent in agents.values():
#         if hasattr(agent, 'target_pos'):
#             move_towards(agent.id, agent.target_pos, agent_orientation)
#     p.stepSimulation()
#     time.sleep(1./240)

for _ in range(1000):
    for agent in agents.values():
        if agent.task is None:
            continue

        obs_vec = get_obs_for_agent(agent, agent.task).astype(np.float32)
        actions = policy.predict_action({'obs': obs_vec})  # shape: (8, 2)

        # === 当前agent位置 ===
        pos, _ = p.getBasePositionAndOrientation(agent.id)
        current_xy = np.array(pos[:2])

        # === Diffusion Policy输出的是绝对目标点坐标，需要做差 ===
        predicted_target_xy = actions[0]  # shape: (2,)
        direction = predicted_target_xy - current_xy

        # === 控制最大移动速度 ===
        max_step_size = 0.05
        norm = np.linalg.norm(direction)
        if norm > max_step_size:
            step = direction / norm * max_step_size
        else:
            step = direction

        # === 更新位置 ===
        new_pos_2d = current_xy + step
        new_pos_3d = [new_pos_2d[0], new_pos_2d[1], pos[2]]
        p.resetBasePositionAndOrientation(agent.id, new_pos_3d, agent_orientation)

    p.stepSimulation()
    time.sleep(1. / 240)



print("agent_xy:", agent_xy)
print("task_xy:", task_xy)
print("relative_xy:", relative_xy)
print("obs:", full_obs)

p.disconnect()
