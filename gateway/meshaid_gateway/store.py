"""
SQLite persistence for the gateway.

- messages:        verified, deduplicated civilian messages (the operator feed)
- security_events: everything rejected or suspicious at ingest (SRS 8.4)
- nodes:           mesh health, last-heard per Meshtastic node (SRS 7.4)

UNIQUE(hp_id, seq) on messages is the durable replay/dedup backstop: it
survives gateway restarts, which service_protocol's in-memory ReplayGuard does not.
"""

import json
import sqlite3
import threading
import time
from pathlib import Path
from typing import Optional

SCHEMA = """
CREATE TABLE IF NOT EXISTS messages (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    hp_id           INTEGER NOT NULL,
    seq             INTEGER NOT NULL,
    msg_type        TEXT    NOT NULL,
    schema_version  INTEGER NOT NULL,
    fields_json     TEXT    NOT NULL,
    hp_timestamp    INTEGER,
    received_at     REAL    NOT NULL,
    verify_status   TEXT    NOT NULL,          -- accepted | flagged_stale
    priority        INTEGER NOT NULL,
    from_node       INTEGER,
    hops            INTEGER,
    snr             REAL,
    ack_state       TEXT    NOT NULL DEFAULT 'new',   -- new | acknowledged | resolved
    ack_at          REAL,
    ack_note        TEXT,
    UNIQUE (hp_id, seq)
);
CREATE INDEX IF NOT EXISTS ix_messages_received ON messages (received_at);

CREATE TABLE IF NOT EXISTS security_events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    received_at REAL    NOT NULL,
    kind        TEXT    NOT NULL,   -- malformed | unknown_node | unauthentic | duplicate | stale | rate_limited
    severity    TEXT    NOT NULL,   -- info | warning | alert
    hp_id       INTEGER,
    seq         INTEGER,
    from_node   INTEGER,
    detail      TEXT,
    raw_hex     TEXT
);
CREATE INDEX IF NOT EXISTS ix_security_received ON security_events (received_at);

CREATE TABLE IF NOT EXISTS nodes (
    node_num    INTEGER PRIMARY KEY,
    node_id     TEXT,
    long_name   TEXT,
    short_name  TEXT,
    last_heard  REAL,
    snr         REAL,
    hops_away   INTEGER,
    battery     INTEGER,
    updated_at  REAL NOT NULL
);
"""

ACK_STATES = ("new", "acknowledged", "resolved")
SORTS = {
    "priority": "priority DESC, received_at DESC",
    "newest": "received_at DESC",
    "oldest": "received_at ASC",
}


class Store:
    def __init__(self, path):
        self.path = str(path)
        if self.path != ":memory:":
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._lock = threading.Lock()
        with self._lock:
            self._conn.executescript(SCHEMA)
            self._conn.commit()

    def close(self):
        with self._lock:
            self._conn.close()

    # ---- messages -------------------------------------------------------

    def insert_message(self, *, hp_id, seq, msg_type, schema_version, fields, hp_timestamp,
                       received_at, verify_status, priority, from_node=None, hops=None, snr=None) -> Optional[dict]:
        """Returns the stored row, or None if (hp_id, seq) was already stored (duplicate)."""
        with self._lock:
            try:
                cur = self._conn.execute(
                    """INSERT INTO messages (hp_id, seq, msg_type, schema_version, fields_json, hp_timestamp,
                                             received_at, verify_status, priority, from_node, hops, snr)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (hp_id, seq, msg_type, schema_version, json.dumps(fields), hp_timestamp,
                     received_at, verify_status, priority, from_node, hops, snr),
                )
            except sqlite3.IntegrityError:
                return None
            self._conn.commit()
            return self._get_message(cur.lastrowid)

    def has_message(self, hp_id: int, seq: int) -> bool:
        with self._lock:
            row = self._conn.execute("SELECT 1 FROM messages WHERE hp_id=? AND seq=?", (hp_id, seq)).fetchone()
        return row is not None

    def get_message(self, message_id: int) -> Optional[dict]:
        with self._lock:
            return self._get_message(message_id)

    def _get_message(self, message_id: int) -> Optional[dict]:
        row = self._conn.execute("SELECT * FROM messages WHERE id=?", (message_id,)).fetchone()
        return _message_row(row) if row else None

    def list_messages(self, *, msg_type=None, hp_id=None, ack_state=None, min_priority=None,
                      verify_status=None, sort="priority", limit=500) -> list:
        where, args = [], []
        for col, val in (("msg_type", msg_type), ("hp_id", hp_id), ("ack_state", ack_state),
                         ("verify_status", verify_status)):
            if val is not None:
                where.append(f"{col}=?")
                args.append(val)
        if min_priority is not None:
            where.append("priority>=?")
            args.append(min_priority)
        sql = "SELECT * FROM messages"
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += f" ORDER BY {SORTS.get(sort, SORTS['priority'])} LIMIT ?"
        args.append(limit)
        with self._lock:
            rows = self._conn.execute(sql, args).fetchall()
        return [_message_row(r) for r in rows]

    def set_ack_state(self, message_id: int, state: str, note: Optional[str] = None) -> Optional[dict]:
        if state not in ACK_STATES:
            raise ValueError(f"ack state must be one of {ACK_STATES}")
        with self._lock:
            cur = self._conn.execute(
                "UPDATE messages SET ack_state=?, ack_at=?, ack_note=COALESCE(?, ack_note) WHERE id=?",
                (state, time.time() if state != "new" else None, note, message_id),
            )
            self._conn.commit()
            return self._get_message(message_id) if cur.rowcount else None

    def seen_sequences(self) -> dict:
        """{hp_id: [seq, ...] ascending} - used to re-seed ReplayGuard after a restart."""
        with self._lock:
            rows = self._conn.execute("SELECT hp_id, seq FROM messages ORDER BY hp_id, seq").fetchall()
        out = {}
        for r in rows:
            out.setdefault(r["hp_id"], []).append(r["seq"])
        return out

    # ---- security events ------------------------------------------------

    def insert_security_event(self, *, kind, severity, received_at, hp_id=None, seq=None,
                              from_node=None, detail=None, raw: bytes = b"") -> dict:
        raw_hex = raw[:64].hex() if raw else None
        with self._lock:
            cur = self._conn.execute(
                """INSERT INTO security_events (received_at, kind, severity, hp_id, seq, from_node, detail, raw_hex)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (received_at, kind, severity, hp_id, seq, from_node, detail, raw_hex),
            )
            self._conn.commit()
            row = self._conn.execute("SELECT * FROM security_events WHERE id=?", (cur.lastrowid,)).fetchone()
        return dict(row)

    def list_security_events(self, *, kind=None, limit=200) -> list:
        sql, args = "SELECT * FROM security_events", []
        if kind:
            sql += " WHERE kind=?"
            args.append(kind)
        sql += " ORDER BY received_at DESC LIMIT ?"
        args.append(limit)
        with self._lock:
            return [dict(r) for r in self._conn.execute(sql, args).fetchall()]

    # ---- nodes ----------------------------------------------------------

    def upsert_node(self, node_num: int, **fields) -> dict:
        allowed = {"node_id", "long_name", "short_name", "last_heard", "snr", "hops_away", "battery"}
        fields = {k: v for k, v in fields.items() if k in allowed and v is not None}
        now = time.time()
        with self._lock:
            self._conn.execute("INSERT OR IGNORE INTO nodes (node_num, updated_at) VALUES (?, ?)", (node_num, now))
            if fields:
                sets = ", ".join(f"{k}=?" for k in fields)
                self._conn.execute(f"UPDATE nodes SET {sets}, updated_at=? WHERE node_num=?",
                                   (*fields.values(), now, node_num))
            self._conn.commit()
            return dict(self._conn.execute("SELECT * FROM nodes WHERE node_num=?", (node_num,)).fetchone())

    def list_nodes(self) -> list:
        with self._lock:
            return [dict(r) for r in self._conn.execute("SELECT * FROM nodes ORDER BY node_num").fetchall()]

    # ---- stats / retention ---------------------------------------------

    def stats(self) -> dict:
        with self._lock:
            by_type = {r["msg_type"]: r["n"] for r in self._conn.execute(
                "SELECT msg_type, COUNT(*) n FROM messages GROUP BY msg_type")}
            by_ack = {r["ack_state"]: r["n"] for r in self._conn.execute(
                "SELECT ack_state, COUNT(*) n FROM messages GROUP BY ack_state")}
            open_medical = self._conn.execute(
                "SELECT COUNT(*) FROM messages WHERE msg_type='MEDICAL_URGENT' AND ack_state!='resolved'").fetchone()[0]
            sec = {r["kind"]: r["n"] for r in self._conn.execute(
                "SELECT kind, COUNT(*) n FROM security_events GROUP BY kind")}
        return {"messages_by_type": by_type, "messages_by_ack_state": by_ack,
                "open_medical": open_medical, "security_events_by_kind": sec}

    def purge_older_than(self, cutoff: float) -> int:
        with self._lock:
            n = self._conn.execute("DELETE FROM messages WHERE received_at < ?", (cutoff,)).rowcount
            n += self._conn.execute("DELETE FROM security_events WHERE received_at < ?", (cutoff,)).rowcount
            self._conn.commit()
        return n


def _message_row(row: sqlite3.Row) -> dict:
    d = dict(row)
    d["fields"] = json.loads(d.pop("fields_json"))
    return d
