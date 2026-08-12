"""SQLite-backed cache for resolved song lookups — a get-or-compute layer.

Deliberately disposable: if a free-tier host's disk doesn't persist
across restarts, the app just re-fetches and rebuilds this rather than
breaking. Entries expire after 30 days (checked lazily on read, no
separate cleanup job) rather than being kept forever, since LRCLIB and
YouTube data can occasionally change.

Kept as plain synchronous sqlite3 rather than an async driver — a single
key lookup/insert on a small local file is fast enough that the
complexity isn't worth it. Callers use asyncio.to_thread() so this
doesn't block the event loop.
"""

import json
import sqlite3
import time
from pathlib import Path
from typing import Any

DB_PATH = Path(__file__).resolve().parent.parent.parent / "cache.db"
TTL_SECONDS = 30 * 24 * 60 * 60


def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS song_cache ("
        "cache_key TEXT PRIMARY KEY, response_json TEXT NOT NULL, created_at REAL NOT NULL)"
    )
    return conn


def make_key(title: str, artist: str) -> str:
    return f"{title.strip().lower()}|{artist.strip().lower()}"


def get(cache_key: str) -> dict[str, Any] | None:
    conn = _get_connection()
    try:
        row = conn.execute(
            "SELECT response_json, created_at FROM song_cache WHERE cache_key = ?",
            (cache_key,),
        ).fetchone()
    finally:
        conn.close()

    if row is None:
        return None

    response_json, created_at = row
    if time.time() - created_at > TTL_SECONDS:
        return None  # expired — treat as a miss

    return json.loads(response_json)


def set(cache_key: str, value: dict[str, Any]) -> None:
    conn = _get_connection()
    try:
        conn.execute(
            "INSERT OR REPLACE INTO song_cache (cache_key, response_json, created_at) "
            "VALUES (?, ?, ?)",
            (cache_key, json.dumps(value), time.time()),
        )
        conn.commit()
    finally:
        conn.close()
