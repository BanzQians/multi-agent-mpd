import pybullet as p
import pybullet_data
import time
import numpy as np
import json

# === Utility Functions ===
def move_towards(agent_id, target_pos, step_size=0.01):
    pos, _ = p.getBasePositionAndOrientation(agent_id)
    pos = np.array(pos)
    direction = np.array(target_pos) - pos
    norm = np.linalg.norm(direction)
    if norm > step_size:
        direction = direction / norm * step_size
    new_pos = pos + direction
    p.resetBasePositionAndOrientation(agent_id, new_pos.tolist(), agent_orientation)

def assign_task(agent_id, task_pool, exclude_list=None):
    if exclude_list is None:
        exclude_list = []
    agent_pos, _ = p.getBasePositionAndOrientation(agent_id)
    min_distance = float('inf')
    selected_task = None
    for obj_id in task_pool:
        if obj_id in exclude_list:
            continue
        obj_pos, _ = p.getBasePositionAndOrientation(obj_id)
        distance = np.linalg.norm(np.array(agent_pos) - np.array(obj_pos))
        if distance < min_distance:
            min_distance = distance
            selected_task = obj_id
    return selected_task

def create_protocol_message(sender_id, receiver_id, task_id, msg_type="task_claim", priority=1, response_required=True, valid_duration=5.0):
    return {
        "sender": sender_id,
        "receiver": receiver_id,
        "msg_type": msg_type,
        "task": task_id,
        "priority": priority,
        "response_required": response_required,
        "valid_until": time.time() + valid_duration,
        "status": "pending",
        "timestamp": time.time()
    }

def send_claim(sender_id, task_id, priority, recipients, queue):
    for target in recipients:
        msg = create_protocol_message(
            sender_id=sender_id,
            receiver_id=target,
            task_id=task_id,
            msg_type="task_claim",
            priority=priority,
            response_required=True,
            valid_duration=5.0
        )
        queue.append(msg)
    print(f"{sender_id} sends claim for: {task_name_map[task_id]} with priority {priority}")

def read_messages(receiver_id, queue):
    # agent scans the queue and read messages
    return [msg for msg in queue if msg["receiver"] == receiver_id]

def respond_to_claims(self_name, self_id, current_task, queue, task_pool):
    inbox = read_messages(self_name, queue)
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
            sender_id=self_id,
            receiver_id=msg["sender"],
            task_id=claimed_task,
            msg_type="response",
            priority=1,
            response_required=False,
            valid_duration=3.0
        )

        if claimed_task == current_task:
            if sender_priority > 1:
                print(f"{self_name} gives up {task_name_map[claimed_task]} to {msg['sender']} with higher priority ({sender_priority})")
                response["status"] = "accepted"
                current_task = assign_task(self_id, task_pool, exclude_list=[claimed_task])
                print(f"{self_name} reassigns to: {task_name_map[current_task]}")
            else:
                print(f"{self_name} keeps {task_name_map[claimed_task]}, rejects claim from {msg['sender']}")
                response["status"] = "rejected"
        else:
            response["status"] = "accepted"

        queue.append(response)
        responses.append(response)

    return current_task

def check_response(agent_id, task_id, queue):
    inbox = read_messages(agent_id, queue)
    for msg in inbox:
        if msg["msg_type"] == "response" and msg["task"] == task_id:
            if msg["status"] == "accepted":
                print(f"{agent_id}'s claim for {task_name_map[task_id]} was accepted")
                return True
            else:
                print(f"{agent_id}'s claim for {task_name_map[task_id]} was rejected by {msg['sender']}")
                return False
    print(f"{agent_id} received no response for task {task_name_map[task_id]}")
    return False

# === Simulation Setup ===
p.connect(p.GUI)
p.setAdditionalSearchPath(pybullet_data.getDataPath())
p.setGravity(0, 0, -9.8)
planeId = p.loadURDF("plane.urdf")

agent1_start = [0, -1, 0.5]
agent2_start = [0, 1, 0.5]
agent3_start = [-1, 0, 0.5]
agent_orientation = p.getQuaternionFromEuler([0, 0, 0])

agent1_id = p.loadURDF("r2d2.urdf", agent1_start, agent_orientation)
agent2_id = p.loadURDF("r2d2.urdf", agent2_start, agent_orientation)
agent3_id = p.loadURDF("r2d2.urdf", agent3_start, agent_orientation)

message_queue = []
num_objects = 3
object_ids = []
task_name_map = {}

for i in range(num_objects):
    pos = np.random.uniform(low=[-2, -2, 0.5], high=[2, 2, 0.5])
    obj_id = p.loadURDF("cube_small.urdf", pos)
    object_ids.append(obj_id)
    task_name_map[obj_id] = f"cube_{i}"

task_pool = object_ids.copy()

# === Agent: Task Claim Attempt ===

priority_start = 1
max_retries = 3

agent_state = {
    "agent1":  {"id": agent1_id,  "task": None, "success": False, "priority": priority_start},
    "agent2":  {"id": agent2_id,  "task": None, "success": False, "priority": priority_start},
    "agent3":  {"id": agent3_id,  "task": None, "success": False, "priority": priority_start},
}

for agent_name, state in agent_state.items():
    state["task"] = assign_task(state["id"], task_pool)

for attempt in range(max_retries):
    print(f"\n=== Attempt #{attempt} ===")
    
    # Phase 1: broadcast claims
    for sender_name, sender_state in agent_state.items():
        if not sender_state["success"]:
            receivers = [a for a in agent_state if a != sender_name]
            send_claim(sender_name, sender_state["task"], sender_state["priority"], receivers, message_queue)

    time.sleep(0.2)

    # Phase 2: process others' claims
    for agent_name, state in agent_state.items():
        state["task"] = respond_to_claims(agent_name, state["id"], state["task"], message_queue, task_pool)

    # Phase 3: check results
    all_success = True
    for agent_name, state in agent_state.items():
        if not state["success"]:
            state["success"] = check_response(agent_name, state["task"], message_queue)

        if state["success"]:
            if state["task"] in task_pool:
                task_pool.remove(state["task"])
        else:
            state["priority"] += 1
            state["task"] = assign_task(state["id"], task_pool, exclude_list=[state["task"]])
            all_success = False
    
    if all(state["success"] for state in agent_state.values()):
        break


# === Execute Simulation ===
agent1_target = p.getBasePositionAndOrientation(agent_state["agent1"]["task"])[0]
agent2_target = p.getBasePositionAndOrientation(agent_state["agent2"]["task"])[0]
agent3_target = p.getBasePositionAndOrientation(agent_state["agent3"]["task"])[0]
print(f"Agent1 target object id: {agent_state['agent1']['task']}, assigned: {task_name_map[agent_state['agent1']['task']]}")
print(f"Agent2 target object id: {agent_state['agent2']['task']}, assigned: {task_name_map[agent_state['agent2']['task']]}")
print(f"Agent3 target object id: {agent_state['agent3']['task']}, assigned: {task_name_map[agent_state['agent3']['task']]}")

for _ in range(1000):
    move_towards(agent1_id, agent1_target)
    move_towards(agent2_id, agent2_target)
    move_towards(agent3_id, agent3_target)
    p.stepSimulation()
    time.sleep(1./240)

p.disconnect()
