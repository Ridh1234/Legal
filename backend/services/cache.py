import os
import time
import sqlite3
from typing import Any, Optional

# Simple hybrid cache: in-memory + optional SQLite persistence

_MEM_CACHE: dict[str, tuple[float, Any]] = {}
_DB_PATH = os.getenv("CACHE_DB")


def _ensure_db():
    if not _DB_PATH:
        return
    # Ensure parent directory exists
    try:
        parent = os.path.dirname(_DB_PATH)
        if parent:
            os.makedirs(parent, exist_ok=True)
    except Exception:
        pass
    conn = sqlite3.connect(_DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "CREATE TABLE IF NOT EXISTS cache (k TEXT PRIMARY KEY, v BLOB, exp REAL)"
    )
    conn.commit()
    conn.close()


_ensure_db()


def cache_set(key: str, value: Any, ttl_seconds: int = 3600):
    exp = time.time() + ttl_seconds
    _MEM_CACHE[key] = (exp, value)
    if _DB_PATH:
        conn = sqlite3.connect(_DB_PATH)
        cur = conn.cursor()
        cur.execute(
            "REPLACE INTO cache (k, v, exp) VALUES (?, ?, ?)",
            (key, repr(value), exp),
        )
        conn.commit()
        conn.close()


def cache_get(key: str) -> Optional[Any]:
    now = time.time()
    entry = _MEM_CACHE.get(key)
    if entry:
        exp, val = entry
        if now < exp:
            return val
        else:
            _MEM_CACHE.pop(key, None)
    if _DB_PATH:
        conn = sqlite3.connect(_DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT v, exp FROM cache WHERE k=?", (key,))
        row = cur.fetchone()
        conn.close()
        if row:
            v_str, exp = row
            if now < exp:
                try:
                    # unsafe eval avoided; use literal eval if possible
                    import ast
                    return ast.literal_eval(v_str)
                except Exception:
                    return None
    return None
