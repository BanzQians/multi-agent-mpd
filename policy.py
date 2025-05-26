# policy.py

import numpy as np
import pybullet as p
import random

class BasePolicy:
    def choose(self, agent, task_pool):
        raise NotImplementedError

class NearestTaskPolicy(BasePolicy):
    def choose(self, agent, task_pool):
        if not task_pool:
            return None
        agent_pos, _ = p.getBasePositionAndOrientation(agent.id)
        distances = {
            obj_id: np.linalg.norm(np.array(p.getBasePositionAndOrientation(obj_id)[0]) - np.array(agent_pos))
            for obj_id in task_pool
        }
        return min(distances, key=distances.get)

class DiffusionPolicyStub(BasePolicy):
    def choose(self, agent, task_pool):
        # 模拟一个策略：随机 + 特征依赖
        if not task_pool:
            return None
        # 比如以后会根据 agent 的状态 / 历史动作 / 编码输入做预测
        return random.choice(task_pool)