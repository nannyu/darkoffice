# 回合流程

## 1. 文档目的

本文档定义《暗黑职场》的正式回合状态机、各节点职责、结算顺序与事件链生成原则。

当前项目优先采用聊天对话形态推进，因此本流程既描述内部规则结算顺序，也约束外部对话节奏。

## 2. 时间单位

- 每回合代表 `20 分钟` 职场时间
- 回合既是系统结算单位，也是叙事推进单位

## 3. 回合状态机总览

```text
[TURN_START]
    ↓
[TIME_ADVANCE]
    ↓
[STATUS_TICK]
    ↓
[HAZARD_TICK]
    ↓
[PROJECT_TICK]
    ↓
[MECHANIC_TICK]
    ↓
[RENDER_STATUS_BAR]
    ↓
[DRAW_CHARACTER]
    ↓
[DRAW_EVENT]
    ↓
[RENDER_CHOICES]
    ↓
[PLAYER_DECISION]
    ↓
[ROLL_CHECK]
    ↓
[RESOLVE_EFFECT]
    ↓
[GENERATE_CHAIN]
    ↓
[CHECK_FAIL_OR_END]
    ↓
[REFRESH_ACTION_POOL]
    ↓
[TURN_END]
    ↓
[下一回合]
```

## 4. 状态机节点定义

| 状态节点 | 名称 | 输入 | 输出 | 说明 |
| --- | --- | --- | --- | --- |
| `TURN_START` | 回合开始 | 上回合结果 | 当前回合上下文 | 初始化 |
| `TIME_ADVANCE` | 时间推进 | 当前时间 | 新时间段 | 时间前进 20 分钟 |
| `STATUS_TICK` | 状态结算 | 状态区 | 数值变化 | 持续状态生效 |
| `HAZARD_TICK` | 隐患倒计时 | 隐患区 | 新隐患状态或翻面结果 | 倒计时与爆炸 |
| `PROJECT_TICK` | 项目结算 | 项目区 | 每回合压力 | 持续任务施压 |
| `MECHANIC_TICK` | 机制结算 | 机制区 | 全局修正 | 阶段环境规则 |
| `RENDER_STATUS_BAR` | 渲染状态栏 | 当前数值与状态 | 对话顶部状态摘要 | 面向用户显示 |
| `DRAW_CHARACTER` | 抽取角色 | 权重池 | 当前角色 | 确定本回合施压者 |
| `DRAW_EVENT` | 抽取事件 | 角色与权重池 | 当前事件 | 生成主冲突 |
| `RENDER_CHOICES` | 渲染选项 | 事件与可用动作池 | 3 到 5 个推荐行动 | 面向用户显示 |
| `PLAYER_DECISION` | 玩家决策 | 选项、关键词或自然语言 | 应对选择 | 核心操作 |
| `ROLL_CHECK` | 骰子判定 | 当前事件、行动与修正值 | 判定结果档位 | 仅在关键场景触发 |
| `RESOLVE_EFFECT` | 结算效果 | 事件、应对与修正 | 数值和状态变化 | 核心计算 |
| `GENERATE_CHAIN` | 生成链条 | 结算结果 | 新状态、隐患、项目或后续事件 | 长期推进 |
| `CHECK_FAIL_OR_END` | 检查失败 | 当前全局状态 | 是否失败或阶段结束 | 判定 |
| `REFRESH_ACTION_POOL` | 刷新行动池 | 规则池与当前上下文 | 下一轮候选行动 | 准备下回合 |
| `TURN_END` | 回合结束 | 全部状态 | 历史记录 | 写入回顾 |

## 5. 正式阶段说明

### 5.1 回合开始阶段

依次执行：

1. 时间推进
2. 状态结算
3. 隐患倒计时
4. 项目压迫结算
5. 机制卡结算
6. 渲染状态栏

### 5.2 事件生成阶段

依次执行：

1. 根据权重抽取来访角色
2. 从对应事件池抽取主事件
3. 必要时追加副事件

### 5.3 玩家应对阶段

- 系统默认给出 3 到 5 个可执行选项
- 用户可以回复数字、关键词或自然语言
- 系统优先匹配明确选项，匹配不到时再做意图归类
- 某些状态或事件会限制可选行动

用户侧不必显式理解“出牌”概念；“出牌”是系统内部规则对象，对话界面呈现为“行动选项”。

### 5.4 判定阶段

默认情况下，行动直接进入结算。

只有以下场景触发骰子判定：

1. 高风险行动
2. 关键事件
3. 隐患翻面
4. 阶段节点

推荐判定模型为 `2d6 + 修正值`。

### 5.5 结算阶段

系统整合事件、应对、骰子结果档位、人物被动、状态修正、机制修正与阈值修正，产出本回合结果。

### 5.6 回合结束阶段

- 刷新下一轮可用行动池
- 写入历史记录
- 输出事件结果叙述
- 进入下一回合

## 6. 聊天界面硬规则

### 6.1 状态栏规则

每轮对话必须在顶部显示简洁状态栏，固定包含：

- 当前时间
- `生命`
- `精力`
- `体力`
- `绩效`
- `风险`
- `污染`
- 当前关键状态

推荐格式：

```text
状态栏｜周二 20:40
生命 100/100 | 精力 36/100 | 体力 48/100 | 绩效 92 | 风险 17 | 污染 4
状态：疲惫(2)、被盯上(1)
```

若当前无状态，显示：

```text
状态：无
```

### 6.2 回合消息结构

推荐每轮消息结构固定为：

1. 状态栏
2. 事件摘要
3. 风险提示
4. 可选行动
5. 用户回复指引

### 6.3 可选行动规则

- 默认展示 3 到 5 个行动
- 每个行动应提示主要收益与主要代价
- 至少保留一个偏保守选项与一个偏激进选项
- 若存在明显高风险隐患，应优先展示与其相关的行动

### 6.4 掷骰提示规则

若本轮会触发骰子判定，消息中必须明确显示：

- 本轮是否需要掷骰
- 当前判定类型
- 修正值来源
- 结果档位说明

## 7. 正式结算顺序

| 顺位 | 结算项 | 说明 |
| --- | --- | --- |
| 1 | 事件基础效果 | 先计算事件原始压力 |
| 2 | 应对卡减免或替换 | 玩家主动操作介入 |
| 3 | 骰子判定结果 | 仅在关键场景触发 |
| 4 | 人物被动修正 | 角色个性影响 |
| 5 | 状态修正 | 疲惫、透支、被盯上等 |
| 6 | 机制修正 | 全局环境 |
| 7 | 数值阈值修正 | 低精力、低体力附加惩罚 |
| 8 | 生成状态 | 例如获得“被盯上” |
| 9 | 生成隐患 | 例如“责任未明确” |
| 10 | 生成项目或后续事件 | 例如返工任务 |
| 11 | 更新角色态度 | 好感、敌意、满意度变化 |
| 12 | 检查失败 | HP、KPI、暴雷等判定 |

## 8. 时间段系统

当前建议的一天时间段：

- `09:00-12:00` 上午工作
- `12:00-13:00` 午休
- `13:00-18:00` 下午工作
- `18:00-21:00` 加班时间
- `21:00-24:00` 深夜危险时间

时间段会影响：

- 角色抽取权重
- 事件类型权重
- 恢复事件概率
- 高压或崩溃类事件概率

## 9. 权重抽取原则

### 9.1 角色抽取权重因子

- 当前时间段
- 当前机制卡
- 玩家状态
- 当前项目区任务
- 当前隐患内容
- 历史关系与角色态度
- KPI、RISK、COR 等核心数值区间

示意公式：

`最终权重 = 基础权重 × 时间修正 × 状态修正 × 项目修正 × 隐患修正 × 机制修正`

### 9.2 事件抽取权重因子

- 来源角色
- 当前压力等级
- 当前机制
- 当前状态
- 最近历史事件

## 10. 链式事件原则

《暗黑职场》的核心不是随机散点，而是链式事件推进。

处理不当的事件会生成：

- 新状态
- 新隐患
- 新项目
- 新后续事件

典型链条包括：

- 推活 -> 模糊责任 -> 背锅
- 甲方加急 -> 熬夜硬扛 -> 透支 -> 次日翻车
- 灰色合规 -> 风险累积 -> 审计引爆
- 站队 -> 短期庇护 -> 长期反噬

## 11. 伪代码示意

```python
def run_turn(game_state):
    game_state.time += 20_minutes

    apply_status_tick(game_state)
    apply_hazard_tick(game_state)
    apply_project_tick(game_state)
    apply_mechanic_tick(game_state)
    render_status_bar(game_state)

    current_character = draw_character(game_state)
    current_event = draw_event(game_state, current_character)
    choices = render_choices(game_state, current_event)

    player_response = get_player_response(game_state, current_event, choices)

    roll_result = maybe_roll_check(game_state, current_event, player_response)

    result = resolve_event(
        game_state=game_state,
        character=current_character,
        event=current_event,
        response=player_response,
        roll_result=roll_result,
    )

    apply_result(game_state, result)
    generate_followups(game_state, result)

    if check_failure(game_state):
        return end_game(game_state)

    refresh_action_pool(game_state)
    archive_turn_history(game_state, current_character, current_event, player_response, result)

    return game_state
```

## 12. 与其他文档的关系

- [card-system.md](/Users/niunan/project/darkoffice/docs/systems/card-system.md) 定义参与本流程的卡牌对象
- [stats-and-resources.md](/Users/niunan/project/darkoffice/docs/systems/stats-and-resources.md) 定义本流程中的数值变化规则
- [core-loop.md](/Users/niunan/project/darkoffice/docs/design/core-loop.md) 从玩家体验角度描述该流程
- [conversation-interaction.md](/Users/niunan/project/darkoffice/docs/systems/conversation-interaction.md) 定义聊天载体下的消息结构与输入归类规则
- [rules-and-resolution.md](/Users/niunan/project/darkoffice/docs/systems/rules-and-resolution.md) 定义骰子判定的正式规则
