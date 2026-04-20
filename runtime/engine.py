import json
import random
from dataclasses import dataclass

from runtime.db import connect, init_db


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
    roll_value: int
    result_tier: str
    delta: dict
    state: dict


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
    state["risk"] = max(0, state["risk"])
    state["cor"] = max(0, state["cor"])
    return state


def create_session(session_id: str, db_path: str | None = None) -> dict:
    conn = connect(db_path)
    init_db(conn)
    conn.execute(
        """
        INSERT INTO game_sessions (
            session_id, hp, en, st, kpi, risk, cor
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            session_id,
            INITIAL_STATE["hp"],
            INITIAL_STATE["en"],
            INITIAL_STATE["st"],
            INITIAL_STATE["kpi"],
            INITIAL_STATE["risk"],
            INITIAL_STATE["cor"],
        ),
    )
    conn.commit()
    return get_session(session_id, db_path)


def get_session(session_id: str, db_path: str | None = None) -> dict:
    conn = connect(db_path)
    row = conn.execute(
        "SELECT * FROM game_sessions WHERE session_id = ?",
        (session_id,),
    ).fetchone()
    if not row:
        raise ValueError(f"session not found: {session_id}")
    return dict(row)


def apply_turn(
    session_id: str,
    action_type: str,
    action_mod: int = 0,
    db_path: str | None = None,
) -> TurnResult:
    conn = connect(db_path)
    session = conn.execute(
        "SELECT * FROM game_sessions WHERE session_id = ?",
        (session_id,),
    ).fetchone()
    if not session:
        raise ValueError(f"session not found: {session_id}")

    roll = random.randint(1, 20)
    score = roll + action_mod
    tier = _tier_by_roll(score)

    # 用最小可运行规则跑通持久化闭环，后续可替换为完整文档规则。
    base = {"hp": 0, "en": -10, "st": -5, "kpi": 0, "risk": 1, "cor": 0}
    multiplier = {
        "CRITICAL_FAIL": 1.5,
        "FAIL": 1.0,
        "BARELY": 0.7,
        "SUCCESS": 0.4,
        "CRITICAL_SUCCESS": 0.2,
    }[tier]

    delta = {k: int(v * multiplier) for k, v in base.items()}
    new_state = {
        "hp": session["hp"] + delta["hp"],
        "en": session["en"] + delta["en"],
        "st": session["st"] + delta["st"],
        "kpi": session["kpi"] + delta["kpi"],
        "risk": session["risk"] + delta["risk"],
        "cor": session["cor"] + delta["cor"],
    }
    new_state = _clamp_state(new_state)
    new_turn = int(session["turn_index"]) + 1

    conn.execute(
        """
        UPDATE game_sessions
        SET turn_index = ?, hp = ?, en = ?, st = ?, kpi = ?, risk = ?, cor = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE session_id = ?
        """,
        (
            new_turn,
            new_state["hp"],
            new_state["en"],
            new_state["st"],
            new_state["kpi"],
            new_state["risk"],
            new_state["cor"],
            session_id,
        ),
    )
    conn.execute(
        """
        INSERT INTO turn_logs (
            session_id, turn_index, action_type, roll_value, result_tier,
            delta_json, state_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            session_id,
            new_turn,
            action_type,
            roll,
            tier,
            json.dumps(delta, ensure_ascii=False),
            json.dumps(new_state, ensure_ascii=False),
        ),
    )
    conn.commit()

    return TurnResult(
        session_id=session_id,
        turn_index=new_turn,
        roll_value=roll,
        result_tier=tier,
        delta=delta,
        state=new_state,
    )
