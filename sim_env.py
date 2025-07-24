import pybullet as p
import pybullet_data
import numpy as np

from agent import Agent
from protocol import Protocol
from policy import NearestTaskPolicy  # You can swap in DiffusionPolicy later
from task_conflict_gen import assign_conflicting_tasks

class SimEnv:
    def __init__(self, num_agents=3, num_objects=3):
        self.num_agents = num_agents
        self.num_objects = num_objects

        # === PyBullet setup ===
        p.connect(p.DIRECT)
        p.setAdditionalSearchPath(pybullet_data.getDataPath())
        p.setGravity(0, 0, -9.8)
        p.loadURDF("plane.urdf")

        # === Create task objects ===
        self.object_ids = []
        self.task_name_map = {}

        for i in range(num_objects):
            pos = np.random.uniform(low=[-2, -2, 0.5], high=[2, 2, 0.5])
            obj_id = p.loadURDF("cube_small.urdf", pos)
            self.object_ids.append(obj_id)
            self.task_name_map[obj_id] = f"cube_{i}"

        # === Assign task types ===
        self.task_type_map = {
            self.object_ids[0]: "cooperative",
            self.object_ids[1]: "urgent",
            self.object_ids[2]: "solo"
        }

        # === Create agents ===
        agent_starts = {
            "agent1": [0, -1, 0.5],
            "agent2": [0, 1, 0.5],
            "agent3": [-1, 0, 0.5]
        }
        agent_orientation = p.getQuaternionFromEuler([0, 0, 0])
        policy = NearestTaskPolicy()

        self.agents = {}
        for name, pos in list(agent_starts.items())[:num_agents]:
            uid = p.loadURDF("r2d2.urdf", pos, agent_orientation)
            self.agents[name] = Agent(name, uid, self.task_name_map, policy, self.task_type_map)

        # === Initialize protocol ===
        self.protocol = Protocol(self.agents, self.task_name_map, self.object_ids, self.task_type_map)

    def assign_tasks(self, conflict_ratio=0.8, max_retries=3):
        assign_conflicting_tasks(self.agents, self.object_ids.copy(), self.task_name_map, conflict_ratio)

        # === initialize agents priorities===
        fixed_weight = {
            "agent1": 0,
            "agent2": 2,
            "agent3": 5
        }

        for name, agent in self.agents.items():
            agent_xy = np.array(p.getBasePositionAndOrientation(agent.id)[0][:2])
            total_dist = 0.0
            for obj_id in self.object_ids:
                obj_xy = np.array(p.getBasePositionAndOrientation(obj_id)[0][:2])
                total_dist += np.linalg.norm(agent_xy - obj_xy)
            avg_dist = total_dist / len(self.object_ids)

            distance_score = avg_dist * 10  # index
            weight_score = fixed_weight.get(name, 0)
            agent.priority = int(distance_score + weight_score)

            agent.try_count = 0
            print(f"[INIT] {agent.name} priority={agent.priority:.1f} (dist={distance_score:.1f} + weight={weight_score})")

        for attempt in range(max_retries):
            print(f"\n=== Attempt #{attempt} ===")
            self.protocol.receive_claims()
            self.protocol.evaluate_conflicts()
            success = self.protocol.resolve_outcomes()

            if success:
                print("[SUCCESS] All agents assigned.")
                break

            for agent in self.agents.values():
                if agent.task not in self.protocol.outcomes:
                    continue
                winner = self.protocol.outcomes[agent.task]
                if winner != agent.name:
                    print(f"[REASSIGN] {agent.name} failed to get {self.task_name_map.get(agent.task, 'None')} → reselecting task")
                    
                    # === increase priority ===
                    agent.try_count += 1
                    agent.priority += 5  
                    print(f"[BOOST] {agent.name} priority increased to {agent.priority} (attempt {agent.try_count})")

                    # === reassign task ===
                    agent.task = None
                    claimed_tasks = set(self.protocol.outcomes.keys())
                    used_by_others = {t for t, w in self.protocol.outcomes.items() if w != agent.name}
                    available_tasks = [t for t in self.object_ids if t not in used_by_others]

                    if available_tasks:
                        new_task = agent.policy.choose(agent, available_tasks)
                        if new_task:
                            agent.task = new_task
                            print(f"[REASSIGN] {agent.name} → new task {self.task_name_map[new_task]}")


    def step(self):
        self.protocol.cleanup_expired_messages()
        self.protocol.handle_assist_requests()

        for agent in self.agents.values():
            # === Auto trigger cooperative assist request if not already sent ===
            if agent.reached_goal:
                continue

            if self.task_type_map.get(agent.task) == "cooperative":
                already_requested = any(r["sender"] == agent.name and r["task_id"] == agent.task
                                        for r in self.protocol.assist_requests)
                if not already_requested:
                    if self.protocol.get_assist_request_sender(agent.task) is None:
                        assist_msg = self.protocol.create_request_assist(agent.name, agent.task)
                        self.protocol.assist_requests.append(assist_msg)
                        print(f"[AUTO-ASSIST] {agent.name} initiated assist for {self.task_name_map[agent.task]}")

            agent.update(self.protocol)

        # Remove tasks that were not accepted in conflict resolution
        for agent in self.agents.values():
            # If task is assisting then skip
            if agent.assisting:
                continue

            accepted = any(
                winner == agent.name and agent.task == task
                for task, winner in self.protocol.outcomes.items()
            )
            if not accepted:
                agent.task = None

        # for agent in self.agents.values():
        #     print(f"[STATE] {agent.name} task={agent.task}, assist={agent.assist_task_id}, assisting={agent.assisting}, started={agent.started}")

        p.stepSimulation()

    def close(self):
        p.disconnect()
