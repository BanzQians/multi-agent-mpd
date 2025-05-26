import numpy as np
import pybullet as p
from protocol import create_protocol_message, read_messages 
import time

__all__ = ["assign_task", "move_towards", "send_claim", "respond_to_claims"]

def score(agent, task_id):
    """
    计算agent执行某个任务的综合评分
    当前评分由：-距离 + 任务重要性（可扩展）组成
    """
    agent_pos, _ = p.getBasePositionAndOrientation(agent.id)
    task_pos, _ = p.getBasePositionAndOrientation(task_id)
    distance = np.linalg.norm(np.array(agent_pos) - np.array(task_pos))

    # 示例：任务重要性设置为1.0（未来可接入任务权重表）
    task_value = 1.0

    # 示例结构：- 距离 + 任务价值
    return -distance + 1.0 * task_value

class Agent:
    def __init__(self, name, agent_id, task_name_map):
        self.name = name
        self.id = agent_id
        self.task_name_map = task_name_map
        self.task = None
        self.success = False
        self.priority = 1
        self.task_pool = []  # at first is empty and wait for set_task_pool

    def set_task_pool(self, task_pool):
        self.task_pool = task_pool

    def assign_task(self, exclude_list=None):
        if exclude_list is None:
            exclude_list = []

        available = [obj_id for obj_id in self.task_pool if obj_id not in exclude_list]
        if not available:
            print(f"[WARNING] {self.name} cannot find available task, will skip assignment.")
            self.task = None
            return

        agent_pos, _ = p.getBasePositionAndOrientation(self.id)
        selected_task = min(
            available,
            key=lambda obj_id: np.linalg.norm(
                np.array(p.getBasePositionAndOrientation(obj_id)[0]) - np.array(agent_pos)
            )
        )
        self.task = selected_task

    def is_closest_to_task(self, task_id, agents):
        self_pos, _ = p.getBasePositionAndOrientation(self.id)
        self_dist = np.linalg.norm(np.array(p.getBasePositionAndOrientation(task_id)[0]) - np.array(self_pos))

        for other in agents.values():
            if other.name == self.name:
                continue
            if other.task == task_id:
                other_pos, _ = p.getBasePositionAndOrientation(other.id)
                other_dist = np.linalg.norm(np.array(p.getBasePositionAndOrientation(task_id)[0]) - np.array(other_pos))
                if other_dist < self_dist:
                    return False
        return True


    # Message Sending
    def send_claim(self, recipients, queue):
        if self.task is None:
            print(f"[SKIP] {self.name} has no task to claim.")
            return  # skip

        for target in recipients:
            msg = create_protocol_message(
                sender_id=self.name,
                receiver_id=target,
                task_id=self.task,
                msg_type="task_claim",
                priority=self.priority,
                response_required=True,
                valid_duration=5.0
            )
            queue.append(msg)
        print(f"{self.name} sends claim for: {self.task_name_map[self.task]} with priority {self.priority}")


    def respond_to_claims(self, queue, other_agents):
        inbox = read_messages(self.name, queue)
        latest_claims = {}
        responses = []

        for msg in inbox:
            if msg["msg_type"] != "task_claim":
                continue
            claimed_task = msg["task"]
            sender_priority = msg["priority"]
            if claimed_task not in latest_claims or sender_priority > latest_claims[claimed_task]["priority"]:
                latest_claims[claimed_task] = msg

        for msg in latest_claims.values():
            claimed_task = msg["task"]
            sender_priority = msg["priority"]

            response = create_protocol_message(
                sender_id=self.name,
                receiver_id=msg["sender"],
                task_id=claimed_task,
                msg_type="response",
                priority=1,
                response_required=False,
                valid_duration=3.0
            )

            if claimed_task == self.task:
                if self.evaluate_claim(msg, other_agents):
                    print(f"{self.name} yields {self.task_name_map[claimed_task]} to closer agent {msg['sender']}")
                    response["status"] = "accepted"
                    self.assign_task(exclude_list=[claimed_task])
                    print(f"{self.name} reassigns to: {self.task_name_map.get(self.task, 'None')}")
                else:
                    print(f"{self.name} keeps {self.task_name_map[claimed_task]}, rejects claim from {msg['sender']}")
                    response["status"] = "rejected"
            else:
                response["status"] = "accepted"

            queue.append(response)
            responses.append(response)
    
    def evaluate_claim(self, claimant_msg, other_agents):
        """
        比较当前智能体与另一个智能体对同一任务的评分，决定是否让步。
        claimant_msg: 来自其他Agent的claim消息
        other_agents: 所有agent的字典 {agent_name: Agent}
        """
        task_id = claimant_msg["task"]
        sender = claimant_msg["sender"]
        sender_agent = other_agents[sender]
        
        own_score = score(self, task_id)
        other_score = score(sender_agent, task_id)

        print(f"[SCORE] {self.name} score = {own_score:.2f}, {sender} score = {other_score:.2f}")

        return other_score > own_score  # 对方评分高，就让



