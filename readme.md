# 🧠 MCP-MAS: Modular Communication Protocol for Multi-Agent Systems

## 📌 项目简介

本项目旨在构建一个**去中心化的多智能体系统框架**，使每个智能体具备完整的决策与执行能力，通过结构化通信协议（MCP）进行任务分配、自主协调与协同执行，最终实现可扩展、可解释、策略可插拔的分布式协作系统。

系统支持多种类型策略（如 Rule-based、PPO、Diffusion Policy）自由接入，任务由 Agent 自主 claim 并通过通信进行冲突协调，无需中心调度控制，具备良好的通用性与工程可落地性。

---

## ✅ 当前系统能力

- **多智能体运行**：支持3个Agent同时运行，具备感知、通信、动作能力；
- **任务环境**：多个可分配目标点，任务随机生成，Agent通过通信完成任务协商；
- **通信协议 MCP**：
  - 支持任务 claim、respond、retry、优先级判断等结构化消息；
  - 协议模块独立封装，易于维护与扩展；
- **策略模块化**：
  - 所有策略遵循统一接口 `policy.compute_action(obs, messages)`；
  - 已集成 `NearestTaskPolicy`、`RuleBasedPolicy`、`DiffusionPolicyWrapperAdapter`；
- **模拟环境**：当前使用 PyBullet 实现轻量仿真，任务与 Agent 均支持随机初始化；
- **系统可视化**：支持 GUI 模式实时可视化系统行为，便于调试与演示。

---

## 🚧 当前开发进度（截至 2025年6月）

| 模块 | 状态 | 说明 |
|------|------|------|
| MCP通信结构 | ✅ 已完成封装，支持多轮通信与冲突协调 |
| 多Agent并行 | ✅ 支持三Agent稳定运行，行为正常 |
| 策略模块接口 | ✅ 已实现策略统一接口与封装 |
| Diffusion Policy接入 | ✅ 已完成Wrapper，支持运行stub策略 |
| 环境构建 | ✅ PyBullet运行稳定，任务生成可控 |
| 执行行为问题排查 | 🟡 已定位目标位置未正确设置的问题，待验证修复 |
| 项目结构文档化 | ✅ 正在完成当前README与任务规划整理 |

---

## 📈 未来阶段规划

### 🔄 阶段3：引入协作任务 & 协议扩展

- [ ] 实现需要两个或多个Agent协同完成的任务类型；
- [ ] 扩展通信协议，支持 `request_assist`、`ack_assist`、`sync_start` 等消息类型；
- [ ] 支持Agent之间的任务等待、同步启动与联合执行逻辑；
- [ ] **迁移当前系统至更适合复杂协作任务的虚拟环境**（如 Isaac Lab 或 PettingZoo），并保留当前结构化协议与策略接口；
- [ ] 保持 MCP 协议和策略接口环境无关性（实现环境抽象接口封装）；

### 🧠 阶段4：接入学习型策略并进行性能评估

- [ ] 接入 PPO 等强化学习策略（通信感知决策）；
- [ ] 对比 Rule-based / DP / PPO 在不同任务下的表现；
- [ ] 设计任务复杂度递增的测试环境，逐步验证系统性能扩展性与策略协作能力；

### 🌐 阶段5：系统稳定性测试 & 高复杂度协作场景扩展

- [ ] 多任务并行（多个agent + 多种任务同时进行）；
- [ ] Agent能力异构（不同速度、可达性、策略组合）；
- [ ] 引入任务调度规则（如deadline、成本权重）；
- [ ] 系统级指标评估（成功率、任务效率、通信开销）；
- [ ] 可视化协作行为与通信流程图，用于后续展示与分析。

---

## 📂 项目目录结构（建议）

multi_agent_mpd/
├── main.py # Entry point: launches simulation
├── agent.py # Agent logic (communication + strategy)
├── protocol.py # MCP protocol structure & message handling
├── policy.py # Policy switch logic (rule-based, DP wrapper, etc.)
├── task_conflict_gen.py # Task assignment and conflict generation
├── strategy/ # Additional policy wrappers & tests
│ ├── dp_wrapper.py
│ └── test_dp_wrapper.py
├── tools/
│ └── data_collector.py # Data recording / test scripts
├── logs/ # Experiment notes & logs
│ └── 2025-06-25-exp1.md
├── pybullet_log.txt # Output log (optional)
├── requirements.txt # Python dependencies
├── readme.md # Project overview (this file)

Diffusion Policy repository (as submodule or separate folder)

├── dp_repo/ # Official DP codebase
│ ├── diffusion_policy/ # Model, training, evaluation
│ ├── train.py / eval.py # Training and testing scripts
│ ├── outputs/ / media/ # Saved models and visual logs
│ └── ... # Additional DP files

Data & environment

├── data/ # Collected trajectories, training logs
│ └── collected_trajs/
├── venv_mpd/ # Local virtual environment (excluded in version control)

---

## 📎 附：使用建议

- 启动主程序：`python main.py`，运行模拟并观察行为
- 修改Agent策略：在 `main.py` 中配置 `agent.policy = ...`
- 调试信息开启：在各模块中加入日志输出或查看`print()`信息
- 策略开发：继承 `BasePolicy` 并实现 `compute_action()` 方法

---
# 🧠 MCP-MAS: Modular Communication Protocol for Multi-Agent Systems

## 📌 Project Overview

This project aims to build a **decentralized multi-agent system framework** in which each agent is fully autonomous and capable of decision-making and task execution. Through a structured communication protocol (Modular Communication Protocol, MCP), agents coordinate task allocation, conflict resolution, and cooperative execution — all without any centralized controller.

The system supports plug-and-play policies (e.g., Rule-based, PPO, Diffusion Policy) and enables flexible agent behaviors through message-driven coordination, making it suitable for research in distributed robotics, collaborative AI, and communication-based planning.

---

## ✅ Current Features

- **Multi-Agent Operation**: Supports 3 simultaneous agents, each capable of observation, communication, decision-making, and movement;
- **Task Environment**: Multiple target objects randomly initialized; agents autonomously claim and execute tasks through communication;
- **Structured Communication Protocol (MCP)**:
  - Supports structured messages: `claim`, `respond`, `retry`, and priority-based resolution;
  - All messages are handled via a unified protocol module (`protocol.py`);
- **Modular Policy Interface**:
  - Unified API `compute_action(obs, messages)` for all policies;
  - Integrated: `NearestTaskPolicy`, `RuleBasedPolicy`, `DiffusionPolicyWrapperAdapter`;
- **Simulation Environment**:
  - Lightweight simulation using PyBullet;
  - Agent and task initialization randomized;
- **Real-time Visualization**: Agents’ behaviors are rendered in PyBullet GUI for debugging and demonstration.

---

## 🚧 Current Development Status (as of June 2025)

| Module | Status | Notes |
|--------|--------|-------|
| MCP Protocol | ✅ Completed, supports multi-round negotiation and resolution |
| Multi-Agent Integration | ✅ 3 agents running stably with full autonomy |
| Policy Interface | ✅ Unified and plug-and-play for various strategies |
| Diffusion Policy Integration | ✅ Wrapper completed, stub version running |
| Environment | ✅ PyBullet-based, stable and modular |
| Behavior Bug Fix | 🟡 Diagnosed issue: target position not correctly set; pending verification |
| Documentation | ✅ Current README + development roadmap finalized |

---

## 📈 Upcoming Development Plan

### 🔄 Phase 3: Cooperative Tasks & Protocol Extension

- [ ] Introduce cooperative task types requiring multiple agents to succeed;
- [ ] Extend MCP to support new message types: `request_assist`, `ack_assist`, `sync_start`;
- [ ] Implement synchronization and cooperative behavior primitives (e.g., wait, joint move);
- [ ] **Migrate the project to a more advanced simulation environment** (e.g., Isaac Lab or PettingZoo) to support complex cooperative scenarios;
- [ ] Abstract simulation environment interface to keep MCP & policy components environment-agnostic;

### 🧠 Phase 4: Communication-Aware Learning Strategies

- [ ] Integrate PPO and other RL algorithms with message-based observation;
- [ ] Compare rule-based vs learned policies (e.g., PPO, DP) in cooperative settings;
- [ ] Design diverse task scenarios to benchmark system performance and robustness;

### 🌐 Phase 5: Scalability, Robustness & Complex Scenarios

- [ ] Support concurrent multi-task execution (more agents, more task types);
- [ ] Introduce agent heterogeneity (e.g., speed, capabilities, policy type);
- [ ] Add task constraints: deadlines, priorities, costs;
- [ ] System-wide evaluation: success rate, task throughput, communication overhead;
- [ ] Visualize agent trajectories, communication flows, and task coordination.

---

## 📂 Project Structure

multi_agent_mpd/
├── main.py # Entry point: launches simulation
├── agent.py # Agent logic (communication + strategy)
├── protocol.py # MCP protocol structure & message handling
├── policy.py # Policy switch logic (rule-based, DP wrapper, etc.)
├── task_conflict_gen.py # Task assignment and conflict generation
├── strategy/ # Additional policy wrappers & tests
│ ├── dp_wrapper.py
│ └── test_dp_wrapper.py
├── tools/
│ └── data_collector.py # Data recording / test scripts
├── logs/ # Experiment notes & logs
│ └── 2025-06-25-exp1.md
├── pybullet_log.txt # Output log (optional)
├── requirements.txt # Python dependencies
├── readme.md # Project overview (this file)

Diffusion Policy repository (as submodule or separate folder)

├── dp_repo/ # Official DP codebase
│ ├── diffusion_policy/ # Model, training, evaluation
│ ├── train.py / eval.py # Training and testing scripts
│ ├── outputs/ / media/ # Saved models and visual logs
│ └── ... # Additional DP files

Data & environment

├── data/ # Collected trajectories, training logs
│ └── collected_trajs/
├── venv_mpd/ # Local virtual environment (excluded in version control)
---

## 📎 Usage Guide

- Run simulation: `python main.py`
- Set agent policy: assign in `main.py`, e.g., `agent.policy = NearestTaskPolicy(...)`
- Debugging: enable `print()` logs in relevant modules for inspection
- Add new policy: implement subclass of `BasePolicy` with `compute_action()` method

---

This project is actively evolving. The next step is to expand to cooperative task execution and transition to a more complex environment with enhanced communication and strategy capabilities.
