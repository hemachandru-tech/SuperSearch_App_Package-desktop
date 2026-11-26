"""
Activity log for the desktop app.

- Every user action (login, opening a file, ...) is written to a LOCAL queue first.
- A background worker POSTs queued rows to the central activity-log API.
- When the machine is offline the worker does NOT try the API; rows simply wait in the
  queue and are sent automatically the next time the network is reachable.
- Queue lives in its own SQLite file in the app data folder, so it never touches tags.db.
"""
import json
import os
import socket
import sqlite3
import threading
import time
from datetime import datetime, timezone
from urllib import request as _urlrequest
from urllib.error import URLError, HTTPError

from modules import paths

ACTIVITY_API_URL = os.getenv(
    "ACTIVITY_API_URL",
    "https://supersearch.chennaisuperkings.com/ABE/api/user/activity-log",
)
SYNC_INTERVAL_SEC = int(os.getenv("ACTIVITY_SYNC_INTERVAL", "30"))
BATCH_SIZE = 50
_lock = threading.Lock()
_started = False


def _db_path():
    return paths.data_path("activity_queue.db")


def _conn():
    conn = sqlite3.connect(_db_path(), timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS activity_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            action_type TEXT NOT NULL,
            details TEXT,
            created_at TEXT NOT NULL,
            synced_at TEXT
        )
    """)
    return conn


def enqueue(username: str, action_type: str, details: dict | None = None) -> int:
    """Store one activity row locally. Never blocks on the network."""
    username = (username or "").strip()
    action_type = (action_type or "").strip()
    if not username or not action_type:
        raise ValueError("username and actionType are required")
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with _lock, _conn() as conn:
        cur = conn.execute(
            "INSERT INTO activity_queue (username, action_type, details, created_at) VALUES (?, ?, ?, ?)",
            (username, action_type, json.dumps(details or {}, ensure_ascii=False), now),
        )
        return cur.lastrowid


def pending_count() -> int:
    with _lock, _conn() as conn:
        return conn.execute("SELECT COUNT(*) FROM activity_queue WHERE synced_at IS NULL").fetchone()[0]


def is_online(timeout: float = 3.0) -> bool:
    """Cheap reachability check. If False we skip the API call entirely."""
    host = "supersearch.chennaisuperkings.com"
    try:
        socket.create_connection((host, 443), timeout=timeout).close()
        return True
    except OSError:
        return False


def _post(row: dict) -> bool:
    body = {
        "username": row["username"],
        "actionType": row["action_type"],
        "timestamp": row["created_at"],
        **(json.loads(row["details"] or "{}")),
    }
    req = _urlrequest.Request(
        ACTIVITY_API_URL,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with _urlrequest.urlopen(req, timeout=10) as resp:
            return 200 <= resp.status < 300
    except HTTPError as e:
        # 4xx means the server rejected this row; keep it queued but log why.
        print(f"[ACTIVITY] server rejected row {row['id']}: HTTP {e.code}")
        return False
    except (URLError, OSError):
        return False


def sync_pending() -> dict:
    """Send queued rows oldest-first. Stops at the first network failure."""
    if pending_count() == 0:
        return {"sent": 0, "pending": 0, "online": None}
    if not is_online():
        return {"sent": 0, "pending": pending_count(), "online": False}
    with _lock, _conn() as conn:
        rows = [dict(r) for r in conn.execute(
            "SELECT * FROM activity_queue WHERE synced_at IS NULL ORDER BY id LIMIT ?", (BATCH_SIZE,)
        ).fetchall()]
    sent = 0
    for row in rows:  # network calls happen outside the lock so logging never waits on them
        if not _post(row):
            break
        with _lock, _conn() as conn:
            conn.execute(
                "UPDATE activity_queue SET synced_at = ? WHERE id = ?",
                (datetime.now(timezone.utc).isoformat(timespec="seconds"), row["id"]),
            )
        sent += 1
    return {"sent": sent, "pending": pending_count(), "online": True}


def _worker():
    while True:
        try:
            sync_pending()
        except Exception as e:  # never let the worker die
            print(f"[ACTIVITY] sync error: {e}")
        time.sleep(SYNC_INTERVAL_SEC)


def start_background_sync():
    """Start the auto-sync worker once per process."""
    global _started
    if _started:
        return
    _started = True
    threading.Thread(target=_worker, name="activity-sync", daemon=True).start()
