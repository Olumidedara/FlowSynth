import json
from datetime import datetime

import asyncpg
from asyncpg import Pool

from src.config import settings

pool: Pool | None = None


async def init_db() -> None:
    global pool
    url = settings.database_url
    if not url:
        raise RuntimeError(
            "DATABASE_URL is not set. "
            "Get a free Neon database at https://neon.tech and add the connection string to your .env file."
        )
    pool = await asyncpg.create_pool(url, min_size=1, max_size=5)
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT NOW()
            );
            CREATE TABLE IF NOT EXISTS research (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id),
                query TEXT NOT NULL,
                result TEXT,
                status TEXT NOT NULL DEFAULT 'running',
                task_id TEXT,
                created_at TIMESTAMP NOT NULL DEFAULT NOW()
            );
            CREATE INDEX IF NOT EXISTS idx_research_user ON research(user_id);
        """)


async def close_db() -> None:
    global pool
    if pool:
        await pool.close()
        pool = None


def _get_pool() -> Pool:
    global pool
    if pool is None:
        raise RuntimeError("Database pool not initialized. Call init_db() first.")
    return pool


# --- Users ---

async def create_user(email: str, password_hash: str) -> int:
    p = _get_pool()
    async with p.acquire() as conn:
        return await conn.fetchval(
            "INSERT INTO users (email, password_hash) VALUES ($1, $2) RETURNING id",
            email, password_hash,
        )


async def get_user_by_email(email: str) -> dict | None:
    p = _get_pool()
    async with p.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM users WHERE email = $1", email,
        )
        return dict(row) if row else None


async def get_user_by_id(user_id: int) -> dict | None:
    p = _get_pool()
    async with p.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM users WHERE id = $1", user_id,
        )
        return dict(row) if row else None


# --- Research ---

async def create_research(user_id: int, query: str, task_id: str = "") -> int:
    p = _get_pool()
    async with p.acquire() as conn:
        return await conn.fetchval(
            "INSERT INTO research (user_id, query, task_id) VALUES ($1, $2, $3) RETURNING id",
            user_id, query, task_id,
        )


async def update_research(research_id: int, status: str, result: dict | None = None) -> None:
    p = _get_pool()
    result_json = json.dumps(result) if result else None
    async with p.acquire() as conn:
        await conn.execute(
            "UPDATE research SET status = $1, result = $2 WHERE id = $3",
            status, result_json, research_id,
        )


async def get_research_history(user_id: int, limit: int = 20) -> list[dict]:
    p = _get_pool()
    async with p.acquire() as conn:
        rows = await conn.fetch(
            "SELECT id, query, status, task_id, created_at FROM research WHERE user_id = $1 ORDER BY created_at DESC LIMIT $2",
            user_id, limit,
        )
        return [dict(r) for r in rows]


async def get_research_by_task_id(task_id: str, user_id: int) -> dict | None:
    p = _get_pool()
    async with p.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM research WHERE task_id = $1 AND user_id = $2",
            task_id, user_id,
        )
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


async def get_research_by_id(research_id: int, user_id: int) -> dict | None:
    p = _get_pool()
    async with p.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM research WHERE id = $1 AND user_id = $2",
            research_id, user_id,
        )
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


async def get_latest_research(user_id: int) -> dict | None:
    p = _get_pool()
    async with p.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, task_id FROM research WHERE user_id = $1 AND task_id IS NOT NULL AND task_id != '' ORDER BY created_at DESC LIMIT 1",
            user_id,
        )
        return dict(row) if row else None


async def delete_research(research_id: int, user_id: int) -> bool:
    p = _get_pool()
    async with p.acquire() as conn:
        result = await conn.execute(
            "DELETE FROM research WHERE id = $1 AND user_id = $2",
            research_id, user_id,
        )
        return result != "DELETE 0"
