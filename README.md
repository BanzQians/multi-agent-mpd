# Multi-Agent MPD System – 开发日志（Day 1–2）

### 🗓️ 日期：
2025年5月22日

---

## ✅ 目标阶段：Phase 0 – 基础仿真系统搭建

### 🎯 本阶段目标：
- 在 PyBullet 中搭建一个简单的多智能体仿真环境；
- 每个 agent 可以朝目标物体移动；
- 为后续任务协作与通信做准备。

---

## 🔧 已完成任务：

### ✅ 环境配置：
- Ubuntu + Python 3.8.10
- 创建 `venv_mpd` 虚拟环境并成功运行 PyBullet GUI
- 配置显卡驱动并解决图形显示问题

### ✅ PyBullet 场景搭建：
- 创建地面平面
- 加载两个 R2D2 机器人
- 随机生成三个目标方块（cube_small.urdf）

### ✅ 控制逻辑：
- 每个 agent 指定一个目标（object_ids[0], object_ids[1]）
- 实现 `move_towards()` 函数，实现 agent 逐步靠近目标
- 调整 step_size 控制移动速度

### ✅ debug 经验：
- 注意 URDF 文件名大小写敏感
- 明确使用 `getBasePositionAndOrientation(id)[0]` 仅获取位置
- 避免将 agent2 的控制目标误写为 agent1 的
- 学会使用 print 和可视化判断变量行为

---

## 🧠 收获与理解：
- 学会在 PyBullet 中手动控制物体移动；
- 理解了获取位置与设置位置的基本API；
- 建立了一个能演示 agent 行为的最小系统，为后续通信、策略、MPD构建打下基础。

---

## 📁 文件结构（初步）：
multi_agent_mpd/
│
├── main.py # 主仿真脚本
├── venv_mpd/ # Python 虚拟环境文件夹
├── README.md # 项目说明（建议新建）
└── utils/
└── comm.py # 后续通信结构模块（待开发）

---

## 🚀 下一步计划（Day 3）：

- 构建任务池结构；
- 实现最简单的目标分配机制；
- 准备通信消息结构：sender、receiver、priority、content等字段。

---

---

## 🧠 Phase 1: Task Assignment + Communication Structure (Day 3)

### 🗓️ Date: 2025-05-22

### ✅ New Features Implemented

- 📦 **Task Pool Initialization**:
  - Created a `task_pool` list based on the loaded target objects.
  - Maintained an `assigned_tasks` record to avoid reuse.

- 🤖 **Distance-Based Task Assignment**:
  - Implemented `assign_task()` function.
  - Each agent chooses the closest available task.

- 🚫 **Conflict Avoidance via Task Removal**:
  - Once a task is assigned, it is removed from the pool.
  - Ensures agents do not select the same task.

- 🧾 **Message Format Construction**:
  - Built a message dictionary structure for future communication:
    ```json
    {
      "sender": "agent1",
      "receiver": "agent2",
      "action": "assign",
      "task": <task_id>,
      "priority": 1,
      "timestamp": <float>
    }
    ```

- 🏷️ **Task Name Mapping**:
  - Introduced `task_name_map` to convert internal PyBullet object IDs to human-readable task names (`cube_0`, `cube_1`, etc.).

---

## 🧠 Phase 2: Communication & Conflict Resolution (Day 4)

### 🗓️ Date: 2025-05-22

### ✅ New Features Implemented

- 📨 **Message Queue**:
  - Simulated a global `message_queue` list.
  - Each agent can push structured messages into the queue.

- 📥 **Inbox Filtering**:
  - Implemented `read_messages(receiver_id, queue)` to extract relevant messages for each agent.

- 🔄 **Agent2 Dynamic Task Selection**:
  - Agent2 first selects a task based on proximity.
  - Then scans its inbox:
    - If another agent has already claimed the same task, agent2 will:
      - Print a conflict warning;
      - Reassign to the next best available task.
    - Otherwise, it confirms its initial choice.

- 📣 **Decision Trace Logging**:
  - Agent2 now logs its reasoning process:
    ```
    Agent2 initially planned to take: cube_1
    ⚠️ Conflict detected: cube_1 already claimed by agent1!
    Agent2 reassigns to: cube_0
    ```

---

### 📈 System Status Summary

| Module | Status |
|--------|--------|
| PyBullet simulation | ✅ Stable |
| Multi-agent + target system | ✅ Completed |
| Task assignment logic | ✅ Functional |
| Structured communication format | ✅ Implemented |
| Conflict detection & resolution | ✅ Working |
| Human-readable task tracing | ✅ Printed via `task_name_map` |

---

### 🔜 Next (Day 5 Plan)

- Introduce **message priorities**, **multi-step negotiation**, and **role-aware protocols**;
- Add support for **message filters**, delays, and **decision time window**;
- Begin preparing logs/visuals for **system explanation or publication**.

---
