import pybullet as p
import pybullet_data
import time
import numpy as np
import json

p.connect(p.GUI) 
# p.connect(p.DIRECT) # no graph
p.setAdditionalSearchPath(pybullet_data.getDataPath())
p.setGravity(0, 0, -9.8)

# set the ground
planeId = p.loadURDF("plane.urdf")

# set agents
agent1_start = [0, -1, 0.5]
agent2_start = [0, 1, 0.5]
agent_orientation= p.getQuaternionFromEuler([0, 0, 0])

# load agents
agent1_id = p.loadURDF("r2d2.urdf", agent1_start, agent_orientation)
agent2_id = p.loadURDF("r2d2.urdf", agent2_start, agent_orientation)

# set Comm channel
message_queue = []

# set up objects
num_objects = 3
object_ids = []
task_name_map = {}

for i in range(num_objects):
    pos = np.random.uniform(low=[-2, -2, 0.5], high=[2, 2, 0.5])
    obj_id = p.loadURDF("cube_small.urdf", pos)
    object_ids.append(obj_id)
    task_name_map[obj_id] = f"cube_{i}" # add jection

# set up task pool
task_pool = object_ids.copy()
assigned_tasks = {}

# fundamental moving functions
def move_towards(agent_id, target_pos, step_size=0.01):
    # let robots directly move at first
    pos, _ = p.getBasePositionAndOrientation(agent_id)
    pos = np.array(pos)
    direction = np.array(target_pos) - pos
    norm = np.linalg.norm(direction)
    if norm > step_size:
        direction = direction / norm * step_size
    new_pos = pos + direction
    p.resetBasePositionAndOrientation(agent_id, new_pos.tolist(), agent_orientation)

def assign_task(agent_id,task_pool, exclude_list=None):
    # distribute tasks with  exclusion
    if exclude_list is None:
        exclude_list = []

    agent_pos, _  = p.getBasePositionAndOrientation(agent_id)
    min_distance = float('inf')
    seleceted_task = None
    for obj_id in task_pool:
        if obj_id in exclude_list:
            continue

        obj_pos, _ = p.getBasePositionAndOrientation(obj_id)
        distance = np.linalg.norm(np.array(agent_pos) - np.array(obj_pos))
        if distance < min_distance:
            min_distance = distance
            seleceted_task =obj_id
    return seleceted_task

def create_protocol_message(
    sender_id, receiver_id, task_id, msg_type="task_claim",
    priority=1, response_required=True, valid_duration=5.0
):
    return{
        "sender": sender_id,
        "receiver": receiver_id,
        "msg_type": msg_type,    # e.g., "task_claim", "response", "release"
        "task": task_id,
        "priority": priority,
        "response_required": response_required,
        "valid_until": time.time() + valid_duration,
        "status": "pending",    # or "accepted", "rejected"
        "timestamp": time.time()
    }

def read_messages(receiver_id, queue):
    # agent scans the queue and read messages
    inbox = []
    for msg in queue:
        if msg["receiver"] == receiver_id:
            inbox.append(msg)
    return inbox

# Agent1
max_retries = 3
claim_success = False
priority = 1
attempt = 0
agent1_task = assign_task(agent1_id, task_pool)

while attempt < max_retries and not claim_success:
    
    print(f"\n Agent1 attempt #{attempt} to claim {task_name_map[agent1_task]} with priority {priority}")

    msg1 = create_protocol_message(
        sender_id="agent1",
        receiver_id="agent2",
        task_id=agent1_task,
        msg_type="task_claim",
        priority=priority,
        response_required=True,
        valid_duration=5.0
    )
    message_queue.append(msg1)

    print("Agent1 sends:", json.dumps(msg1, indent=2))
    print("Which means: agent1 claims", task_name_map[agent1_task])

    # simulate delay
    time.sleep(0.2)

    # let agent2 react immediatly
    agent2_original_task = assign_task(agent2_id, task_pool)
    agent2_task = agent2_original_task
    print(f"Agent2 initially planned to take: {task_name_map[agent2_original_task]}")

    agent2_inbox = read_messages("agent2", message_queue)
    responses = []

    # select the highest priority whith  the latest claim
    latest_claims = {}
    for raw_msg in agent2_inbox:
        if time.time() > raw_msg["valid_until"]:
            continue

        if raw_msg["msg_type"] == "task_claim":
            claimed_task = raw_msg["task"]
            sender_priority = raw_msg["priority"]

            if claimed_task not in latest_claims or sender_priority > latest_claims[claimed_task]["priority"]:
                latest_claims[claimed_task] = raw_msg

    # response only once for each task
    for msg in latest_claims.values():
        claimed_task = msg["task"]
        sender_priority = msg["priority"]

        response = create_protocol_message(
            sender_id="agent2",
            receiver_id="agent1",
            task_id=claimed_task,
            msg_type="response",
            priority=1,
            response_required=False,
            valid_duration=3.0
        )

        if claimed_task == agent2_task:
            if sender_priority > 1:
                print(f"Conflict: agent2 also wants {task_name_map[claimed_task]}, but agent1 has higher priority ({sender_priority}). Giving up.")
                response["status"] = "accepted"
                agent2_task = assign_task(agent2_id, task_pool, exclude_list=[claimed_task])
                print(f"Agent2 reassigns to: {task_name_map[agent2_task]}")
            else:
                print(f"Conflict: agent2 keeps {task_name_map[claimed_task]} (priority too low). Rejecting.")
                response["status"] = "rejected"
        else:
            response["status"] = "accepted"

    message_queue.append(response)
    responses.append(response)

    #  check responses
    agent1_inbox = read_messages("agent1", message_queue)
    response_found = False

    for msg in agent1_inbox:
        if msg["msg_type"]  == "response" and msg["task"] == agent1_task:
            if msg["status"] == "accepted":
                print(f"Agent1's claim for {task_name_map[agent1_task]} was accepted")
                claim_success = True
                break
            elif msg["status"] == "rejected":
                print(f"Agent1's claim for {task_name_map[agent1_task]} was rehjected")
    if not claim_success:
        attempt += 1
        priority += 1 # increase the priority for the next round

if not claim_success:
    print(f"Agent1 failed to claim {task_name_map[agent1_task]} after {max_retries} attempts.")
else:
    if agent1_task in task_pool:
        task_pool.remove(agent1_task)

# Agent2
agent2_inbox = read_messages("agent2", message_queue)
claimed_task = [msg['task'] for msg in agent2_inbox]

# renew task pool
if agent2_task in task_pool:
    task_pool.remove(agent2_task)

# send a fianl claim
msg2 = create_protocol_message("agent2", "agent1", agent2_task)
message_queue.append(msg2)
print("Agent2 sends message:", msg2)
print("Which means: assigned task =", task_name_map[agent2_task])

for r in responses:
    print("Agent2 responds:", json.dumps(r, indent=2))

# acquire object positons
agent1_target = p.getBasePositionAndOrientation(agent1_task)[0]
agent2_target = p.getBasePositionAndOrientation(agent2_task)[0]
print(f"Agent1 target object id: {agent1_task}, assigned: {task_name_map[agent1_task]}")
print(f"Agent2 target object id: {agent2_task}, assigned: {task_name_map[agent2_task]}")


# simulation for a duration
for i in range(1000):
    move_towards(agent1_id, agent1_target)
    move_towards(agent2_id, agent2_target)
    p.stepSimulation()
    time.sleep(1./240)

p.disconnect()