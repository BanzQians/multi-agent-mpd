import numpy as np
import pybullet as p
from collections import deque

def score(agent, task_id):
    agent_pos, _ = p.getBasePositionAndOrientation(agent.id)
    task_pos, _ = p.getBasePositionAndOrientation(task_id)
    distance = np.linalg.norm(np.array(agent_pos) - np.array(task_pos))
    task_value = 1.0
    return -distance + 1.0 * task_value

class Agent:
    def __init__(self, name, agent_id, task_name_map, policy):
        self.name = name
        self.id = agent_id
        self.task_name_map = task_name_map
        self.policy = policy
        self.task = None
        self.success = False
        self.priority = 1
        self.task_pool = []
        self.obs_buffer = deque(maxlen=2)  # save two history predictions

    def set_task_pool(self, task_pool):
        self.task_pool = task_pool

    def assign_task(self, exclude_list=None):
        if exclude_list is None:
            exclude_list = []

        available = [obj_id for obj_id in self.task_pool if obj_id not in exclude_list]
        self.task = self.policy.choose(self,  available)

        if not available:
            print(f"[WARNING] {self.name} found no available task (exclude_list = {exclude_list})")
            self.task = None
            return
    
    def update_obs(self):
        pos, _ = p.getBasePositionAndOrientation(self.id)
        obs = np.zeros(20)  # 20维 obs：你可以按需补充其他维度
        obs[:2] = np.array(pos[:2])
        self.obs_buffer.append(obs)

    def get_obs_sequence(self):
        if len(self.obs_buffer) < 2:
            # 用当前帧重复填充
            return np.stack([self.obs_buffer[-1]] * 2)
        return np.stack(self.obs_buffer)

