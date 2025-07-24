# protocol.py

import time
import numpy as np
import pybullet as p

class Protocol:
    def __init__(self, agents, task_name_map, task_pool, task_type_map):
        self.agents = agents
        self.task_name_map = task_name_map
        self.task_pool = task_pool
        self.task_type_map = task_type_map
        
        self.sync_sent = set()
        self.claims = []  # List of all task claims (agent, task, priority)
        self.outcomes = {}  # Mapping from task ID to assigned agent name
        self.ack_registry = {}  # Mapping from task_id to a set of agent names that acknowledged assistance
        self.assist_requests = []  # List of assistance request messages
        self.msg_queue = {name: [] for name in agents}  # Simulated message queue for each agent
        self.sync_requires_reach = False # Check whether sync_agents require reaching same position

    def receive_claims(self):
        """Collects task claims from agents."""
        self.claims.clear()
        for name, agent in self.agents.items():
            if agent.task is not None:
                self.claims.append((name, agent.task, agent.priority))
                print(f"[CLAIM] {name} claims {self.task_name_map[agent.task]} (priority {agent.priority})")

    def evaluate_conflicts(self):
        """Evaluates conflicts between multiple claims and selects winners."""
        claim_dict = {}
        for name, task, priority in self.claims:
            claim_dict.setdefault(task, []).append((priority, name))

        for task, entries in claim_dict.items():
            entries.sort(reverse=True)   # Higher priority number means higher priority
            winner = entries[0][1]
            self.outcomes[task] = winner

    def resolve_outcomes(self):
        """Finalizes the outcomes of task assignments."""
        task_assigned = set()
        for task, winner in self.outcomes.items():
            if task in task_assigned:
                continue
            agent = self.agents[winner]
            if agent.task == task:
                print(f"[ACCEPTED] {winner}'s claim for {self.task_name_map[task]}")
                task_assigned.add(task)
            else:
                print(f"[REJECTED] {winner}'s claim for {self.task_name_map[task]}")

        return len(task_assigned) == len(self.agents)

    def send(self, receiver_name, msg):
        """Sends a message to a specified agent."""
        if receiver_name in self.msg_queue:
            self.msg_queue[receiver_name].append((time.time(), msg))

    def recv(self, receiver_name):
        """Retrieves all messages for a given agent."""
        return [msg for ts, msg in self.msg_queue.get(receiver_name, [])]

    def cleanup_expired_messages(self, ttl=3.0):
        """Cleans up expired messages based on a time-to-live (TTL)."""
        now = time.time()
        for name in self.msg_queue:
            self.msg_queue[name] = [
                (ts, msg) for ts, msg in self.msg_queue[name] if now - ts <= ttl
            ]
        self.assist_requests = [
            r for r in self.assist_requests if now - r.get("timestamp", now) <= r.get("ttl", ttl)
        ]

    def get_pending_assist_requests(self):
        """Returns active cooperative task assist requests."""
        return [
            r for r in self.assist_requests
            if self.task_type_map.get(r["task_id"]) == "cooperative"
        ]

    def get_task_priority(self, task_id):
        """Returns the current priority of the task based on agent claims."""
        for agent in self.agents.values():
            if agent.task == task_id:
                return agent.priority
        return 999

    def create_request_assist(self, sender, task_id, urgency=1, ttl=3.0):
        """Creates an assistance request message."""
        return {
            "type": "request_assist",
            "sender": sender,
            "task_id": task_id,
            "urgency": urgency,
            "timestamp": time.time(),
            "ttl": ttl
        }

    def record_ack_assist(self, task_id, agent_name):
        """Records an agent's agreement to assist with a task."""
        self.ack_registry.setdefault(task_id, set()).add(agent_name)

    def get_assist_request_sender(self, task_id):
        """Returns the sender of the assist request for a given task."""
        for r in self.assist_requests:
            if r["task_id"] == task_id:
                return r["sender"]
        return None

    def get_assist_group(self, task_id):
        """Returns a list of agent names who are ready to synchronize on the task."""
        return [
            a.name for a in self.agents.values()
            if a.task == task_id and (a.waiting_for_sync or a.sync_start)
        ]
    def get_assisted_tasks(self):
        """Returns a set of task_ids that currently have active assist requests."""
        return {r["task_id"] for r in self.assist_requests if self.task_type_map.get(r["task_id"]) == "cooperative"}

    def is_ready_for_sync(self, task_id):
        """Checks whether a task has enough agents ready to start execution."""
        group = self.get_assist_group(task_id)
        return len(group) >= 2 and all(self.agents[name].reached_goal for name in group)
    
    def get_agent_obs(self, agent, task_obj_id):
        """Returns a low-dimensional observation vector for the agent and its target task."""
        if task_obj_id is None:
            print(f"[ERROR] get_agent_obs called with None task for {agent.name}")
            return np.zeros(2)  # or return None
        agent_pos, _ = p.getBasePositionAndOrientation(agent.id)
        agent_vel, _ = p.getBaseVelocity(agent.id)
        obj_pos, _ = p.getBasePositionAndOrientation(task_obj_id)
        obj_vel, _ = p.getBaseVelocity(task_obj_id)

        agent_cos, agent_sin = 1.0, 0.0  # Placeholder for orientation
        task_name = agent.task_name_map[task_obj_id]
        obj_idx = int(task_name.split("_")[1])
        one_hot = np.zeros(8)
        one_hot[obj_idx] = 1.0

        obs = np.concatenate([
            agent_pos[:2], agent_vel[:2],
            obj_pos[:2], obj_vel[:2],
            [agent_cos, agent_sin, 0.0, 0.0],
            one_hot
        ])
        return np.stack([obs, obs])

    def handle_assist_requests(self):
        """Processes incoming assist requests and manages sync start logic."""
        if not hasattr(self, "sync_sent"):
            self.sync_sent = set()

        for msg in self.get_pending_assist_requests():
            task_id = msg["task_id"]
            sender = msg["sender"]

            # Already enough helpers?
            helpers = [
                a for a in self.agents.values()
                if a.task == task_id and a.assisting
            ]
            if len(helpers) >= 2:
                continue

            if task_id in self.sync_sent:
                continue  # Already sync-started

            for agent in self.agents.values():
                if agent.name == sender:
                    continue
                if agent.task is None and agent.assist_task_id is not None:
                    continue  
                if agent.reached_goal or agent.assisting or agent.sync_start or agent.waiting_for_sync:
                    continue
                if self.task_type_map.get(agent.task) in ["cooperative", "urgent"]:
                    continue  

                # Priority check
                sender_prio = self.get_task_priority(task_id)
                my_prio = self.get_task_priority(agent.task)
                if my_prio < sender_prio:
                    continue

                print(f"[ASSIST] {agent.name} assists {sender} on {self.task_name_map[task_id]}")
                agent.backup_task = agent.task  
                agent.task = task_id           
                agent.assist_task_id = task_id
                agent.assisting = True
                agent.waiting_for_sync = True
                agent.sync_start = False
                agent.started = False
                agent.reached_goal = False

                self.record_ack_assist(task_id, agent.name)

        # === check if we can sync-start===
        for task_id, agents_ready in self.ack_registry.items():
            if task_id in self.sync_sent:
                continue

            agents_ready = set(agents_ready)
            requester = self.get_assist_request_sender(task_id)
            if requester:
                agents_ready.add(requester)

            if len(agents_ready) < 2:
                continue

            if getattr(self, "sync_requires_reach", True):
                if not all(self.agents[name].reached_goal for name in agents_ready):
                    continue

            for name in agents_ready:
                self.agents[name].sync_start = True
                self.agents[name].waiting_for_sync = False
            self.sync_sent.add(task_id)
            print(f"[SYNC-START] Task {self.task_name_map[task_id]}: {[name for name in agents_ready]}")

