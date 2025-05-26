import numpy as np
import pybullet as p

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

