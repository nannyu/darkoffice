import sqlite3
from pathlib import Path


DEFAULT_DB_PATH = Path("runtime/darkoffice.sqlite3")


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
            action_type TEXT NOT NULL,
            roll_value INTEGER NOT NULL,
            result_tier TEXT NOT NULL,
            delta_json TEXT NOT NULL,
            state_json TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(session_id) REFERENCES game_sessions(session_id)
        );
        """
    )
    conn.commit()
