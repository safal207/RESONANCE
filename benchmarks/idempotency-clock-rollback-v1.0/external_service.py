from __future__ import annotations

import argparse
import json
import os
import socket
import sqlite3
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse
from uuid import uuid4

LOCK = threading.Lock()
BOOT_ID = uuid4().hex
STATE_DB = Path(os.environ.get("STATE_DB", "/state/remote.db"))
DEFAULT_TTL_SECONDS = int(os.environ.get("DEFAULT_TTL_SECONDS", "60"))


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(STATE_DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    STATE_DB.parent.mkdir(parents=True, exist_ok=True)
    with connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS effects (
                effect_id INTEGER PRIMARY KEY AUTOINCREMENT,
                operation_id TEXT NOT NULL,
                idempotency_key TEXT NOT NULL,
                created_at INTEGER NOT NULL,
                temporal_epoch INTEGER NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS idempotency_records (
                idempotency_key TEXT PRIMARY KEY,
                operation_id TEXT NOT NULL,
                created_at INTEGER NOT NULL,
                expires_at INTEGER NOT NULL,
                temporal_epoch INTEGER NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS request_log (
                request_id INTEGER PRIMARY KEY AUTOINCREMENT,
                operation_id TEXT NOT NULL,
                idempotency_key TEXT NOT NULL,
                logical_time INTEGER NOT NULL,
                temporal_epoch INTEGER NOT NULL,
                outcome TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS ack_drops (
                operation_id TEXT PRIMARY KEY,
                count INTEGER NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS metadata (
                key TEXT PRIMARY KEY,
                value INTEGER NOT NULL
            )
            """
        )
        conn.execute("INSERT OR IGNORE INTO metadata(key, value) VALUES ('temporal_epoch', 1)")
        conn.commit()


def temporal_epoch(conn: sqlite3.Connection) -> int:
    row = conn.execute("SELECT value FROM metadata WHERE key='temporal_epoch'").fetchone()
    if row is None:
        raise RuntimeError("temporal_epoch missing")
    return int(row[0])


def snapshot(operation_id: str, now: int) -> dict[str, object]:
    with LOCK, connect() as conn:
        epoch = temporal_epoch(conn)
        effects = [dict(row) for row in conn.execute(
            "SELECT effect_id, operation_id, idempotency_key, created_at, temporal_epoch FROM effects WHERE operation_id=? ORDER BY effect_id",
            (operation_id,),
        )]
        records = [dict(row) for row in conn.execute(
            "SELECT idempotency_key, operation_id, created_at, expires_at, temporal_epoch FROM idempotency_records WHERE operation_id=? ORDER BY idempotency_key",
            (operation_id,),
        )]
        request_count = int(conn.execute(
            "SELECT COUNT(*) FROM request_log WHERE operation_id=?",
            (operation_id,),
        ).fetchone()[0])
        ack_row = conn.execute("SELECT count FROM ack_drops WHERE operation_id=?", (operation_id,)).fetchone()
        ack_drops = 0 if ack_row is None else int(ack_row[0])
    for record in records:
        record["active_at_query"] = now < int(record["expires_at"])
    count = len(effects)
    return {
        "operation_id": operation_id,
        "logical_time": now,
        "temporal_epoch": epoch,
        "status": "absent" if count == 0 else "committed" if count == 1 else "conflict",
        "effect_count": count,
        "effects": effects,
        "idempotency_records": records,
        "active_idempotency_records": sum(1 for r in records if r["active_at_query"]),
        "post_requests": request_count,
        "ack_drops": ack_drops,
        "boot_id": BOOT_ID,
    }


class Handler(BaseHTTPRequestHandler):
    server_version = "RESONANCEExternalClockRollback/1.0"

    def log_message(self, fmt: str, *args: object) -> None:
        print(f"{self.address_string()} - {fmt % args}", flush=True)

    def send_json(self, status: int, payload: dict[str, object]) -> None:
        body = (json.dumps(payload, sort_keys=True) + "\n").encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
        self.wfile.flush()

    def logical_time(self) -> int:
        value = self.headers.get("X-Logical-Time", "").strip()
        if not value:
            raise ValueError("missing X-Logical-Time")
        return int(value)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/health":
            with LOCK, connect() as conn:
                epoch = temporal_epoch(conn)
            self.send_json(200, {
                "status": "ok",
                "service": "resonance-external-http-clock-rollback",
                "boot_id": BOOT_ID,
                "hostname": socket.gethostname(),
                "pid": os.getpid(),
                "state_db": str(STATE_DB),
                "default_ttl_seconds": DEFAULT_TTL_SECONDS,
                "temporal_epoch": epoch,
            })
            return

        prefix = "/status/"
        if parsed.path.startswith(prefix):
            try:
                now = self.logical_time()
            except (ValueError, TypeError):
                self.send_json(400, {"error": "invalid_or_missing_logical_time"})
                return
            operation_id = unquote(parsed.path[len(prefix):])
            if not operation_id:
                self.send_json(400, {"error": "missing_operation_id"})
                return
            self.send_json(200, snapshot(operation_id, now))
            return

        self.send_json(404, {"error": "not_found"})

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path.startswith("/maintenance/gc/"):
            try:
                now = self.logical_time()
            except (ValueError, TypeError):
                self.send_json(400, {"error": "invalid_or_missing_logical_time"})
                return
            operation_id = unquote(parsed.path[len("/maintenance/gc/"):])
            if not operation_id:
                self.send_json(400, {"error": "missing_operation_id"})
                return
            with LOCK, connect() as conn:
                before = temporal_epoch(conn)
                cur = conn.execute(
                    "DELETE FROM idempotency_records WHERE operation_id=? AND expires_at<=?",
                    (operation_id, now),
                )
                removed = int(cur.rowcount)
                after = before
                if removed:
                    after = before + 1
                    conn.execute("UPDATE metadata SET value=? WHERE key='temporal_epoch'", (after,))
                conn.commit()
            self.send_json(200, {
                "operation_id": operation_id,
                "logical_time": now,
                "removed_records": removed,
                "temporal_epoch_before": before,
                "temporal_epoch_after": after,
            })
            return

        if parsed.path != "/effects":
            self.send_json(404, {"error": "not_found"})
            return

        operation_id = self.headers.get("X-Operation-Id", "").strip()
        key = self.headers.get("Idempotency-Key", "").strip()
        drop_ack = self.headers.get("X-Drop-Ack", "0").strip() == "1"
        require_fence = self.headers.get("X-Require-Temporal-Fence", "0").strip() == "1"
        expected_epoch_raw = self.headers.get("X-Expected-Temporal-Epoch", "").strip()
        try:
            now = self.logical_time()
            ttl = int(self.headers.get("X-Idempotency-TTL", str(DEFAULT_TTL_SECONDS)))
            expected_epoch = int(expected_epoch_raw) if expected_epoch_raw else None
        except (ValueError, TypeError):
            self.send_json(400, {"error": "invalid_time_ttl_or_epoch"})
            return
        if not operation_id or not key or ttl <= 0:
            self.send_json(400, {"error": "missing_operation_key_or_invalid_ttl"})
            return

        length = int(self.headers.get("Content-Length", "0") or "0")
        if length:
            self.rfile.read(length)

        with LOCK, connect() as conn:
            epoch = temporal_epoch(conn)
            if require_fence and expected_epoch != epoch:
                payload = {
                    "error": "temporal_epoch_mismatch",
                    "delivery": "fenced_out",
                    "expected_temporal_epoch": expected_epoch,
                    "current_temporal_epoch": epoch,
                    **snapshot_unlocked(conn, operation_id, now),
                }
                self.send_json(409, payload)
                return

            existing = conn.execute(
                "SELECT operation_id, created_at, expires_at, temporal_epoch FROM idempotency_records WHERE idempotency_key=?",
                (key,),
            ).fetchone()
            active = existing is not None and now < int(existing["expires_at"])
            if active and str(existing["operation_id"]) != operation_id:
                self.send_json(409, {"error": "active_idempotency_key_reused_for_different_operation"})
                return

            if active:
                delivery = "deduplicated"
            else:
                delivery = "applied"
                conn.execute(
                    "INSERT INTO effects(operation_id, idempotency_key, created_at, temporal_epoch) VALUES (?, ?, ?, ?)",
                    (operation_id, key, now, epoch),
                )
                conn.execute(
                    """
                    INSERT INTO idempotency_records(idempotency_key, operation_id, created_at, expires_at, temporal_epoch)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(idempotency_key) DO UPDATE SET
                        operation_id=excluded.operation_id,
                        created_at=excluded.created_at,
                        expires_at=excluded.expires_at,
                        temporal_epoch=excluded.temporal_epoch
                    """,
                    (key, operation_id, now, now + ttl, epoch),
                )

            conn.execute(
                "INSERT INTO request_log(operation_id, idempotency_key, logical_time, temporal_epoch, outcome) VALUES (?, ?, ?, ?, ?)",
                (operation_id, key, now, epoch, delivery),
            )
            if drop_ack:
                conn.execute(
                    """
                    INSERT INTO ack_drops(operation_id, count) VALUES (?, 1)
                    ON CONFLICT(operation_id) DO UPDATE SET count=count+1
                    """,
                    (operation_id,),
                )
            conn.commit()
            payload = {"delivery": delivery, "idempotency_key": key, "ttl_seconds": ttl, **snapshot_unlocked(conn, operation_id, now)}

        if drop_ack:
            self.close_connection = True
            try:
                self.connection.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            try:
                self.connection.close()
            except OSError:
                pass
            return

        self.send_json(200, payload)


def snapshot_unlocked(conn: sqlite3.Connection, operation_id: str, now: int) -> dict[str, object]:
    epoch = temporal_epoch(conn)
    effects = [dict(row) for row in conn.execute(
        "SELECT effect_id, operation_id, idempotency_key, created_at, temporal_epoch FROM effects WHERE operation_id=? ORDER BY effect_id",
        (operation_id,),
    )]
    records = [dict(row) for row in conn.execute(
        "SELECT idempotency_key, operation_id, created_at, expires_at, temporal_epoch FROM idempotency_records WHERE operation_id=? ORDER BY idempotency_key",
        (operation_id,),
    )]
    request_count = int(conn.execute("SELECT COUNT(*) FROM request_log WHERE operation_id=?", (operation_id,)).fetchone()[0])
    ack_row = conn.execute("SELECT count FROM ack_drops WHERE operation_id=?", (operation_id,)).fetchone()
    ack_drops = 0 if ack_row is None else int(ack_row[0])
    for record in records:
        record["active_at_query"] = now < int(record["expires_at"])
    count = len(effects)
    return {
        "operation_id": operation_id,
        "logical_time": now,
        "temporal_epoch": epoch,
        "status": "absent" if count == 0 else "committed" if count == 1 else "conflict",
        "effect_count": count,
        "effects": effects,
        "idempotency_records": records,
        "active_idempotency_records": sum(1 for r in records if r["active_at_query"]),
        "post_requests": request_count,
        "ack_drops": ack_drops,
        "boot_id": BOOT_ID,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()
    init_db()
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(json.dumps({"service": "resonance-external-http-clock-rollback", "boot_id": BOOT_ID, "port": args.port}), flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
