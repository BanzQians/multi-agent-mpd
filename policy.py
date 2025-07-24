# policy.py
import numpy as np
import pybullet as p
import random
from strategy.dp_wrapper import DiffusionPolicyWrapper

class BasePolicy:
    def choose(self, agent, task_pool):
        raise NotImplementedError("Subclasses must implement choose() method")

class NearestTaskPolicy:
    def __init__(self):
        pass

    def choose(self, agent, task_pool):
        """
        Choose the nearest task based on Euclidean distance.
        """
        if not task_pool:
            return None
        agent_pos, _ = p.getBasePositionAndOrientation(agent.id)
        distances = {
            obj_id: np.linalg.norm(
                np.array(p.getBasePositionAndOrientation(obj_id)[0]) - np.array(agent_pos)
            ) for obj_id in task_pool
        }
        return min(distances, key=distances.get)

    def predict_action(self, agent):
        """
        Generate a simple linear movement towards the target.
        Args:
            agent: an Agent instance with .id and .task
        Returns:
            actions: np.ndarray of shape (8, 2) — repeated identical direction steps
        """
        if agent.task is None:
            print(f"[WARN] {agent.name} has no task assigned.")
            return np.zeros((8, 2))  # No task → stay still

        task_id = agent.get_effective_task()
        if task_id is None:
            print(f"[ERROR] {agent.name} has no effective task!")
            return np.zeros((8, 2))

        agent_pos, _ = p.getBasePositionAndOrientation(agent.id)
        task_pos, _ = p.getBasePositionAndOrientation(task_id)

        agent_xy = np.array(agent_pos[:2])
        obj_xy = np.array(task_pos[:2])
        delta = obj_xy - agent_xy
        norm = np.linalg.norm(delta)
        direction = delta / norm if norm > 1e-5 else np.zeros_like(delta)

        step = direction * 0.05  # max step size
        actions = np.tile(step, (8, 1))

        # print(f"[DEBUG] {agent.name} | pos: {agent_xy}, target: {obj_xy}, step: {step}")

        return actions


class DiffusionPolicyStub(BasePolicy):
    def choose(self, agent, task_pool):
        """
        Dummy task selection: randomly choose one from task_pool.
        """
        if not task_pool:
            return None
        return random.choice(task_pool)

class DiffusionPolicyWrapperAdapter(BasePolicy):
    def __init__(self, ckpt_path):
        self.model = DiffusionPolicyWrapper(ckpt_path)

    def choose(self, agent, task_pool):
        """
        Placeholder task selection — future DP-based selection logic can go here.
        """
        return random.choice(task_pool)

    def predict_action(self, obs_dict):
        """
        Predict actions based on observation using Diffusion Policy.
        Args:
            obs_dict: {'obs': np.ndarray of shape (2, 20)}
        Returns:
            np.ndarray of shape (8, 2)
        """
        return self.model.predict(obs_dict)



