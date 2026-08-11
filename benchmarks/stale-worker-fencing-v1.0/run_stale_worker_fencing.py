from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import psycopg

CONTAINER = "resonance-external-stale-worker-fence"
VOLUME = "resonance-stale-worker-fencing-v1"
IMAGE = os.environ.get("HTTP_SERVICE_IMAGE", "python:3.12-slim")
BASE_URL = os.environ.get("EXTERNAL_BASE_URL", "http://127.0.0.1:18085")
SERVICE = Path("benchmarks/stale-worker-fencing-v1.0/external_service.py").resolve()


def db(dsn):
    return psycopg.connect(dsn, autocommit=False)


def init_schema(dsn):
    with db(dsn) as c:
        with c.cursor() as cur:
            cur.execute("CREATE TABLE IF NOT EXISTS worker_ownership(resource_id text PRIMARY KEY, owner text NOT NULL, fence bigint NOT NULL)")
        c.commit()


def reset_coordination(dsn, resource_id):
    with db(dsn) as c:
        with c.cursor() as cur:
            cur.execute("DELETE FROM worker_ownership WHERE resource_id=%s", (resource_id,))
        c.commit()


def acquire(dsn, resource_id, worker):
    with db(dsn) as c:
        with c.cursor() as cur:
            cur.execute("SELECT fence FROM worker_ownership WHERE resource_id=%s FOR UPDATE", (resource_id,))
            row = cur.fetchone()
            token = 1 if row is None else int(row[0]) + 1
            if row is None:
                cur.execute("INSERT INTO worker_ownership(resource_id, owner, fence) VALUES (%s,%s,%s)", (resource_id, worker, token))
            else:
                cur.execute("UPDATE worker_ownership SET owner=%s, fence=%s WHERE resource_id=%s", (worker, token, resource_id))
        c.commit()
    return token


def owner_snapshot(dsn, resource_id):
    with db(dsn) as c:
        with c.cursor() as cur:
            cur.execute("SELECT owner, fence FROM worker_ownership WHERE resource_id=%s", (resource_id,))
            row = cur.fetchone()
        c.commit()
    return {"owner": str(row[0]), "fence": int(row[1])}


def run(*args, check=True):
    return subprocess.run(args, text=True, capture_output=True, check=check)


def req_json(method, path, headers=None):
    r = urllib.request.Request(BASE_URL + path, method=method, data=b"{}" if method == "POST" else None, headers={"Content-Type": "application/json", **(headers or {})})
    try:
        with urllib.request.urlopen(r, timeout=5) as resp:
            return {"http_status": resp.status, "payload": json.loads(resp.read().decode())}
    except urllib.error.HTTPError as exc:
        return {"http_status": exc.code, "payload": json.loads(exc.read().decode())}


def start_service():
    run("docker", "rm", "-f", CONTAINER, check=False)
    run("docker", "volume", "rm", "-f", VOLUME, check=False)
    run("docker", "volume", "create", VOLUME)
    run("docker", "run", "-d", "--name", CONTAINER, "-p", "18085:8080", "-e", "STATE_DB=/state/resource.db", "-v", f"{VOLUME}:/state", "-v", f"{SERVICE}:/app/external_service.py:ro", IMAGE, "python", "/app/external_service.py", "--host", "0.0.0.0", "--port", "8080")
    for _ in range(40):
        try:
            h = req_json("GET", "/health")
            if h["http_status"] == 200:
                return h["payload"]
        except Exception:
            pass
        time.sleep(0.25)
    raise RuntimeError("external service not healthy")


def post(resource_id, worker, fence, enforce):
    return req_json("POST", "/effects", {"X-Resource-Id": resource_id, "X-Worker": worker, "X-Fencing-Token": str(fence), "X-Enforce-Fence": "1" if enforce else "0"})


def status(resource_id):
    return req_json("GET", f"/status/{resource_id}")["payload"]


def unsafe_split_brain(dsn):
    rid = "unsafe-resource"
    reset_coordination(dsn, rid)
    a = acquire(dsn, rid, "worker-A")
    # A stalls. B takes over with a later token.
    b = acquire(dsn, rid, "worker-B")
    after_takeover = owner_snapshot(dsn, rid)
    b_write = post(rid, "worker-B", b, False)
    a_resurrected = post(rid, "worker-A", a, False)
    return {"resource_id": rid, "worker_a_token": a, "worker_b_token": b, "coordination_after_takeover": after_takeover, "worker_b_write": b_write, "worker_a_resurrected_write": a_resurrected, "final_remote": status(rid)}


def safe_fencing(dsn):
    rid = "fenced-resource"
    reset_coordination(dsn, rid)
    a = acquire(dsn, rid, "worker-A")
    b = acquire(dsn, rid, "worker-B")
    after_takeover = owner_snapshot(dsn, rid)
    b_write = post(rid, "worker-B", b, True)
    a_resurrected = post(rid, "worker-A", a, True)
    return {"resource_id": rid, "worker_a_token": a, "worker_b_token": b, "coordination_after_takeover": after_takeover, "worker_b_write": b_write, "worker_a_resurrected_write": a_resurrected, "final_remote": status(rid)}


def safe_recheck_only(dsn):
    rid = "recheck-resource"
    reset_coordination(dsn, rid)
    a = acquire(dsn, rid, "worker-A")
    b = acquire(dsn, rid, "worker-B")
    current = owner_snapshot(dsn, rid)
    stale_detected = current["owner"] != "worker-A" or current["fence"] != a
    a_write_made = False
    if not stale_detected:
        a_write_made = True
        post(rid, "worker-A", a, False)
    b_write = post(rid, "worker-B", b, True)
    return {"resource_id": rid, "worker_a_token": a, "worker_b_token": b, "current_owner_before_a_replay": current, "stale_detected": stale_detected, "worker_a_write_made": a_write_made, "worker_b_write": b_write, "final_remote": status(rid)}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dsn", default=os.environ.get("DATABASE_URL", "postgresql://resonance:resonance@127.0.0.1:5432/resonance"))
    p.add_argument("--out", default="benchmark-results/stale-worker-fencing-v1.0")
    args = p.parse_args()
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    init_schema(args.dsn)
    health = start_service()
    try:
        unsafe = unsafe_split_brain(args.dsn)
        fenced = safe_fencing(args.dsn)
        recheck = safe_recheck_only(args.dsn)
        with db(args.dsn) as c:
            with c.cursor() as cur:
                cur.execute("SHOW server_version"); pg = str(cur.fetchone()[0])
            c.commit()
        digest = run("docker", "image", "inspect", IMAGE, "--format", "{{index .RepoDigests 0}}").stdout.strip()
        checks = [
            {"id":"new_owner_receives_strictly_higher_fencing_token","points":2,"pass":unsafe["worker_b_token"] > unsafe["worker_a_token"] and fenced["worker_b_token"] > fenced["worker_a_token"],"evidence":{"unsafe":[unsafe["worker_a_token"],unsafe["worker_b_token"]],"fenced":[fenced["worker_a_token"],fenced["worker_b_token"]]}},
            {"id":"ownership_without_resource_fence_allows_stale_worker_duplicate","points":2,"pass":unsafe["coordination_after_takeover"]["owner"]=="worker-B" and unsafe["final_remote"]["effect_count"]==2 and unsafe["final_remote"]["status"]=="conflict","evidence":unsafe},
            {"id":"external_resource_rejects_stale_fencing_token","points":2,"pass":fenced["worker_b_write"]["http_status"]==200 and fenced["worker_a_resurrected_write"]["http_status"]==409 and fenced["worker_a_resurrected_write"]["payload"].get("delivery")=="fenced_out","evidence":fenced},
            {"id":"fenced_path_preserves_single_effect","points":2,"pass":fenced["final_remote"]["effect_count"]==1 and fenced["final_remote"]["highest_fence"]==fenced["worker_b_token"],"evidence":fenced["final_remote"]},
            {"id":"fresh_coordination_recheck_can_stop_stale_worker_before_external_call","points":2,"pass":recheck["stale_detected"] and not recheck["worker_a_write_made"] and recheck["final_remote"]["effect_count"]==1,"evidence":recheck},
        ]
        score = sum(x["points"] for x in checks if x["pass"])
        result = {"benchmark":"RESONANCE Stale Worker Resurrection / Fencing Token Split-Brain","benchmark_version":"1.0","executed_at":datetime.now(timezone.utc).isoformat(),"protocol":"RESONANCE Transactional Trust Protocol v1.0","database":{"server_version":pg},"http_service":health,"http_service_image":IMAGE,"http_service_image_digest":digest,"unsafe_split_brain":unsafe,"safe_fencing":fenced,"safe_recheck":recheck,"checks":checks,"score":score,"max_score":10,"classification":"Stale-worker fencing protocol passes" if score==10 else "Protocol incomplete","invariants":["Lease or ownership claim is not external execution authority unless the protected resource enforces a monotonic fence.","A stale worker that resumes after takeover must not be able to commit with an older fencing token.","Fencing tokens must be compared at the protected resource boundary.","Fresh ownership recheck can prevent replay before the external call, but fencing remains the resource-side protection."],"external_safety_certification":False,"vulnerability_claim":False}
        (out/"result.json").write_text(json.dumps(result, indent=2, sort_keys=True)+"\n")
        (out/"RESULT.md").write_text(f"# Stale Worker Fencing v1.0\n\nScore: **{score}/10**\n\nUnsafe effects: **{unsafe['final_remote']['effect_count']}**\n\nFenced effects: **{fenced['final_remote']['effect_count']}**\n\nStale worker response: **HTTP {fenced['worker_a_resurrected_write']['http_status']} / {fenced['worker_a_resurrected_write']['payload'].get('delivery')}**\n")
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if score==10 else 1
    finally:
        run("docker", "rm", "-f", CONTAINER, check=False)
        run("docker", "volume", "rm", "-f", VOLUME, check=False)


if __name__ == "__main__":
    raise SystemExit(main())
