import json
import random
import sqlite3
from dataclasses import dataclass
from typing import Optional

from runtime.db import connect, init_db
from runtime.content import (
    ACTION_DISPLAY,
    ACTION_MODIFIERS,
    CHARACTER_NAME_MAP,
    CHARACTERS,
    EVENTS_BY_CHARACTER,
)
from runtime.materials import (
    load_active_custom_characters,
    load_active_custom_events,
    load_active_custom_hazards,
    merge_characters,
    merge_events,
)
from runtime.storylines import get_active_storyline, advance_act


INITIAL_STATE = {
    "hp": 100,
    "en": 100,
    "st": 100,
    "kpi": 100,
    "risk": 0,
    "cor": 0,
}

# 每 24 回合为 1 个工作日（每回合 20 分钟，24 回合 = 8 小时）
TURNS_PER_DAY = 24


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


def _json_load(text: str | None, fallback: object) -> object:
    if not text:
        return fallback
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return fallback


def _tier_by_roll(score: int) -> str:
    if score <= 5:
        return "CRITICAL_FAIL"
    if score <= 10:
        return "FAIL"
    if score <= 14:
        return "BARELY"
    if score <= 18:
        return "SUCCESS"
    return "CRITICAL_SUCCESS"


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
    day_turn = turn_index % TURNS_PER_DAY
    if day_turn < 9:          # 09:00-12:00 上午
        return "上午"
    elif day_turn < 12:       # 12:00-13:00 午休
        return "午休"
    elif day_turn < 21:       # 13:00-18:00 下午
        return "下午"
    elif day_turn < 24:       # 18:00-21:00 加班
        return "加班"
    else:                     # 21:00+ 深夜
        return "深夜"


def _time_period_weight_modifier(time_period: str) -> dict[str, float]:
    """不同时间段的角色权重修正。"""
    modifiers = {
        "上午": {"CHR_01": 1.0, "CHR_02": 1.0, "CHR_03": 1.2, "CHR_04": 0.8, "CHR_05": 1.0, "CHR_06": 0.8},
        "午休": {"CHR_01": 0.5, "CHR_02": 1.5, "CHR_03": 0.5, "CHR_04": 0.5, "CHR_05": 0.5, "CHR_06": 0.3},
        "下午": {"CHR_01": 1.0, "CHR_02": 1.0, "CHR_03": 1.5, "CHR_04": 1.0, "CHR_05": 1.2, "CHR_06": 1.0},
        "加班": {"CHR_01": 1.5, "CHR_02": 0.5, "CHR_03": 1.8, "CHR_04": 0.8, "CHR_05": 1.0, "CHR_06": 0.5},
        "深夜": {"CHR_01": 1.8, "CHR_02": 0.3, "CHR_03": 0.8, "CHR_04": 1.2, "CHR_05": 0.5, "CHR_06": 0.3},
    }
    return modifiers.get(time_period, modifiers["上午"])


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
# 隐患生成：覆盖文档中定义的所有事件-隐患映射
# ---------------------------------------------------------------------------

# 事件→隐患映射表（对应 Skill 文档 possible_followups）
_EVENT_HAZARD_MAP: dict[str, dict] = {
    "EVT_04": {"id": "HZD_RESPONSIBILITY", "name": "责任未明确", "countdown": 3, "severity": 2},
    "EVT_06": {"id": "HZD_RESPONSIBILITY", "name": "责任未明确", "countdown": 3, "severity": 2},
    "EVT_07": {"id": "HZD_ORAL_PROMISE", "name": "口头承诺", "countdown": 2, "severity": 1},
    "EVT_08": {"id": "HZD_REQ_UNCONFIRMED", "name": "需求未确认", "countdown": 3, "severity": 1},
    "EVT_10": {"id": "HZD_ORAL_PROMISE", "name": "口头承诺", "countdown": 2, "severity": 1},
    "EVT_17": {"id": "HZD_BACKDATED_DOC", "name": "倒签文件", "countdown": 5, "severity": 2},
    "EVT_18": {"id": "HZD_MISSING_RECEIPT", "name": "报销缺材料", "countdown": 3, "severity": 1},
    "EVT_19": {"id": "HZD_COMPLIANCE", "name": "合规隐患", "countdown": 3, "severity": 2},
    "EVT_23": {"id": "HZD_WEEKLY_REPORT", "name": "周报未交", "countdown": 2, "severity": 1},
    "EVT_24": {"id": "HZD_UNREAD_MSG", "name": "未回消息", "countdown": 2, "severity": 1},
}

# 行动→隐患映射
_ACTION_HAZARD_MAP: dict[str, dict] = {
    "SHIFT_BLAME": {"id": "HZD_ACTION_BLAME", "name": "甩锅痕迹", "countdown": 3, "severity": 1},
    "DELAY_AVOID": {"id": "HZD_ACTION_DELAY", "name": "拖延积压", "countdown": 2, "severity": 1},
}


def _new_hazard(event_id: str, action_type: str, db_path: str | None = None) -> dict | None:
    """根据事件和行动类型生成隐患卡。合并内置映射与自定义映射。"""
    # 合并自定义隐患
    custom_hazard_map = load_active_custom_hazards(db_path)
    combined_map = {**_EVENT_HAZARD_MAP, **custom_hazard_map}

    # 优先检查事件映射
    hazard = combined_map.get(event_id)
    if hazard:
        return dict(hazard)
    # 其次检查行动映射
    action_hazard = _ACTION_HAZARD_MAP.get(action_type.upper())
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
    option_keys = ["DIRECT_EXECUTE", "EMAIL_TRACE", "NARROW_SCOPE", "SOFT_REFUSE"]
    if state["en"] < 35:
        option_keys.append("RECOVERY_BREAK")
    else:
        option_keys.append("REQUEST_CONFIRMATION")
    options = []
    for idx, key in enumerate(option_keys[:5], start=1):
        display = ACTION_DISPLAY.get(key, {"title": key, "summary": "执行该策略"})
        options.append(
            {
                "index": idx,
                "action": key,
                "title": display["title"],
                "summary": display["summary"],
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
        character_id = _pick_character(raw, conn, next_time_period, db_path)
        event = _pick_event(session_id, character_id, conn, db_path)
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
                "actor": CHARACTER_NAME_MAP.get(character_id, "未知角色"),
                "event": event.get("name") or event.get("event_name") or event["event_id"],
                "prompt": f"{CHARACTER_NAME_MAP.get(character_id, '某人')} 发来新压力：{event.get('name') or event['event_id']}",
            },
            "risk_tip": risk_tip,
            "options": _build_options(raw),
            "input_hint": "回复编号或直接说你的应对方式。",
        }
    finally:
        conn.close()


def _replenish_project() -> dict:
    """当所有项目完成时，自动补充新项目（已文档化）。"""
    return {"id": "PRJ_WEEKLY", "name": "本周交付", "progress": 0, "target": 5, "pressure": 2}


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
        tier = _tier_by_roll(score)
        multiplier = {"CRITICAL_FAIL": 1.5, "FAIL": 1.0, "BARELY": 0.7, "SUCCESS": 0.4, "CRITICAL_SUCCESS": 0.2}[tier]

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

        # ---- 剧情线推进 ----
        # 当幕事件已结算，检查是否需要推进到下一幕
        storyline_context = None
        if raw_session.get("storyline_id"):
            next_act = advance_act(session_id, db_path)
            if next_act:
                storyline_context = {
                    "storyline_id": raw_session["storyline_id"],
                    "next_act": next_act,
                }

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
