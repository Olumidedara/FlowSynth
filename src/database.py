import json
import sqlite3
import threading
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "flowsynth.db"
_local = threading.local()


def get_conn() -> sqlite3.Connection:
    if not hasattr(_local, "conn") or _local.conn is None:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        _local.conn = sqlite3.connect(str(DB_PATH))
        _local.conn.row_factory = sqlite3.Row
        _local.conn.execute("PRAGMA journal_mode=WAL")
    return _local.conn


def init_db() -> None:
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS research (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            query TEXT NOT NULL,
            result TEXT,
            status TEXT NOT NULL DEFAULT 'running',
            task_id TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        CREATE INDEX IF NOT EXISTS idx_research_user ON research(user_id);
    """)
    conn.commit()

    # migrate: add task_id column if missing
    try:
        conn.execute("ALTER TABLE research ADD COLUMN task_id TEXT")
        conn.commit()
    except Exception:
        pass


# --- Users ---

def create_user(email: str, password_hash: str) -> int:
    conn = get_conn()
    cur = conn.execute("INSERT INTO users (email, password_hash) VALUES (?, ?)", (email, password_hash))
    conn.commit()
    return cur.lastrowid


def get_user_by_email(email: str) -> dict | None:
    conn = get_conn()
    row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    return dict(row) if row else None


def get_user_by_id(user_id: int) -> dict | None:
    conn = get_conn()
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return dict(row) if row else None


# --- Research ---

def create_research(user_id: int, query: str, task_id: str = "") -> int:
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO research (user_id, query, task_id) VALUES (?, ?, ?)",
        (user_id, query, task_id),
    )
    conn.commit()
    return cur.lastrowid


def update_research(research_id: int, status: str, result: dict | None = None) -> None:
    conn = get_conn()
    result_json = json.dumps(result) if result else None
    conn.execute(
        "UPDATE research SET status = ?, result = ? WHERE id = ?",
        (status, result_json, research_id),
    )
    conn.commit()


def get_research_history(user_id: int, limit: int = 20) -> list[dict]:
    conn = get_conn()
    rows = conn.execute(
        "SELECT id, query, status, task_id, created_at FROM research WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
        (user_id, limit),
    ).fetchall()
    return [dict(r) for r in rows]


def get_research_by_task_id(task_id: str, user_id: int) -> dict | None:
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM research WHERE task_id = ? AND user_id = ?", (task_id, user_id)
    ).fetchone()
    if not row:
        return None
    r = dict(row)
    if r.get("result"):
        try:
            parsed = json.loads(r["result"])
            r["result"] = parsed
        except (json.JSONDecodeError, TypeError):
            r["result"] = None
    return r


def get_research_by_id(research_id: int, user_id: int) -> dict | None:
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM research WHERE id = ? AND user_id = ?", (research_id, user_id)
    ).fetchone()
    if not row:
        return None
    r = dict(row)
    if r.get("result"):
        try:
            parsed = json.loads(r["result"])
            r["result"] = parsed
        except (json.JSONDecodeError, TypeError):
            r["result"] = None
    return r


def get_latest_research(user_id: int) -> dict | None:
    conn = get_conn()
    row = conn.execute(
        "SELECT id, task_id FROM research WHERE user_id = ? AND task_id IS NOT NULL AND task_id != '' ORDER BY created_at DESC LIMIT 1",
        (user_id,),
    ).fetchone()
    return dict(row) if row else None


def delete_research(research_id: int, user_id: int) -> bool:
    conn = get_conn()
    cur = conn.execute(
        "DELETE FROM research WHERE id = ? AND user_id = ?", (research_id, user_id)
    )
    conn.commit()
    return cur.rowcount > 0
