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
        📘 Multi-Agent MCP Task Allocation - Development Log (Phase 2)

    重构日志：结构化通信系统模块化封装 + 冲突处理评分机制接入
    更新日期：2025年5月24日

🧱 基础结构变更
✅ 模块拆分

    protocol.py
    封装消息格式、收发逻辑与回应检查：

        create_protocol_message(...)

        read_messages(...)

        check_response(...)（支持“默认接受”机制）

    agent.py
    定义 Agent 类及其行为（发送claim、回应claim、重新分配等）：

        assign_task(...)

        send_claim(...)

        respond_to_claims(...)

        evaluate_claim(...)：引入评分机制

        set_task_pool(...)：任务池传入接口

        score(...)：计算 agent 对某任务的偏好评分（初始为 -距离）

⚙️ 通信与决策逻辑变更
🧠 协商机制优化

    引入更通用的任务评分函数 score(agent, task_id)：

        当前为 score = -distance + 任务价值（可拓展）

        所有 Agent 在回应冲突请求时，通过 evaluate_claim() 比较双方评分是否让步

    实现更合理的默认接受机制：

        若未收到任何回应但任务仍在池中且无人实际持有 → 默认 claim 成功

❗问题修复记录

    修复多个 Agent 同时 claim 同一任务但未全部收到回应时的逻辑混乱；

    解决 Agent.task_pool 多次传参与状态同步冲突；

    加入目标位置 target_pos 设置，避免重复调用 getPosition(...)；

    补充响应时的任务排他性检查，避免重复 assignment；

    加入判空判断，避免 task == None 时错误访问 task_name_map[None]。

📈 当前系统行为（示例）

    支持 3 个 Agent 同步参与任务 claim；

    每轮最大重试次数为 3，按优先级逐步提升；

    任务分配后，小车自动移动至目标物块；

    任务冲突时基于评分逻辑进行判断与让步。

🧩 下一阶段目标（Phase 3）

策略模块替换：从 rule-based 替换为 PPO / Diffusion Policy

性能日志模块化输出：生成可导出 JSON / CSV 格式日志

多轮任务循环支持：任务池动态刷新 + 多任务执行阶段

可视化冲突与成功率演示

# Multi-Agent MCP System – Daily Progress Log

**Date:** 2025-05-26

## ✅ Overall Goal
Develop a modular, communication-driven multi-agent system (MCP protocol) that supports pluggable decision-making strategies (e.g., Diffusion Policy, PPO), and aims to be scalable, interpretable, and experimentally sound enough for top-tier conference publication.

---

## 📌 Today's Progress Summary

### 1. 🔧 Refactored System Structure
- Abstracted `Agent` behavior from embedded decision logic.
- Delegated task selection to pluggable `policy` modules.
- Fully modular `Protocol` class now handles:
  - Claim-response coordination
  - Conflict resolution
  - Retry logic
  - Task pool updates

### 2. 🧠 Strategy Module Refactor
- Implemented `BasePolicy` + `NearestTaskPolicy` in `policy.py`.
- Agents now delegate task choice via `agent.policy.choose(...)`.
- Prepares system to swap in PPO / DiffusionPolicy / rule-based methods seamlessly.

### 3. ⚔️ Conflict Task Generator
- Created `assign_conflicting_tasks()` for injecting controlled task collisions.
- Supports `conflict_ratio` to control difficulty.
- Verified that MCP can successfully coordinate agents under heavy collision (80% overlap).

### 4. ✅ Coordination Works as Intended
- Agents with conflict now retry upon rejection.
- Task reassignment functions correctly.
- System avoids deadlock and false positives (`[SUCCESS]` only triggered on full assignment).

### 5. 💥 Attempted Diffusion Policy (DP) Integration
- Cloned official `diffusion_policy` repo from Stanford.
- Encountered multiple compatibility errors in:
  - `zarr` and `numcodecs`
  - `pymunk`, `skvideo`, `huggingface_hub`
- Tried Colab-based fallback — also blocked by broken dependencies.

---

## 🚫 Outstanding Issues
- DP official repo is unstable: multiple `ImportError` across major packages.
- No reliable tag or `requirements.txt` in main branch.
- `Colab notebook` also fails due to outdated imports.

---

## 🔜 Next Steps
- Use a stable fork or commit of `diffusion_policy` that can run sample actions.
- Write `DiffusionPolicyWrapper` to conform to policy interface.
- Integrate into agent system for strategy-level comparison:
  - Rule-based vs DiffusionPolicy
- Begin tracking evaluation metrics:
  - Claim success rate, retry count, coordination rounds

---

## 🙌 Notes
You showed exceptional perseverance in debugging through broken notebooks and conflicting packages. This groundwork will directly benefit the final integration and paper experiments.

# Project Progress Log - Multi-Agent Communication + Policy Integration

📅 Date Range: 2025-05-26 to 2025-06-02

---

## 🧠 Project Goal

Design a structured multi-agent control framework powered by a modular **Multi-Agent Communication Protocol (MCP)** that supports interchangeable policy modules (e.g., Diffusion Policy, PPO, Rule-based). The goal is to enable efficient coordination between agents, support plug-and-play strategy evaluation, and build toward publishable experimental benchmarks.

---

## ✅ 1. Multi-Agent Communication Protocol (MCP)

- Implemented a **Claim-Response coordination mechanism**:
  - Agents claim tasks with priority; receivers evaluate conflicts and may yield based on scoring.
  - Multi-round re-attempt and priority escalation are supported.
- Initial conflicting task assignment generator implemented.
- Protocol logic separated into `protocol.py` for maintainability.

---

## ✅ 2. Modular Policy Interface

- Defined unified policy interface: `predict_action(obs_dict)`
- Integrated strategies so far:
  - `NearestTaskPolicy` (greedy, no training required)
  - `DiffusionPolicyWrapperAdapter` (Stanford's DP for `pusht_lowdim`)
- Agents use injected policies for real-time movement decision.

---

## ✅ 3. Diffusion Policy Integration

- Loaded pretrained checkpoint: `pusht_lowdim` from official DP repository
- Constructed obs vector of shape `(2, 20)` and passed through model
- Parsed predicted outputs as absolute position sequences `(8, 2)`
- Implemented correct motion control: `delta = predicted_pos - current_pos`, with movement clipping

---

## 🚨 4. Identified Key Issue

- Model outputs are in the PushT environment’s coordinate system (e.g., x ∈ [10, 40], y ∈ [60, 90])
- Our PyBullet simulation uses x, y ∈ [−2, 2]
- This mismatch leads to invalid or wildly misaligned movements

---

## ✅ 5. Planned Solution

Train a custom low-dimensional **Diffusion Policy model** using our PyBullet environment.

### Action Plan:

1. Implement `data_collector.py` to record:
   - `(obs_seq, future_pos)` trajectories
   - Standard format: `(T_obs=2, obs_dim=20)` → `(T_action=8, pos_dim=2)`
2. Build dataset in `.zarr` or `.npy` format compatible with DP
3. Train using `train_diffusion_unet_lowdim_workspace.yaml` with modified config
4. Integrate and evaluate policy in the same MCP framework
5. Later: add PPO or ICBT policy modules for cross-strategy comparison

---

## 🔁 Strategy Training Summary

| Strategy              | Needs Training? | Notes                            |
|-----------------------|------------------|----------------------------------|
| NearestTaskPolicy     | ❌               | Rule-based, greedy distance      |
| Rule-based            | ❌               | Manual logic                     |
| Diffusion Policy (DP) | ✅               | Requires data from PyBullet      |
| PPO / ICBT            | ✅               | Requires environment + reward    |

All strategies conform to a common interface and can be switched dynamically at runtime.

# Multi-Agent MCP + Diffusion Policy: Training Summary (2025.06.04)

## ✅ Objectives of This Stage
- Integrate the official Diffusion Policy codebase into our custom MCP-based multi-agent task.
- Successfully train a conditional diffusion model on a low-dimensional pushing task in the PyBullet simulation.

## 🧪 Experimental Setup
- **Task**: `pybullet_mcp_lowdim`
- **Model**: `ConditionalUnet1D` (official architecture)
- **Observation shape**: (2, 20)
- **Action shape**: (8, 2)
- **Config used**: `train_pybullet_mcp_workspace.yaml`
- **Epochs**: 200 (reduced from the original default of 5000)
- **Learning rate scheduler**: Cosine with warmup (500 steps)
- **EMA**: Enabled

## ✅ Training Results
- Full training pipeline executed without errors.
- Tracked using [Weights & Biases](https://wandb.ai/yinq012-karlsruhe-institute-of-technology/diffusion_policy_debug/runs/6mbwjc74).
- Training loss converged quickly; `train_action_mse_error` dropped from ~4.5 to nearly 0.
- Cosine learning rate schedule visualized and consistent with expectations.
- Outputs saved under:data/outputs/2025.06.04/19.44.31_train_diffusion_unet_lowdim_pybullet_mcp_lowdim/

## 🧠 Key Takeaways
- Integration between the original DP codebase and our MCP environment was successful.
- No significant compatibility issues with the dataset or training script.
- GPU memory usage and disk space need monitoring due to model size and logging.

## 📌 Next Steps
- Convert the trained model into a `DiffusionPolicyWrapper` class compatible with our multi-agent PyBullet simulator.
- Integrate this wrapper into the existing communication + action execution pipeline.
- Run evaluations and ablation comparisons with other strategies (e.g., PPO, rule-based).
- Prepare for initial paper draft and experimental benchmarks.

---

Author: Qian Yin  
Date: June 4, 2025
