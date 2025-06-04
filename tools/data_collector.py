import os
import numpy as np
import pybullet as p
import pybullet_data
from pathlib import Path
from collections import deque

# === Config ===
NUM_EPISODES = 100
MAX_STEPS = 120
OBS_HORIZON = 2
ACTION_HORIZON = 8
SAVE_PATH = Path("data/collected_trajs")
SAVE_PATH.mkdir(parents=True, exist_ok=True)

# === Bullet Setup ===
p.connect(p.DIRECT)
p.setAdditionalSearchPath(pybullet_data.getDataPath())

def reset_world():
    p.resetSimulation()
    p.setGravity(0, 0, -9.8)
    p.loadURDF("plane.urdf")
    agent_pos = np.random.uniform([-1, -1, 0.5], [1, 1, 0.5])
    obj_pos = np.random.uniform([-1, -1, 0.5], [1, 1, 0.5])
    agent_id = p.loadURDF("r2d2.urdf", agent_pos)
    obj_id = p.loadURDF("cube_small.urdf", obj_pos)
    return agent_id, obj_id

def get_obs(agent_id, obj_id):
    agent_pos, _ = p.getBasePositionAndOrientation(agent_id)
    agent_vel, _ = p.getBaseVelocity(agent_id)
    obj_pos, _ = p.getBasePositionAndOrientation(obj_id)
    obj_vel, _ = p.getBaseVelocity(obj_id)
    one_hot = np.zeros(8)
    one_hot[0] = 1.0  # assume cube_0
    return np.concatenate([
        agent_pos[:2], agent_vel[:2],
        obj_pos[:2], obj_vel[:2],
        [1.0, 0.0, 0.0, 0.0],  # orientation dummy
        one_hot
    ])

def move_towards(agent_id, target, step_size=0.05):
    pos, _ = p.getBasePositionAndOrientation(agent_id)
    direction = np.array(target[:2]) - np.array(pos[:2])
    norm = np.linalg.norm(direction)
    if norm > step_size:
        direction = direction / norm * step_size
    new_xy = np.array(pos[:2]) + direction
    p.resetBasePositionAndOrientation(agent_id, [new_xy[0], new_xy[1], pos[2]], [0, 0, 0, 1])
    return new_xy

# === Collect
obs_list, action_list = [], []

for ep in range(NUM_EPISODES):
    agent_id, obj_id = reset_world()
    obs_buf = deque(maxlen=OBS_HORIZON)
    pos_buf = []

    for t in range(MAX_STEPS):
        obs = get_obs(agent_id, obj_id)
        obs_buf.append(obs)
        if len(obs_buf) < OBS_HORIZON:
            continue
        obs_seq = np.stack(obs_buf)

        # start recording future positions
        future_positions = []
        target_pos, _ = p.getBasePositionAndOrientation(obj_id)
        for _ in range(ACTION_HORIZON):
            agent_xy = move_towards(agent_id, target_pos)
            p.stepSimulation()
            pos, _ = p.getBasePositionAndOrientation(agent_id)
            future_positions.append(np.array(pos[:2]))

        obs_list.append(obs_seq)
        action_list.append(np.stack(future_positions))

        # reset for next sample in episode
        obs_buf.clear()

p.disconnect()

# === Save
obs_arr = np.array(obs_list)     # (N, 2, 20)
action_arr = np.array(action_list)  # (N, 8, 2)
out_path = SAVE_PATH / "pusht_lowdim_dataset.npz"
np.savez_compressed(out_path, obs=obs_arr, action=action_arr)

print(f"[SAVED] Dataset to {out_path}")
print(f"Shape: obs = {obs_arr.shape}, action = {action_arr.shape}")
