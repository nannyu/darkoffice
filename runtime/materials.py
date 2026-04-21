"""素材库管理、文件导入、自定义卡牌加载与合并。

职责：
1. 素材库 CRUD（materials 表）
2. 文件导入（.md / .txt / .pdf）
3. 自定义卡牌 CRUD（custom_cards 表）
4. 自定义卡牌加载到内存并合并入引擎
"""

from __future__ import annotations

import json
from pathlib import Path

from runtime.content import Character, Event, EVENTS_BY_CHARACTER
from runtime.db import connect, init_db


# ---------------------------------------------------------------------------
# 素材库 CRUD
# ---------------------------------------------------------------------------

def add_material(
    title: str,
    source: str = "",
    category: str = "",
    content: str = "",
    file_type: str = "MANUAL",
    original_filename: str | None = None,
    tags: list[str] | None = None,
    metadata: dict | None = None,
    db_path: str | None = None,
) -> int:
    """新增一条素材，返回自增 id。"""
    conn = connect(db_path)
    try:
        init_db(conn)
        cur = conn.execute(
            """
            INSERT INTO materials (title, source, category, content, file_type,
                                   original_filename, tags_json, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                title,
                source,
                category,
                content,
                file_type,
                original_filename,
                json.dumps(tags or [], ensure_ascii=False),
                json.dumps(metadata or {}, ensure_ascii=False),
            ),
        )
        conn.commit()
        return cur.lastrowid  # type: ignore[return-value]
    finally:
        conn.close()


def list_materials(
    category: str | None = None,
    source: str | None = None,
    db_path: str | None = None,
) -> list[dict]:
    """列出素材，可按 category / source 过滤。"""
    conn = connect(db_path)
    try:
        clauses: list[str] = []
        params: list[object] = []
        if category:
            clauses.append("category = ?")
            params.append(category)
        if source:
            clauses.append("source = ?")
            params.append(source)
        where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        rows = conn.execute(
            f"SELECT id, title, source, category, file_type, original_filename, tags_json, created_at FROM materials{where} ORDER BY id DESC",
            params,
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_material(material_id: int, db_path: str | None = None) -> dict:
    """获取单条素材详情。"""
    conn = connect(db_path)
    try:
        row = conn.execute("SELECT * FROM materials WHERE id = ?", (material_id,)).fetchone()
        if not row:
            raise ValueError(f"material not found: {material_id}")
        return dict(row)
    finally:
        conn.close()


def search_materials(keyword: str, db_path: str | None = None) -> list[dict]:
    """按关键词搜索素材（标题 + 内容模糊匹配）。"""
    conn = connect(db_path)
    try:
        pattern = f"%{keyword}%"
        rows = conn.execute(
            """
            SELECT id, title, source, category, file_type, tags_json, created_at
            FROM materials
            WHERE title LIKE ? OR content LIKE ? OR source LIKE ?
            ORDER BY id DESC
            """,
            (pattern, pattern, pattern),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def delete_material(material_id: int, db_path: str | None = None) -> bool:
    """删除一条素材。"""
    conn = connect(db_path)
    try:
        cur = conn.execute("DELETE FROM materials WHERE id = ?", (material_id,))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# 文件导入
# ---------------------------------------------------------------------------

def _read_txt_md(path: Path) -> str:
    """读取 .txt / .md 文件的文本内容。"""
    return path.read_text(encoding="utf-8")


def _read_pdf(path: Path) -> tuple[str, str]:
    """尝试用 pypdf 提取 PDF 文本。

    Returns:
        (content, file_type) — 成功时 file_type="PDF"，失败时 file_type="PDF_BINARY"
    """
    try:
        from pypdf import PdfReader  # type: ignore[import-untyped]

        reader = PdfReader(str(path))
        pages = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
        content = "\n\n".join(pages)
        return content, "PDF"
    except Exception:
        # pypdf 不可用或提取失败，存储文件路径让 Agent 侧读取
        return str(path.resolve()), "PDF_BINARY"


def import_material(
    file_path: str,
    source: str = "",
    category: str = "",
    tags: list[str] | None = None,
    metadata: dict | None = None,
    db_path: str | None = None,
) -> int:
    """从文件导入素材，自动识别格式并提取文本。

    支持 .md / .txt / .pdf。
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"file not found: {file_path}")

    suffix = path.suffix.lower()
    original_filename = path.name
    # 用文件名（去掉扩展名）作为默认标题
    title = path.stem

    if suffix in (".md", ".txt"):
        content = _read_txt_md(path)
        file_type = suffix.lstrip(".").upper()  # "MD" or "TXT"
    elif suffix == ".pdf":
        content, file_type = _read_pdf(path)
    else:
        raise ValueError(f"unsupported file format: {suffix} (supported: .md, .txt, .pdf)")

    return add_material(
        title=title,
        source=source,
        category=category,
        content=content,
        file_type=file_type,
        original_filename=original_filename,
        tags=tags,
        metadata=metadata,
        db_path=db_path,
    )


# ---------------------------------------------------------------------------
# 自定义卡牌 CRUD
# ---------------------------------------------------------------------------

def add_custom_card(
    card_id: str,
    card_type: str,
    card_name: str,
    card_data: dict,
    source_material_id: int | None = None,
    is_active: int = 0,
    db_path: str | None = None,
) -> str:
    """新增一张自定义卡牌，返回 card_id。"""
    conn = connect(db_path)
    try:
        init_db(conn)
        conn.execute(
            """
            INSERT INTO custom_cards (card_id, card_type, card_name, card_data_json,
                                      source_material_id, is_active)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                card_id,
                card_type,
                card_name,
                json.dumps(card_data, ensure_ascii=False),
                source_material_id,
                is_active,
            ),
        )
        conn.commit()
        return card_id
    finally:
        conn.close()


def list_custom_cards(
    card_type: str | None = None,
    active_only: bool = False,
    db_path: str | None = None,
) -> list[dict]:
    """列出自定义卡牌。"""
    conn = connect(db_path)
    try:
        clauses: list[str] = []
        params: list[object] = []
        if card_type:
            clauses.append("card_type = ?")
            params.append(card_type)
        if active_only:
            clauses.append("is_active = 1")
        where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        rows = conn.execute(
            f"SELECT card_id, card_type, card_name, is_active, source_material_id, created_at FROM custom_cards{where} ORDER BY card_id",
            params,
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_custom_card(card_id: str, db_path: str | None = None) -> dict:
    """获取自定义卡牌详情（含 card_data_json 解析后的数据）。"""
    conn = connect(db_path)
    try:
        row = conn.execute("SELECT * FROM custom_cards WHERE card_id = ?", (card_id,)).fetchone()
        if not row:
            raise ValueError(f"custom card not found: {card_id}")
        result = dict(row)
        result["card_data"] = json.loads(result.get("card_data_json", "{}"))
        return result
    finally:
        conn.close()


def activate_card(card_id: str, db_path: str | None = None) -> bool:
    """激活一张自定义卡牌（is_active = 1）。"""
    conn = connect(db_path)
    try:
        cur = conn.execute("UPDATE custom_cards SET is_active = 1 WHERE card_id = ?", (card_id,))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def deactivate_card(card_id: str, db_path: str | None = None) -> bool:
    """停用一张自定义卡牌（is_active = 0）。"""
    conn = connect(db_path)
    try:
        cur = conn.execute("UPDATE custom_cards SET is_active = 0 WHERE card_id = ?", (card_id,))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def delete_custom_card(card_id: str, db_path: str | None = None) -> bool:
    """删除一张自定义卡牌。"""
    conn = connect(db_path)
    try:
        cur = conn.execute("DELETE FROM custom_cards WHERE card_id = ?", (card_id,))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# 自定义卡牌加载与合并
# ---------------------------------------------------------------------------

def load_active_custom_characters(db_path: str | None = None) -> list[Character]:
    """从 custom_cards 加载所有 is_active=1 的 CHARACTER 类型卡牌。

    返回 Character 对象列表，card_id 以 CUSTOM_CHR_ 前缀。
    """
    conn = connect(db_path)
    try:
        rows = conn.execute(
            "SELECT card_id, card_name, card_data_json FROM custom_cards WHERE card_type = 'CHARACTER' AND is_active = 1"
        ).fetchall()
        characters = []
        for row in rows:
            data = json.loads(row["card_data_json"])
            characters.append(
                Character(
                    character_id=row["card_id"],
                    name=data.get("name", row["card_name"]),
                    base_weight=data.get("base_weight", 10),
                    role_type=data.get("role_type"),
                    faction=data.get("faction"),
                    tags=data.get("tags"),
                    passive_effect=data.get("passive_effect"),
                    speech_style=data.get("speech_style"),
                )
            )
        return characters
    finally:
        conn.close()


def load_active_custom_events(db_path: str | None = None) -> dict[str, list[Event]]:
    """从 custom_cards 加载所有 is_active=1 的 EVENT 类型卡牌。

    返回 {character_id: [Event, ...]} 映射，与 EVENTS_BY_CHARACTER 结构一致。
    """
    conn = connect(db_path)
    try:
        rows = conn.execute(
            "SELECT card_id, card_name, card_data_json FROM custom_cards WHERE card_type = 'EVENT' AND is_active = 1"
        ).fetchall()
        events_by_char: dict[str, list[Event]] = {}
        for row in rows:
            data = json.loads(row["card_data_json"])
            character_id = data.get("character_id", "CHR_01")
            event = Event(
                event_id=row["card_id"],
                character_id=character_id,
                name=data.get("name", row["card_name"]),
                base_effect=data.get("base_effect", {"hp": 0, "en": -8, "st": -4, "kpi": 0, "risk": 2, "cor": 0}),
                event_category=data.get("event_category"),
                pressure_level=data.get("pressure_level"),
                tags=data.get("tags"),
                flavor_text=data.get("flavor_text"),
                dice_dc=data.get("dice_dc"),
            )
            events_by_char.setdefault(character_id, []).append(event)
        return events_by_char
    finally:
        conn.close()


def load_active_custom_hazards(db_path: str | None = None) -> dict[str, dict]:
    """从 custom_cards 加载所有 is_active=1 的 HAZARD 类型卡牌。

    返回 {event_id: hazard_data} 映射，可合并入 engine 的 _EVENT_HAZARD_MAP。
    """
    conn = connect(db_path)
    try:
        rows = conn.execute(
            "SELECT card_id, card_name, card_data_json FROM custom_cards WHERE card_type = 'HAZARD' AND is_active = 1"
        ).fetchall()
        hazard_map: dict[str, dict] = {}
        for row in rows:
            data = json.loads(row["card_data_json"])
            trigger_event = data.get("trigger_event", row["card_id"])
            hazard_map[trigger_event] = {
                "id": row["card_id"],
                "name": data.get("name", row["card_name"]),
                "countdown": data.get("countdown", 3),
                "severity": data.get("severity", 1),
            }
        return hazard_map
    finally:
        conn.close()


def merge_characters(
    built_in: list[Character],
    custom: list[Character],
) -> list[Character]:
    """合并内置角色与自定义角色列表。"""
    return built_in + custom


def merge_events(
    built_in: dict[str, list[Event]],
    custom: dict[str, list[Event]],
) -> dict[str, list[Event]]:
    """合并内置事件与自定义事件映射。自定义事件追加到对应角色的列表末尾。"""
    merged = dict(built_in)
    for char_id, events in custom.items():
        if char_id in merged:
            merged[char_id] = merged[char_id] + events
        else:
            merged[char_id] = list(events)
    return merged
