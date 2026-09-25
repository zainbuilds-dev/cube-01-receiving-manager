import sqlite3
import threading

from .config import CFG

_lock = threading.Lock()

SCHEMA = """
CREATE TABLE IF NOT EXISTS records(
  id TEXT PRIMARY KEY, po_json TEXT NOT NULL, status TEXT NOT NULL,
  decision TEXT, evidence_json TEXT, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS images(
  sha256 TEXT PRIMARY KEY, ext TEXT NOT NULL, size INTEGER NOT NULL,
  created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS record_images(
  record_id TEXT NOT NULL, sha256 TEXT NOT NULL, idx INTEGER NOT NULL,
  filename TEXT, PRIMARY KEY(record_id, idx));
"""

def connect():
    CFG.db_path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(CFG.db_path, check_same_thread=False)
    con.execute("PRAGMA journal_mode=WAL")
    return con

def init_db():
    with _lock, connect() as con:
        con.executescript(SCHEMA)

def run(sql, params=(), fetch=False):
    """Execute one statement under the lock; return rows if fetch."""
    with _lock:
        con = connect()
        try:
            cur = con.execute(sql, params)
            rows = cur.fetchall() if fetch else None
            con.commit()
            return rows
        finally:
            con.close()