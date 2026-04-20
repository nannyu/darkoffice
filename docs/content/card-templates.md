# 卡牌模板

## 1. 文档目的

本文档定义《暗黑职场》中各类卡牌的策划填写模板，用于后续内容生产与数据结构整理。

## 2. 使用原则

- 模板用于统一内容生产，不等于最终程序数据格式
- 结构化字段优先，描述文本用于辅助阅读
- 每张卡必须能映射回系统职责
- 一张卡尽量只承载一个核心冲突或核心作用
- 需要触发骰子判定的卡牌，必须显式标注触发类型与结果档位

## 3. 通用填写模板

```markdown
- card_id:
- card_name:
- card_type:
- rarity:
- tags:
- desc:
- effect_text:
- source:
- trigger_condition:
- duration:
- stack_rule:
- priority:
- result_payload:
```

## 3.1 掷骰补充字段

对于会触发掷骰的事件卡、应对卡、隐患卡或阶段节点，建议补充以下字段：

- `roll_trigger`: 是否触发掷骰，取值建议为 `none / required / conditional`
- `roll_type`: 判定类型，取值建议为 `high_risk_action / critical_event / hazard_flip / stage_checkpoint`
- `roll_modifier_rule`: 修正值来源说明
- `roll_outcome_table`: 四档结果摘要

说明：

- `none`：不触发掷骰，按确定性规则结算
- `required`：进入该对象时必须触发掷骰
- `conditional`：满足条件时才触发掷骰

## 4. 人物卡模板

### 4.1 字段建议

- `character_id`
- `name`
- `role_type`
- `faction`
- `tags`
- `persona_summary`
- `passive_effect`
- `event_pool`
- `attitude_rule`
- `weight_modifiers`

### 4.2 填写模板

```markdown
## 人物卡

- character_id:
- name:
- role_type:
- faction:
- tags:
- persona_summary:
- passive_effect:
- common_pressure_types:
- event_pool:
- attitude_rule:
- weight_modifiers:
```

## 5. 事件卡模板

### 5.1 字段建议

- `event_id`
- `name`
- `source_character`
- `event_category`
- `pressure_level`
- `trigger_condition`
- `base_effect`
- `response_constraints`
- `followup_rule`
- `flavor_text`
- `roll_trigger`
- `roll_type`
- `roll_modifier_rule`
- `roll_outcome_table`

### 5.2 填写模板

```markdown
## 事件卡

- event_id:
- name:
- source_character:
- event_category:
- pressure_level:
- tags:
- trigger_condition:
- base_effect:
- response_constraints:
- possible_followups:
- flavor_text:
- roll_trigger:
- roll_type:
- roll_modifier_rule:
- roll_outcome_table:
```

## 6. 应对卡模板

### 6.1 字段建议

- `response_id`
- `name`
- `response_category`
- `cost`
- `effect`
- `risk_change`
- `cor_change`
- `usage_limit`
- `combo_rule`
- `side_effect`
- `roll_trigger`
- `roll_type`
- `roll_modifier_rule`
- `roll_outcome_table`

### 6.2 填写模板

```markdown
## 应对卡

- response_id:
- name:
- response_category:
- tags:
- cost:
- effect:
- risk_change:
- cor_change:
- usage_limit:
- combo_rule:
- side_effect:
- roll_trigger:
- roll_type:
- roll_modifier_rule:
- roll_outcome_table:
```

## 7. 状态卡模板

### 7.1 字段建议

- `status_id`
- `name`
- `status_type`
- `duration`
- `tick_effect`
- `stack_rule`
- `remove_condition`

### 7.2 填写模板

```markdown
## 状态卡

- status_id:
- name:
- status_type:
- tags:
- duration:
- tick_effect:
- stack_rule:
- remove_condition:
- flavor_text:
```

## 8. 隐患卡模板

### 8.1 字段建议

- `hazard_id`
- `name`
- `hazard_category`
- `countdown`
- `explode_condition`
- `explode_effect`
- `clear_method`
- `linked_roles`
- `roll_trigger`
- `roll_type`
- `roll_modifier_rule`
- `roll_outcome_table`

### 8.2 填写模板

```markdown
## 隐患卡

- hazard_id:
- name:
- hazard_category:
- tags:
- countdown:
- explode_condition:
- explode_effect:
- clear_method:
- linked_roles:
- flavor_text:
- roll_trigger:
- roll_type:
- roll_modifier_rule:
- roll_outcome_table:
```

## 9. 机制卡模板

### 9.1 字段建议

- `mechanic_id`
- `name`
- `mechanic_scope`
- `duration`
- `global_modifier`
- `affected_pools`
- `exit_condition`

### 9.2 填写模板

```markdown
## 机制卡

- mechanic_id:
- name:
- mechanic_scope:
- tags:
- duration:
- global_modifier:
- affected_pools:
- exit_condition:
- flavor_text:
```

## 10. 项目卡模板

### 10.1 字段建议

- `project_id`
- `name`
- `slot_cost`
- `remaining_steps`
- `per_turn_pressure`
- `deadline`
- `fail_effect`
- `clear_reward`
- `linked_characters`
- `project_tags`

### 10.2 填写模板

```markdown
## 项目卡

- project_id:
- name:
- slot_cost:
- remaining_steps:
- per_turn_pressure:
- deadline:
- fail_effect:
- clear_reward:
- linked_characters:
- project_tags:
```

## 11. 模板使用要求

- 必填字段不可省略
- 待定内容必须显式标记，不允许空着不解释
- 描述文本要能映射到结构化字段
- 不同卡牌类型不要混用字段含义

## 12. 与其他文档的关系

- [card-system.md](/Users/niunan/project/darkoffice/docs/systems/card-system.md) 定义这些模板对应的系统职责
- [stats-and-resources.md](/Users/niunan/project/darkoffice/docs/systems/stats-and-resources.md) 定义常见数值变化范围
