import sys
sys.path.insert(0, "./dp_repo")

import pybullet as p
import pybullet_data
import time
import numpy as np
import sys

sys.path.insert(0, "./dp_repo")

from sim_env import SimEnv

# === Create simulation environment ===
env = SimEnv(num_agents=3, num_objects=3)

# === Distribute tasks ===
env.assign_tasks(conflict_ratio=0.8)

# === Show task type info ===
print("\n=== [DEBUG] Task Type Map ===")
for obj_id, task_type in env.task_type_map.items():
    print(f"  - {env.task_name_map[obj_id]}: {task_type}")
print("=============================\n")

# === Main execution loop ===
for _ in range(1000):
    env.step()
    time.sleep(1. / 240)

env.close()
