import json
import random
import sqlite3
from dataclasses import dataclass
from copy import deepcopy
from typing import Optional

from runtime.db import connect, init_db
from runtime.content import (
    ACTION_DISPLAY,
    ACTION_MODIFIERS,
    CHARACTER_NAME_MAP,
    CHARACTERS,
    EVENTS_BY_CHARACTER,
    # --- scene-driven v2 imports ---
    CharacterState,
    Intel,
    RenderedScene,
    SceneOption,
    SceneResult,
)
from runtime.materials import (
    load_active_custom_characters,
    load_active_custom_events,
    load_active_custom_hazards,
    merge_characters,
    merge_events,
)
from runtime.rules import (
    ACTION_HAZARD_MAP,
    ACTION_OPTION_POLICY,
    ACTION_RULES,
    DEFAULT_PROJECT,
    EVENT_HAZARD_MAP,
    TURNS_PER_DAY,
    resolution_tier_for_score,
    time_period_for_turn,
    time_period_weight_modifiers,
)
from runtime.storylines import get_active_storyline, advance_act
from runtime.scenes import (
    SCENES,
    TIME_PERIOD_SCENE_POOLS,
    get_scene,
    get_scenes_for_period,
    get_scene_weight_modifiers,
)
from runtime.narrative_fns import (
    NarrativeContext,
    get_narrative_fn,
)
from runtime.relation_graph import RelationGraph, build_initial_relation_graph
from runtime.strategy_prototypes import STRATEGY_PROTOTYPES


def _character_name_map(db_path: str | None = None) -> dict[str, str]:
    """构建包含内置和自定义角色的名称映射。"""
    names = dict(CHARACTER_NAME_MAP)
    for c in load_active_custom_characters(db_path):
        names[c.character_id] = c.name
    return names


INITIAL_STATE = {
    "hp": 100,
    "en": 100,
    "st": 100,
    "kpi": 100,
    "risk": 0,
    "cor": 0,
}

@dataclass
class TurnResult:
    session_id: str
    turn_index: int
    day: int
    time_period: str
    character_id: str
    event_id: str
    roll_value: int
    total_score: int
    action_mod: int
    result_tier: str
    failure_type: str | None
    delta: dict
    state: dict
    statuses: list[dict]
    hazards: list[dict]
    projects: list[dict]
    next_prompt: dict
    storyline_context: dict | None = None
    ending: dict | None = None


def _json_load(text: str | None, fallback: object) -> object:
    if not text:
        return fallback
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return fallback


def _tier_by_roll(score: int) -> str:
    return str(resolution_tier_for_score(score)["id"])


def _clamp_state(state: dict) -> dict:
    state["hp"] = max(0, min(100, state["hp"]))
    state["en"] = max(0, min(100, state["en"]))
    state["st"] = max(0, min(100, state["st"]))
    state["kpi"] = max(0, min(100, state["kpi"]))
    state["risk"] = max(0, min(100, state["risk"]))
    state["cor"] = max(0, min(100, state["cor"]))
    return state


def _status_modifier(state: dict) -> int:
    mod = 0
    if state["en"] >= 70:
        mod += 2
    elif state["en"] < 10:
        mod -= 5
    elif state["en"] < 30:
        mod -= 2
    if state["st"] < 30:
        mod -= 1
    if state["kpi"] < 40:
        mod -= 1
    if state["risk"] >= 50:
        mod -= 1
    return mod


def _derive_statuses(state: dict, event_id: str, hazards: list[dict]) -> list[dict]:
    """根据当前状态推导持续状态。

    event_id 用于判断特定事件触发的状态（如 EVT_03/EVT_11 触发"被盯上"），
    而非从隐患倒计时推导。
    """
    statuses = []
    if state["en"] < 10:
        statuses.append({"id": "STATUS_EXHAUSTED", "name": "濒临崩溃", "duration": 1})
    elif state["en"] < 30:
        statuses.append({"id": "STATUS_LOW_EN", "name": "低精力", "duration": 1})
    if state["st"] < 30:
        statuses.append({"id": "STATUS_LOW_ST", "name": "低体力", "duration": 1})
    if state["kpi"] < 40:
        statuses.append({"id": "STATUS_LOW_KPI", "name": "危险绩效", "duration": 1})
    if state["risk"] >= 50:
        statuses.append({"id": "STATUS_HIGH_RISK", "name": "高风险", "duration": 1})
    if state["cor"] >= 50:
        statuses.append({"id": "STATUS_HIGH_COR", "name": "高污染", "duration": 1})
    # "被盯上"由特定事件触发，不再从隐患倒计时推导
    if event_id in {"EVT_03", "EVT_11", "EVT_16"}:
        statuses.append({"id": "STATUS_UNDER_WATCH", "name": "被盯上", "duration": 2})
    return statuses


def _time_period(turn_index: int) -> str:
    """根据回合数计算当前时间段。

    每 24 回合 = 1 个工作日，按 20 分钟/回合映射到职场时间。
    """
    return str(time_period_for_turn(turn_index)["id"])


def _time_period_weight_modifier(time_period: str) -> dict[str, float]:
    """不同时间段的角色权重修正。"""
    return time_period_weight_modifiers(time_period)


def _weighted_pick(options: list[tuple[object, int]]) -> object:
    pool = [item for item, _ in options]
    weights = [max(1, int(w)) for _, w in options]
    return random.choices(pool, weights=weights, k=1)[0]


def _pick_character(session: dict, conn: sqlite3.Connection, time_period: str, db_path: str | None = None) -> str:
    """抽取本回合来访角色。

    优先级：
    1. 若有激活的剧情线，返回剧情线当前幕指定角色
    2. 否则合并内置角色 + 自定义角色后加权抽取
    """
    # 剧情线优先
    storyline = get_active_storyline(session["session_id"], db_path)
    if storyline and storyline.get("current_act"):
        char_id = storyline["current_act"].get("character_id")
        if char_id:
            return char_id

    # 合并内置 + 自定义角色
    built_in = CHARACTERS
    custom = load_active_custom_characters(db_path)
    all_characters = merge_characters(built_in, custom)

    weighted = []
    period_mods = _time_period_weight_modifier(time_period)
    for c in all_characters:
        w = c.base_weight
        w = int(w * period_mods.get(c.character_id, 1.0))
        if c.character_id == "CHR_04" and session["kpi"] < 40:
            w = int(w * 2)
        if c.character_id == "CHR_05" and session["risk"] >= 50:
            w = int(w * 1.6)
        if c.character_id == "CHR_06" and session["cor"] >= 50:
            w = int(w * 1.6)
        # 自定义角色使用默认权重，不再做特殊修正
        weighted.append((c.character_id, w))

    prev = conn.execute(
        "SELECT character_id FROM turn_logs WHERE session_id = ? ORDER BY id DESC LIMIT 1",
        (session["session_id"],),
    ).fetchone()
    if prev:
        previous_id = prev["character_id"]
        weighted = [(cid, int(w * 0.45) if cid == previous_id else w) for cid, w in weighted]
    return _weighted_pick(weighted)


def _pick_event(session_id: str, character_id: str, conn: sqlite3.Connection, db_path: str | None = None) -> dict:
    """抽取本回合事件。

    优先级：
    1. 若有激活的剧情线且当前幕指定了 event_ids，从中抽取
    2. 否则合并内置事件 + 自定义事件后抽取
    """
    # 剧情线优先
    storyline = get_active_storyline(session_id, db_path)
    if storyline and storyline.get("current_act"):
        event_ids = storyline["current_act"].get("event_ids", [])
        if event_ids:
            picked_id = random.choice(event_ids)
            # 尝试从合并后的事件池查找
            built_in_events = EVENTS_BY_CHARACTER
            custom_events = load_active_custom_events(db_path)
            all_events = merge_events(built_in_events, custom_events)
            for event in all_events.get(character_id, []):
                if event.event_id == picked_id:
                    return {"event_id": event.event_id, "name": event.name, "base_effect": event.base_effect}
            # 若在事件池中找不到（可能是其他角色的事件），返回通用事件
            return {
                "event_id": picked_id,
                "name": "剧情事件",
                "base_effect": {"hp": 0, "en": -10, "st": -5, "kpi": 0, "risk": 3, "cor": 0},
            }

    # 合并内置 + 自定义事件
    built_in_events = EVENTS_BY_CHARACTER
    custom_events = load_active_custom_events(db_path)
    all_events = merge_events(built_in_events, custom_events)

    pool = all_events.get(character_id, [])
    if not pool:
        return {
            "event_id": "EVT_GENERIC",
            "name": "临时任务压迫",
            "base_effect": {"hp": 0, "en": -8, "st": -4, "kpi": 0, "risk": 2, "cor": 0},
        }
    prev = conn.execute(
        "SELECT event_id FROM turn_logs WHERE session_id = ? ORDER BY id DESC LIMIT 1",
        (session_id,),
    ).fetchone()
    prev_event = prev["event_id"] if prev else None
    weighted = []
    for event in pool:
        weighted.append((event, 2 if event.event_id == prev_event else 10))
    picked = _weighted_pick(weighted)
    return {"event_id": picked.event_id, "name": picked.name, "base_effect": picked.base_effect}


# ---------------------------------------------------------------------------
# Scene-Driven v2: 角色状态与场景构建
# ---------------------------------------------------------------------------

def _init_character_state(character_id: str) -> CharacterState:
    """根据内置角色定义初始化动态状态。"""
    for c in CHARACTERS:
        if c.character_id == character_id:
            return CharacterState(
                character_id=character_id,
                relation_to_player=c.initial_relation,
                mood=c.initial_mood,
                trust=c.initial_trust,
                stress=c.initial_stress,
                power=c.initial_power,
                hidden_stance=c.hidden_stance,
            )
    return CharacterState(character_id=character_id)


def _load_character_states(session_id: str, conn: sqlite3.Connection) -> dict[str, CharacterState]:
    """从数据库加载角色动态状态，缺失的自动初始化。"""
    states = {}
    rows = conn.execute(
        "SELECT * FROM character_states WHERE session_id = ?", (session_id,)
    ).fetchall()
    for row in rows:
        states[row["character_id"]] = CharacterState(
            character_id=row["character_id"],
            relation_to_player=row["relation_to_player"],
            mood=row["mood"],
            trust=row["trust"],
            stress=row["stress"],
            power=row["power"],
            hidden_stance=row["hidden_stance"],
        )
    # 补齐缺失的角色
    for c in CHARACTERS:
        if c.character_id not in states:
            states[c.character_id] = _init_character_state(c.character_id)
    return states


def _save_character_states(session_id: str, states: dict[str, CharacterState], conn: sqlite3.Connection):
    """保存角色动态状态到数据库（覆盖更新）。"""
    for char_id, state in states.items():
        conn.execute(
            """
            INSERT INTO character_states (session_id, character_id, relation_to_player, mood, trust, stress, power, hidden_stance)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(session_id, character_id) DO UPDATE SET
                relation_to_player=excluded.relation_to_player,
                mood=excluded.mood,
                trust=excluded.trust,
                stress=excluded.stress,
                power=excluded.power,
                hidden_stance=excluded.hidden_stance,
                updated_at=CURRENT_TIMESTAMP
            """,
            (session_id, char_id, state.relation_to_player, state.mood, state.trust, state.stress, state.power, state.hidden_stance),
        )


# ---------------------------------------------------------------------------
# Phase 2: 角色状态波动逻辑
# ---------------------------------------------------------------------------

MOOD_DRIFT_TABLE: list[tuple[str, callable]] = [
    # (目标心情, 条件函数(state, char))
    ("恐慌", lambda s, c: s.stress >= 85),
    ("冷漠", lambda s, c: s.stress >= 75 and s.relation_to_player < -30),
    ("得意", lambda s, c: s.relation_to_player >= 50 and s.stress < 50),
    ("平静", lambda s, c: s.relation_to_player >= 20 and s.stress < 60),
    ("阴沉", lambda s, c: s.relation_to_player <= -50 and s.stress >= 50),
    ("急躁", lambda s, c: s.relation_to_player <= -30 and s.stress >= 40),
]


def _target_mood(state: CharacterState, char) -> str:
    """根据当前状态计算目标心情。"""
    for mood, cond in MOOD_DRIFT_TABLE:
        if cond(state, char):
            return mood
    return state.mood


def _update_mood_from_relation(state: CharacterState, char):
    """心情随关系和压力自然漂移。

    规则：
    - stress >= 85 → 恐慌（高压崩溃）
    - stress >= 75 + relation < -30 → 冷漠（情感封闭）
    - relation >= 50 + stress < 50 → 得意（关系好+压力低）
    - relation >= 20 + stress < 60 → 平静
    - relation <= -50 + stress >= 50 → 阴沉
    - relation <= -30 + stress >= 40 → 急躁
    - 当前心情已为目标时，30%概率随机回退到"平静"
    """
    target = _target_mood(state, char)
    if state.mood == target:
        # 已经在目标心情，30%概率回退到平静（情绪波动）
        if random.random() < 0.3:
            state.mood = "平静"
        return
    # 有 40% 概率向目标心情漂移
    if random.random() < 0.4:
        state.mood = target


def _update_stress_natural(state: CharacterState, char, was_present: bool):
    """压力自然波动（每回合结算后调用）。

    规则：
    - 基础：每回合 +2（职场自然压力）
    - 在场：额外 +3（场景中的压力）
    - 野心加成：ambition > 60 时，额外 +(ambition-60)//10
    - 犬儒加成：cynicism > 70 时，额外 +2
    - 崩溃恢复：stress > 90 时，自动 -15（崩溃后的短暂恢复）
    - 信任缓冲：trust > 60 时，-1
    - 权力缓冲：power > 70 时，-1
    """
    delta = 2
    if was_present:
        delta += 3
    if char.personality.ambition > 60:
        delta += (char.personality.ambition - 60) // 10
    if char.personality.cynicism > 70:
        delta += 2
    if state.trust > 60:
        delta -= 1
    if state.power > 70:
        delta -= 1

    new_stress = state.stress + delta

    # 崩溃恢复
    if state.stress > 90:
        new_stress -= 15

    state.stress = max(0, min(100, new_stress))


def _relation_edge_effects(state: CharacterState, char) -> list[str]:
    """返回当前触发的关系边缘效应标签。"""
    tags = []
    if state.relation_to_player >= 60:
        tags.append("坚定盟友")
    if state.relation_to_player <= -60:
        tags.append("死敌")
    if state.trust <= 20:
        tags.append("不信任")
    if state.trust >= 70:
        tags.append("深度信任")
    if state.stress >= 80:
        tags.append("高压崩溃边缘")
    if state.stress >= 90:
        tags.append("已崩溃")
    return tags


# ---------------------------------------------------------------------------
# Phase 3: 信息系统 — 情报发现与 THREATEN 锁钥
# ---------------------------------------------------------------------------

def _load_discovered_intel(session_id: str, conn: sqlite3.Connection) -> list[str]:
    """加载玩家已发现的情报ID列表。"""
    rows = conn.execute(
        "SELECT intel_id FROM intel_discovered WHERE session_id = ?", (session_id,)
    ).fetchall()
    return [r["intel_id"] for r in rows]


def _discover_intel(
    session_id: str,
    intel: Intel,
    turn_index: int,
    scene_id: str,
    method: str,
    conn: sqlite3.Connection,
) -> bool:
    """记录一条新发现的情报。返回是否为新发现。"""
    existing = conn.execute(
        "SELECT 1 FROM intel_discovered WHERE session_id = ? AND intel_id = ?",
        (session_id, intel.intel_id),
    ).fetchone()
    if existing:
        return False
    conn.execute(
        """
        INSERT INTO intel_discovered (session_id, intel_id, source_character, target_character,
                                       discovered_at_turn, discovered_in_scene, discovery_method)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (session_id, intel.intel_id, intel.source_character, intel.target_character,
         turn_index, scene_id, method),
    )
    return True


def _check_intel_discovery(
    intel: Intel,
    scene_id: str,
    present_chars: list[str],
    chosen_option: SceneOption,
    char_states: dict[str, CharacterState],
    turn_index: int,
) -> bool:
    """检查情报发现条件是否满足。"""
    cond = intel.discovery_condition
    if not cond:
        return False

    parts = [p.strip() for p in cond.split("and")]
    for part in parts:
        # 场景检查
        if part.startswith("scene=="):
            if scene_id != part[7:]:
                return False
        elif part == "scene_has_CHR_01":
            if "CHR_01" not in present_chars:
                return False
        elif part == "scene_has_CHR_03":
            if "CHR_03" not in present_chars:
                return False
        elif part == "scene_has_CHR_05":
            if "CHR_05" not in present_chars:
                return False
        elif part == "scene_has_CHR_06":
            if "CHR_06" not in present_chars:
                return False
        # 行动检查
        elif part == "PROBE":
            if chosen_option.prototype != "PROBE":
                return False
        elif part == "PROBE_passive":
            if chosen_option.prototype != "PROBE" or chosen_option.sub_mode != "passive":
                return False
        elif part == "PROBE_active":
            if chosen_option.prototype != "PROBE" or chosen_option.sub_mode != "active":
                return False
        elif part == "DOCUMENT":
            if chosen_option.prototype != "DOCUMENT":
                return False
        # 角色状态检查
        elif part.startswith("stress_CHR_01>"):
            threshold = int(part[14:])
            state = char_states.get("CHR_01")
            if not state or state.stress <= threshold:
                return False
        elif part.startswith("trust_CHR_01>"):
            threshold = int(part[13:])
            state = char_states.get("CHR_01")
            if not state or state.trust <= threshold:
                return False
        # 回合检查
        elif part.startswith("turn>"):
            threshold = int(part[5:])
            if turn_index <= threshold:
                return False
    return True


def _check_threaten_unlock(
    target_character: str,
    discovered_intel: list[str],
    player_power: int,
    char_states: dict[str, CharacterState],
) -> bool:
    """检查 THREATEN 是否对目标角色解锁。

    解锁条件（满足任一）：
    1. 玩家掌握目标角色的 leverage 类把柄
    2. 玩家 power > 目标角色 power + 30（上位者对下位者）
    3. 目标角色 stress > 80（趁人之危）
    """
    from runtime.content import INTEL_POOL

    # 条件1: 掌握把柄
    for intel in INTEL_POOL:
        if intel.intel_id in discovered_intel and intel.intel_type == "leverage":
            if intel.target_character == target_character:
                return True

    # 条件2: 权力差
    target_state = char_states.get(target_character)
    if target_state and player_power > target_state.power + 30:
        return True

    # 条件3: 趁人之危
    if target_state and target_state.stress > 80:
        return True

    return False


def _evaluate_condition(condition: str, char_states: dict[str, CharacterState], session: dict) -> bool:
    """评估简单的 visibility_condition 表达式。"""
    if not condition:
        return True
    # 简单解析：relation>30, mood=='急躁', turn>5
    try:
        if condition.startswith("relation"):
            # 格式如 "relation>30"，默认检查第一个在场角色
            for char_id, state in char_states.items():
                expr = f"{state.relation_to_player}{condition[8:]}"
                if eval(expr):
                    return True
            return False
        if condition.startswith("mood=="):
            expected = condition[6:].strip("'\"")
            for state in char_states.values():
                if state.mood == expected:
                    return True
            return False
        if condition.startswith("turn"):
            turn_idx = session.get("turn_index", 0)
            return eval(f"{turn_idx}{condition[4:]}")
        return True
    except Exception:
        return True


# ---------------------------------------------------------------------------
# Phase 4: 七日谈结构 — 幕管理与 Boss 战
# ---------------------------------------------------------------------------

ACT_CONFIG: dict[int, dict] = {
    1: {"name": "温水煮青蛙", "turn_range": (1, 14), "boss_turn": 14, "boss_scene": "SCENE_BOSS_FIRST_REVIEW"},
    2: {"name": "裂痕显现", "turn_range": (15, 28), "boss_turn": 18, "boss_scene": "SCENE_BOSS_FACTION_CLASH"},
    3: {"name": "风暴中心", "turn_range": (29, 35), "boss_turn": 35, "boss_scene": "SCENE_BOSS_AUDIT_EVE"},
}

BOSS_ENDING_TURN = 35


def _current_act(turn_index: int) -> dict | None:
    """根据回合数返回当前幕配置。"""
    for act_num, config in ACT_CONFIG.items():
        min_turn, max_turn = config["turn_range"]
        if min_turn <= turn_index <= max_turn:
            return {**config, "act_number": act_num}
    return None


def _is_boss_turn(turn_index: int, time_period: str) -> str | None:
    """检查当前是否为 Boss 战回合。返回 Boss 场景ID或None。

    Boss 战在指定回合强制触发，无视当前时段匹配。
    """
    act = _current_act(turn_index)
    if not act:
        return None
    if turn_index == act["boss_turn"]:
        return act["boss_scene"]
    return None


def _resolve_ending(session_id: str, char_states: dict[str, CharacterState], raw_session: dict, conn: sqlite3.Connection) -> dict | None:
    """根据游戏状态判定结局。

    结局条件（按优先级）：
    1. 隐藏结局·扳倒上司: 掌握 INTEL_CHEN_PANIC + relation_CHR_01<=-50 + cor>=50
    2. 好结局·自立门户: cor>=60 + kpi>=80 + relation_CHR_06>=30
    3. 中结局·跳槽成功: en>=30 + 至少1个leverage + 至少1个外部联系(intel)
    4. 坏结局·背锅离职: risk>=80 or hp<=0 or st<=0
    5. 普通结局·继续苟着: 以上均不满足
    """
    from runtime.content import INTEL_POOL

    discovered = _load_discovered_intel(session_id, conn)
    discovered_set = set(discovered)

    # 收集状态
    state = dict(raw_session)
    for cid, cs in char_states.items():
        state[f"relation_with_{cid}"] = cs.relation_to_player
    state["discovered_intel"] = discovered

    # 检查隐藏结局
    has_chen_leverage = "INTEL_CHEN_PANIC" in discovered_set
    rel_chen = char_states.get("CHR_01", CharacterState("")).relation_to_player
    cor = raw_session.get("cor", 0)
    if has_chen_leverage and rel_chen <= -60 and cor >= 55:
        return {"ending_id": "END_HIDDEN_TAKEDOWN", "name": "扳倒上司", "description": "你利用掌握的把柄，成功让陈总监下了台。但你不知道的是，下一个被针对的会不会是你。", "ending_type": "hidden"}

    # 检查好结局
    kpi = raw_session.get("kpi", 100)
    rel_rival = char_states.get("CHR_06", CharacterState("")).relation_to_player
    if cor >= 60 and kpi >= 80 and rel_rival >= 30:
        return {"ending_id": "END_GOOD_INDEPENDENT", "name": "自立门户", "description": "你积累了足够的资源和盟友，终于不用再受制于人。", "ending_type": "good"}

    # 检查中结局
    en = raw_session.get("en", 100)
    has_leverage = any(i.intel_type == "leverage" for i in INTEL_POOL if i.intel_id in discovered_set)
    has_external = any(i.intel_id in discovered_set for i in INTEL_POOL if i.source_character in ("CHR_03", "CHR_06"))
    if en >= 30 and has_leverage and has_external:
        return {"ending_id": "END_NEUTRAL_ESCAPE", "name": "跳槽成功", "description": "你带着积累的经验和人脉，跳到了更好的平台。", "ending_type": "neutral"}

    # 检查坏结局
    risk = raw_session.get("risk", 0)
    hp = raw_session.get("hp", 100)
    st = raw_session.get("st", 100)
    if risk >= 70 or hp <= 0 or st <= 0:
        return {"ending_id": "END_BAD_SCAPEGOAT", "name": "背锅离职", "description": "审计的风暴中，你成了那个被推出的替罪羊。", "ending_type": "bad"}

    # 普通结局
    return {"ending_id": "END_NORMAL_CONTINUE", "name": "继续苟着", "description": "你熬过了这一周，但下周呢？", "ending_type": "normal"}


def _build_scene(session_id: str, conn: sqlite3.Connection, time_period: str, db_path: str | None = None) -> tuple[Scene, dict[str, CharacterState]] | None:
    """构建本回合场景。

    返回 (Scene, 角色状态字典) 或 None（走旧路径）。
    """
    # 获取当前回合数
    session_row = conn.execute("SELECT turn_index FROM game_sessions WHERE session_id = ?", (session_id,)).fetchone()
    current_turn = int(session_row["turn_index"]) + 1 if session_row else 1

    # Phase 4: Boss 战强制触发
    boss_scene_id = _is_boss_turn(current_turn, time_period)
    if boss_scene_id:
        scene = get_scene(boss_scene_id)
        if scene:
            char_states = _load_character_states(session_id, conn)
            present_chars = list(scene.required_characters)
            for char_id in scene.optional_characters:
                if char_id in char_states and _evaluate_condition(scene.inclusion_rules.get(char_id, ""), {char_id: char_states[char_id]}, dict(session_row or {})):
                    present_chars.append(char_id)
            for char_id in present_chars:
                if char_id not in char_states:
                    char_states[char_id] = _init_character_state(char_id)
            return scene, {cid: char_states[cid] for cid in present_chars if cid in char_states}

    # 1. 从时段场景池获取场景列表
    scene_pool = get_scenes_for_period(time_period)
    if not scene_pool:
        return None

    # 2. 随机选一个场景（P1 简化，后续加权）
    scene_id = random.choice(scene_pool)
    scene = get_scene(scene_id)
    if not scene:
        return None

    # 3. 加载角色动态状态
    session = dict(conn.execute("SELECT * FROM game_sessions WHERE session_id = ?", (session_id,)).fetchone() or {})
    char_states = _load_character_states(session_id, conn)

    # 4. 确定在场角色
    present_chars = list(scene.required_characters)
    for char_id in scene.optional_characters:
        if char_id in char_states and _evaluate_condition(scene.inclusion_rules.get(char_id, ""), {char_id: char_states[char_id]}, session):
            present_chars.append(char_id)

    # 5. 角色劫持：stress 最高的角色强制插入
    if char_states:
        stressed_chars = sorted(
            [(cid, s.stress) for cid, s in char_states.items() if cid not in present_chars],
            key=lambda x: x[1],
            reverse=True,
        )
        if stressed_chars and stressed_chars[0][1] > 80:
            present_chars.append(stressed_chars[0][0])

    # 6. 截断到 max_characters（留1个位置给玩家）
    max_chars = min(scene.max_characters - 1, len(present_chars))
    present_chars = present_chars[:max_chars]

    # 7. 确保在场角色都有状态记录
    for char_id in present_chars:
        if char_id not in char_states:
            char_states[char_id] = _init_character_state(char_id)

    return scene, {cid: char_states[cid] for cid in present_chars if cid in char_states}


# ---------------------------------------------------------------------------
# 隐患生成：覆盖文档中定义的所有事件-隐患映射
# ---------------------------------------------------------------------------

def _new_hazard(event_id: str, action_type: str, db_path: str | None = None) -> dict | None:
    """根据事件和行动类型生成隐患卡。合并内置映射与自定义映射。"""
    # 合并自定义隐患
    custom_hazard_map = load_active_custom_hazards(db_path)
    combined_map = {**EVENT_HAZARD_MAP, **custom_hazard_map}

    # 优先检查事件映射
    hazard = combined_map.get(event_id)
    if hazard:
        return dict(hazard)
    # 其次检查行动映射
    action_hazard = ACTION_HAZARD_MAP.get(action_type.upper())
    if action_hazard:
        return dict(action_hazard)
    return None


def _tick_hazards(hazards: list[dict]) -> tuple[list[dict], dict]:
    delta = {"hp": 0, "en": 0, "st": 0, "kpi": 0, "risk": 0, "cor": 0}
    remaining = []
    for hazard in hazards:
        current = dict(hazard)
        current["countdown"] = int(current.get("countdown", 1)) - 1
        if current["countdown"] <= 0:
            severity = int(current.get("severity", 1))
            delta["hp"] -= 2 * severity
            delta["kpi"] -= 4 * severity
            delta["risk"] += 6 * severity
        else:
            remaining.append(current)
    return remaining, delta


def _tick_projects(projects: list[dict], action_type: str) -> tuple[list[dict], dict]:
    delta = {"hp": 0, "en": 0, "st": 0, "kpi": 0, "risk": 0, "cor": 0}
    progress_actions = {"DIRECT_EXECUTE", "WORK_OVERTIME", "REQUEST_CONFIRMATION"}
    updated = []
    for project in projects:
        current = dict(project)
        pressure = int(current.get("pressure", 1))
        delta["en"] -= pressure
        delta["st"] -= max(1, pressure // 2)
        if action_type.upper() in progress_actions:
            current["progress"] = int(current.get("progress", 0)) + 1
            delta["kpi"] += 1
        if int(current.get("progress", 0)) >= int(current.get("target", 5)):
            delta["kpi"] += 3
            delta["risk"] -= 2
            continue
        updated.append(current)
    return updated, delta


def _merge_delta(*parts: dict) -> dict:
    merged = {"hp": 0, "en": 0, "st": 0, "kpi": 0, "risk": 0, "cor": 0}
    for part in parts:
        for key in merged:
            merged[key] += int(part.get(key, 0))
    return merged


def _resolve_failure(state: dict) -> str | None:
    """检查是否触发失败结局。

    HP/EN/ST/KPI 归零 → 对应失败结局
    RISK/COR 满100 → 对应失败结局
    优先级：HP > EN > ST > KPI > RISK > COR（同时触发多项时取最高优先级）
    """
    if state["hp"] <= 0:
        return "HP_DEPLETED"       # 崩溃结局
    if state["en"] <= 0:
        return "EN_DEPLETED"       # 精神崩溃结局
    if state["st"] <= 0:
        return "ST_DEPLETED"       # 体力耗尽结局
    if state["kpi"] <= 0:
        return "KPI_DEPLETED"      # 被开除结局
    if state["risk"] >= 100:
        return "RISK_OVERFLOW"     # 暴雷结局
    if state["cor"] >= 100:
        return "COR_OVERFLOW"      # 黑化结局
    return None


def _build_options(state: dict) -> list[dict]:
    option_keys = list(ACTION_OPTION_POLICY["core"])
    if state["en"] < 35:
        option_keys.append(str(ACTION_OPTION_POLICY["low_energy_bonus"]))
    else:
        option_keys.append(str(ACTION_OPTION_POLICY["default_bonus"]))
    options = []
    for idx, key in enumerate(option_keys[:5], start=1):
        display = ACTION_DISPLAY.get(key, {"title": key, "summary": "执行该策略"})
        options.append(
            {
                "index": idx,
                "action": key,
                "title": display["title"],
                "summary": display["summary"],
                "category": ACTION_RULES.get(key, {}).get("category", "通用策略"),
            }
        )
    return options


def build_next_prompt(session_id: str, db_path: str | None = None) -> dict:
    conn = connect(db_path)
    try:
        session = conn.execute("SELECT * FROM game_sessions WHERE session_id = ?", (session_id,)).fetchone()
        if not session:
            raise ValueError(f"session not found: {session_id}")
        raw = dict(session)
        simulated_next_turn = int(raw["turn_index"]) + 1
        next_time_period = _time_period(simulated_next_turn)
        name_map = _character_name_map(db_path)

        # === Scene-Driven v2: 尝试构建场景 ===
        scene_result = _build_scene(session_id, conn, next_time_period, db_path)
        if scene_result:
            scene, char_states = scene_result
            # 保存当前场景到 session（供 apply_turn 使用）
            scene_meta = {
                "current_scene_id": scene.scene_id,
                "present_characters": list(char_states.keys()),
            }
            conn.execute(
                "UPDATE game_sessions SET status_json = ? WHERE session_id = ?",
                (json.dumps(scene_meta, ensure_ascii=False), session_id)
            )
            conn.commit()

            # 构建 NarrativeContext
            ctx = NarrativeContext(
                session=raw,
                player_state={"name": "你"},
                character_states=char_states,
                relation_graph=RelationGraph(),
                turn_history=[],
                active_chains=[],
                active_storyline=None,
                time_period=next_time_period,
                turn_index=simulated_next_turn,
            )

            # Phase 3: 加载已发现情报，用于 THREATEN 锁钥检查
            discovered_intel = _load_discovered_intel(session_id, conn)
            player_power = 50  # P1: 玩家固定power，后续可从session扩展

            # 过滤选项：visibility_condition + THREATEN锁钥
            visible_options = []
            for opt in scene.player_options:
                # 检查 visibility_condition
                if opt.visibility_condition:
                    target_state = char_states.get(opt.target_character) if opt.target_character else None
                    check_states = {opt.target_character: target_state} if target_state else char_states
                    if not _evaluate_condition(opt.visibility_condition, check_states, raw):
                        continue
                # 检查 THREATEN 锁钥
                if opt.prototype == "THREATEN" and opt.target_character:
                    if not _check_threaten_unlock(opt.target_character, discovered_intel, player_power, char_states):
                        continue
                visible_options.append(opt)

            # 如果过滤后没有选项，保留第一个作为保底
            if not visible_options and scene.player_options:
                visible_options = [scene.player_options[0]]

            # 调用 narrative_fn 渲染场景
            fn = get_narrative_fn(scene.narrative_fn)
            if fn:
                rendered = fn(scene, ctx)
            else:
                rendered = RenderedScene(opening=scene.title, options=visible_options)

            # 用过滤后的选项覆盖渲染出的选项
            rendered_options = visible_options

            return {
                "turn_index": simulated_next_turn,
                "day": int(raw.get("day", 1)),
                "time_period": next_time_period,
                "status_bar": {
                    "生命": f"{raw['hp']}/100",
                    "精力": f"{raw['en']}/100",
                    "体力": f"{raw['st']}/100",
                    "绩效": raw["kpi"],
                    "风险": raw["risk"],
                    "污染": raw["cor"],
                },
                "scene": {
                    "scene_id": scene.scene_id,
                    "title": scene.title,
                    "location": scene.location,
                    "opening": rendered.opening,
                    "lines": [
                        {"speaker": l.speaker, "mood": l.mood, "text": l.text, "subtext": l.subtext}
                        for l in rendered.lines
                    ],
                    "options": [
                        {"index": i + 1, "option_id": opt.option_id, "label": opt.label, "prototype": opt.prototype}
                        for i, opt in enumerate(rendered_options)
                    ],
                },
                "input_hint": "回复选项编号或描述你的应对方式。",
            }

        # === 旧路径：剧情线/随机抽卡 ===
        storyline = get_active_storyline(session_id, db_path)
        if storyline and storyline.get("current_act"):
            act = storyline["current_act"]
            character_id = act.get("character_id", "CHR_01")
            event_ids = act.get("event_ids", [])
            if event_ids:
                event_id = event_ids[0]
                built_in_events = EVENTS_BY_CHARACTER
                custom_events = load_active_custom_events(db_path)
                all_events = merge_events(built_in_events, custom_events)
                event_name = event_id
                for ev in all_events.get(character_id, []):
                    if ev.event_id == event_id:
                        event_name = ev.name
                        break
            else:
                event_id = "EVT_GENERIC"
                event_name = "剧情事件"
        else:
            character_id = _pick_character(raw, conn, next_time_period, db_path)
            event = _pick_event(session_id, character_id, conn, db_path)
            event_id = event.get("event_id", "EVT_GENERIC")
            event_name = event.get("name") or event.get("event_name") or event_id

        risk_tip = "风险偏高，优先考虑留痕或缩小范围。" if raw["risk"] >= 40 else "保持节奏，避免口头承诺。"
        return {
            "turn_index": simulated_next_turn,
            "day": int(raw.get("day", 1)),
            "time_period": next_time_period,
            "status_bar": {
                "生命": f"{raw['hp']}/100",
                "精力": f"{raw['en']}/100",
                "体力": f"{raw['st']}/100",
                "绩效": raw["kpi"],
                "风险": raw["risk"],
                "污染": raw["cor"],
            },
            "event_summary": {
                "actor": name_map.get(character_id, "未知角色"),
                "event": event_name,
                "prompt": f"{name_map.get(character_id, '某人')} 发来新压力：{event_name}",
            },
            "risk_tip": risk_tip,
            "options": _build_options(raw),
            "input_hint": "回复编号或直接说你的应对方式。",
        }
    finally:
        conn.close()


def _replenish_project() -> dict:
    """当所有项目完成时，自动补充新项目（已文档化）。"""
    return deepcopy(DEFAULT_PROJECT)


def create_session(session_id: str, db_path: str | None = None) -> dict:
    conn = connect(db_path)
    try:
        init_db(conn)
        projects = [_replenish_project()]
        conn.execute(
            """
            INSERT INTO game_sessions (
                session_id, hp, en, st, kpi, risk, cor, project_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                INITIAL_STATE["hp"],
                INITIAL_STATE["en"],
                INITIAL_STATE["st"],
                INITIAL_STATE["kpi"],
                INITIAL_STATE["risk"],
                INITIAL_STATE["cor"],
                json.dumps(projects, ensure_ascii=False),
            ),
        )
        # Phase 2: 初始化角色动态状态
        for c in CHARACTERS:
            state = _init_character_state(c.character_id)
            conn.execute(
                """
                INSERT INTO character_states (session_id, character_id, relation_to_player, mood, trust, stress, power, hidden_stance)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (session_id, c.character_id, state.relation_to_player, state.mood, state.trust, state.stress, state.power, state.hidden_stance),
            )
        # Phase 2: 初始化关系图（逐边写入）
        init_graph = build_initial_relation_graph()
        for edge_key, value in init_graph.edges.items():
            chars = sorted(list(edge_key))
            conn.execute(
                "INSERT INTO relation_edges (session_id, character_a, character_b, relation_value) VALUES (?, ?, ?, ?)",
                (session_id, chars[0], chars[1], value),
            )
        conn.commit()
    finally:
        conn.close()
    return get_session(session_id, db_path)


def get_session(session_id: str, db_path: str | None = None) -> dict:
    conn = connect(db_path)
    try:
        row = conn.execute("SELECT * FROM game_sessions WHERE session_id = ?", (session_id,)).fetchone()
        if not row:
            raise ValueError(f"session not found: {session_id}")
        return dict(row)
    finally:
        conn.close()


def _apply_scene_turn(
    session_id: str,
    option_id: str,
    raw_session: dict,
    scene_meta: dict,
    hazards: list,
    projects: list,
    conn: sqlite3.Connection,
    db_path: str | None = None,
) -> TurnResult:
    """场景模式的回合结算（P1 简化版）。"""
    scene_id = scene_meta.get("current_scene_id", "")
    scene = get_scene(scene_id)
    if not scene:
        raise ValueError(f"scene not found: {scene_id}")

    present_char_ids = scene_meta.get("present_characters", [])
    char_states = _load_character_states(session_id, conn)
    present_states = {cid: char_states[cid] for cid in present_char_ids if cid in char_states}

    # 找到玩家选择的选项
    chosen_option = None
    for opt in scene.player_options:
        if opt.option_id == option_id:
            chosen_option = opt
            break
    if not chosen_option:
        chosen_option = scene.player_options[0] if scene.player_options else None
    if not chosen_option:
        raise ValueError(f"no valid option found for {option_id}")

    # 获取原型
    prototype = STRATEGY_PROTOTYPES.get(chosen_option.prototype)
    if not prototype:
        raise ValueError(f"prototype not found: {chosen_option.prototype}")

    new_turn = int(raw_session["turn_index"]) + 1
    new_day = int(raw_session.get("day", 1)) + (new_turn // TURNS_PER_DAY - int(raw_session["turn_index"]) // TURNS_PER_DAY)
    time_period = _time_period(new_turn)

    # ---- 骰子结算 ----
    auto_action_mod = prototype.modifier
    status_mod = _status_modifier(raw_session)
    roll = random.randint(1, 20)
    score = roll + auto_action_mod + status_mod
    tier_rule = resolution_tier_for_score(score)
    tier = str(tier_rule["id"])
    multiplier = float(tier_rule["multiplier"])

    # ---- 基础数值效果 ----
    base_effects = dict(prototype.base_effects)
    for k, v in chosen_option.custom_effect.items():
        base_effects[k] = base_effects.get(k, 0) + v

    _PENALTY_WHEN_POSITIVE = {"risk", "cor"}
    player_delta = {}
    for k, v in base_effects.items():
        if v >= 0 and k not in _PENALTY_WHEN_POSITIVE:
            player_delta[k] = int(v * (2.0 - multiplier))
        else:
            player_delta[k] = int(v * multiplier)

    for key in ["hp", "en", "st", "kpi", "risk", "cor"]:
        if key not in player_delta:
            player_delta[key] = 0

    # ---- 关系变化 ----
    relation_changes = {}
    for char_id, state in present_states.items():
        char = next((c for c in CHARACTERS if c.character_id == char_id), None)
        if char:
            role = char.role_type or "中立者"
            delta = prototype.relation_impact_by_role.get(role, 0)
            relation_changes[char_id] = delta
            state.relation_to_player = max(-100, min(100, state.relation_to_player + delta))

    # ---- Phase 2: 角色状态波动 ----
    edge_effect_tags: dict[str, list[str]] = {}
    for char_id, state in char_states.items():
        char = next((c for c in CHARACTERS if c.character_id == char_id), None)
        if not char:
            continue
        was_present = char_id in present_states

        # 1. 场景内即时压力影响（在场角色）
        if was_present:
            if prototype.category == "对抗":
                state.stress = max(0, min(100, state.stress + 5))
            elif prototype.category == "社交":
                state.stress = max(0, min(100, state.stress - 3))

        # 2. 自然波动（所有角色）
        _update_stress_natural(state, char, was_present)
        _update_mood_from_relation(state, char)

        # 3. 关系边缘效应
        edge_effect_tags[char_id] = _relation_edge_effects(state, char)

    # ---- Phase 3: 情报发现 ----
    newly_discovered: list[dict] = []
    from runtime.content import INTEL_POOL
    for intel in INTEL_POOL:
        if _check_intel_discovery(
            intel, scene_id, present_char_ids, chosen_option, char_states, new_turn
        ):
            if _discover_intel(session_id, intel, new_turn, scene_id, chosen_option.prototype, conn):
                newly_discovered.append({
                    "intel_id": intel.intel_id,
                    "intel_type": intel.intel_type,
                    "description": intel.description,
                })

    # ---- Phase 3: 隐藏立场揭示 ----
    revealed_stances: list[dict] = []
    for char_id, state in present_states.items():
        char = next((c for c in CHARACTERS if c.character_id == char_id), None)
        if not char or not char.hidden_stance:
            continue
        # 揭示条件：trust >= 60 或 relation >= 50
        if state.trust >= 60 or state.relation_to_player >= 50:
            # 检查是否已记录
            existing = conn.execute(
                "SELECT 1 FROM player_notes WHERE session_id = ? AND target_id = ? AND note_type = 'stance'",
                (session_id, char_id),
            ).fetchone()
            if not existing:
                conn.execute(
                    "INSERT INTO player_notes (session_id, note_type, target_id, content) VALUES (?, ?, ?, ?)",
                    (session_id, "stance", char_id, char.hidden_stance),
                )
                revealed_stances.append({
                    "character_id": char_id,
                    "character_name": char.name,
                    "stance": char.hidden_stance,
                })

    # ---- 系统结算 ----
    hazards, hazard_tick_delta = _tick_hazards(hazards)
    projects, project_tick_delta = _tick_projects(projects, chosen_option.prototype)

    delta = _merge_delta(player_delta, hazard_tick_delta, project_tick_delta)

    if not projects:
        projects = [_replenish_project()]

    new_state = {
        "hp": raw_session["hp"] + delta["hp"],
        "en": raw_session["en"] + delta["en"],
        "st": raw_session["st"] + delta["st"],
        "kpi": raw_session["kpi"] + delta["kpi"],
        "risk": raw_session["risk"] + delta["risk"],
        "cor": raw_session["cor"] + delta["cor"],
    }
    new_state = _clamp_state(new_state)
    statuses = _derive_statuses(new_state, scene_id, hazards)
    failure_type = _resolve_failure(new_state)

    # 保存角色状态
    _save_character_states(session_id, char_states, conn)

    # 清除当前场景标记
    conn.execute(
        "UPDATE game_sessions SET status_json = ? WHERE session_id = ?",
        (json.dumps([], ensure_ascii=False), session_id)
    )

    # 更新游戏状态
    conn.execute(
        """
        UPDATE game_sessions
        SET turn_index = ?, day = ?, hp = ?, en = ?, st = ?, kpi = ?, risk = ?, cor = ?,
            status_json = ?, hazard_json = ?, project_json = ?, updated_at = CURRENT_TIMESTAMP
        WHERE session_id = ?
        """,
        (
            new_turn,
            new_day,
            new_state["hp"],
            new_state["en"],
            new_state["st"],
            new_state["kpi"],
            new_state["risk"],
            new_state["cor"],
            json.dumps(statuses, ensure_ascii=False),
            json.dumps(hazards, ensure_ascii=False),
            json.dumps(projects, ensure_ascii=False),
            session_id,
        ),
    )
    conn.execute(
        """
        INSERT INTO turn_logs (
            session_id, turn_index, character_id, event_id, action_type, action_mod,
            roll_value, total_score, result_tier, failure_type, delta_json, state_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            session_id,
            new_turn,
            ",".join(present_char_ids) if present_char_ids else "CHR_01",
            scene_id,
            option_id,
            auto_action_mod,
            roll,
            score,
            tier,
            failure_type,
            json.dumps(delta, ensure_ascii=False),
            json.dumps(new_state, ensure_ascii=False),
        ),
    )
    conn.commit()

    # Phase 4: 结局判定（第 35 回合后）
    ending: dict | None = None
    if new_turn >= BOSS_ENDING_TURN:
        ending = _resolve_ending(session_id, char_states, raw_session, conn)

    return TurnResult(
        session_id=session_id,
        turn_index=new_turn,
        day=new_day,
        time_period=time_period,
        character_id=",".join(present_char_ids) if present_char_ids else "CHR_01",
        event_id=scene_id,
        roll_value=roll,
        total_score=score,
        action_mod=auto_action_mod,
        result_tier=tier,
        failure_type=failure_type,
        delta=delta,
        state=new_state,
        statuses=statuses,
        hazards=hazards,
        projects=projects,
        next_prompt=build_next_prompt(session_id, db_path),
        storyline_context=None,
        ending=ending,
    )


def apply_turn(
    session_id: str,
    action_type: str,
    action_mod: int | None = None,
    db_path: str | None = None,
) -> TurnResult:
    conn = connect(db_path)
    try:
        session = conn.execute("SELECT * FROM game_sessions WHERE session_id = ?", (session_id,)).fetchone()
        if not session:
            raise ValueError(f"session not found: {session_id}")
        raw_session = dict(session)
        hazards = _json_load(raw_session.get("hazard_json"), [])
        projects = _json_load(raw_session.get("project_json"), [])
        if not isinstance(hazards, list):
            hazards = []
        if not isinstance(projects, list):
            projects = []

        # ---- 检查场景模式 ----
        status_data = _json_load(raw_session.get("status_json"), [])
        scene_meta = status_data if isinstance(status_data, dict) else {}
        if scene_meta.get("current_scene_id"):
            return _apply_scene_turn(
                session_id=session_id,
                option_id=action_type,
                raw_session=raw_session,
                scene_meta=scene_meta,
                hazards=hazards,
                projects=projects,
                conn=conn,
                db_path=db_path,
            )

        # ---- 时间与日期 ----
        new_turn = int(raw_session["turn_index"]) + 1
        new_day = int(raw_session.get("day", 1)) + (new_turn // TURNS_PER_DAY - int(raw_session["turn_index"]) // TURNS_PER_DAY)
        time_period = _time_period(new_turn)

        # ---- 事件生成 ----
        character_id = _pick_character(raw_session, conn, time_period, db_path)
        event = _pick_event(session_id, character_id, conn, db_path)
        auto_action_mod = ACTION_MODIFIERS.get(action_type.upper(), 0)
        resolved_action_mod = auto_action_mod if action_mod is None else action_mod
        status_mod = _status_modifier(raw_session)

        # ---- 骰子结算 ----
        roll = random.randint(1, 20)
        score = roll + resolved_action_mod + status_mod
        tier_rule = resolution_tier_for_score(score)
        tier = str(tier_rule["id"])
        multiplier = float(tier_rule["multiplier"])

        # 正值需区分"奖励"和"惩罚"属性：
        # 奖励属性（kpi 正值）：好结果保留/增加，坏结果减少
        # 惩罚属性（risk/cor 正值、所有负值）：好结果减轻，坏结果加重
        _PENALTY_WHEN_POSITIVE = {"risk", "cor"}
        base_event_delta = {}
        for k, v in event["base_effect"].items():
            if v >= 0 and k not in _PENALTY_WHEN_POSITIVE:
                base_event_delta[k] = int(v * (2.0 - multiplier))
            else:
                base_event_delta[k] = int(v * multiplier)

        # ---- 行动修正 ----
        action_delta = {"hp": 0, "en": 0, "st": 0, "kpi": 0, "risk": 0, "cor": 0}
        if tier == "CRITICAL_FAIL":
            action_delta["risk"] += 5
        if action_type.upper() == "EMAIL_TRACE":
            action_delta["risk"] -= 8
        if action_type.upper() == "SHIFT_BLAME":
            action_delta["cor"] += 6
            action_delta["risk"] += 3
        if action_type.upper() == "WORK_OVERTIME":
            action_delta["en"] -= 4
            action_delta["st"] -= 4
        if action_type.upper() == "RECOVERY_BREAK":
            action_delta["en"] += 10
            action_delta["st"] += 6
            action_delta["kpi"] -= 2

        # ---- 系统结算 ----
        hazards, hazard_tick_delta = _tick_hazards(hazards)
        projects, project_tick_delta = _tick_projects(projects, action_type)
        new_hazard = _new_hazard(event["event_id"], action_type, db_path)
        if new_hazard and not any(h.get("id") == new_hazard["id"] for h in hazards):
            hazards.append(new_hazard)

        delta = _merge_delta(base_event_delta, action_delta, hazard_tick_delta, project_tick_delta)

        # 项目自动补充：当所有项目完成后，自动分配新项目
        if not projects:
            projects = [_replenish_project()]

        new_state = {
            "hp": raw_session["hp"] + delta["hp"],
            "en": raw_session["en"] + delta["en"],
            "st": raw_session["st"] + delta["st"],
            "kpi": raw_session["kpi"] + delta["kpi"],
            "risk": raw_session["risk"] + delta["risk"],
            "cor": raw_session["cor"] + delta["cor"],
        }
        new_state = _clamp_state(new_state)
        statuses = _derive_statuses(new_state, event["event_id"], hazards)
        failure_type = _resolve_failure(new_state)

        # ---- 剧情线推进 ----
        storyline_context = None
        ending = None
        if raw_session.get("storyline_id"):
            # 获取历史回合日志用于 action_history 判断
            history_rows = conn.execute(
                "SELECT action_type FROM turn_logs WHERE session_id = ? ORDER BY id",
                (session_id,),
            ).fetchall()
            turn_logs = [dict(r) for r in history_rows]
            next_result = advance_act(
                session_id,
                action_type=action_type,
                result_tier=tier,
                state=new_state,
                turn_logs=turn_logs,
                turn_index=new_turn,
                db_path=db_path,
            )
            if next_result and "ending" in next_result:
                ending = next_result["ending"]
                storyline_context = {
                    "storyline_id": raw_session["storyline_id"],
                    "ending": ending,
                }
            elif next_result:
                storyline_context = {
                    "storyline_id": raw_session["storyline_id"],
                    "next_act": next_result,
                }

        conn.execute(
            """
            UPDATE game_sessions
            SET turn_index = ?, day = ?, hp = ?, en = ?, st = ?, kpi = ?, risk = ?, cor = ?,
                status_json = ?, hazard_json = ?, project_json = ?, updated_at = CURRENT_TIMESTAMP
            WHERE session_id = ?
            """,
            (
                new_turn,
                new_day,
                new_state["hp"],
                new_state["en"],
                new_state["st"],
                new_state["kpi"],
                new_state["risk"],
                new_state["cor"],
                json.dumps(statuses, ensure_ascii=False),
                json.dumps(hazards, ensure_ascii=False),
                json.dumps(projects, ensure_ascii=False),
                session_id,
            ),
        )
        conn.execute(
            """
            INSERT INTO turn_logs (
                session_id, turn_index, character_id, event_id, action_type, action_mod,
                roll_value, total_score, result_tier, failure_type, delta_json, state_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                new_turn,
                character_id,
                event["event_id"],
                action_type,
                resolved_action_mod,
                roll,
                score,
                tier,
                failure_type,
                json.dumps(delta, ensure_ascii=False),
                json.dumps(new_state, ensure_ascii=False),
            ),
        )
        conn.commit()

        return TurnResult(
            session_id=session_id,
            turn_index=new_turn,
            day=new_day,
            time_period=time_period,
            character_id=character_id,
            event_id=event["event_id"],
            roll_value=roll,
            total_score=score,
            action_mod=resolved_action_mod,
            result_tier=tier,
            failure_type=failure_type,
            delta=delta,
            state=new_state,
            statuses=statuses,
            hazards=hazards,
            projects=projects,
            next_prompt=build_next_prompt(session_id, db_path),
            storyline_context=storyline_context,
            ending=ending,
        )
    finally:
        conn.close()


def get_history(session_id: str, limit: int = 10, db_path: str | None = None) -> list[dict]:
    conn = connect(db_path)
    try:
        rows = conn.execute(
            """
            SELECT turn_index, character_id, event_id, action_type, action_mod,
                   roll_value, total_score, result_tier, failure_type, delta_json, created_at
            FROM turn_logs
            WHERE session_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (session_id, limit),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_action_stats(session_id: str, db_path: str | None = None) -> list[dict]:
    conn = connect(db_path)
    try:
        rows = conn.execute(
            """
            SELECT action_type,
                   COUNT(*) AS turns,
                   ROUND(AVG(total_score), 2) AS avg_score,
                   SUM(CASE WHEN result_tier IN ('SUCCESS', 'CRITICAL_SUCCESS') THEN 1 ELSE 0 END) AS success_count,
                   SUM(CASE WHEN result_tier = 'CRITICAL_FAIL' THEN 1 ELSE 0 END) AS critical_fail_count
            FROM turn_logs
            WHERE session_id = ?
            GROUP BY action_type
            ORDER BY turns DESC, avg_score DESC
            """,
            (session_id,),
        ).fetchall()
        stats = []
        for row in rows:
            item = dict(row)
            turns = item["turns"] or 1
            item["success_rate"] = round(item["success_count"] / turns, 3)
            stats.append(item)
        return stats
    finally:
        conn.close()
