from __future__ import annotations

import argparse
import json
import sqlite3
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

STATE_DB = Path("/state/resource.db")


def db():
    c = sqlite3.connect(STATE_DB)
    c.row_factory = sqlite3.Row
    c.execute("CREATE TABLE IF NOT EXISTS fences(resource_id TEXT PRIMARY KEY, highest_fence INTEGER NOT NULL)")
    c.execute("""
        CREATE TABLE IF NOT EXISTS effects(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          resource_id TEXT NOT NULL,
          worker TEXT NOT NULL,
          fence INTEGER NOT NULL,
          artifact_digest TEXT NOT NULL,
          phase TEXT NOT NULL,
          enforce_fence INTEGER NOT NULL
        )
    """)
    c.commit()
    return c


class Handler(BaseHTTPRequestHandler):
    server_version = "RESONANCE-ResultHandoff/1.0"

    def log_message(self, fmt, *args):
        return

    def send_json(self, status, payload):
        body = json.dumps(payload, sort_keys=True).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/health":
            self.send_json(200, {"status": "ok", "state_db": str(STATE_DB)})
            return
        if self.path.startswith("/status/"):
            resource_id = self.path.split("/", 2)[2]
            with db() as c:
                rows = c.execute(
                    "SELECT id, resource_id, worker, fence, artifact_digest, phase, enforce_fence FROM effects WHERE resource_id=? ORDER BY id",
                    (resource_id,),
                ).fetchall()
                fence_row = c.execute("SELECT highest_fence FROM fences WHERE resource_id=?", (resource_id,)).fetchone()
            effects = [dict(x) for x in rows]
            self.send_json(200, {
                "resource_id": resource_id,
                "effect_count": len(effects),
                "effects": effects,
                "highest_fence": int(fence_row[0]) if fence_row else 0,
                "status": "absent" if not effects else ("committed" if len(effects) == 1 else "conflict"),
            })
            return
        self.send_json(404, {"error": "not_found"})

    def do_POST(self):
        if self.path != "/effects":
            self.send_json(404, {"error": "not_found"})
            return
        resource_id = self.headers.get("X-Resource-Id", "")
        worker = self.headers.get("X-Worker", "")
        fence = int(self.headers.get("X-Fencing-Token", "0"))
        artifact_digest = self.headers.get("X-Artifact-Digest", "")
        phase = self.headers.get("X-Phase", "commit")
        enforce = self.headers.get("X-Enforce-Fence", "0") == "1"
        with db() as c:
            row = c.execute("SELECT highest_fence FROM fences WHERE resource_id=?", (resource_id,)).fetchone()
            highest = int(row[0]) if row else 0
            if enforce and fence < highest:
                count = c.execute("SELECT COUNT(*) FROM effects WHERE resource_id=?", (resource_id,)).fetchone()[0]
                self.send_json(409, {
                    "delivery": "fenced_out",
                    "presented_fence": fence,
                    "highest_fence": highest,
                    "effect_count": int(count),
                    "artifact_digest": artifact_digest,
                })
                return
            c.execute(
                "INSERT INTO effects(resource_id, worker, fence, artifact_digest, phase, enforce_fence) VALUES (?,?,?,?,?,?)",
                (resource_id, worker, fence, artifact_digest, phase, 1 if enforce else 0),
            )
            if fence > highest:
                c.execute(
                    "INSERT INTO fences(resource_id, highest_fence) VALUES (?,?) ON CONFLICT(resource_id) DO UPDATE SET highest_fence=excluded.highest_fence",
                    (resource_id, fence),
                )
            c.commit()
            count = c.execute("SELECT COUNT(*) FROM effects WHERE resource_id=?", (resource_id,)).fetchone()[0]
            new_highest = max(highest, fence)
        self.send_json(200, {
            "delivery": "applied",
            "resource_id": resource_id,
            "worker": worker,
            "presented_fence": fence,
            "highest_fence": new_highest,
            "artifact_digest": artifact_digest,
            "phase": phase,
            "effect_count": int(count),
        })


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--host", default="0.0.0.0")
    p.add_argument("--port", type=int, default=8080)
    args = p.parse_args()
    STATE_DB.parent.mkdir(parents=True, exist_ok=True)
    with db():
        pass
    ThreadingHTTPServer((args.host, args.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
