import sys
sys.path.insert(0, "./dp_repo")

import pybullet as p
import pybullet_data
import time
import numpy as np
from agent import Agent
from protocol import Protocol
from policy import NearestTaskPolicy, DiffusionPolicyStub, DiffusionPolicyWrapperAdapter
from task_conflict_gen import assign_conflicting_tasks
from pathlib import Path

# === Simulation Setup ===
p.connect(p.GUI)
p.setAdditionalSearchPath(pybullet_data.getDataPath())
p.setGravity(0, 0, -9.8)
planeId = p.loadURDF("plane.urdf")

# Create task objects
num_objects = 3
object_ids = []
task_name_map = {}

for i in range(num_objects):
    pos = np.random.uniform(low=[-2, -2, 0.5], high=[2, 2, 0.5])
    obj_id = p.loadURDF("cube_small.urdf", pos)
    object_ids.append(obj_id)
    task_name_map[obj_id] = f"cube_{i}"

task_pool = object_ids.copy()

task_type_map = {
    object_ids[0]: "cooperative",
    object_ids[1]: "urgent",
    object_ids[2]: "solo"
}

agent_starts = {
    "agent1": [0, -1, 0.5],
    "agent2": [0, 1, 0.5],
    "agent3": [-1, 0, 0.5]
}

agent_orientation = p.getQuaternionFromEuler([0, 0, 0])
agents = {}

# ckpt_path = Path("dp_repo/data/outputs/2025.06.04/20.16.23_train_diffusion_unet_lowdim_pybullet_mcp_lowdim/checkpoints/epoch=0150-test_mean_score=0.098.ckpt").resolve()
# policy = DiffusionPolicyWrapperAdapter(str(ckpt_path))
policy = NearestTaskPolicy()

for name, pos in agent_starts.items():
    uid = p.loadURDF("r2d2.urdf", pos, agent_orientation)
    agents[name] = Agent(name, uid, task_name_map, policy, task_type_map)
    agents[name].reached_goal = False
    agents[name].ready_to_start = False
    agents[name].started = False

# === Let objects settle ===
for _ in range(100):
    p.stepSimulation()
    time.sleep(1./240)

# Distribute initial tasks
assign_conflicting_tasks(agents, task_pool, task_name_map, conflict_ratio=0.8)

# === Coordination Loop via Protocol ===
protocol = Protocol(agents, task_name_map, task_pool)

max_retries = 3
for attempt in range(max_retries):
    print(f"\n=== Attempt #{attempt} ===")
    protocol.receive_claims()
    protocol.evaluate_conflicts()
    success = protocol.resolve_outcomes()
    if success:
        print("[SUCCESS] All agents assigned.")
        break

# === 协作机制辅助函数 ===
stuck_threshold = 0.01
stuck_history_len = 10
assist_ttl = 3.0

agent_position_history = {name: [] for name in agents}
assisted_tasks = set()
assisted_agents = set()

sync_distance = 0.2

sync_started = set()

sync_messages = []  # 可选: 用于扩展 sync 协议的消息缓存

def update_agent_stuck_state(agent, current_xy):
    pos_list = agent_position_history[agent.name]
    pos_list.append(current_xy)
    if len(pos_list) > stuck_history_len:
        pos_list.pop(0)

def is_agent_stuck(agent, target_xy, reach_threshold=0.1):
    """
    Returns True if the agent is not near the target and has not moved significantly.
    """
    pos_list = agent_position_history[agent.name]
    if len(pos_list) < stuck_history_len:
        return False

    # 判断是否在目标附近
    current_pos = pos_list[-1]
    if np.linalg.norm(current_pos - target_xy) < reach_threshold:
        return False  # Near goal → not stuck

    # 判断位置变化是否过小（连续多帧）
    diffs = [np.linalg.norm(pos_list[i+1] - pos_list[i]) for i in range(len(pos_list)-1)]
    if all(d < stuck_threshold for d in diffs):
        return True  # 远离目标 + 静止 → 是 stuck

    return False


def detect_and_send_assist(agent, protocol):
    if agent.task is None or agent.name in assisted_agents or agent.reached_goal:
        return
    
    target_xy = np.array(p.getBasePositionAndOrientation(agent.task)[0][:2])
    if is_agent_stuck(agent, target_xy, reach_threshold):
        existing = any(r["sender"] == agent.name and r["task"] == agent.task for r in protocol.assist_requests)
        if not existing:
            msg = protocol.create_request_assist(agent.name, agent.task, urgency=1, ttl=assist_ttl)
            protocol.assist_requests.append(msg)
            assisted_agents.add(agent.name)
            print(f"[HELP REQUEST] {agent.name} is stuck — requesting assist for {task_name_map[agent.task]}")


def handle_assist_requests(protocol, agents):
    for agent in agents.values():
        messages = protocol.recv(agent.name)
        for msg in messages:
            if msg["type"] == "request_assist":
                task_id = msg["task_id"]
                from_agent = msg["from"]
                if agent.task is None or agent.reached_goal:
                    # 优先响应协助请求
                    print(f"[ASSIST] {agent.name} assigned to assist {from_agent} on {task_name_map[task_id]}")
                    agent.task = task_id
                    agent.reached_goal = False
                    agent.started = False
                    agent.ready_to_start = False
                    assisted_tasks.add(task_id)
                    agent.task_type_map[task_id] = "cooperative"
                    # 自动清除 stuck 状态
                    agent.stuck_count = 0
                    agent.stuck_pos = None


def send_sync_if_ready(agents, protocol):
    # 收集每个任务有哪些 agent 已准备好
    task_to_agents = {}

    for agent in agents.values():
        if agent.task is None:
            continue

        is_coop = agent.task in agent.task_type_map and agent.task_type_map[agent.task] == "cooperative"
        if agent.task in assisted_tasks or is_coop:
            if agent.reached_goal:
                task_to_agents.setdefault(agent.task, []).append(agent)

    for task_id, group in task_to_agents.items():
        if len(group) >= 2:
            # 至少两个 agent 到达协作任务，发 sync_start 给所有 agent
            for agent in group:
                if not agent.ready_to_start:
                    protocol.send(agent.name, {
                        "type": "sync_start",
                        "task_id": task_id
                    })
                    agent.ready_to_start = True
            print(f"[SYNC] Sent sync_start to agents for task {task_name_map[task_id]}")



# === Execute Simulation ===
def get_obs_for_agent(agent, task_obj_id):
    agent_pos, _ = p.getBasePositionAndOrientation(agent.id)
    agent_vel, _ = p.getBaseVelocity(agent.id)
    obj_pos, _ = p.getBasePositionAndOrientation(task_obj_id)
    obj_vel, _ = p.getBaseVelocity(task_obj_id)
    agent_cos, agent_sin = 1.0, 0.0
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

MAX_STEP_SIZE = 0.01
reach_threshold = 0.1

print("\n=== [DEBUG] Task Type Map ===")
for obj_id, task_type in task_type_map.items():
    print(f"  - {task_name_map[obj_id]}: {task_type}")
print("=============================\n")

# for _ in range(1000):
#     for agent in agents.values():
#         if agent.task is None:
#             continue

#         current_xy = np.array(p.getBasePositionAndOrientation(agent.id)[0][:2])
#         update_agent_stuck_state(agent, current_xy)
#         detect_and_send_assist(agent, protocol)

#         if agent.reached_goal:
#             continue

#         if agent.task is not None and not agent.reached_goal:
#              agent.target_pos = p.getBasePositionAndOrientation(agent.task)[0]

#         # 检查是否已达到目标附近
#         target_xy = np.array(p.getBasePositionAndOrientation(agent.task)[0][:2])
#         distance = np.linalg.norm(current_xy - target_xy)
#         if distance < reach_threshold:
#             agent.reached_goal = True

#         # === Get action ===
#         obs_vec = get_obs_for_agent(agent, agent.task).astype(np.float32)

#         if isinstance(agent.policy, NearestTaskPolicy):
#             actions = agent.policy.predict_action(agent)
#             step = actions[0]
#             norm = np.linalg.norm(step)
#             if norm > MAX_STEP_SIZE:
#                 step = step / norm * MAX_STEP_SIZE
#         else:
#             actions = agent.policy.predict_action({'obs': obs_vec})
#             predicted_target_xy = actions[0]
#             direction = predicted_target_xy - current_xy
#             norm = np.linalg.norm(direction)
#             step = direction / norm * MAX_STEP_SIZE if norm > MAX_STEP_SIZE else direction

#         new_pos_2d = current_xy + step
#         new_pos_3d = [new_pos_2d[0], new_pos_2d[1], p.getBasePositionAndOrientation(agent.id)[0][2]]

#         # 是否已收到同步开始指令（协作任务）
#         is_coop_task = agent.task_type_map.get(agent.task) == "cooperative"

#         # cooperative 任务才需要等待 sync_start；其他任务（包括被协助的）直接执行
#         if is_coop_task:
#             # 检查是否有多个 agent 拥有同一个 cooperative 任务
#             shared_agents = [
#                 a for a in agents.values()
#                 if a.task == agent.task and a.name != agent.name
#             ]

#             if not shared_agents:
#                 # 没有其他 agent 分配到这个任务，直接执行
#                 p.resetBasePositionAndOrientation(agent.id, new_pos_3d, agent_orientation)
#             else:
#                 # 否则按同步机制处理
#                 if not agent.ready_to_start:
#                     print(f"[WAITING] {agent.name} waiting for sync_start on {task_name_map[agent.task]}")
#                     continue
#                 if not agent.started:
#                     agent.started = True
#                     print(f"[START] {agent.name} begins executing shared task {task_name_map[agent.task]}")
#                 p.resetBasePositionAndOrientation(agent.id, new_pos_3d, agent_orientation)
#         else:
#             p.resetBasePositionAndOrientation(agent.id, new_pos_3d, agent_orientation)



#     handle_assist_requests(protocol, agents)
#     send_sync_if_ready(agents, protocol)
#     protocol.cleanup_expired_messages()

#     p.stepSimulation()
#     time.sleep(1. / 240)

for _ in range(1000):
    for agent in agents.values():
        if agent.task is None:
            continue

        current_xy = np.array(p.getBasePositionAndOrientation(agent.id)[0][:2])
        update_agent_stuck_state(agent, current_xy)
        detect_and_send_assist(agent, protocol)

        if agent.reached_goal:
            continue

        if agent.task is not None and not agent.reached_goal:
            agent.target_pos = p.getBasePositionAndOrientation(agent.task)[0]

        # 检查是否已达到目标附近
        target_xy = np.array(p.getBasePositionAndOrientation(agent.task)[0][:2])
        distance = np.linalg.norm(current_xy - target_xy)
        if distance < reach_threshold:
            agent.reached_goal = True
            print(f"[REACHED] {agent.name} reached {task_name_map[agent.task]}")

        # === Get action ===
        obs_vec = get_obs_for_agent(agent, agent.task).astype(np.float32)

        if isinstance(agent.policy, NearestTaskPolicy):
            actions = agent.policy.predict_action(agent)
            step = actions[0]
            norm = np.linalg.norm(step)
            if norm > MAX_STEP_SIZE:
                step = step / norm * MAX_STEP_SIZE
        else:
            actions = agent.policy.predict_action({'obs': obs_vec})
            predicted_target_xy = actions[0]
            direction = predicted_target_xy - current_xy
            norm = np.linalg.norm(direction)
            step = direction / norm * MAX_STEP_SIZE if norm > MAX_STEP_SIZE else direction

        new_pos_2d = current_xy + step
        new_pos_3d = [new_pos_2d[0], new_pos_2d[1], p.getBasePositionAndOrientation(agent.id)[0][2]]

        # 协作判断逻辑
        is_coop_task = (
            agent.task in assisted_tasks or
            agent.task_type_map.get(agent.task) == "cooperative"
        )

        if is_coop_task:
            if not agent.ready_to_start:
                print(f"[WAITING] {agent.name} waiting for sync_start on {task_name_map[agent.task]}")
                continue
            if not agent.started:
                agent.started = True
                print(f"[START] {agent.name} begins executing shared task {task_name_map[agent.task]}")
        else:
            # 非协作任务直接开始
            if not agent.started:
                agent.started = True

        # 执行动作
        p.resetBasePositionAndOrientation(agent.id, new_pos_3d, agent_orientation)

    handle_assist_requests(protocol, agents)
    send_sync_if_ready(agents, protocol)
    protocol.cleanup_expired_messages()

    p.stepSimulation()
    time.sleep(1. / 240)

p.disconnect()

