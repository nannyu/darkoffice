"""定制剧情线管理。

职责：
1. 剧情线 CRUD（storylines 表）
2. 激活 / 停用管理
3. 幕推进逻辑
4. 当前激活剧情线查询

剧情线数据结构（acts_json）:
[
    {
        "act_index": 0,
        "title": "第一幕：入局",
        "character_id": "CHR_01",
        "event_ids": ["EVT_01", "CUSTOM_EVT_01"],
        "narrative_bridge": "你刚入职，直属上司陈总监就给了你一个下马威……",
        "completion_condition": "turn_resolved"
    },
    ...
]

act_index 从 0 开始。completion_condition 目前仅支持 "turn_resolved"（该幕事件被处理后自动推进）。
"""

from __future__ import annotations

import json
from typing import Optional

from runtime.db import connect, init_db
from runtime.branches import match_branch, check_endings


# ---------------------------------------------------------------------------
# 剧情线 CRUD
# ---------------------------------------------------------------------------

def create_storyline(
    storyline_id: str,
    title: str,
    description: str = "",
    acts: list[dict] | None = None,
    metadata: dict | None = None,
    db_path: str | None = None,
) -> str:
    """创建一条剧情线，返回 storyline_id。"""
    conn = connect(db_path)
    try:
        init_db(conn)
        conn.execute(
            """
            INSERT INTO storylines (storyline_id, title, description, acts_json, metadata_json)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                storyline_id,
                title,
                description,
                json.dumps(acts or [], ensure_ascii=False),
                json.dumps(metadata or {}, ensure_ascii=False),
            ),
        )
        conn.commit()
        return storyline_id
    finally:
        conn.close()


def list_storylines(db_path: str | None = None) -> list[dict]:
    """列出所有剧情线。"""
    conn = connect(db_path)
    try:
        rows = conn.execute(
            "SELECT storyline_id, title, description, is_active, current_act_index, session_id, created_at FROM storylines ORDER BY storyline_id"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_storyline(storyline_id: str, db_path: str | None = None) -> dict:
    """获取剧情线详情（含解析后的 acts 列表）。"""
    conn = connect(db_path)
    try:
        row = conn.execute(
            "SELECT * FROM storylines WHERE storyline_id = ?", (storyline_id,)
        ).fetchone()
        if not row:
            raise ValueError(f"storyline not found: {storyline_id}")
        result = dict(row)
        result["acts"] = json.loads(result.get("acts_json", "[]"))
        result["metadata"] = json.loads(result.get("metadata_json", "{}"))
        return result
    finally:
        conn.close()


def delete_storyline(storyline_id: str, db_path: str | None = None) -> bool:
    """删除一条剧情线。"""
    conn = connect(db_path)
    try:
        cur = conn.execute("DELETE FROM storylines WHERE storyline_id = ?", (storyline_id,))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# 激活 / 停用管理
# ---------------------------------------------------------------------------

def activate_storyline(
    session_id: str,
    storyline_id: str,
    db_path: str | None = None,
) -> bool:
    """将剧情线激活并绑定到指定 session。

    同时更新 game_sessions 的 storyline_id 字段。
    """
    conn = connect(db_path)
    try:
        # 停用该 session 已有的剧情线
        conn.execute(
            "UPDATE storylines SET is_active = 0 WHERE session_id = ?",
            (session_id,),
        )
        # 激活新剧情线
        cur = conn.execute(
            """
            UPDATE storylines
            SET is_active = 1, current_act_index = 0, session_id = ?
            WHERE storyline_id = ?
            """,
            (session_id, storyline_id),
        )
        if cur.rowcount == 0:
            return False
        # 同步更新 game_sessions
        conn.execute(
            "UPDATE game_sessions SET storyline_id = ? WHERE session_id = ?",
            (storyline_id, session_id),
        )
        conn.commit()
        return True
    finally:
        conn.close()


def deactivate_storyline(session_id: str, db_path: str | None = None) -> bool:
    """停用当前 session 的剧情线，恢复随机模式。"""
    conn = connect(db_path)
    try:
        cur = conn.execute(
            "UPDATE storylines SET is_active = 0 WHERE session_id = ? AND is_active = 1",
            (session_id,),
        )
        conn.execute(
            "UPDATE game_sessions SET storyline_id = NULL WHERE session_id = ?",
            (session_id,),
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# 幕推进
# ---------------------------------------------------------------------------

def advance_act(
    session_id: str,
    action_type: str | None = None,
    result_tier: str | None = None,
    state: dict | None = None,
    turn_logs: list[dict] | None = None,
    turn_index: int | None = None,
    db_path: str | None = None,
) -> dict | None:
    """推进剧情线到下一幕。支持分支条件和结局判定。

    Args:
        action_type: 当前回合行动类型（用于分支判断）
        result_tier: 当前回合结果等级（用于分支判断）
        state: 当前状态（用于分支/结局判断）
        turn_logs: 历史回合日志（用于 action_history 判断）
        turn_index: 当前回合数（用于 turn_index_min/max 判断）

    Returns:
        - 下一幕 dict（正常推进或分支跳转）
        - {"ending": ending_dict}（触发结局）
        - None（剧情线结束且无结局）
    """
    conn = connect(db_path)
    try:
        row = conn.execute(
            "SELECT * FROM storylines WHERE session_id = ? AND is_active = 1",
            (session_id,),
        ).fetchone()

        # 如果剧情线已结束，仍检查结局条件
        if not row:
            ended_row = conn.execute(
                "SELECT * FROM storylines WHERE session_id = ? AND is_active = 0",
                (session_id,),
            ).fetchone()
            if ended_row and state is not None:
                ended_storyline = dict(ended_row)
                metadata = json.loads(ended_storyline.get("metadata_json", "{}"))
                endings = metadata.get("endings", [])
                if endings:
                    triggered = check_endings(endings, state, turn_logs, turn_index)
                    if triggered:
                        return {"ending": triggered}
            return None

        storyline = dict(row)
        acts = json.loads(storyline.get("acts_json", "[]"))
        current_idx = int(storyline.get("current_act_index", 0))
        metadata = json.loads(storyline.get("metadata_json", "{}"))
        endings = metadata.get("endings", [])

        # ---- 1. 检查当前幕的分支条件（优先于结局） ----
        current_act = acts[current_idx] if current_idx < len(acts) else None
        if current_act and action_type is not None:
            branches = current_act.get("branches", [])
            if branches and state is not None:
                matched = match_branch(
                    branches,
                    action_type,
                    result_tier or "",
                    state,
                    turn_logs,
                    turn_index,
                )
                if matched:
                    target_act_index = matched["target_act"]
                    # target_act 是 act_index 而非数组索引，需要查找
                    target_array_idx = None
                    for idx, act in enumerate(acts):
                        if act.get("act_index") == target_act_index:
                            target_array_idx = idx
                            break
                    if target_array_idx is not None:
                        conn.execute(
                            "UPDATE storylines SET current_act_index = ? WHERE storyline_id = ?",
                            (target_array_idx, storyline["storyline_id"]),
                        )
                        conn.commit()
                        # 将分支的 narrative 合并到目标幕
                        target_act = dict(acts[target_array_idx])
                        if matched.get("narrative"):
                            target_act["_branch_narrative"] = matched["narrative"]
                        if matched.get("label"):
                            target_act["_branch_label"] = matched["label"]
                        return target_act

        # ---- 2. 默认推进 ----
        # 优先使用当前幕的 next_act_index 字段；否则查找当前 act_index 的下一个
        current_act_data = acts[current_idx] if current_idx < len(acts) else None
        next_act_index = current_act_data.get("next_act_index") if current_act_data else None

        if next_act_index is not None:
            # 通过 act_index 查找目标数组索引
            target_array_idx = None
            for idx, act in enumerate(acts):
                if act.get("act_index") == next_act_index:
                    target_array_idx = idx
                    break
            if target_array_idx is not None:
                conn.execute(
                    "UPDATE storylines SET current_act_index = ? WHERE storyline_id = ?",
                    (target_array_idx, storyline["storyline_id"]),
                )
                conn.commit()
                return acts[target_array_idx]

        # ---- 3. 剧情线自然结束，检查结局条件 ----
        if endings and state is not None:
            triggered = check_endings(endings, state, turn_logs, turn_index)
            if triggered:
                # 触发结局，停用剧情线
                conn.execute(
                    "UPDATE storylines SET is_active = 0 WHERE storyline_id = ?",
                    (storyline["storyline_id"],),
                )
                conn.commit()
                return {"ending": triggered}

        # 无结局，剧情线结束（保留 game_sessions.storyline_id 以便后续结局检查）
        conn.execute(
            "UPDATE storylines SET is_active = 0 WHERE storyline_id = ?",
            (storyline["storyline_id"],),
        )
        conn.commit()
        return None
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# 查询
# ---------------------------------------------------------------------------

def get_active_storyline(session_id: str, db_path: str | None = None) -> Optional[dict]:
    """获取当前 session 激活的剧情线及当前幕信息。

    Returns:
        {"storyline_id", "title", "current_act": {...}, "total_acts": N}
        若无激活剧情线返回 None。
    """
    conn = connect(db_path)
    try:
        row = conn.execute(
            "SELECT * FROM storylines WHERE session_id = ? AND is_active = 1",
            (session_id,),
        ).fetchone()
        if not row:
            return None

        storyline = dict(row)
        acts = json.loads(storyline.get("acts_json", "[]"))
        current_idx = int(storyline.get("current_act_index", 0))

        current_act = acts[current_idx] if current_idx < len(acts) else None
        metadata = json.loads(storyline.get("metadata_json", "{}"))
        return {
            "storyline_id": storyline["storyline_id"],
            "title": storyline["title"],
            "description": storyline.get("description", ""),
            "current_act_index": current_idx,
            "current_act": current_act,
            "total_acts": len(acts),
            "metadata": metadata,
        }
    finally:
        conn.close()
