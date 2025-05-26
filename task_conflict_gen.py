# task_conflict_gen.py

import random

def assign_conflicting_tasks(agents, task_pool, task_name_map, conflict_ratio=0.5):
    """
    在多个 agent 中制造部分任务冲突：
    - conflict_ratio 表示有多少比例的 agents 会分配到相同目标上
    - 比如 0.5 → 一半的 agent 会冲突，剩下正常分配
    """

    num_agents = len(agents)
    agents_list = list(agents.values())
    num_conflict_agents = int(num_agents * conflict_ratio)

    if not task_pool:
        print("[WARNING] Task pool is empty.")
        return

    # 1. 随机选一个任务作为“热点任务”
    conflict_task = random.choice(task_pool)
    print(f"[GEN] Conflict task selected: {task_name_map[conflict_task]}")

    # 2. 随机选一些 agent 去 claim 这个冲突任务
    conflict_agents = random.sample(agents_list, num_conflict_agents)
    for agent in conflict_agents:
        agent.task = conflict_task
        print(f"[ASSIGN] {agent.name} assigned conflicting task {task_name_map[conflict_task]}")

    # 3. 剩下的 agent 正常分配不冲突的任务（排除冲突任务）
    remaining_agents = [a for a in agents_list if a not in conflict_agents]
    available_tasks = [t for t in task_pool if t != conflict_task]

    for agent in remaining_agents:
        agent.set_task_pool(available_tasks)
        agent.assign_task()
        print(f"[ASSIGN] {agent.name} assigned task {task_name_map.get(agent.task, 'None')}")
    
    # 确保所有 agent 都能看到完整 task_pool（用于 retry）
    for agent in agents.values():
        agent.set_task_pool(task_pool)
