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


# ---------------------------------------------------------------------------
# 剧情线 CRUD
# ---------------------------------------------------------------------------

def create_storyline(
    storyline_id: str,
    title: str,
    description: str = "",
    acts: list[dict] | None = None,
    db_path: str | None = None,
) -> str:
    """创建一条剧情线，返回 storyline_id。"""
    conn = connect(db_path)
    try:
        init_db(conn)
        conn.execute(
            """
            INSERT INTO storylines (storyline_id, title, description, acts_json)
            VALUES (?, ?, ?, ?)
            """,
            (
                storyline_id,
                title,
                description,
                json.dumps(acts or [], ensure_ascii=False),
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
            "UPDATE storylines SET is_active = 0, session_id = NULL WHERE session_id = ?",
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
            "UPDATE storylines SET is_active = 0, session_id = NULL WHERE session_id = ? AND is_active = 1",
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

def advance_act(session_id: str, db_path: str | None = None) -> Optional[dict]:
    """推进剧情线到下一幕。

    Returns:
        下一幕的信息 dict，若剧情线已结束返回 None。
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
        next_idx = current_idx + 1

        if next_idx >= len(acts):
            # 剧情线已完成，自动停用
            conn.execute(
                "UPDATE storylines SET is_active = 0, session_id = NULL WHERE storyline_id = ?",
                (storyline["storyline_id"],),
            )
            conn.execute(
                "UPDATE game_sessions SET storyline_id = NULL WHERE session_id = ?",
                (session_id,),
            )
            conn.commit()
            return None

        conn.execute(
            "UPDATE storylines SET current_act_index = ? WHERE storyline_id = ?",
            (next_idx, storyline["storyline_id"]),
        )
        conn.commit()
        return acts[next_idx]
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
        return {
            "storyline_id": storyline["storyline_id"],
            "title": storyline["title"],
            "description": storyline.get("description", ""),
            "current_act_index": current_idx,
            "current_act": current_act,
            "total_acts": len(acts),
        }
    finally:
        conn.close()
