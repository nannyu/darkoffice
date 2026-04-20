# DarkOffice Skill（正式入口）

> 本文件是 `darkoffice` 技能的唯一入口说明。用于 OpenClaw / WorkBuddy / Qclaw 的部署、运行、验收和故障处理。  
> 目标：让任意接手人只看本文件，也能完整跑起技能并理解规则边界。

---

## 1. 技能定位

`DarkOffice Skill` 是一个可持久化的对话式卡牌叙事生存技能，聚焦“恶性职场中的资源管理与长期代价”：

- 单次输入驱动完整回合：**结算 + 推进 + 下一回合展示**
- 状态可恢复：支持会话中断后继续
- 结果可审计：所有回合写入数据库日志
- 可做平衡分析：支持历史查询与统计脚本

---

## 2. 事实源与优先级

当规则冲突时，按以下优先级判定：

1. 本文件 `skill.md`（运行与交互入口规则）
2. `skill/darkoffice-persistent-skill.md`（技能运行规范）
3. `runtime/*.py`（当前可执行实现）
4. `darkoffice-skill.md`（完整设计母版）
5. `docs/systems/*`（系统规则文档）

说明：`darkoffice-skill.md` 是设计母版，不代表每一条都已 1:1 落入当前运行时代码。

---

## 3. 目录与职责

- `skill/adapter.ts`：统一命令适配层（Node 入口，调用 Python）
- `runtime/engine.py`：回合结算主引擎
- `runtime/content.py`：角色/事件/行动映射与展示文案
- `runtime/db.py`：SQLite 持久化与表迁移
- `scripts/game_state_cli.py`：CLI 命令入口
- `scripts/simulate_balance.py`：自动仿真与平衡报告
- `deploy/manifests/*.skill.json`：三平台部署清单
- `deploy/templates/DEPLOYMENT.md`：部署流程模板
- `release/darkoffice-skill-bundle/`：可分发封装产物

---

## 4. 运行入口（标准）

统一入口命令：

- `npx tsx skill/adapter.ts <command> ...args`

常用命令：

- `health`：环境健康检查
- `init`：初始化数据库
- `create <session_id>`：创建会话
- `turn <session_id> --action <ACTION_TYPE>`：推进一个回合
- `prompt <session_id>`：拉取下一回合展示块
- `show <session_id>`：查看当前状态快照
- `history <session_id> --limit N`：查看历史回合
- `stats <session_id>`：查看动作统计

NPM 快捷命令：

- `npm run skill:health`
- `npm run skill:init`
- `npm run skill:create -- <session_id>`
- `npm run skill:turn -- <session_id> --action <ACTION_TYPE>`
- `npm run skill:prompt -- <session_id>`
- `npm run skill:show -- <session_id>`
- `npm run skill:history -- <session_id> --limit 10`
- `npm run skill:stats -- <session_id>`

---

## 5. 回合协议（强制）

### 5.1 单回合闭环

用户每次输入（编号或自然语言）必须完成：

1. 执行 `turn`
2. 返回本回合结算结果（骰子、结果等级、delta、状态变化）
3. 同时返回 `next_prompt`
4. 前端/平台立即渲染 `next_prompt`

### 5.2 禁止行为

- 禁止在 `turn` 后等待用户再输入“继续”才能出现下一事件
- 禁止把“结算”和“下一回合展示”拆成两个用户交互步骤

---

## 6. 用户展示规范（强制）

### 6.1 状态栏

用户可见状态栏必须使用中文：

- 生命 / 精力 / 体力 / 绩效 / 风险 / 污染

示例：

`生命 98/100 | 精力 61/100 | 体力 86/100 | 绩效 89 | 风险 12 | 污染 6`

### 6.2 去技术化输出

- 禁止展示内部字段 ID：如 `EVT_02`、`CHR_01`、`STATUS_LOW_EN`
- 禁止在选项中显示括号机制细节：
  - 例如“骰子修正 +0”“被动 -2”
- 允许内部记录，但用户只看自然语言动作描述

---

## 7. 数据与持久化约束

### 7.1 数据库

默认数据库：`runtime/darkoffice.sqlite3`

关键表：

- `game_sessions`：会话快照（当前回合状态）
- `turn_logs`：回合日志（可审计、可统计）

### 7.2 必须写库

- 任意 `turn` 必须落 `turn_logs`
- 任意核心状态变更必须更新 `game_sessions`
- 会话恢复仅依赖数据库快照，不依赖内存

---

## 8. 规则实现范围（当前版本）

当前运行时已实现：

- 角色权重抽取
- 事件池抽取（含反重复策略）
- 行动修正与状态阈值修正
- 隐患生成/倒计时/爆炸
- 项目持续压力与进度推进
- 回合统计与平衡分析

未完全覆盖的扩展规则应以 `darkoffice-skill.md` 为规划来源逐步补齐。

---

## 9. 部署到三平台

清单文件：

- OpenClaw：`deploy/manifests/openclaw.skill.json`
- WorkBuddy：`deploy/manifests/workbuddy.skill.json`
- Qclaw：`deploy/manifests/qclaw.skill.json`

共同约束：

- 每次 `turn` 后必须消费 `payload.next_prompt`
- 不允许把下一回合展示延迟到“继续”输入

---

## 10. 标准验收流程

### 10.1 基础链路验收

1. `npm ci`
2. `npm run skill:health`
3. `npm run skill:init`
4. `npm run skill:create -- demo`
5. `npm run skill:turn -- demo --action EMAIL_TRACE`
6. 验证返回体包含 `next_prompt`

### 10.2 平衡性验收

- `python3 scripts/simulate_balance.py --runs 20 --turns 30`
- 检查 `docs/project/balance-report.md`

---

## 11. 故障排查速查

### 11.1 “输入编号后没有下一事件”

检查项：

1. `turn` 响应是否包含 `next_prompt`
2. 平台是否渲染了 `payload.next_prompt`
3. 是否错误等待了“继续”输入

### 11.2 “状态丢失或回档”

检查项：

1. 是否写入 `runtime/darkoffice.sqlite3`
2. `game_sessions` 是否更新 `turn_index`
3. `turn_logs` 是否新增记录

### 11.3 “输出出现 EVT_XX 等字段”

检查项：

1. 是否直接把内部 JSON 原样展示给用户
2. 是否绕过了去技术化展示层

---

## 12. 与母版关系

`darkoffice-skill.md` 是设计母版，负责完整玩法定义。  
本文件负责“可执行入口与部署标准”，并以母版为持续补全依据：

- 母版改规则 -> 先更新 `skill/` 与 `runtime/` -> 再更新本入口文档

---

## 13. 维护要求

- 变更技能协议、命令、展示约束时，必须同步更新本文件
- 发布新 bundle 前必须执行一次标准验收流程
- 本文件必须始终存在于仓库根目录，作为技能正式入口

