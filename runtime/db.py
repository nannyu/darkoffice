import sqlite3
from pathlib import Path


DEFAULT_DB_PATH = Path(__file__).resolve().parents[1] / "runtime" / "darkoffice.sqlite3"


def connect(db_path: str | None = None) -> sqlite3.Connection:
    path = Path(db_path) if db_path else DEFAULT_DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS game_sessions (
            session_id TEXT PRIMARY KEY,
            day INTEGER NOT NULL DEFAULT 1,
            turn_index INTEGER NOT NULL DEFAULT 0,
            hp INTEGER NOT NULL,
            en INTEGER NOT NULL,
            st INTEGER NOT NULL,
            kpi INTEGER NOT NULL,
            risk INTEGER NOT NULL,
            cor INTEGER NOT NULL,
            status_json TEXT NOT NULL DEFAULT '[]',
            hazard_json TEXT NOT NULL DEFAULT '[]',
            project_json TEXT NOT NULL DEFAULT '[]',
            storyline_id TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS turn_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            turn_index INTEGER NOT NULL,
            character_id TEXT NOT NULL DEFAULT 'CHR_01',
            event_id TEXT NOT NULL DEFAULT 'EVT_GENERIC',
            action_type TEXT NOT NULL,
            action_mod INTEGER NOT NULL DEFAULT 0,
            roll_value INTEGER NOT NULL,
            total_score INTEGER NOT NULL DEFAULT 0,
            result_tier TEXT NOT NULL,
            failure_type TEXT,
            delta_json TEXT NOT NULL,
            state_json TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(session_id) REFERENCES game_sessions(session_id)
        );

        CREATE TABLE IF NOT EXISTS materials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            source TEXT NOT NULL DEFAULT '',
            category TEXT NOT NULL DEFAULT '',
            content TEXT NOT NULL DEFAULT '',
            file_type TEXT NOT NULL DEFAULT 'MANUAL',
            original_filename TEXT,
            tags_json TEXT NOT NULL DEFAULT '[]',
            metadata_json TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS custom_cards (
            card_id TEXT PRIMARY KEY,
            card_type TEXT NOT NULL,
            card_name TEXT NOT NULL,
            card_data_json TEXT NOT NULL DEFAULT '{}',
            source_material_id INTEGER,
            is_active INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(source_material_id) REFERENCES materials(id)
        );

        CREATE TABLE IF NOT EXISTS storylines (
            storyline_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            acts_json TEXT NOT NULL DEFAULT '[]',
            metadata_json TEXT NOT NULL DEFAULT '{}',
            is_active INTEGER NOT NULL DEFAULT 0,
            current_act_index INTEGER NOT NULL DEFAULT 0,
            session_id TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(session_id) REFERENCES game_sessions(session_id)
        );

        -- 角色动态状态（每局每个角色的当前值，覆盖更新）
        CREATE TABLE IF NOT EXISTS character_states (
            session_id TEXT NOT NULL,
            character_id TEXT NOT NULL,
            relation_to_player INTEGER DEFAULT 0,
            mood TEXT DEFAULT '平静',
            trust INTEGER DEFAULT 50,
            stress INTEGER DEFAULT 50,
            power INTEGER DEFAULT 50,
            hidden_stance TEXT DEFAULT '',
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (session_id, character_id)
        );

        -- 角色关系网
        CREATE TABLE IF NOT EXISTS relation_edges (
            session_id TEXT NOT NULL,
            character_a TEXT NOT NULL,
            character_b TEXT NOT NULL,
            relation_value INTEGER DEFAULT 0,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (session_id, character_a, character_b)
        );

        -- 角色状态关键变化日志
        CREATE TABLE IF NOT EXISTS character_state_changes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            turn_index INTEGER NOT NULL,
            character_id TEXT NOT NULL,
            field_changed TEXT NOT NULL,
            old_value TEXT,
            new_value TEXT,
            reason TEXT,
            timestamp TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        -- 事件链进度
        CREATE TABLE IF NOT EXISTS chain_progress (
            session_id TEXT NOT NULL,
            chain_id TEXT NOT NULL,
            current_position INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            next_trigger_turn INTEGER DEFAULT 0,
            completed_at TEXT,
            PRIMARY KEY (session_id, chain_id)
        );

        -- 剧情线推进状态
        CREATE TABLE IF NOT EXISTS storyline_progress (
            session_id TEXT NOT NULL,
            storyline_id TEXT NOT NULL,
            current_act_index INTEGER DEFAULT 0,
            act_start_turn INTEGER DEFAULT 0,
            branch_taken TEXT DEFAULT '',
            completed INTEGER DEFAULT 0,
            PRIMARY KEY (session_id, storyline_id)
        );

        -- Phase 3: 玩家已发现的情报
        CREATE TABLE IF NOT EXISTS intel_discovered (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            intel_id TEXT NOT NULL,
            source_character TEXT NOT NULL,
            target_character TEXT NOT NULL,
            discovered_at_turn INTEGER NOT NULL,
            discovered_in_scene TEXT NOT NULL DEFAULT '',
            discovery_method TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(session_id) REFERENCES game_sessions(session_id)
        );

        -- Phase 3: 玩家笔记
        CREATE TABLE IF NOT EXISTS player_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            note_type TEXT NOT NULL DEFAULT 'character',  -- character / intel / event
            target_id TEXT NOT NULL DEFAULT '',            -- character_id 或 intel_id
            content TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(session_id) REFERENCES game_sessions(session_id)
        );
        """
    )
    _migrate_turn_logs(conn)
    _migrate_game_sessions(conn)
    _migrate_storylines(conn)
    conn.commit()


def _column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return any(row[1] == column for row in rows)


def _migrate_turn_logs(conn: sqlite3.Connection) -> None:
    # 向后兼容已有数据库：逐列补齐分析所需字段。
    additions = [
        ("character_id", "TEXT NOT NULL DEFAULT 'CHR_01'"),
        ("event_id", "TEXT NOT NULL DEFAULT 'EVT_GENERIC'"),
        ("action_mod", "INTEGER NOT NULL DEFAULT 0"),
        ("total_score", "INTEGER NOT NULL DEFAULT 0"),
        ("failure_type", "TEXT"),
    ]
    for name, sql_type in additions:
        if not _column_exists(conn, "turn_logs", name):
            conn.execute(f"ALTER TABLE turn_logs ADD COLUMN {name} {sql_type}")


def _migrate_game_sessions(conn: sqlite3.Connection) -> None:
    """向后兼容：为旧 game_sessions 表补齐 storyline_id 字段。"""
    if not _column_exists(conn, "game_sessions", "storyline_id"):
        conn.execute("ALTER TABLE game_sessions ADD COLUMN storyline_id TEXT")


def _migrate_storylines(conn: sqlite3.Connection) -> None:
    """向后兼容：为旧 storylines 表补齐 metadata_json 字段。"""
    if not _column_exists(conn, "storylines", "metadata_json"):
        conn.execute("ALTER TABLE storylines ADD COLUMN metadata_json TEXT NOT NULL DEFAULT '{}'")
