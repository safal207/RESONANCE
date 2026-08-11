from __future__ import annotations

import argparse
import json
import os
import socket
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote, urlparse

LOCK = threading.Lock()
EFFECTS_BY_KEY: dict[str, dict[str, str]] = {}
POST_REQUESTS_BY_OPERATION: dict[str, int] = {}
ACK_DROPS_BY_OPERATION: dict[str, int] = {}


def operation_snapshot(operation_id: str) -> dict[str, object]:
    with LOCK:
        effects = [
            {"idempotency_key": key, "operation_id": record["operation_id"]}
            for key, record in EFFECTS_BY_KEY.items()
            if record["operation_id"] == operation_id
        ]
        effects.sort(key=lambda item: str(item["idempotency_key"]))
        count = len(effects)
        return {
            "operation_id": operation_id,
            "status": "absent" if count == 0 else "committed" if count == 1 else "conflict",
            "effect_count": count,
            "effects": effects,
            "post_requests": POST_REQUESTS_BY_OPERATION.get(operation_id, 0),
            "ack_drops": ACK_DROPS_BY_OPERATION.get(operation_id, 0),
        }


class Handler(BaseHTTPRequestHandler):
    server_version = "RESONANCEExternalHTTP/1.0"

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
                    "service": "resonance-external-http",
                    "service_instance": os.environ.get("SERVICE_INSTANCE", "external-http-container"),
                    "hostname": socket.gethostname(),
                    "pid": os.getpid(),
                },
            )
            return

        prefix = "/status/"
        if parsed.path.startswith(prefix):
            operation_id = unquote(parsed.path[len(prefix) :])
            if not operation_id:
                self.send_json(400, {"error": "missing_operation_id"})
                return
            self.send_json(200, operation_snapshot(operation_id))
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

        with LOCK:
            POST_REQUESTS_BY_OPERATION[operation_id] = POST_REQUESTS_BY_OPERATION.get(operation_id, 0) + 1
            existing = EFFECTS_BY_KEY.get(idempotency_key)
            if existing is not None and existing["operation_id"] != operation_id:
                self.send_json(409, {"error": "idempotency_key_reused_for_different_operation"})
                return
            applied = existing is None
            if applied:
                EFFECTS_BY_KEY[idempotency_key] = {"operation_id": operation_id}
            if drop_ack:
                ACK_DROPS_BY_OPERATION[operation_id] = ACK_DROPS_BY_OPERATION.get(operation_id, 0) + 1

        snapshot = operation_snapshot(operation_id)
        payload = {
            "delivery": "applied" if applied else "deduplicated",
            "idempotency_key": idempotency_key,
            **snapshot,
        }

        # Deliberately commit the in-memory effect first, then terminate the
        # connection without an HTTP response. The client therefore observes an
        # ambiguous acknowledgement even though the remote effect already exists.
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

    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(json.dumps({"service": "resonance-external-http", "host": args.host, "port": args.port}), flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
