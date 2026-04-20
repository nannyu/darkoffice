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
        """
    )
    _migrate_turn_logs(conn)
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
