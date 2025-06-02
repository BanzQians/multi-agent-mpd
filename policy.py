# policy.py

import numpy as np
import pybullet as p
import random

from strategy.dp_wrapper import DiffusionPolicyWrapper

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

class DiffusionPolicyWrapperAdapter(BasePolicy):
    def __init__(self, ckpt_path):
        self.model = DiffusionPolicyWrapper(ckpt_path)

    def choose(self, agent, task_pool):
        # 先做 dummy 选择，未来这里可用于基于 DP 的 task select（可跳过）
        return random.choice(task_pool)

    def predict_action(self, obs_dict):
        # n_obs_steps = 2
        # obs_dim = 20
        # obs_dict = {'obs': obs_vector.reshape(n_obs_steps, obs_dim)}

        return self.model.predict(obs_dict)  # 调用 dp_wrapper.py 中的 predict()


