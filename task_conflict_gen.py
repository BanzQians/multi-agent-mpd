# task_conflict_gen.py

import random

def assign_conflicting_tasks(agents, task_pool, task_name_map, conflict_ratio):
    """
    Assign conflicting and unique tasks to agents.
    conflict_ratio: proportion of agents assigned the same (conflicting) task
    """
    num_agents = len(agents)
    agents_list = list(agents.values())
    num_conflict_agents = int(num_agents * conflict_ratio)

    if not task_pool:
        print("[WARNING] Task pool is empty.")
        return

    # 1. Pick a conflict task
    conflict_task = random.choice(task_pool)
    print(f"[GEN] Conflict task selected: {task_name_map[conflict_task]}")

    # 2. Assign it to some agents
    conflict_agents = random.sample(agents_list, num_conflict_agents)
    for agent in conflict_agents:
        agent.task = conflict_task
        print(f"[ASSIGN] {agent.name} assigned conflicting task {task_name_map[conflict_task]}")

    # 3. Assign unique tasks to the rest
    remaining_agents = [a for a in agents_list if a not in conflict_agents]
    available_tasks = [t for t in task_pool if t != conflict_task]

    for agent, task in zip(remaining_agents, available_tasks):
        agent.task = task
        print(f"[ASSIGN] {agent.name} assigned task {task_name_map.get(task, 'None')}")

