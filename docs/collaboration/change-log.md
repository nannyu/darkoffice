# 文档变更记录

## 2026-04-20

- 建立 `docs/` 文档体系与分区 README
- 新增项目入口 `README.md`
- 新增 `docs/INDEX.md` 作为导航中枢
- 新增开发规范、事实源说明、文档风格与 AI/Agent 交接规范
- 将历史总案拆分为项目、设计、系统与内容层事实源文档

## 2026-04-20（实现阶段启动）

**项目从文档建设阶段进入实现阶段。**

### 新增 runtime 模块

- `runtime/db.py`：SQLite 持久化层（5张表：game_sessions, turn_logs, materials, custom_cards, storylines）
- `runtime/engine.py`：回合结算引擎（状态机、判定、隐患、项目、时间段系统）
- `runtime/content.py`：Character/Event dataclass（含扩展可选字段）
- `scripts/game_state_cli.py`：CLI 入口（init/create/turn/show + material-*/card-*/storyline-* 子命令）
- `skill/darkoffice-persistent-skill.md`：可交付 Agent Skill（含 DB 约束与完整规则）
- `skill/adapter.ts`：Node.js → Python 桥接

### 代码审计

- 发现 2 个严重 Bug（结算倍率正值反转、连接泄漏）+ 4 个逻辑缺陷
- 全部 9 项问题已修复并通过验证
- 详见 `docs/project/code-audit-report.md`

## 2026-04-21（素材库与剧情线扩展）

### 新增系统模块

- `runtime/materials.py`：素材库 CRUD + 文件导入(md/txt/pdf) + 自定义卡牌管理 + 卡牌合并
- `runtime/storylines.py`：剧情线 CRUD + 激活/推进/完成管理
- `scripts/distill_template.py`：卡牌蒸馏提示词模板 + JSON Schema 校验

### 素材库数据

- 从中央纪委"警钟"栏目爬取并导入 19 条反腐案例素材
- 爬取策略：列表页用 requests，详情页需 8 秒间隔或 web_fetch 绕验证码
- 素材分类：反腐案例，来源：中央纪委国家监委网站-警钟

### 文档更新

- `darkoffice-skill.md`：新增第14章（素材库与蒸馏器）、第15章（定制剧情线）
- `docs/INDEX.md`：更新项目状态、补充代码-文档映射表
- `docs/project/scope-and-milestones.md`：里程碑从 M0-M4 扩展到 M5-M7
- `docs/project/current-status-and-next-step.md`：全面更新为已实现状态
- `docs/collaboration/change-log.md`：本文件（记录实现阶段变更）

## 2026-04-21（剧情库与自然语言选择）

### 新增功能

- **剧情库浏览与自然语言选择**：玩家开始新游戏时，Agent 先展示可用剧情库列表，支持编号选择、关键词匹配和自然语言描述三种方式
- **游戏启动流程重构**：新游戏流程从"直接开始"改为"先选剧情再开始"
- 自由模式始终作为最后选项保留，剧情库为空时自动跳过选择步骤

### 文档更新

- `darkoffice-skill.md`：第15章新增 §15.7 剧情库与自然语言选择（含选择流程、匹配规则、展示格式）
- `skill/darkoffice-persistent-skill.md`：新增"剧情库与游戏开始流程"完整操作指令
- `docs/project/current-status-and-next-step.md`：已完成列表新增"剧情库选择"，推进建议新增"剧情库体验优化"
