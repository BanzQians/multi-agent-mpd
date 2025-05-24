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

---

## 🔄 Phase 3: Response Handling & Negotiation Feedback (Day 5)

### 🗓️ Date: 2025-05-23

### ✅ Implemented Features

- 📡 **Structured Messaging Protocol Extended**:
  - Introduced additional fields into messages:
    - `msg_type`: "task_claim" or "response"
    - `response_required`: whether a reply is expected
    - `valid_until`: timestamp when message expires
    - `status`: "pending", "accepted", or "rejected"
    - `priority`, `timestamp`

- 🤖 **Agent2: Message Interpretation & Response**:
  - Reads task claims from agent1;
  - If agent2's target conflicts → returns `response: rejected`;
  - Otherwise → returns `response: accepted`.

- 📩 **Agent2 Response Messages**:
  - Appends response back to the global `message_queue`;
  - Each message carries full protocol-compliant content.

- 🧠 **Agent1: Response Parsing & Feedback**:
  - Reads `response` messages from inbox;
  - If claim was accepted → keeps current task;
  - If rejected (not occurred in current test) → can trigger reassignment in future.

- 🖨️ **Console Output** clearly reflects decision process:
Agent1 sends: task_claim for cube_2
Agent2 initially planned cube_0 → no conflict
Agent2 responds: accepted
✅ Agent1's claim for cube_2 was accepted

---

### 📈 System Status After Day 5

| Component                          | Status  |
|-----------------------------------|---------|
| Task claim protocol (message v2)  | ✅ Done |
| Validity & timestamp mechanism    | ✅ Done |
| Conflict detection & reply        | ✅ Done |
| Agent1 claim response parsing     | ✅ Done |
| Console-based traceability        | ✅ Done |

---

### 🔜 Coming in Day 6

- 🥇 Priority-based task arbitration (agent1 vs agent2);
- 🔁 Multi-round claim negotiation;
- ⏱️ Message timeouts & re-request;
- 📡 Simulated message filtering (by type / importance);
- 📦 Logging or exporting protocol history (for evaluation / paper).

---
🗓️ Day 6 Log - 多智能体结构化通信与任务协商机制实现

日期：2025年5月24日
关键词：任务冲突、优先级机制、通信结构优化、claim-response协议、Agent2主动让步
✅ 今日完成内容

    Agent1 多轮 claim 尝试机制

        最多 3 次尝试，优先级递增（从 1 → 3）。

        每次尝试发送 task_claim 消息，并等待 response。

        若接收 accepted，则任务确认；否则进入下一轮。

    Agent2 响应机制重构

        使用 read_messages() 读取全部 task_claim。

        对于每个任务，只响应优先级最高的那条 claim（防止重复响应）。

        若存在冲突：

            若 Agent1 优先级更高，Agent2 让步并重新选择任务；

            否则保留原任务，reject Agent1 的 claim。

        每条 claim 都发送相应 response 消息。

    消息结构改进

        所有 message 中使用 msg_type 字段区分 claim/response。

        增加 priority 和 valid_until 字段。

        使用 json.dumps 打印结构化日志。

    调试并解决逻辑 Bug

        修复 Agent1 无法接收到有效 response 导致连续尝试失败的问题。

        解决因重复处理 claim 导致多个 accepted 的问题。

        输出结构清晰，能够准确反映 claim → response → reassign 的完整过程。
