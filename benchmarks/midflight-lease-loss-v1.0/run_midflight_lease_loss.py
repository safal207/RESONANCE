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

CONTAINER = "resonance-external-midflight-lease-loss"
VOLUME = "resonance-midflight-lease-loss-v1"
IMAGE = os.environ.get("HTTP_SERVICE_IMAGE", "python:3.12-slim")
BASE_URL = os.environ.get("EXTERNAL_BASE_URL", "http://127.0.0.1:18087")
SERVICE = Path("benchmarks/midflight-lease-loss-v1.0/external_service.py").resolve()
LEASE_TTL = 60
T0 = 1000
START_TIME = 1020
TAKEOVER_TIME = 1070
FINISH_TIME = 1080
CONTROL_FINISH_TIME = 1050


def db(dsn):
    return psycopg.connect(dsn, autocommit=False)


def init_schema(dsn):
    with db(dsn) as c:
        with c.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS midflight_leases(
                  resource_id text PRIMARY KEY,
                  owner text NOT NULL,
                  fence bigint NOT NULL,
                  lease_version bigint NOT NULL,
                  expires_at bigint NOT NULL
                )
            """)
        c.commit()


def reset_lease(dsn, rid):
    with db(dsn) as c:
        with c.cursor() as cur:
            cur.execute("DELETE FROM midflight_leases WHERE resource_id=%s", (rid,))
        c.commit()


def snapshot(dsn, rid):
    with db(dsn) as c:
        with c.cursor() as cur:
            cur.execute("SELECT owner, fence, lease_version, expires_at FROM midflight_leases WHERE resource_id=%s", (rid,))
            row = cur.fetchone()
        c.commit()
    if row is None:
        return None
    return {"owner": str(row[0]), "fence": int(row[1]), "lease_version": int(row[2]), "expires_at": int(row[3])}


def acquire(dsn, rid, worker, now):
    with db(dsn) as c:
        with c.cursor() as cur:
            cur.execute("INSERT INTO midflight_leases(resource_id, owner, fence, lease_version, expires_at) VALUES (%s,%s,1,1,%s)", (rid, worker, now + LEASE_TTL))
        c.commit()
    return snapshot(dsn, rid)


def authorize(dsn, rid, worker, expected_fence, expected_version, now):
    with db(dsn) as c:
        with c.cursor() as cur:
            cur.execute("""
                SELECT owner, fence, lease_version, expires_at
                  FROM midflight_leases
                 WHERE resource_id=%s
                   AND owner=%s
                   AND fence=%s
                   AND lease_version=%s
                   AND expires_at >= %s
            """, (rid, worker, expected_fence, expected_version, now))
            row = cur.fetchone()
        c.commit()
    return {"authorized": row is not None, "decision_time": now, "expected_fence": expected_fence, "expected_version": expected_version, "observed": snapshot(dsn, rid)}


def takeover(dsn, rid, worker, now):
    with db(dsn) as c:
        with c.cursor() as cur:
            cur.execute("SELECT fence, lease_version, expires_at FROM midflight_leases WHERE resource_id=%s FOR UPDATE", (rid,))
            row = cur.fetchone()
            if row is None or now <= int(row[2]):
                raise RuntimeError("takeover precondition not met")
            cur.execute("UPDATE midflight_leases SET owner=%s, fence=%s, lease_version=%s, expires_at=%s WHERE resource_id=%s", (worker, int(row[0]) + 1, int(row[1]) + 1, now + LEASE_TTL, rid))
        c.commit()
    return snapshot(dsn, rid)


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
    run("docker", "run", "-d", "--name", CONTAINER, "-p", "18087:8080", "-e", "STATE_DB=/state/resource.db", "-v", f"{VOLUME}:/state", "-v", f"{SERVICE}:/app/external_service.py:ro", IMAGE, "python", "/app/external_service.py", "--host", "0.0.0.0", "--port", "8080")
    for _ in range(40):
        try:
            h = req_json("GET", "/health")
            if h["http_status"] == 200:
                return h["payload"]
        except Exception:
            pass
        time.sleep(0.25)
    raise RuntimeError("external service not healthy")


def post(rid, worker, fence, enforce, phase):
    return req_json("POST", "/effects", {"X-Resource-Id": rid, "X-Worker": worker, "X-Fencing-Token": str(fence), "X-Enforce-Fence": "1" if enforce else "0", "X-Phase": phase})


def remote_status(rid):
    return req_json("GET", f"/status/{rid}")["payload"]


def setup_midflight(dsn, rid):
    reset_lease(dsn, rid)
    a = acquire(dsn, rid, "worker-A", T0)
    start = authorize(dsn, rid, "worker-A", a["fence"], a["lease_version"], START_TIME)
    b = takeover(dsn, rid, "worker-B", TAKEOVER_TIME)
    return a, start, b


def unsafe_start_only(dsn):
    rid = "unsafe-midflight-resource"
    a, start, b = setup_midflight(dsn, rid)
    b_write = post(rid, "worker-B", b["fence"], False, "new-owner-commit")
    a_finish = post(rid, "worker-A", a["fence"], False, "finish-using-start-proof")
    return {"resource_id": rid, "worker_a_initial": a, "start_authorization": start, "worker_b_after_takeover": b, "worker_b_write": b_write, "worker_a_finish": a_finish, "final_lease": snapshot(dsn, rid), "final_remote": remote_status(rid)}


def safe_commit_recheck(dsn):
    rid = "safe-commit-recheck-resource"
    a, start, b = setup_midflight(dsn, rid)
    b_write = post(rid, "worker-B", b["fence"], True, "new-owner-commit")
    finish_auth = authorize(dsn, rid, "worker-A", a["fence"], a["lease_version"], FINISH_TIME)
    a_write_made = False
    if finish_auth["authorized"]:
        a_write_made = True
        post(rid, "worker-A", a["fence"], True, "old-worker-final-commit")
    return {"resource_id": rid, "start_authorization": start, "finish_authorization": finish_auth, "worker_b_after_takeover": b, "worker_b_write": b_write, "worker_a_write_made": a_write_made, "final_lease": snapshot(dsn, rid), "final_remote": remote_status(rid)}


def resource_fence_defense(dsn):
    rid = "resource-fence-midflight"
    a, start, b = setup_midflight(dsn, rid)
    b_write = post(rid, "worker-B", b["fence"], True, "new-owner-commit")
    a_finish = post(rid, "worker-A", a["fence"], True, "old-worker-final-commit")
    return {"resource_id": rid, "start_authorization": start, "worker_b_after_takeover": b, "worker_b_write": b_write, "worker_a_finish": a_finish, "final_lease": snapshot(dsn, rid), "final_remote": remote_status(rid)}


def valid_completion_before_expiry(dsn):
    rid = "valid-midflight-control"
    reset_lease(dsn, rid)
    a = acquire(dsn, rid, "worker-A", T0)
    start = authorize(dsn, rid, "worker-A", a["fence"], a["lease_version"], START_TIME)
    finish_auth = authorize(dsn, rid, "worker-A", a["fence"], a["lease_version"], CONTROL_FINISH_TIME)
    write = post(rid, "worker-A", a["fence"], True, "valid-final-commit") if finish_auth["authorized"] else None
    return {"resource_id": rid, "start_authorization": start, "finish_authorization": finish_auth, "worker_a_write": write, "final_remote": remote_status(rid)}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dsn", default=os.environ.get("DATABASE_URL", "postgresql://resonance:resonance@127.0.0.1:5432/resonance"))
    p.add_argument("--out", default="benchmark-results/midflight-lease-loss-v1.0")
    args = p.parse_args()
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    init_schema(args.dsn)
    health = start_service()
    try:
        unsafe = unsafe_start_only(args.dsn)
        recheck = safe_commit_recheck(args.dsn)
        fence = resource_fence_defense(args.dsn)
        control = valid_completion_before_expiry(args.dsn)
        with db(args.dsn) as c:
            with c.cursor() as cur:
                cur.execute("SHOW server_version"); pg = str(cur.fetchone()[0])
            c.commit()
        digest = run("docker", "image", "inspect", IMAGE, "--format", "{{index .RepoDigests 0}}").stdout.strip()
        checks = [
            {"id":"start_was_authorized_and_takeover_advanced_execution_epoch","points":2,"pass":unsafe["start_authorization"]["authorized"] and unsafe["worker_b_after_takeover"]["fence"] > unsafe["worker_a_initial"]["fence"],"evidence":{"start":unsafe["start_authorization"],"takeover":unsafe["worker_b_after_takeover"]}},
            {"id":"start_time_only_authority_duplicates_after_midflight_lease_loss","points":2,"pass":unsafe["final_remote"]["effect_count"] == 2 and unsafe["final_remote"]["status"] == "conflict","evidence":unsafe},
            {"id":"commit_time_revalidation_blocks_stale_worker_before_external_call","points":2,"pass":not recheck["finish_authorization"]["authorized"] and not recheck["worker_a_write_made"] and recheck["final_remote"]["effect_count"] == 1,"evidence":recheck},
            {"id":"resource_side_fence_rejects_old_worker_at_final_commit","points":2,"pass":fence["worker_a_finish"]["http_status"] == 409 and fence["worker_a_finish"]["payload"].get("delivery") == "fenced_out" and fence["final_remote"]["effect_count"] == 1 and fence["final_remote"]["highest_fence"] == 2,"evidence":fence},
            {"id":"valid_long_action_can_finish_while_original_epoch_is_still_current","points":2,"pass":control["start_authorization"]["authorized"] and control["finish_authorization"]["authorized"] and control["worker_a_write"]["http_status"] == 200 and control["final_remote"]["effect_count"] == 1,"evidence":control},
        ]
        score = sum(x["points"] for x in checks if x["pass"])
        result = {
            "benchmark":"RESONANCE Mid-flight Lease Loss / Long-Running Action","benchmark_version":"1.0","executed_at":datetime.now(timezone.utc).isoformat(),"protocol":"RESONANCE Transactional Trust Protocol v1.0","database":{"server_version":pg},
            "lease_model":{"ttl_seconds":LEASE_TTL,"initial_time":T0,"start_time":START_TIME,"takeover_time":TAKEOVER_TIME,"finish_time":FINISH_TIME,"control_finish_time":CONTROL_FINISH_TIME},
            "http_service":health,"http_service_image":IMAGE,"http_service_image_digest":digest,"unsafe_start_only":unsafe,"safe_commit_recheck":recheck,"resource_fence_defense":fence,"valid_control":control,"checks":checks,"score":score,"max_score":10,
            "classification":"Mid-flight authority protocol passes" if score == 10 else "Protocol incomplete",
            "invariants":["AUTHORIZED AT START DOES NOT IMPLY AUTHORIZED AT COMMIT.","LONG-RUNNING CONSEQUENTIAL WORK MUST REVALIDATE OR PRESENT A CURRENT FENCING EPOCH AT THE COMMIT BOUNDARY.","LEASE LOSS WHILE WORK IS IN FLIGHT IS AN AUTHORITY-LIFECYCLE TRANSITION.","RESOURCE-SIDE FENCING IS THE FINAL GUARD AGAINST A STALE COMPLETION."],
            "vulnerability_claim":False,"external_safety_certification":False,
        }
        (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        md = f"# RESONANCE Mid-flight Lease Loss / Long-Running Action\n\nScore: **{score}/10**\n\n- A start authorized: `{unsafe['start_authorization']['authorized']}`\n- A fence at start: `{unsafe['worker_a_initial']['fence']}`\n- B fence after takeover: `{unsafe['worker_b_after_takeover']['fence']}`\n- Unsafe final effects: `{unsafe['final_remote']['effect_count']}`\n- Commit-time A authorized: `{recheck['finish_authorization']['authorized']}`\n- Resource-fenced A HTTP: `{fence['worker_a_finish']['http_status']}` / `{fence['worker_a_finish']['payload'].get('delivery')}`\n- Safe final effects: `{fence['final_remote']['effect_count']}`\n"
        (out / "RESULT.md").write_text(md, encoding="utf-8")
        print(json.dumps(result, indent=2, sort_keys=True))
        if score != 10:
            raise SystemExit(1)
    finally:
        run("docker", "rm", "-f", CONTAINER, check=False)


if __name__ == "__main__":
    main()
