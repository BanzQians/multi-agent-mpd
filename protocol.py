# protocol.py

import time
import numpy as np
import pybullet as p

class Protocol:
    def __init__(self, agents, task_name_map, task_pool):
        self.agents = agents
        self.task_pool = task_pool
        self.task_name_map = task_name_map
        self.claims = []
        self.responses = []
        self.assigned_tasks = set()

    def receive_claims(self):
        self.claims.clear()
        for agent in self.agents.values():
            if not agent.success and agent.task:
                self.claims.append({
                    "sender": agent.name,
                    "task": agent.task,
                    "priority": agent.priority,
                    "timestamp": time.time()
                })
                print(f"[CLAIM] {agent.name} claims {self.task_name_map[agent.task]} (priority {agent.priority})")

    def evaluate_conflicts(self):
        self.responses.clear()
        grouped_claims = {}

        for msg in self.claims:
            grouped_claims.setdefault(msg["task"], []).append(msg)

        for task_id, claim_list in grouped_claims.items():
            # Sort by priority then distance
            claim_list.sort(key=lambda m: (m["priority"], self._distance(m["sender"], task_id)))
            winner = claim_list[0]["sender"]

            for msg in claim_list:
                result = "accepted" if msg["sender"] == winner else "rejected"
                self.responses.append({
                    "to": msg["sender"],
                    "task": task_id,
                    "result": result
                })

    def resolve_outcomes(self):
        all_success = True
        for agent in self.agents.values():
            if agent.success:
                continue

            if not agent.task:
                print(f"[FAIL] {agent.name} has no task to claim — possibly no available task left.")
                all_success = False
                continue

            # Check if task is already assigned
            if agent.task in self.assigned_tasks:
                print(f"[REJECTED] {agent.name}'s claim for {self.task_name_map[agent.task]} — task already assigned.")
                agent.success = False
                agent.priority += 1
                agent.assign_task(exclude_list=[agent.task])
                all_success = False
                continue

            outcome = next((r for r in self.responses if r["to"] == agent.name and r["task"] == agent.task), None)

            if outcome is None:
                # Fallback: no response, assume accepted if task not taken
                taken = any(
                    a.name != agent.name and a.task == agent.task and a.success
                    for a in self.agents.values()
                )
                agent.success = not taken
                if agent.success:
                    print(f"[ASSUME] {agent.name} assumes claim success for {self.task_name_map[agent.task]}")
            else:
                agent.success = (outcome["result"] == "accepted")
                status = "ACCEPTED" if agent.success else "REJECTED"
                print(f"[{status}] {agent.name}'s claim for {self.task_name_map[agent.task]}")

            if agent.success:
                self.assigned_tasks.add(agent.task)
                if agent.task in self.task_pool:
                    self.task_pool.remove(agent.task)
            else:
                agent.priority += 1
                agent.assign_task(exclude_list=[agent.task])
                all_success = False

        return all_success


    def _distance(self, agent_name, task_id):
        agent = self.agents[agent_name]
        agent_pos, _ = p.getBasePositionAndOrientation(agent.id)
        task_pos, _ = p.getBasePositionAndOrientation(task_id)
        return np.linalg.norm(np.array(agent_pos) - np.array(task_pos))
