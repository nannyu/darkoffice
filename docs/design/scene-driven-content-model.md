# Scene-Driven Content Model Design

> 本文档定义《暗黑职场》从"单回合抽卡"到"多角色场景驱动"的内容模型改造设计。
> 事实源优先级：本文档 > 代码实现 > 口头讨论。

---

## 1. 概述

### 1.1 设计目标

将现有"每回合随机抽取一个角色 + 一个独立事件"的 roguelite 模式，改造为"每回合构建一个多角色场景"的叙事驱动模式。

核心变化：
- 事件不是"抽出来的"，是角色带着自己的状态、欲望和恐惧主动生成的
- 同一场景中多个角色同时在场，各自有隐藏议程
- 玩家的选择同时影响多个角色的看法
- 场景之间有因果链，角色会随着剧情推进演化

### 1.2 设计原则

1. **向后兼容**：保留现有 `CHARACTERS`/`EVENTS`/`EVENTS_BY_CHARACTER` 结构，新字段全部用 Optional/默认值
2. **角色即叙事引擎**：事件由角色状态驱动，不是随机抽卡
3. **场景是核心单元**：所有玩家交互发生在 Scene 中，单角色事件是 Scene 的退化形式
4. **统一数据结构**：Scene 支持 0/1/N 个角色在场，渲染层自动降级
5. **函数生成叙事**：`narrative_fn` 是 Python 函数，支持任意复杂逻辑
6. **硬切换**：旧代码不保留双轨，改造后旧 CLI 需要重新 init

---

## 2. 核心概念

| 概念 | 说明 |
|---|---|
| **Scene** | 玩家交互的核心单元。包含在场角色、场景描述、角色台词、玩家选项、隐藏目标 |
| **Strategy Prototype** | 全局策略原型（共9个），定义基础效果。Scene 中的选项是原型的"场景实例" |
| **Character State** | 角色的动态状态（relation/mood/trust/stress/power），每局独立，持久化到 SQLite |
| **Relation Graph** | 角色之间的关系网，无向加权图，边权重 -100~+100 |
| **Event Chain** | 有序的事件序列，同一 chain 内的事件有因果引用 |
| **Narrative Fn** | 渲染场景文本的 Python 函数，输入 NarrativeContext，返回 RenderedScene |
| **Hidden Goal** | 场景中完全隐藏的目标，玩家通过观察角色反应自行发现，零提示 |

---

## 3. 数据模型

### 3.1 Character（扩展）

```python
@dataclass(frozen=True)
class Personality:
    aggression: int = 50   # 攻击性 0-100
    ambition: int = 50     # 野心 0-100
    loyalty: int = 50      # 忠诚度 0-100
    cynicism: int = 50     # 犬儒程度 0-100
    greed: int = 50        # 贪婪度 0-100
    paranoia: int = 50     # 多疑度 0-100

@dataclass(frozen=True)
class Character:
    # === 原有字段（保留，向后兼容）===
    character_id: str
    name: str
    base_weight: int

    # === 叙事层（新增）===
    role_type: str = ""            # 施压者/同盟者/中立者/观察者/背叛者
    faction: str = ""              # 所属派系
    personality: Personality = field(default_factory=Personality)
    desires: list[str] = field(default_factory=list)   # 如 ["升职","避开审计"]
    fears: list[str] = field(default_factory=list)     # 如 ["被取代","背锅"]
    tagline: str = ""              # 标志性台词

    # === 动态层初始值（新增）===
    initial_relation: int = 0      # 对玩家初始关系 -100~+100
    initial_mood: str = "平静"      # 初始心情
    initial_trust: int = 50        # 初始信任
    initial_stress: int = 50       # 初始压力
    initial_power: int = 50        # 初始影响力
    hidden_stance: str = ""        # 隐藏立场

    # === 元数据 ===
    tags: list[str] = field(default_factory=list)
    speech_style: str = ""         # 说话风格标签
    portrait_prompt: str = ""      # AI生成立绘的prompt模板
```

**心情枚举（P1硬编码，P2加转换规则）**：

```python
VALID_MOODS = ["平静", "急躁", "阴沉", "得意", "恐慌", "冷漠"]
```

### 3.2 Event（扩展）

```python
@dataclass(frozen=True)
class EventPrerequisites:
    min_relation: Optional[int] = None       # 关系值下限
    max_relation: Optional[int] = None       # 关系值上限
    required_moods: list[str] = field(default_factory=list)   # 需要的角色心情
    required_status_tags: list[str] = field(default_factory=list)
    required_events: list[str] = field(default_factory=list)  # 前置事件ID（本chain内）
    turn_min: int = 0                        # 最早触发回合
    turn_max: int = 999                      # 最晚触发回合

@dataclass(frozen=True)
class Event:
    # === 原有字段（保留）===
    event_id: str
    character_id: str
    name: str
    base_effect: dict[str, int]

    # === 叙事层（新增）===
    event_type: str = "施压"               # 诉求/恐惧/试探/求助/施压/情报/陷阱
    narrative_template: str = ""           # 函数名，指向 narrative_fns.py 中的函数

    # === 条件层（新增）===
    prerequisites: EventPrerequisites = field(default_factory=EventPrerequisites)

    # === 连锁层（新增）===
    chain_id: str = ""                     # 所属事件链
    chain_position: int = 0                # 在链中的位置
    chain_delay: int = 0                   # 触发后延迟N回合

    # === 动态效果层（新增）===
    mood_modifiers: dict[str, dict] = field(default_factory=dict)
    # 示例: {"急躁": {"en": -3}, "阴沉": {"risk": +2}}

    # === 关系影响（新增）===
    relation_impact: dict[str, int] = field(default_factory=dict)
    # 示例: {"DIRECT_EXECUTE": -5, "EMAIL_TRACE": -10}

    # === 元数据 ===
    tags: list[str] = field(default_factory=list)
    pressure_level: str = "normal"         # normal/high/critical
    dice_dc: Optional[int] = None
    flavor_text: Optional[str] = None
    possible_followups: Optional[list[str]] = None
```

### 3.3 Scene（新增）

```python
@dataclass(frozen=True)
class SceneOption:
    option_id: str
    prototype: str                         # 引用哪个策略原型
    label: str                             # 玩家看到的文本
    target_character: Optional[str] = None # 对谁使用
    visibility_condition: str = ""         # 显示条件，简单表达式字符串
    custom_effect: dict[str, int] = field(default_factory=dict)  # 场景专属数值修正
    sub_mode: Optional[str] = None         # 子模式（如PROBE的"主动/被动"）
    sort_priority: int = 0                 # 排序权重

@dataclass(frozen=True)
class HiddenGoal:
    goal_id: str
    description: str                       # 内部描述，不对玩家显示
    reward: dict = field(default_factory=dict)  # 达成奖励
    trigger_condition: str = ""            # 达成条件，简单表达式

@dataclass(frozen=True)
class Scene:
    scene_id: str
    title: str
    time_periods: list[str]               # 可在哪些时段出现
    location: str = ""                     # 地点描述

    # 角色配置
    required_characters: list[str] = field(default_factory=list)   # 必须在场
    optional_characters: list[str] = field(default_factory=list)   # 可选
    inclusion_rules: dict[str, str] = field(default_factory=dict)  # {character_id: condition}
    exclusion_rules: dict[str, str] = field(default_factory=dict)  # 互斥规则
    max_characters: int = 4               # 最多在场人数（含玩家）

    # 场景内容
    narrative_fn: str = ""                # 渲染函数名
    player_options: list[SceneOption] = field(default_factory=list)
    hidden_goals: list[HiddenGoal] = field(default_factory=list)

    # 场景池标记
    scene_pool_tags: list[str] = field(default_factory=list)  # 用于时段场景池分类
```

### 3.4 SceneResult（新增）

场景结算后的完整结果。

```python
@dataclass
class SceneResult:
    # 玩家数值变化
    player_delta: dict[str, int] = field(default_factory=dict)

    # 角色关系变化 {character_id: delta}
    relation_changes: dict[str, int] = field(default_factory=dict)

    # 角色状态变化 {character_id: {field: new_value}}
    character_state_changes: dict[str, dict] = field(default_factory=dict)

    # 生成的新状态卡
    new_statuses: list[dict] = field(default_factory=list)

    # 生成的新隐患卡
    new_hazards: list[dict] = field(default_factory=list)

    # 隐藏目标达成
    hidden_goals_achieved: list[str] = field(default_factory=list)

    # 下回合提示
    next_turn_hint: str = ""

    # 事件链推进
    chain_progress: Optional[dict] = None

    # 幕推进标记
    act_advanced: bool = False

    # 结局标记
    ending_triggered: Optional[str] = None
```

### 3.5 StrategyPrototype（改造自 ACTION_RULES）

```python
@dataclass(frozen=True)
class StrategyPrototype:
    prototype_id: str
    title: str
    summary: str
    modifier: int                          # 骰子修正
    category: str                          # 对抗/防守/回避/社交/信息/灰色
    energy_cost: str                       # low/medium/high

    # 基础数值效果
    base_effects: dict[str, int] = field(default_factory=dict)

    # 对角色关系的基础影响（按 role_type 分类）
    relation_impact_by_role: dict[str, int] = field(default_factory=dict)

    # 特殊效果描述
    special: str = ""

    # 使用建议
    when_to_use: str = ""
    when_not_to_use: str = ""
```

### 3.6 EventChain（新增）

```python
@dataclass(frozen=True)
class ChainEventRef:
    event_id: str
    delay_turns: int = 0
    branch_condition: Optional[str] = None      # 条件表达式
    branch_target_chain: Optional[str] = None   # 条件满足时跳转

@dataclass(frozen=True)
class EventChain:
    chain_id: str
    title: str
    description: str
    character_id: str                        # 主导角色
    events: list[ChainEventRef]              # 有序事件序列
    is_interruptible: bool = True            # 是否允许被支线打断
    priority: int = 1                        # 优先级
```

### 3.7 Act / Storyline（升级）

```python
@dataclass(frozen=True)
class ActBranch:
    condition: str              # 条件表达式
    target_act_index: int       # 跳转目标幕
    narrative: str              # 分支过渡文本

@dataclass(frozen=True)
class Act:
    act_index: int
    title: str
    narrative_bridge: str = ""
    core_conflict: str = ""
    duration_turns: int = 10

    main_chain: Optional[str] = None
    required_characters: list[str] = field(default_factory=list)
    completion_condition: str = "chain_completed"
    branches: list[ActBranch] = field(default_factory=list)
```

### 3.8 RelationGraph（新增）

```python
@dataclass
class RelationGraph:
    """角色关系网：无向加权图"""
    edges: dict[frozenset[str], int] = field(default_factory=dict)

    def _key(self, a: str, b: str) -> frozenset[str]:
        return frozenset({a, b})

    def get(self, a: str, b: str) -> int:
        return self.edges.get(self._key(a, b), 0)

    def set(self, a: str, b: str, value: int):
        self.edges[self._key(a, b)] = max(-100, min(100, value))

    def modify(self, a: str, b: str, delta: int):
        self.set(a, b, self.get(a, b) + delta)

    def get_allies(self, character_id: str, threshold: int = 30) -> list[str]:
        result = []
        for edge_key, value in self.edges.items():
            if value >= threshold and character_id in edge_key:
                result.append([c for c in edge_key if c != character_id][0])
        return result
```

### 3.9 NarrativeContext（新增）

```python
@dataclass
class NarrativeContext:
    session: dict
    player_state: dict
    character_states: dict[str, "CharacterState"]
    relation_graph: RelationGraph
    turn_history: list[dict]
    active_chains: list[dict]
    active_storyline: Optional[dict]
    time_period: str
    turn_index: int
```

### 3.10 CharacterState（新增，运行时动态）

```python
@dataclass
class CharacterState:
    character_id: str
    relation_to_player: int = 0
    mood: str = "平静"
    trust: int = 50
    stress: int = 50
    power: int = 50
    hidden_stance: str = ""
```

---

## 4. 引擎流程

### 4.1 场景构建流程 `_build_scene`

```
1. 检查强制主线场景
   - 剧情线当前 act 有 scheduled_scene 且条件满足？
   - → 触发主线场景（不可跳过）

2. 检查待续场景链
   - 上一回合触发 chain，当前有 delay=0 的后续？
   - → 触发链式场景

3. 检查角色主动诉求
   - 按 urgency = stress × power × desire_intensity 排序角色
   - urgency 最高者带着诉求来找玩家
   - → 生成该角色的诉求场景

4. 检查日常填充
   - 以上都没有，从当前时段场景池随机抽
   - → 触发日常场景

5. 退化到单角色事件
   - 以上都为空 → 回退到旧 _pick_character + _pick_event
```

### 4.2 场景结算流程

```
Step 1: 基础影响（玩家→角色）
  根据选项原型 + 场景实例，计算对每个在场角色的直接影响

Step 2: 关系网传导（角色→角色，最多2跳，每跳×0.5衰减）
  对每一对在场角色 (A, B)：
    如果 A 对玩家的 relation 变化了 Δ：
      B 根据 B对A 的关系调整对玩家的看法

Step 3: 数值影响（角色→玩家数值）
  所有在场角色的 power × relation 加权平均
  影响玩家的 HP/EN/KPI/RISK

Step 4: 角色状态更新
  更新 mood/stress/trust

Step 5: 隐藏目标检查
  检查 hidden_goals 是否达成

Step 6: 生成连锁
  生成新状态、隐患、项目推进、事件链后续

Step 7: 幕推进检查
  检查 act completion_condition

Step 8: 失败/结局检查
```

---

## 5. 策略原型详解

### 5.1 完整定义

详见 `runtime/strategy_prototypes.py`。本节给出最终定稿的9个原型摘要。

| 原型 | 组别 | 核心哲学 | 消耗 | 直接收益 | 长期风险 |
|---|---|---|---|---|---|
| **ASSERT** | 对抗 | "我来扛" | EN 高 | KPI + | 关系 - |
| **THREATEN** | 对抗 | "我知道你的秘密" | EN 中 | 立即脱身 | RISK+15/COR+10 |
| **DOCUMENT** | 防守 | "我留证" | EN 低 | RISK - | 关系 - |
| **EVADE** | 回避 | "再等等" | EN 低 | 无 | 隐患 + |
| **ALLY** | 社交 | "我跟你" | EN 中 | 同盟 + | 树敌 + |
| **TRADE** | 社交 | "互相帮忙" | EN 中 | 双向约束 | 债务未还 |
| **CHARM** | 社交 | "您真好" | EN 中 | 关系 + | 被看低 |
| **PROBE** | 信息 | "让我探" | EN 中 | 情报 + | 被发现 |
| **DEFLECT** | 灰色 | "是他的" | EN 中 | 脱身 | COR+/关系崩 |

### 5.2 THREATEN 解锁条件

```python
def can_threaten(ctx: NarrativeContext, target_id: str) -> bool:
    # 条件1: 上位者对下位者（权力差>30）
    target_power = ctx.character_states[target_id].power
    if target_power - 10 > 30:  # 玩家固定power=10
        return True

    # 条件2: 掌握对方把柄（P1临时：特定历史事件）
    grip_events = {
        "CHR_01": ["EVT_19"],  # 审计暴露
        "CHR_05": ["EVT_17"],  # 倒签文件
    }
    history = [t["event_id"] for t in ctx.turn_history]
    return any(e in history for e in grip_events.get(target_id, []))
```

### 5.3 PROBE 子模式

```python
# 一个PROBE选项，UI展开后选择子模式
SceneOption(
    option_id="OPT_PROBE",
    prototype="PROBE",
    label="试探情报",
    sub_mode=None,  # UI展开后选择
)

# 子模式定义（在原型中）
PROBE_SUBMODES = {
    "active": {
        "label": "主动套话",
        "modifier": 0,
        "en_cost": -5,
        "relation_impact": -3,
        "success_rate": 0.50,
        "intel_depth": "deep",
    },
    "passive": {
        "label": "被动观察",
        "modifier": +1,
        "en_cost": -2,
        "relation_impact": 0,
        "success_rate": 0.80,
        "intel_depth": "surface",
    },
}
```

### 5.4 标签系统

| 标签 | 触发条件 | 效果 |
|---|---|---|
| 刺头 | 连续3次ASSERT对抗上司 | 上司敌意+，同级尊重+ |
| 过度防御 | 连续3次DOCUMENT | 被认为不信任团队，晋升- |
| 老油条 | 连续3次EVADE | HR关注，合作事件- |
| 变色龙 | 连续3次ALLY站不同队 | 所有人信任- |
| 债奴 | 累积3笔未还TRADE债务 | 被追讨事件触发频率×2 |
| 马屁精 | 对同一人连续3次CHARM | 同事-5，该人+20 |
| 威胁者 | 连续2次THREATEN | 所有人防备，情报获取-30% |
| 甩锅王 | 连续3次DEFLECT | 没人愿意合作 |

---

## 6. 场景系统

### 6.1 场景触发机制（混合驱动）

优先级从高到低：
1. **强制主线**（剧情线指定，不可跳过）
2. **链式场景**（EventChain 的后续事件）
3. **角色诉求**（urgency 最高的角色主动找玩家）
4. **日常填充**（从时段场景池随机）
5. **退化**（回退到旧单角色事件）

### 6.2 时段场景池

每个时段有独立的场景池，角色劫持权重但不能跳出池。

```python
TIME_PERIOD_SCENE_POOLS = {
    "早晨": {
        "themes": ["正式推进"],
        "scenes": ["SCENE_MORNING_MEETING", "SCENE_BOSS_DROP_BY", "SCENE_PROGRESS_REPORT"],
        "weight_modifiers": {"CHR_01": 1.5, "CHR_03": 1.2},
    },
    "中午": {
        "themes": ["非正式社交"],
        "scenes": ["SCENE_CAFE_ENCOUNTER", "SCENE_WATERCOOLER", "SCENE_LUNCH_PUSH"],
        "weight_modifiers": {"CHR_02": 1.8, "CHR_04": 1.3},
    },
    "下午": {
        "themes": ["交付压力"],
        "scenes": ["SCENE_CLIENT_CALL", "SCENE_REVIEW_MEETING", "SCENE_BUDGET_CHECK"],
        "weight_modifiers": {"CHR_03": 1.8, "CHR_01": 1.2, "CHR_05": 1.2},
    },
    "晚上": {
        "themes": ["透支救火"],
        "scenes": ["SCENE_OVERTIME", "SCENE_LATE_EMAIL", "SCENE_BOSS_TALK"],
        "weight_modifiers": {"CHR_01": 1.8, "CHR_03": 1.5},
        "special": "玩家EN<30时，50%概率跳过本时段（累倒）",
    },
    "深夜": {
        "themes": ["独处/灰色"],
        "scenes": ["SCENE_ALONE", "SCENE_GRAY_ACTION", "SCENE_REFLECT"],
        "weight_modifiers": {},
        "special": "无其他角色在场",
    },
}
```

### 6.3 角色在场判定

```
1. required_characters 全部放入
2. optional_characters 按 inclusion_rules 过滤
3. 检查 exclusion_rules（死敌不同时在场）
4. 角色劫持：高urgency角色强制插入，替换最低priority的optional角色
5. 超过 max_characters 时，按 power 排序截断
```

### 6.4 隐藏目标

完全隐藏，零提示。玩家通过观察角色反应自行发现。

```python
HiddenGoal(
    goal_id="GOAL_SPLIT_AB",
    description="让陈总监和小林在会上公开分歧",
    reward={"relation_with_CHR_06": +10, "info_unlock": "CHR_01_weakness"},
    trigger_condition="CHR_01.mood=='急躁' and CHR_02.mood=='懒散' and player_chose_ASSERT",
)
```

### 6.5 选项数量限制

每个场景最多 **6个选项**。超过时按 `sort_priority` 过滤，保留优先级最高的6个。

---

## 7. 持久化设计

### 7.1 新增表

```sql
-- 角色动态状态（覆盖更新，始终只有当前值）
CREATE TABLE character_states (
    session_id TEXT NOT NULL,
    character_id TEXT NOT NULL,
    relation_to_player INTEGER DEFAULT 0,
    mood TEXT DEFAULT '平静',
    trust INTEGER DEFAULT 50,
    stress INTEGER DEFAULT 50,
    power INTEGER DEFAULT 50,
    hidden_stance TEXT DEFAULT '',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (session_id, character_id)
);

-- 角色关系网
CREATE TABLE relation_edges (
    session_id TEXT NOT NULL,
    character_a TEXT NOT NULL,
    character_b TEXT NOT NULL,
    relation_value INTEGER DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (session_id, character_a, character_b)
);

-- 角色状态关键变化日志
CREATE TABLE character_state_changes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    turn_index INTEGER NOT NULL,
    character_id TEXT NOT NULL,
    field_changed TEXT NOT NULL,
    old_value TEXT,
    new_value TEXT,
    reason TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 事件链进度
CREATE TABLE chain_progress (
    session_id TEXT NOT NULL,
    chain_id TEXT NOT NULL,
    current_position INTEGER DEFAULT 0,
    is_active INTEGER DEFAULT 1,
    next_trigger_turn INTEGER DEFAULT 0,
    completed_at TIMESTAMP,
    PRIMARY KEY (session_id, chain_id)
);

-- 剧情线推进状态
CREATE TABLE storyline_progress (
    session_id TEXT NOT NULL,
    storyline_id TEXT NOT NULL,
    current_act_index INTEGER DEFAULT 0,
    act_start_turn INTEGER DEFAULT 0,
    branch_taken TEXT DEFAULT '',
    completed INTEGER DEFAULT 0,
    PRIMARY KEY (session_id, storyline_id)
);
```

### 7.2 "有意义变化"的记录标准

只记录以下变化：
- relation 变化 >= 10 或跨过 0 点
- mood 发生变化
- trust/stress/power 变化 >= 15
- 由重大事件（隐患翻面、项目暴雷）引起的变化

---

## 8. 向后兼容策略

**硬切换**。不保留双轨运行。

### 8.1 旧数据

- 现有 `game_sessions` / `turn_logs` 表保留不动
- 新增表与旧表共存
- 旧存档无法使用新功能，需要重新 `init`

### 8.2 旧代码

- `ACTION_RULES` 保留别名指向 `STRATEGY_PROTOTYPES`
- `Event` / `Character` 的旧字段保持默认值
- `_pick_character` / `_pick_event` 内部调用 `_build_scene`，对外接口不变

### 8.3 CLI 接口

- `game_state_cli.py turn` 命令行为不变
- 输出格式升级：显示场景标题、在场角色、角色台词

---

## 9. 内容生产规范

### 9.1 写一个 Scene 的 checklist

```
□ scene_id: 唯一标识
□ title: 场景标题
□ time_periods: 可出现的时段列表
□ location: 地点描述
□ required_characters: 必须在场的角色（至少1个）
□ optional_characters: 可选角色列表
□ inclusion_rules: 可选角色的准入条件
□ narrative_fn: 渲染函数名（必须在 narrative_fns.py 中定义）
□ player_options: 2-6个选项，每个选项有 prototype/label/target_character
□ hidden_goals: 0-2个隐藏目标（可选）
```

### 9.2 narrative_fn 编写规范

```python
def render_<scene_id>(scene: Scene, ctx: NarrativeContext) -> RenderedScene:
    """
    渲染场景文本。

    Args:
        scene: 场景定义
        ctx: 叙事上下文（包含所有角色状态、关系网、历史等）

    Returns:
        RenderedScene: 包含 opening/lines/options 的渲染结果
    """
    # 1. 获取在场角色状态
    # 2. 构建开场描述（根据角色状态变化）
    # 3. 构建角色台词（根据心情、关系、历史事件）
    # 4. 构建玩家选项（过滤不可见选项）
    # 5. 返回 RenderedScene
```

### 9.3 visibility_condition 语法

简单表达式，引擎用 `eval` 解析：

```
"relation>30"                    # 玩家与目标角色关系>30
"relation<-20"                   # 关系<-20
"mood=='急躁'"                   # 目标角色心情为急躁
"has_event('EVT_19')"            # 本局经历过指定事件
"turn>5"                         # 当前回合>5
"stress>80"                      # 目标角色压力>80
"power>60"                       # 目标角色权力>60
```

支持的操作符：`>`, `<`, `==`, `>=`, `<=`

---

## 10. 与现有系统的关系

| 现有系统 | 关系 | 处理方式 |
|---|---|---|
| `CHARACTERS` / `EVENTS` | 扩展 | 新增字段用默认值，旧数据兼容 |
| `ACTION_RULES` | 改造 | 改名为 `STRATEGY_PROTOTYPES`，保留别名 |
| `storylines.py` | 升级 | `Act` 结构扩展，旧 acts_json 可迁移 |
| `materials.py` | 兼容 | 自定义角色/事件接入新 Scene 系统 |
| `db.py` | 扩展 | 新增5个表，旧表不动 |
| `engine.py` | 改造 | `_build_scene` 替代核心抽卡逻辑 |
| `scripts/game_state_cli.py` | 升级 | 输出格式支持场景渲染 |

---

## 11. 实施检查清单

### Phase 1 编码顺序

- [ ] 创建分支 `feature/scene-driven`
- [ ] 扩展 `content.py`：Character + Event + Scene + SceneOption + SceneResult
- [ ] 新建 `content_v2_types.py`：Personality / CharacterState / NarrativeContext / RenderedScene
- [ ] 新建 `strategy_prototypes.py`：9个原型完整定义
- [ ] 新建 `relation_graph.py`：RelationGraph 类
- [ ] 新建 `narrative_fns.py`：NarrativeContext + 第一个 narrative_fn（项目评审会）
- [ ] 新建 `scenes.py`：场景库，至少定义"项目评审会"场景
- [ ] 扩展 `db.py`：新增5个表 + init_db 更新
- [ ] 改造 `engine.py`：_build_scene + 结算流程
- [ ] 升级 `game_state_cli.py`：show 命令支持场景渲染输出
- [ ] 验证：CLI 跑通"项目评审会"多角色场景

---

*文档版本：v1.0*
*创建日期：2026-05-14*
*事实源状态：有效*
