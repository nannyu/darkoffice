---
name: darkoffice-skill
version: 1.1.0
entry: SKILL.md
language: zh-CN
runtime:
  adapter: skill/adapter.ts
  engine: runtime/engine.py
  database: runtime/darkoffice.sqlite3
commands:
  - health
  - init
  - create
  - turn
  - prompt
  - show
  - history
  - stats
platforms:
  - openclaw
  - workbuddy
  - qclaw
---

# DarkOffice Skill（正式入口）

本文件是 `darkoffice` 技能的标准入口文档，用于部署、运行、验收与排障。

## 1) 入口与命令

统一入口：

`npx tsx skill/adapter.ts <command> ...args`

命令：

- `health`：环境检查
- `init`：初始化数据库
- `create <session_id>`：创建会话
- `turn <session_id> --action <ACTION_TYPE>`：推进回合
- `prompt <session_id>`：下一回合展示块
- `show <session_id>`：当前状态快照
- `history <session_id> --limit N`：历史回合
- `stats <session_id>`：动作统计

## 2) 回合执行协议（强制）

每次用户输入动作后必须：

1. 调用 `turn`
2. 渲染本回合结算
3. 立即渲染 `payload.next_prompt`

禁止等待用户额外输入“继续”。

## 3) 用户可见输出规则

- 状态栏必须中文：`生命/精力/体力/绩效/风险/污染`
- 禁止展示内部字段：`EVT_*`、`CHR_*`、`STATUS_*`
- 禁止在选项中显示括号机制细节（修正值、被动惩罚）

## 4) 持久化约束

数据库：`runtime/darkoffice.sqlite3`

- `game_sessions` 保存会话快照
- `turn_logs` 保存逐回合日志
- 每次 `turn` 必须写 `turn_logs` 并更新 `game_sessions`

## 5) 部署与验收

平台清单：

- OpenClaw：`deploy/manifests/openclaw.skill.json`
- WorkBuddy：`deploy/manifests/workbuddy.skill.json`
- Qclaw：`deploy/manifests/qclaw.skill.json`

验收：

1. `npm run skill:health`
2. `npm run skill:init`
3. `npm run skill:create -- demo`
4. `npm run skill:turn -- demo --action EMAIL_TRACE`
5. 确认返回中包含 `next_prompt`
---
name: darkoffice-skill
version: 1.1.0
entry: SKILL.md
language: zh-CN
runtime:
  adapter: skill/adapter.ts
  engine: runtime/engine.py
  database: runtime/darkoffice.sqlite3
commands:
  - health
  - init
  - create
  - turn
  - prompt
  - show
  - history
  - stats
platforms:
  - openclaw
  - workbuddy
  - qclaw
source_of_truth:
  - SKILL.md
  - skill/darkoffice-persistent-skill.md
  - runtime/*.py
---

# DarkOffice Skill（正式入口）

本文件是 `darkoffice` 技能的标准入口文档，用于部署、运行、验收与排障。

## 1) 技能目标

`DarkOffice Skill` 是可持久化的对话式职场生存技能：

- 单次输入完成“结算 + 推进 + 下一回合展示”
- 状态可恢复（中断后继续）
- 结果可审计（逐回合写库）
- 可做平衡分析（history/stats/simulate）

## 2) 启动与命令

统一入口：

`npx tsx skill/adapter.ts <command> ...args`

命令：

- `health`：环境检查
- `init`：初始化数据库
- `create <session_id>`：创建会话
- `turn <session_id> --action <ACTION_TYPE>`：推进回合
- `prompt <session_id>`：拉取下一回合展示块
- `show <session_id>`：查看会话快照
- `history <session_id> --limit N`：历史回合
- `stats <session_id>`：动作统计

## 3) 回合执行协议（强制）

每次用户输入编号/动作后必须：

1. 调用 `turn`
2. 渲染本回合结算
3. 立即渲染 `payload.next_prompt`

禁止：

- 等用户再输入“继续”才展示下一回合
- 把“结算”和“下一回合展示”拆成两次交互

## 4) 用户可见输出约束

- 状态栏必须中文：`生命/精力/体力/绩效/风险/污染`
- 禁止展示内部 ID：`EVT_*`、`CHR_*`、`STATUS_*`
- 禁止在选项中显示括号机制细节（修正值、被动惩罚）

## 5) 持久化与数据

数据库：`runtime/darkoffice.sqlite3`

核心表：

- `game_sessions`：当前会话快照
- `turn_logs`：逐回合日志

强约束：

- 每次 `turn` 必须写入 `turn_logs`
- 状态变化必须更新 `game_sessions`
- 恢复会话仅依赖数据库快照

## 6) 当前实现范围

运行时已实现：

- 角色权重抽取
- 事件池抽取（含反重复）
- 行动修正与状态阈值
- 隐患生成/倒计时/爆炸
- 项目压力与进度推进
- 历史与统计输出

完整设计母版：`darkoffice-skill.md`。当前运行行为以 `runtime/*.py` 为准。

## 7) 三平台部署

- OpenClaw：`deploy/manifests/openclaw.skill.json`
- WorkBuddy：`deploy/manifests/workbuddy.skill.json`
- Qclaw：`deploy/manifests/qclaw.skill.json`
- 部署模板：`deploy/templates/DEPLOYMENT.md`

平台共同规则：

- 每次 `turn` 后必须渲染 `payload.next_prompt`

## 8) 验收清单

基础链路：

1. `npm ci`
2. `npm run skill:health`
3. `npm run skill:init`
4. `npm run skill:create -- demo`
5. `npm run skill:turn -- demo --action EMAIL_TRACE`
6. 确认返回体包含 `next_prompt`

平衡性：

- `python3 scripts/simulate_balance.py --runs 20 --turns 30`
- 检查 `docs/project/balance-report.md`

## 9) 故障排查

### 输入编号后无下一事件

1. `turn` 返回是否含 `next_prompt`
2. 平台是否渲染了 `payload.next_prompt`
3. 是否仍在用“等待继续”的旧逻辑

### 状态丢失或回档

1. `runtime/darkoffice.sqlite3` 是否可写
2. `game_sessions.turn_index` 是否更新
3. `turn_logs` 是否新增记录

### 出现 EVT_XX / CHR_XX 字段

1. 是否把内部 JSON 直接展示给用户
2. 是否绕过了用户可见层格式化
---
name: darkoffice-skill
version: 1.1.0
entry: SKILL.md
language: zh-CN
runtime:
  adapter: skill/adapter.ts
  engine: runtime/engine.py
  database: runtime/darkoffice.sqlite3
commands:
  - health
  - init
  - create
  - turn
  - prompt
  - show
  - history
  - stats
platforms:
  - openclaw
  - workbuddy
  - qclaw
source_of_truth:
  - SKILL.md
  - skill/darkoffice-persistent-skill.md
  - runtime/*.py
---

# DarkOffice Skill（正式入口）

本文件是 `darkoffice` 技能的标准入口文档。用于部署、运行、验收、排障和交接。

## 1. 技能目标

`DarkOffice Skill` 是一个可持久化的对话式职场生存技能：

- 单次输入完成“结算 + 推进 + 下一回合展示”
- 状态可恢复（会话中断后继续）
- 结果可审计（回合写库）
- 可做平衡性验证（统计与仿真）

## 2. 入口与命令

统一入口：

`npx tsx skill/adapter.ts <command> ...args`

命令列表：

- `health`：环境自检
- `init`：初始化数据库
- `create <session_id>`：创建会话
- `turn <session_id> --action <ACTION_TYPE>`：推进回合
- `prompt <session_id>`：拉取下一回合展示块
- `show <session_id>`：会话快照
- `history <session_id> --limit N`：历史记录
- `stats <session_id>`：动作统计

## 3. 回合执行逻辑（强制）

每次用户输入编号/动作意图时，必须按以下顺序：

1. 调用 `turn`
2. 渲染本回合结算
3. 直接渲染 `payload.next_prompt`

禁止：

- 等待用户额外输入“继续”才进入下一回合
- 把“结算”和“下一回合展示”拆成两次交互

## 4. 用户可见输出规则

- 状态栏必须中文：`生命/精力/体力/绩效/风险/污染`
- 禁止展示内部字段：`EVT_*`、`CHR_*`、`STATUS_*`
- 禁止选项展示括号机制细节（修正值、被动惩罚等）

## 5. 数据与持久化

数据库：`runtime/darkoffice.sqlite3`

关键表：

- `game_sessions`：当前状态快照
- `turn_logs`：逐回合日志

约束：

- 每次 `turn` 必须写 `turn_logs`
- 状态变化必须更新 `game_sessions`
- 恢复会话只能依赖数据库快照

## 6. 规则实现边界

当前引擎已覆盖：

- 角色权重抽取
- 事件池抽取（含反重复）
- 行动修正与状态阈值
- 隐患生成/倒计时/爆炸
- 项目压力与进度推进
- 历史与统计输出

完整设计母版参见 `darkoffice-skill.md`，当前运行规则以代码实现为准。

## 7. 部署映射

- OpenClaw：`deploy/manifests/openclaw.skill.json`
- WorkBuddy：`deploy/manifests/workbuddy.skill.json`
- Qclaw：`deploy/manifests/qclaw.skill.json`
- 部署模板：`deploy/templates/DEPLOYMENT.md`

## 8. 验收清单

基础链路：

1. `npm ci`
2. `npm run skill:health`
3. `npm run skill:init`
4. `npm run skill:create -- demo`
5. `npm run skill:turn -- demo --action EMAIL_TRACE`
6. 验证返回体包含 `next_prompt`

平衡性：

- `python3 scripts/simulate_balance.py --runs 20 --turns 30`
- 检查 `docs/project/balance-report.md`

## 9. 快速排障

问题：输入编号后没有下一事件  
检查：

1. `turn` 返回是否包含 `next_prompt`
2. 平台是否渲染了 `payload.next_prompt`
3. 是否误用了“等待继续”的旧逻辑

问题：状态丢失  
检查：

1. `runtime/darkoffice.sqlite3` 是否可写
2. `game_sessions.turn_index` 是否更新
3. `turn_logs` 是否新增记录

问题：输出出现内部字段  
检查：

1. 是否把内部 JSON 原样直出给用户
2. 是否绕过了用户可见层格式化
---
name: darkoffice-skill
version: 1.1.0
entry: SKILL.md
language: zh-CN
runtime:
  adapter: skill/adapter.ts
  engine: runtime/engine.py
  database: runtime/darkoffice.sqlite3
commands:
  - health
  - init
  - create
  - turn
  - prompt
  - show
  - history
  - stats
platforms:
  - openclaw
  - workbuddy
  - qclaw
source_of_truth:
  - SKILL.md
  - skill/darkoffice-persistent-skill.md
  - runtime/*.py
---

# DarkOffice Skill（正式入口）

本文件是 `darkoffice` 技能的标准入口文档。用于部署、运行、验收、排障和交接。

## 1. 技能目标

`DarkOffice Skill` 是一个可持久化的对话式职场生存技能：

- 单次输入完成“结算 + 推进 + 下一回合展示”
- 状态可恢复（会话中断后继续）
- 结果可审计（回合写库）
- 可做平衡性验证（统计与仿真）

## 2. 入口与命令

统一入口：

`npx tsx skill/adapter.ts <command> ...args`

命令列表：

- `health`：环境自检
- `init`：初始化数据库
- `create <session_id>`：创建会话
- `turn <session_id> --action <ACTION_TYPE>`：推进回合
- `prompt <session_id>`：拉取下一回合展示块
- `show <session_id>`：会话快照
- `history <session_id> --limit N`：历史记录
- `stats <session_id>`：动作统计

## 3. 回合执行逻辑（强制）

每次用户输入编号/动作意图时，必须按以下顺序：

1. 调用 `turn`
2. 渲染本回合结算
3. 直接渲染 `payload.next_prompt`

禁止：

- 等待用户额外输入“继续”才进入下一回合
- 把“结算”和“下一回合展示”拆成两次交互

## 4. 用户可见输出规则

- 状态栏必须中文：`生命/精力/体力/绩效/风险/污染`
- 禁止展示内部字段：`EVT_*`、`CHR_*`、`STATUS_*`
- 禁止选项展示括号机制细节（修正值、被动惩罚等）

## 5. 数据与持久化

数据库：`runtime/darkoffice.sqlite3`

关键表：

- `game_sessions`：当前状态快照
- `turn_logs`：逐回合日志

约束：

- 每次 `turn` 必须写 `turn_logs`
- 状态变化必须更新 `game_sessions`
- 恢复会话只能依赖数据库快照

## 6. 规则实现边界

当前引擎已覆盖：

- 角色权重抽取
- 事件池抽取（含反重复）
- 行动修正与状态阈值
- 隐患生成/倒计时/爆炸
- 项目压力与进度推进
- 历史与统计输出

完整设计母版参见 `darkoffice-skill.md`，当前运行规则以代码实现为准。

## 7. 部署映射

- OpenClaw：`deploy/manifests/openclaw.skill.json`
- WorkBuddy：`deploy/manifests/workbuddy.skill.json`
- Qclaw：`deploy/manifests/qclaw.skill.json`
- 部署模板：`deploy/templates/DEPLOYMENT.md`

## 8. 验收清单

基础链路：

1. `npm ci`
2. `npm run skill:health`
3. `npm run skill:init`
4. `npm run skill:create -- demo`
5. `npm run skill:turn -- demo --action EMAIL_TRACE`
6. 验证返回体包含 `next_prompt`

平衡性：

- `python3 scripts/simulate_balance.py --runs 20 --turns 30`
- 检查 `docs/project/balance-report.md`

## 9. 快速排障

问题：输入编号后没有下一事件  
检查：

1. `turn` 返回是否包含 `next_prompt`
2. 平台是否渲染了 `payload.next_prompt`
3. 是否误用了“等待继续”的旧逻辑

问题：状态丢失  
检查：

1. `runtime/darkoffice.sqlite3` 是否可写
2. `game_sessions.turn_index` 是否更新
3. `turn_logs` 是否新增记录

