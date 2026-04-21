# DarkOffice Working Memory

## 项目概况
- **名称**: 暗黑职场 (Dark Office)
- **类型**: 卡牌驱动叙事生存游戏，聊天式交互
- **状态**: 文档先行，已跑通最小运行闭环，剧情库选择功能已落地
- **技术栈**: Python (SQLite 持久化 + 回合引擎) + TypeScript (adapter 桥接)
- **仓库**: https://github.com/nannyu/darkoffice

## 关键文件
- `darkoffice-skill.md`: 完整游戏规则 Skill（15章，含P0数据包+素材库+蒸馏器+剧情线+剧情库选择）
- `runtime/engine.py`: 回合结算引擎（支持自定义卡牌合并+剧情线驱动）
- `runtime/db.py`: SQLite 持久化层（5张表：game_sessions, turn_logs, materials, custom_cards, storylines）
- `runtime/content.py`: 角色与事件数据（Character/Event 含扩展可选字段）
- `runtime/materials.py`: 素材库 CRUD + 文件导入(md/txt/pdf) + 自定义卡牌加载合并
- `runtime/storylines.py`: 剧情线 CRUD + 激活/推进/完成管理
- `skill/darkoffice-persistent-skill.md`: 持久化版 Agent Skill
- `skill/adapter.ts`: Node.js → Python 桥接
- `scripts/distill_template.py`: 蒸馏提示词模板 + card_data schema 校验

## 代码审计 (2026-04-20)
- 发现2个严重Bug: 结算倍率正值反转、连接泄漏
- 4个逻辑缺陷: day不递增、隐患覆盖不全、状态推导与文档不一致、项目自动补充未文档化
- 完整报告: docs/project/code-audit-report.md

## 代码审计修复 (2026-04-20)
- 全部9项问题已修复并通过验证
- engine.py 重写：连接管理改为 try/finally、倍率方向修正、day+时间段系统、隐患映射表、状态推导由事件触发
- db.py: 默认路径改为基于 __file__ 的绝对路径
- skill/darkoffice-persistent-skill.md: 同步更新10种行动、倍率规则、隐患规则、时间段系统

## 素材库数据导入 (2026-04-21)
- 从中央纪委"警钟"栏目爬取并导入19条反腐案例素材
- 爬取策略：列表页用 requests，详情页需8秒间隔或 web_fetch 绕验证码
- 素材库现有19条素材（ID 1-19），分类"反腐案例"，来源"中央纪委国家监委网站-警钟"
- 相关脚本：crawl_jingzhong.py（列表爬取）、fetch_and_import_jingzhong.py（详情+导入）

## 女娲式蒸馏器升级 (2026-04-21)
- distill_template.py 全面重写，融入女娲 Skill 六维深度分析框架
- 新增字段：mind_model、decision_heuristics、inner_tension、anti_pattern、vulnerability（角色卡）；structural_trap、hidden_cost、hazard_hook（事件卡）；origin_story、explosion_scene、chain_reaction、intervention_chance（隐患卡）；theme、power_arc、power_shift（剧情线）
- 新增 distill_from_material.py 智能工作流脚本（analyze/character/event/hazard/storyline/full/write）
- 设计原则：角色=认知操作系统、事件=结构性困境、隐患=定时炸弹、剧情线=权力演变史

## 素材1(谢玉敏)完整牌库 (2026-04-21)
- 基于警钟栏目素材1生成完整牌库：3角色 + 8事件 + 4隐患 + 1剧情线 = 16张卡牌
- 剧情线"围猎：董事长的坠落"含4幕（破冰→深陷→失控→崩塌），支持一周目游戏
- 全部卡牌已写入数据库并激活（CUSTOM_CHR_001~003, CUSTOM_EVT_001~008, CUSTOM_HZD_001~004, CUSTOM_STL_001）
- 卡牌JSON源文件备份于 `data/cards/set01/`

## 剧情库与自然语言选择 (2026-04-21)
- 新游戏启动流程改为：初始化 → 展示剧情库 → 玩家选择剧情线（或自由模式）→ 开始第一回合
- 支持三种选择方式：编号选择、关键词匹配、自然语言描述
- 剧情库为空时自动跳过选择，直接自由模式
- 文档更新：darkoffice-skill.md §15.7、skill/darkoffice-persistent-skill.md、docs/ 下6个文档

## 失败判定扩展 (2026-04-21)
- 6种失败结局：HP≤0(崩溃)、EN≤0(精神崩溃)、ST≤0(体力耗尽)、KPI≤0(被开除)、RISK≥100(暴雷)、COR≥100(黑化)
- 优先级：HP > EN > ST > KPI > RISK > COR
- risk/cor 上限从无硬上限改为100（_clamp_state 同步修改）
- 文档更新：darkoffice-skill.md 四大结局→六大结局、skill/darkoffice-persistent-skill.md 失败判定重写
