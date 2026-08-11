from __future__ import annotations

import argparse
import json
import os
import socket
import sqlite3
import threading
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

LOCK = threading.Lock()
BOOT_ID = uuid.uuid4().hex
VOLATILE_KEYS: dict[str, str] = {}
STATE_DB = Path(os.environ.get("STATE_DB", "/state/remote.db"))
IDEMPOTENCY_MODE = os.environ.get("IDEMPOTENCY_MODE", "volatile").strip().lower()
if IDEMPOTENCY_MODE not in {"volatile", "durable"}:
    raise RuntimeError(f"unsupported IDEMPOTENCY_MODE={IDEMPOTENCY_MODE}")


def connect() -> sqlite3.Connection:
    STATE_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(STATE_DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_schema() -> None:
    with connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS effects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                operation_id TEXT NOT NULL,
                idempotency_key TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS durable_idempotency (
                idempotency_key TEXT PRIMARY KEY,
                operation_id TEXT NOT NULL,
                effect_id INTEGER NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS request_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                operation_id TEXT NOT NULL,
                idempotency_key TEXT NOT NULL,
                boot_id TEXT NOT NULL,
                ack_dropped INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


def operation_snapshot(operation_id: str) -> dict[str, object]:
    with connect() as conn:
        effects = [
            {
                "effect_id": int(row["id"]),
                "idempotency_key": str(row["idempotency_key"]),
                "operation_id": str(row["operation_id"]),
            }
            for row in conn.execute(
                "SELECT id, operation_id, idempotency_key FROM effects WHERE operation_id=? ORDER BY id",
                (operation_id,),
            ).fetchall()
        ]
        requests = conn.execute(
            "SELECT count(*) AS n, coalesce(sum(ack_dropped), 0) AS drops FROM request_log WHERE operation_id=?",
            (operation_id,),
        ).fetchone()
        durable_rows = conn.execute(
            "SELECT count(*) AS n FROM durable_idempotency WHERE operation_id=?",
            (operation_id,),
        ).fetchone()
    count = len(effects)
    return {
        "operation_id": operation_id,
        "status": "absent" if count == 0 else "committed" if count == 1 else "conflict",
        "effect_count": count,
        "effects": effects,
        "post_requests": int(requests["n"]),
        "ack_drops": int(requests["drops"]),
        "durable_idempotency_records": int(durable_rows["n"]),
    }


def apply_effect(operation_id: str, idempotency_key: str, drop_ack: bool) -> tuple[str, dict[str, object]]:
    with LOCK:
        with connect() as conn:
            if IDEMPOTENCY_MODE == "durable":
                existing = conn.execute(
                    "SELECT operation_id, effect_id FROM durable_idempotency WHERE idempotency_key=?",
                    (idempotency_key,),
                ).fetchone()
                if existing is not None and str(existing["operation_id"]) != operation_id:
                    raise ValueError("idempotency_key_reused_for_different_operation")
                applied = existing is None
                if applied:
                    cur = conn.execute(
                        "INSERT INTO effects(operation_id, idempotency_key) VALUES (?, ?)",
                        (operation_id, idempotency_key),
                    )
                    effect_id = int(cur.lastrowid)
                    conn.execute(
                        "INSERT INTO durable_idempotency(idempotency_key, operation_id, effect_id) VALUES (?, ?, ?)",
                        (idempotency_key, operation_id, effect_id),
                    )
            else:
                existing_operation = VOLATILE_KEYS.get(idempotency_key)
                if existing_operation is not None and existing_operation != operation_id:
                    raise ValueError("idempotency_key_reused_for_different_operation")
                applied = existing_operation is None
                if applied:
                    conn.execute(
                        "INSERT INTO effects(operation_id, idempotency_key) VALUES (?, ?)",
                        (operation_id, idempotency_key),
                    )
                    VOLATILE_KEYS[idempotency_key] = operation_id

            conn.execute(
                "INSERT INTO request_log(operation_id, idempotency_key, boot_id, ack_dropped) VALUES (?, ?, ?, ?)",
                (operation_id, idempotency_key, BOOT_ID, 1 if drop_ack else 0),
            )
            conn.commit()

    return ("applied" if applied else "deduplicated"), operation_snapshot(operation_id)


class Handler(BaseHTTPRequestHandler):
    server_version = "RESONANCEExternalHTTPRestart/1.0"

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

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/health":
            self.send_json(
                200,
                {
                    "status": "ok",
                    "service": "resonance-external-http-restart",
                    "hostname": socket.gethostname(),
                    "pid": os.getpid(),
                    "boot_id": BOOT_ID,
                    "idempotency_mode": IDEMPOTENCY_MODE,
                    "state_db": str(STATE_DB),
                },
            )
            return

        prefix = "/status/"
        if parsed.path.startswith(prefix):
            operation_id = unquote(parsed.path[len(prefix) :])
            if not operation_id:
                self.send_json(400, {"error": "missing_operation_id"})
                return
            self.send_json(200, {"boot_id": BOOT_ID, "idempotency_mode": IDEMPOTENCY_MODE, **operation_snapshot(operation_id)})
            return

        self.send_json(404, {"error": "not_found"})

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/effects":
            self.send_json(404, {"error": "not_found"})
            return

        operation_id = self.headers.get("X-Operation-Id", "").strip()
        idempotency_key = self.headers.get("Idempotency-Key", "").strip()
        drop_ack = self.headers.get("X-Drop-Ack", "0").strip() == "1"
        if not operation_id or not idempotency_key:
            self.send_json(400, {"error": "missing_operation_or_idempotency_key"})
            return

        length = int(self.headers.get("Content-Length", "0") or "0")
        if length:
            self.rfile.read(length)

        try:
            delivery, snapshot = apply_effect(operation_id, idempotency_key, drop_ack)
        except ValueError as exc:
            self.send_json(409, {"error": str(exc)})
            return

        payload = {
            "delivery": delivery,
            "idempotency_key": idempotency_key,
            "boot_id": BOOT_ID,
            "idempotency_mode": IDEMPOTENCY_MODE,
            **snapshot,
        }

        # Persist effect/request state first, then deliberately terminate the
        # connection. The client sees ACK_UNKNOWN while durable state survives.
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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()
    init_schema()
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(
        json.dumps(
            {
                "service": "resonance-external-http-restart",
                "host": args.host,
                "port": args.port,
                "boot_id": BOOT_ID,
                "idempotency_mode": IDEMPOTENCY_MODE,
                "state_db": str(STATE_DB),
            },
            sort_keys=True,
        ),
        flush=True,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
