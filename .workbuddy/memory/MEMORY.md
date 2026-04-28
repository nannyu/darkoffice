# DarkOffice Working Memory

## 项目概况
- **名称**: 暗黑职场 (Dark Office)
- **类型**: 卡牌驱动叙事生存游戏，聊天式交互
- **状态**: 文档先行，已跑通最小运行闭环，剧情库选择功能已落地
- **技术栈**: Python (SQLite 持久化 + 回合引擎) + TypeScript (adapter 桥接) + 微信小程序 (TypeScript 原生)
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

## 分支信息
- **online**: 新分支（2026-04-21），用于线上演示/部署

## 工具模式 MVP 完成 (2026-04-21)
### 产品定位
- **暗黑职场 2.0**：基于真实案例的职场博弈模拟器
- **双模式设计**：工具模式（职场参谋）+ 娱乐模式（暗黑抽卡）
- **核心价值**：不是教你成功学，而是帮你预演职场雷区

### 职场参谋模块（skill/advisor/）
- `darkoffice-advisor-skill.md`: 技能入口，完整规则+触发机制+回答框架
- `fengvideo_core.md`: 峰video核心思维框架（6心智模型+8决策启发式+草台班子分类）
- `response_templates.md`: 标准话术模板库（启动/收束/场景话术/金句库）
- `README.md`: 模块索引

### 核心能力
1. **情境定位**：快速判断问题本质（权力博弈/责任边界/晋升/人际冲突）
2. **选项生成**：3-4个选项，每个带短期/中期/风险/峰video点评
3. **后果预测**：最好/最坏情况 + 概率分布 + 半年后可能
4. **个人建议**：综合分析给出参考建议

### 峰video知识整合
- 整合126万粉职场博主峰video的302个视频内容
- 6大心智模型：信号理论、契约分工、过客主义、信息不对称防御、工具化思维、反常识判断
- 8条决策启发式：重复武器论、防御=犹豫=自残、音量降70%、差不多到位论等
- 草台班子分类学：局部bug型/中层瘫痪型/上层失能型/全面崩塌型

### 触发机制
- 用户描述职场困境时激活（领导/同事/晋升/站队/背锅/加班/绩效）
- "开始游戏""新游戏" → 娱乐模式（不触发工具模式）

### 下一步计划
- 飞书机器人接入（使用飞书Skill）
- 峰video职场视频字幕蒸馏 → 扩充案例库
- 爬取知乎/小红书职场话题 → 扩充案例库

## 微信小程序 阶段A (2026-04-24)
- **分支**: codex/wechat
- **目录**: wechat/（与 runtime/ skill/ 并列）
- **架构**: miniprogram/（前端6页面+6组件+services） + cloudfunctions/（4云函数+shared层）
- **当前模式**: 本地 Mock，不对接云开发
- **核心文件**:
  - wechat/cloudfunctions/shared/types/game.ts: 全部类型定义
  - wechat/cloudfunctions/shared/engine/resolver.ts: TypeScript 回合引擎（对齐 Python engine.py）
  - wechat/cloudfunctions/shared/rules/: 6个规则模块（resources/resolution/time-period/actions/hazards/index）
  - wechat/cloudfunctions/shared/content/: 角色+事件数据（对齐 Python content.py）
  - wechat/cloudfunctions/shared/repositories/mock/: 内存 Mock 数据层（MockRepositories 组合类）
  - wechat/miniprogram/services/api.ts: 前端 API 服务（同步调用 shared 层）
  - wechat/miniprogram/pages/game/: 核心游戏页面
  - wechat/miniprogram/components/: status-bar/event-card/action-sheet/result-modal/hazard-strip/project-panel
- **UI 风格**: Cyberpunk Neon（深色背景+霓虹红/橙/绿功能色）
- **TypeScript 编译**: 逻辑错误全部清零（仅剩微信全局类型 TS2304/TS2339，开发者工具可正常处理）
- **下一步**: 微信开发者工具加载验证 → 对接云开发 → 补充剧情线选择逻辑
