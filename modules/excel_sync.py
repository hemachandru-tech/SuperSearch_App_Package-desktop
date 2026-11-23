"""
modules/excel_sync.py — keeps a master Excel file in sync with tags.db.

Any DB write (new tags, edited/confirmed tags, deleted files, player changes) calls
request_sync(db_path). The export itself runs on a background daemon thread, a few
seconds after the LAST change (debounced, with a max wait so a long tagging run still
refreshes the sheet periodically), so tagging speed is never affected.

If the workbook is open in Excel on Windows the final file swap raises PermissionError;
we log a friendly warning and retry automatically (next change, or after RETRY_SECONDS).
"""

import os
import sqlite3
import threading
import time
from datetime import datetime

from modules import paths

DEBOUNCE_SECONDS = 3.0
MAX_WAIT_SECONDS = 15.0
RETRY_SECONDS = 30.0

VIDEO_EXTS = {".mp4", ".mov", ".m4v", ".avi", ".mkv", ".webm"}

HEADERS = ["File Name", "Folder Path", "Media Type", "Player Names", "Event", "Mood",
           "Action", "Jersey / Apparel", "Date & Time", "Caption", "Status", "Last Updated"]

_lock = threading.Lock()
_timer = None
_first_dirty = None
_db_path = None
_state = {"last_sync": None, "last_error": None, "rows": 0, "locked": False}


def _log(msg):
    print(f"[EXCEL SYNC] {msg}", flush=True)


def _clean(v):
    return "" if v is None else str(v).strip()


def _rows(db_path):
    conn = sqlite3.connect(db_path, timeout=30)
    conn.row_factory = sqlite3.Row
    try:
        recs = conn.execute("SELECT * FROM images ORDER BY id").fetchall()
    finally:
        conn.close()
    out = []
    for r in recs:
        d = dict(r)
        name = _clean(d.get("file_name")) or os.path.basename(_clean(d.get("file_path")))
        ext = os.path.splitext(name)[1].lower()
        jersey = ", ".join(x for x in (_clean(d.get("jersey_color")), _clean(d.get("apparel"))) if x)
        out.append([
            name,
            _clean(d.get("folder")) or os.path.dirname(_clean(d.get("file_path"))),
            "Video" if ext in VIDEO_EXTS else "Photo",
            _clean(d.get("player_names")),
            _clean(d.get("event_type")),
            _clean(d.get("mood")),
            _clean(d.get("action")),
            jersey,
            _clean(d.get("date_time_original")) or _clean(d.get("date")),
            _clean(d.get("caption")),
            _clean(d.get("status")),
            _clean(d.get("updated_at")),
        ])
    return out


def sync_now(db_path=None):
    """Export every DB row to the master workbook. Returns True on success."""
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter

    db_path = db_path or _db_path
    if not db_path or not os.path.exists(db_path):
        return False
    target = paths.excel_sync_path()
    tmp = os.path.splitext(target)[0] + ".syncing.xlsx"
    try:
        rows = _rows(db_path)
        wb = Workbook()
        ws = wb.active
        ws.title = "SuperSearch Data"
        ws.append(HEADERS)
        for r in rows:
            ws.append(r)
        head_font = Font(bold=True, color="FFFFFF")
        head_fill = PatternFill("solid", fgColor="1F3864")
        for c in ws[1]:
            c.font, c.fill = head_font, head_fill
            c.alignment = Alignment(vertical="center")
        ws.freeze_panes = "A2"
        ws.auto_filter.ref = ws.dimensions
        for i, h in enumerate(HEADERS, start=1):
            longest = max([len(h)] + [len(str(r[i - 1]).split("\n")[0]) for r in rows[:2000]])
            ws.column_dimensions[get_column_letter(i)].width = min(max(longest + 2, 10), 60)
        wb.save(tmp)
        try:
            os.replace(tmp, target)          # PermissionError here => open in Excel (Windows)
        except PermissionError:
            try:
                os.remove(tmp)
            except Exception:
                pass
            raise
        _state.update(last_sync=datetime.now().isoformat(timespec="seconds"),
                      last_error=None, rows=len(rows), locked=False)
        _log(f"Synced {len(rows)} rows -> {target}")
        return True
    except PermissionError:
        _state.update(locked=True, last_error="File is open in Excel")
        _log("Master Excel file is open in another program - close it; will retry automatically.")
        _schedule(RETRY_SECONDS)
        return False
    except Exception as e:                    # never let a sync problem break tagging
        _state["last_error"] = str(e)
        _log(f"Sync failed (will retry on next change): {e}")
        return False


def _run():
    global _first_dirty
    with _lock:
        _first_dirty = None
    sync_now()


def _schedule(delay):
    global _timer
    with _lock:
        if _timer is not None:
            _timer.cancel()
        _timer = threading.Timer(delay, _run)
        _timer.daemon = True
        _timer.start()


def request_sync(db_path):
    """Call after any DB commit. Cheap and non-blocking (debounced, runs in background)."""
    global _db_path, _first_dirty
    _db_path = db_path
    now = time.time()
    with _lock:
        if _first_dirty is None:
            _first_dirty = now
        delay = min(DEBOUNCE_SECONDS, max(0.0, _first_dirty + MAX_WAIT_SECONDS - now))
    _schedule(delay)


def status():
    p = paths.excel_sync_path()
    return {"path": p, "exists": os.path.exists(p), **_state}
