from __future__ import annotations

import argparse
import json
import os
import sqlite3
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

DB = os.environ.get("STATE_DB", "/state/resource.db")
BOOT_ID = uuid.uuid4().hex


def conn():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    c.execute("CREATE TABLE IF NOT EXISTS effects(id INTEGER PRIMARY KEY AUTOINCREMENT, resource_id TEXT NOT NULL, worker TEXT NOT NULL, fence INTEGER NOT NULL, artifact_digest TEXT NOT NULL, input_state_version INTEGER NOT NULL, output_value INTEGER NOT NULL, phase TEXT NOT NULL)")
    c.execute("CREATE TABLE IF NOT EXISTS resource_state(resource_id TEXT PRIMARY KEY, highest_fence INTEGER NOT NULL DEFAULT 0)")
    c.commit()
    return c


def snapshot(resource_id: str):
    with conn() as c:
        row = c.execute("SELECT highest_fence FROM resource_state WHERE resource_id=?", (resource_id,)).fetchone()
        effects = [dict(r) for r in c.execute("SELECT id, resource_id, worker, fence, artifact_digest, input_state_version, output_value, phase FROM effects WHERE resource_id=? ORDER BY id", (resource_id,))]
    return {
        "resource_id": resource_id,
        "highest_fence": int(row[0]) if row else 0,
        "effect_count": len(effects),
        "effects": effects,
        "status": "conflict" if len(effects) > 1 else "committed" if effects else "absent",
    }


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def send_json(self, code, payload):
        body = json.dumps(payload, sort_keys=True).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/health":
            return self.send_json(200, {"status": "ok", "boot_id": BOOT_ID, "pid": os.getpid()})
        if self.path.startswith("/status/"):
            return self.send_json(200, snapshot(self.path.rsplit("/", 1)[-1]))
        return self.send_json(404, {"error": "not_found"})

    def do_POST(self):
        if self.path != "/effects":
            return self.send_json(404, {"error": "not_found"})
        resource_id = self.headers.get("X-Resource-Id", "")
        worker = self.headers.get("X-Worker", "")
        fence = int(self.headers.get("X-Fencing-Token", "0"))
        artifact_digest = self.headers.get("X-Artifact-Digest", "")
        input_state_version = int(self.headers.get("X-Input-State-Version", "0"))
        output_value = int(self.headers.get("X-Output-Value", "0"))
        phase = self.headers.get("X-Phase", "commit")
        if not resource_id or not worker or not artifact_digest:
            return self.send_json(400, {"error": "missing_identity"})
        with conn() as c:
            row = c.execute("SELECT highest_fence FROM resource_state WHERE resource_id=?", (resource_id,)).fetchone()
            highest = int(row[0]) if row else 0
            if fence < highest:
                payload = snapshot(resource_id)
                payload.update({"delivery": "fenced_out", "expected_at_least": highest, "presented_fence": fence})
                return self.send_json(409, payload)
            if row is None:
                c.execute("INSERT INTO resource_state(resource_id, highest_fence) VALUES (?, ?)", (resource_id, fence))
            elif fence > highest:
                c.execute("UPDATE resource_state SET highest_fence=? WHERE resource_id=?", (fence, resource_id))
            c.execute("INSERT INTO effects(resource_id, worker, fence, artifact_digest, input_state_version, output_value, phase) VALUES (?, ?, ?, ?, ?, ?, ?)", (resource_id, worker, fence, artifact_digest, input_state_version, output_value, phase))
            c.commit()
        payload = snapshot(resource_id)
        payload.update({"delivery": "applied", "presented_fence": fence})
        return self.send_json(200, payload)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--host", default="0.0.0.0")
    p.add_argument("--port", type=int, default=8080)
    a = p.parse_args()
    conn().close()
    ThreadingHTTPServer((a.host, a.port), Handler).serve_forever()
