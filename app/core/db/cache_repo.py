"""
Cache and Rate Limit persistence repository for LabLink platform.
"""

import json
import time
import sqlite3
from typing import Dict, Any, Optional, Tuple


def get_copilot_cache(conn: sqlite3.Connection, query_hash: str, max_age_seconds: int = 86400) -> Optional[Dict[str, Any]]:
    cursor = conn.cursor()
    min_time = time.time() - max_age_seconds
    cursor.execute("""
    SELECT response_json FROM copilot_cache
    WHERE query_hash = ? AND created_at >= ?;
    """, (query_hash, min_time))
    row = cursor.fetchone()
    if row:
        return json.loads(row["response_json"])
    return None


def set_copilot_cache(conn: sqlite3.Connection, query_hash: str, prompt_text: str, response_data: Dict[str, Any]):
    cursor = conn.cursor()
    cursor.execute("""
    INSERT OR REPLACE INTO copilot_cache (query_hash, prompt_text, response_json, created_at)
    VALUES (?, ?, ?, ?);
    """, (query_hash, prompt_text, json.dumps(response_data), time.time()))
    conn.commit()


def check_rate_limit(conn: sqlite3.Connection, client_key: str, max_requests: int = 60, window_seconds: int = 60) -> Tuple[bool, int]:
    """Persistent sliding-window rate limiter stored in SQLite."""
    now = time.time()
    cutoff = now - window_seconds
    cursor = conn.cursor()

    # Clean old hits
    cursor.execute("DELETE FROM rate_limit_hits WHERE hit_timestamp < ?;", (cutoff,))

    # Count current window hits
    cursor.execute("SELECT COUNT(*) as hit_count FROM rate_limit_hits WHERE client_key = ? AND hit_timestamp >= ?;", (client_key, cutoff))
    row = cursor.fetchone()
    current_count = row["hit_count"] if row else 0

    if current_count >= max_requests:
        conn.commit()
        return False, 0

    cursor.execute("INSERT INTO rate_limit_hits (client_key, hit_timestamp) VALUES (?, ?);", (client_key, now))
    conn.commit()
    remaining = max_requests - (current_count + 1)
    return True, remaining
