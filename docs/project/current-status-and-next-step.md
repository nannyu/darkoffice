# 项目现状与推进结论

## 结论

~~项目已完成高质量“文档事实源层”，但尚未进入“可运行状态层”。~~

**项目已进入实现阶段**：最小运行闭环已跑通，素材库、卡牌蒸馏器、剧情线系统已落地，代码审计问题已修复。

## 当前现状

### 已完成 ✅

| 模块 | 状态 | 关键文件 |
|------|------|---------|
| 文档事实源层 | ✅ 稳定 | `docs/` 全目录 |
| SQLite 持久化 | ✅ 运行中 | `runtime/db.py` |
| 回合结算引擎 | ✅ 运行中 | `runtime/engine.py` |
| CLI 入口 | ✅ 可用 | `scripts/game_state_cli.py` |
| 素材库 | ✅ 运行中 | `runtime/materials.py` |
| 卡牌蒸馏器 | ✅ 可用 | `scripts/distill_template.py` |
| 剧情线系统 | ✅ 运行中 | `runtime/storylines.py` |
| 剧情库选择 | ✅ 可用 | `darkoffice-skill.md` §15.7 + `skill/darkoffice-persistent-skill.md` |
| 代码审计修复 | ✅ 全部完成 | `docs/project/code-audit-report.md` |
| 反腐案例素材 | ✅ 19条已导入 | `scripts/fetch_and_import_jingzhong.py` |

### 技术栈

- **后端**：Python 3.12 + SQLite
- **桥接**：TypeScript (`skill/adapter.ts`) — Node.js → Python 调用
- **部署**：Agent Skill 形态（`skill/darkoffice-persistent-skill.md`）

## 推进判断

- ~~问题本质：你现在缺的不是“规则内容”，而是“规则执行与复盘能力”~~ → 已解决
- 当前问题：**内容规模不足** — 自定义卡牌数量远低于支撑完整游戏体验的需求
- 最短路径：持续运营素材库 → 蒸馏生成卡牌 → 编排剧情线 → 平衡性验证
- 新增能力：**剧情库选择** — 玩家开始新游戏时可浏览剧情库，通过自然语言选择剧情线

## 已实现产物

1. `CLAUDE.md`：项目级约束入口
2. `skill/darkoffice-persistent-skill.md`：可交付 Agent Skill（含完整规则）
3. `runtime/db.py`：SQLite schema + 初始化 + 迁移
4. `runtime/engine.py`：完整回合结算引擎（状态机、判定、隐患、项目、时间段系统）
5. `runtime/materials.py`：素材库 + 自定义卡牌管理 + 文件导入
6. `runtime/storylines.py`：剧情线 CRUD + 激活/推进/完成
7. `scripts/game_state_cli.py`：CLI 入口（含 material-*/card-*/storyline-* 子命令）
8. `scripts/distill_template.py`：卡牌蒸馏模板 + JSON Schema 校验
9. `scripts/fetch_and_import_jingzhong.py`：外部案例爬取 + 素材库导入
10. `scripts/simulate_balance.py`：平衡性模拟脚本

## 下一阶段建议（按优先级）

1. **内容规模化**：从素材库蒸馏生成更多角色卡/事件卡/隐患卡（目标 ≥50 张）
2. **剧情线编排**：设计至少 1 条完整剧情线（≥3 幕），测试剧情模式运行
3. **剧情库体验优化**：基于实际游玩反馈优化自然语言选择体验（模糊匹配、推荐逻辑）
4. **平衡性验证**：运行 `simulate_balance.py`，按行动类型分析生存率与数值波动
5. **内容扩写**：基于 `content/card-templates.md` 批量生产事件卡/角色卡
6. **回放能力**：按 `turn_logs` 还原关键局并定位失衡点
