import time

__all__ = ["create_protocol_message", "read_messages", "check_response"]

# Message Creation
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

# Inbox Reading 
def read_messages(receiver_id, queue):
    # agent scans the queue and read messages
    return [msg for msg in queue if msg["receiver"] == receiver_id]

# Response Checking 
def check_response(agent_id, task_id, queue, task_name_map, task_pool, agents):
    current_time = time.time()
    inbox = [msg for msg in read_messages(agent_id, queue) if msg["valid_until"] >= current_time]
    got_response = False

    for msg in inbox:
        if msg["msg_type"] == "response" and msg["task"] == task_id:
            got_response = True
            if msg["status"] == "accepted":
                print(f"{agent_id}'s claim for {task_name_map[task_id]} was accepted")
                return True
            else:
                print(f"{agent_id}'s claim for {task_name_map[task_id]} was rejected by {msg['sender']} (who holds {task_name_map[task_id]})")
                return False

    # No response then check whether available
    if not got_response:
        task_taken = any(
            other.name != agent_id and other.task == task_id
            for other in agents.values()
        )

        if not task_taken and task_id in task_pool:
            print(f"[INFO] {agent_id}'s claim for {task_name_map[task_id]} had no response, assuming accepted by default")
            return True
        else:
            print(f"[INFO] {agent_id}'s claim for {task_name_map[task_id]} had no response, but task was taken or invalid")
            return False





