# Systems Docs

本目录用于定义正式系统规则，回答“游戏机制如何运行、以什么顺序结算、哪些字段是正式结构”。

当前已建立：

1. [card-system.md](/Users/niunan/project/darkoffice/docs/systems/card-system.md)
2. [turn-flow.md](/Users/niunan/project/darkoffice/docs/systems/turn-flow.md)
3. [stats-and-resources.md](/Users/niunan/project/darkoffice/docs/systems/stats-and-resources.md)
4. [event-generation.md](/Users/niunan/project/darkoffice/docs/systems/event-generation.md)
5. [character-system.md](/Users/niunan/project/darkoffice/docs/systems/character-system.md)
6. [status-hazard-project.md](/Users/niunan/project/darkoffice/docs/systems/status-hazard-project.md)
7. [rules-and-resolution.md](/Users/niunan/project/darkoffice/docs/systems/rules-and-resolution.md)
8. [conversation-interaction.md](/Users/niunan/project/darkoffice/docs/systems/conversation-interaction.md)

## 代码映射

| 系统文档 | 对应 runtime 模块 | 关键函数/类 |
|---------|------------------|------------|
| `card-system.md` | `runtime/content.py` | `Character`, `Event` dataclass |
| `turn-flow.md` | `runtime/engine.py` + `runtime/rules.py` | `apply_turn()`, `build_next_prompt()`, `TURN_FLOW_STEPS` |
| `stats-and-resources.md` | `runtime/engine.py` + `runtime/rules.py` | `_clamp_state()`, `_status_modifier()`, `RESOURCE_DEFINITIONS` |
| `event-generation.md` | `runtime/engine.py` + `runtime/rules.py` | `_pick_character()`, `_pick_event()`, `TIME_PERIOD_RULES` |
| `character-system.md` | `runtime/content.py` + `runtime/materials.py` | `Character` + `load_active_custom_characters()` |
| `status-hazard-project.md` | `runtime/engine.py` + `runtime/rules.py` | `_derive_statuses()`, `_tick_hazards()`, `_tick_projects()`, `EVENT_HAZARD_MAP` |
| `rules-and-resolution.md` | `runtime/engine.py` + `runtime/rules.py` | `_tier_by_roll()`, `RESOLUTION_TIER_RULES` |
| `conversation-interaction.md` | `runtime/engine.py` + `runtime/rules.py` | `build_next_prompt()`, `ACTION_RULES` |
| `visualizations/README.md` | `runtime/mechanics.py` + `scripts/render_mechanics_visual.py` | `build_mechanics_snapshot()`, `game-mechanics.html` |

### 剧情线系统

| 功能 | 对应模块 | 说明 |
|------|---------|------|
| 剧情线 CRUD | `runtime/storylines.py` | `create_storyline()`, `list_storylines()`, `get_storyline()`, `delete_storyline()` |
| 激活/停用 | `runtime/storylines.py` | `activate_storyline()`, `deactivate_storyline()` |
| 幕推进 | `runtime/storylines.py` | `advance_act()` |
| 剧情驱动事件 | `runtime/engine.py` | `_pick_character()`, `_pick_event()` 中剧情线优先逻辑 |
| 剧情库选择 | `darkoffice-skill.md` §15.7 + `skill/darkoffice-persistent-skill.md` | Agent 层自然语言剧情选择流程 |

> 注：完整规则定义见 `darkoffice-skill.md`（第 3-12 章），包含更详细的字段说明和数值约束。剧情线规则见第15章。

后续可扩展文档：

1. `data-structure-spec.md`
2. `storyline-system.md`（剧情线系统详细设计文档）
