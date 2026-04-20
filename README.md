# Dark Office

《暗黑职场》是一个以恶性职场为主题的卡牌驱动叙事生存项目。

它想做的不是把“上班”包装成普通战斗，而是把现实职场中的压迫、甩锅、留痕、站队、灰色合规、绩效规训和长期透支，转成一套可以在聊天对话中推进的系统化玩法。

当前项目仍处于文档建设阶段，重点是先把玩法共识、系统规则、内容结构和协作规范打磨成熟，再进入正式开发。

## 项目特点

- 聊天优先：核心交互优先面向 Agent / 飞书等对话载体设计
- 卡牌驱动：系统内部以事件、应对、状态、隐患、项目等规则对象组织
- 生存叙事：重点不是爽快碾压，而是在高压结构里险中求活
- 延迟代价：很多选择当下有利，但会在后续回合翻面反噬
- AI 友好：文档结构按事实源拆分，适合人类与 AI/Agent 协作接手

## 当前状态

- 阶段：文档先行
- 目标：建立一套清晰、可维护、可继续拆分的项目文档体系
- 范围：已完成项目定位、设计、系统、内容、协作五个维度的基础文档
- 约束：技术栈尚未定案，当前不进入正式开发实现

## 如果你是第一次来到这个仓库

建议按这个顺序阅读：

1. [docs/INDEX.md](/Users/niunan/project/darkoffice/docs/INDEX.md)
2. [docs/project/README.md](/Users/niunan/project/darkoffice/docs/project/README.md)
3. [docs/design/README.md](/Users/niunan/project/darkoffice/docs/design/README.md)
4. [docs/systems/README.md](/Users/niunan/project/darkoffice/docs/systems/README.md)
5. [docs/content/README.md](/Users/niunan/project/darkoffice/docs/content/README.md)

## 如果你要参与协作

先看这几份：

1. [docs/collaboration/development-guidelines.md](/Users/niunan/project/darkoffice/docs/collaboration/development-guidelines.md)
2. [docs/collaboration/source-of-truth.md](/Users/niunan/project/darkoffice/docs/collaboration/source-of-truth.md)
3. [docs/collaboration/agent-handoff.md](/Users/niunan/project/darkoffice/docs/collaboration/agent-handoff.md)

## 仓库结构

```text
docs/
├── INDEX.md
├── project/         # 项目定位、范围、术语、设计支柱
├── design/          # 核心循环、进程推进、结局方向
├── systems/         # 卡牌系统、回合流程、判定规则、聊天交互
├── content/         # 角色池、事件库、应对库、模板与文本规范
├── collaboration/   # 开发规范、事实源、交接与变更记录
└── archive/         # 历史设计来源与迁移说明
```

## 当前事实源

- [docs/INDEX.md](/Users/niunan/project/darkoffice/docs/INDEX.md)：文档导航中枢
- [docs/project/](/Users/niunan/project/darkoffice/docs/project/README.md)：项目级定义
- [docs/design/](/Users/niunan/project/darkoffice/docs/design/README.md)：玩法体验与整体结构
- [docs/systems/](/Users/niunan/project/darkoffice/docs/systems/README.md)：正式规则与流程
- [docs/content/](/Users/niunan/project/darkoffice/docs/content/README.md)：内容模板与资产规划
- [docs/collaboration/](/Users/niunan/project/darkoffice/docs/collaboration/README.md)：协作与开发规范

当多个文档冲突时，以结构化子文档中的最新定义为准；历史归档只用于追溯。

## 历史归档

早期两份根目录设计文档已合并为一份归档稿：

- [docs/archive/initial-design-source-compendium.md](/Users/niunan/project/darkoffice/docs/archive/initial-design-source-compendium.md)

## 下一步

当前最自然的下一阶段不是直接开工写代码，而是继续把内容库做实：

- 补首批 `required` / `conditional` 事件卡
- 补首批高风险应对卡
- 补状态、隐患、项目的样例库
- 在聊天式交互中验证核心循环与骰子系统是否成立

## 已落地的最小运行闭环

仓库已补充“数值持久化最小闭环”，用于把规则从文档推进到可运行状态：

- `skill/darkoffice-persistent-skill.md`：持久化版 Agent Skill
- `runtime/db.py`：SQLite 持久化层
- `runtime/engine.py`：最小回合结算引擎
- `scripts/game_state_cli.py`：初始化、建档、结算、查看命令

快速验证：

1. `python3 scripts/game_state_cli.py init`
2. `python3 scripts/game_state_cli.py create demo`
3. `python3 scripts/game_state_cli.py turn demo --action EMAIL_TRACE --mod 3`
4. `python3 scripts/game_state_cli.py show demo`
