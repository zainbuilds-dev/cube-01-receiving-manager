import sqlite3
import threading

from .config import CFG

_lock = threading.Lock()

SCHEMA = """
CREATE TABLE IF NOT EXISTS records(
  org_id TEXT NOT NULL, id TEXT NOT NULL, unit_id TEXT NOT NULL,
  po_json TEXT NOT NULL, status TEXT NOT NULL, decision TEXT,
  evidence_json TEXT, created_at TEXT NOT NULL,
  PRIMARY KEY(org_id, id));
CREATE TABLE IF NOT EXISTS images(
  org_id TEXT NOT NULL, sha256 TEXT NOT NULL, ext TEXT NOT NULL,
  size INTEGER NOT NULL, created_at TEXT NOT NULL,
  PRIMARY KEY(org_id, sha256));
CREATE TABLE IF NOT EXISTS record_images(
  org_id TEXT NOT NULL, record_id TEXT NOT NULL, sha256 TEXT NOT NULL,
  idx INTEGER NOT NULL, filename TEXT,
  PRIMARY KEY(org_id, record_id, idx));
CREATE TABLE IF NOT EXISTS counters(
  org_id TEXT PRIMARY KEY, last_rcv INTEGER NOT NULL);
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
    with _lock:
        con = connect()
        try:
            cur = con.execute(sql, params)
            rows = cur.fetchall() if fetch else None
            con.commit()
            return rows
        finally:
            con.close()

def next_record_id(org_id: str) -> str:
    """Per-org RCV sequence. Per-org on purpose: a globally shared counter
    would let one org infer another org's shipment volume from record IDs."""
    with _lock:
        con = connect()
        try:
            row = con.execute("SELECT last_rcv FROM counters WHERE org_id=?",
                              (org_id,)).fetchone()
            n = (row[0] if row else 0) + 1
            con.execute(
                "INSERT INTO counters(org_id, last_rcv) VALUES(?, ?) "
                "ON CONFLICT(org_id) DO UPDATE SET last_rcv=excluded.last_rcv",
                (org_id, n))
            con.commit()
            return f"RCV-{n:04d}"
        finally:
            con.close()