# agent.py

import pybullet as p
import numpy as np

class Agent:
    def __init__(self, name, uid, task_name_map, policy, task_type_map):
        self.name = name
        self.id = uid
        self.task_name_map = task_name_map
        self.policy = policy
        self.task_type_map = task_type_map

        # === Task-related state ===
        self.task = None
        self.priority = 0
        self.reached_goal = False
        self.ready_to_start = False
        self.started = False
        self.waiting_for_sync = False
        self.sync_start = False
        self.assisting = False
        self.assist_task_id = None
        self.backup_task = None
        self.priority = 0  
        self.initial_priority = 0  
        self.claim_attempts = 0  

        # === Motion-related info ===
        self.target_pos = None
        self.prev_pos = None
        self.position_buffer = []
        self.stuck_cooldown = 0

        # === Logging/debugging ===
        self.last_log = None
        self.last_debug_key = None

    def reset(self):
        self.task = None
        self.priority = 0
        self.reached_goal = False
        self.ready_to_start = False
        self.started = False
        self.waiting_for_sync = False
        self.sync_start = False
        self.assisting = False
        self.target_pos = None
        self.prev_pos = None
        self.position_buffer.clear()
        self.stuck_cooldown = 0
        self.last_log = None
        self.last_debug_key = None
        self.assist_task_id = None

    def __repr__(self):
        return f"Agent({self.name}, Task={self.task_name_map.get(self.task, 'None')}, Prio={self.priority})"

    def distance_to_target(self):
        if self.target_pos is None:
            return float('inf')
        current_pos = np.array(self.prev_pos[:2]) if self.prev_pos is not None else np.zeros(2)
        return np.linalg.norm(current_pos - np.array(self.target_pos[:2]))
    
    def get_effective_task(self):
        return self.task or self.assist_task_id

    def update(self, protocol):
        # print(f"[DEBUG] update: {self.name} | task={self.task}, assist={self.assist_task_id}, backup={self.backup_task}, assisting={self.assisting}, reached={self.reached_goal}")

        prev_task = self.task
        prev_assist = self.assist_task_id

        effective_task = self.task or self.assist_task_id
        if effective_task is None:
            if self.task is None and self.assist_task_id is not None:
                print(f"[BUG] {self.name} has assist_task_id={self.assist_task_id} but task=None — likely assist logic incomplete")
            if self.task is None and not self.assisting:
                print(f"[BUG] {self.name} has no task and is not assisting — task was likely lost silently")
            return

        # === Get current position ===
        current_xy = np.array(p.getBasePositionAndOrientation(self.id)[0][:2])
        self.prev_pos = current_xy
        self.position_buffer.append(current_xy)
        if len(self.position_buffer) > 10:
            self.position_buffer.pop(0)

        # === Get target position ===
        self.target_pos = np.array(p.getBasePositionAndOrientation(effective_task)[0][:2])
        distance = np.linalg.norm(current_xy - self.target_pos)

        if distance < 0.1:
            print(f"[REACHED] {self.name} reached {self.task_name_map.get(effective_task)} (assist={self.assisting})")
            
            if self.assisting:
                print(f"[RESUME] {self.name} finished assist. Resuming original task.")
                if self.backup_task is not None:
                    self.task = self.backup_task
                else:
                    print(f"[WARN] {self.name} has no backup_task after assist!")
                    self.task = None
                self.backup_task = None
                self.assisting = False
                self.assist_task_id = None
                self.sync_start = False
                self.started = False
                self.reached_goal = False
            else:
                self.reached_goal = True
            return

        # === Determine task type ===
        is_coop_task = (
            effective_task in protocol.get_assisted_tasks() or
            self.task_type_map.get(effective_task) == "cooperative"
        )

        # === Execution logic ===
        if is_coop_task:
            if not self.sync_start:
                if self.last_log != "waiting":
                    print(f"[WAITING] {self.name} waiting for sync_start on {self.task_name_map.get(effective_task)}")
                    self.last_log = "waiting"
                return
            if not self.started:
                self.started = True
                print(f"[START] {self.name} begins executing shared task {self.task_name_map.get(effective_task)}")
                self.last_log = "started"
        else:
            if not self.started:
                self.started = True
                print(f"[START] {self.name} begins solo/urgent task {self.task_name_map.get(effective_task)}")
                self.last_log = "started"

        # === Get action from policy ===
        obs = protocol.get_agent_obs(self, effective_task)
        if hasattr(self.policy, "predict_action"):
            try:
                actions = self.policy.predict_action({'obs': obs}) if isinstance(obs, dict) else self.policy.predict_action(self)

                if isinstance(actions, np.ndarray):
                    step = actions[0] if actions.ndim == 2 else actions
                elif isinstance(actions, (list, tuple)):
                    step = np.array(actions[0]) if isinstance(actions[0], (list, tuple, np.ndarray)) else np.array(actions)
                else:
                    step = np.array([0.0, 0.0])

                norm = np.linalg.norm(step)
                step = step / norm * 0.01 if norm > 0.001 else np.zeros(2)

            except Exception as e:
                print(f"[ERROR] {self.name} failed to compute action: {e}")
                step = np.zeros(2)
        else:
            print(f"[ERROR] {self.name} policy has no predict_action method")
            step = np.zeros(2)

        # === Apply movement ===
        new_pos = self.prev_pos + step
        if self.task != prev_task or self.assist_task_id != prev_assist:
            print(f"[TRACK] {self.name} task changed from {prev_task} → {self.task}, assist_task_id: {prev_assist} → {self.assist_task_id}")

        p.resetBasePositionAndOrientation(
            self.id,
            [float(new_pos[0]), float(new_pos[1]), p.getBasePositionAndOrientation(self.id)[0][2]],
            [0, 0, 0, 1]
        )
