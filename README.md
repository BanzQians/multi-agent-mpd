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

