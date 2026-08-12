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

CONTAINER = "resonance-external-lease-renewal-race"
VOLUME = "resonance-lease-renewal-race-v1"
IMAGE = os.environ.get("HTTP_SERVICE_IMAGE", "python:3.12-slim")
BASE_URL = os.environ.get("EXTERNAL_BASE_URL", "http://127.0.0.1:18086")
SERVICE = Path("benchmarks/lease-renewal-race-v1.0/external_service.py").resolve()
LEASE_TTL = 60
T0 = 1_000
TAKEOVER_TIME = 1_070
LATE_HEARTBEAT_TIME = 1_075


def db(dsn):
    return psycopg.connect(dsn, autocommit=False)


def init_schema(dsn):
    with db(dsn) as c:
        with c.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS worker_leases(
                  resource_id text PRIMARY KEY,
                  owner text NOT NULL,
                  fence bigint NOT NULL,
                  lease_version bigint NOT NULL,
                  expires_at bigint NOT NULL
                )
                """
            )
        c.commit()


def reset_lease(dsn, resource_id):
    with db(dsn) as c:
        with c.cursor() as cur:
            cur.execute("DELETE FROM worker_leases WHERE resource_id=%s", (resource_id,))
        c.commit()


def snapshot(dsn, resource_id):
    with db(dsn) as c:
        with c.cursor() as cur:
            cur.execute("SELECT owner, fence, lease_version, expires_at FROM worker_leases WHERE resource_id=%s", (resource_id,))
            row = cur.fetchone()
        c.commit()
    if row is None:
        return None
    return {"owner": str(row[0]), "fence": int(row[1]), "lease_version": int(row[2]), "expires_at": int(row[3])}


def acquire_initial(dsn, resource_id, worker, now):
    with db(dsn) as c:
        with c.cursor() as cur:
            cur.execute(
                "INSERT INTO worker_leases(resource_id, owner, fence, lease_version, expires_at) VALUES (%s,%s,1,1,%s)",
                (resource_id, worker, now + LEASE_TTL),
            )
        c.commit()
    return snapshot(dsn, resource_id)


def takeover_if_expired(dsn, resource_id, worker, now):
    with db(dsn) as c:
        with c.cursor() as cur:
            cur.execute("SELECT owner, fence, lease_version, expires_at FROM worker_leases WHERE resource_id=%s FOR UPDATE", (resource_id,))
            row = cur.fetchone()
            if row is None:
                raise RuntimeError("lease missing")
            if now <= int(row[3]):
                raise RuntimeError("lease not expired")
            new_fence = int(row[1]) + 1
            new_version = int(row[2]) + 1
            cur.execute(
                "UPDATE worker_leases SET owner=%s, fence=%s, lease_version=%s, expires_at=%s WHERE resource_id=%s",
                (worker, new_fence, new_version, now + LEASE_TTL, resource_id),
            )
        c.commit()
    return snapshot(dsn, resource_id)


def unsafe_blind_heartbeat(dsn, resource_id, worker, cached_fence, cached_version, now):
    # Deliberately unsafe: a delayed heartbeat blindly writes a cached lease snapshot
    # back over whatever ownership epoch currently exists.
    with db(dsn) as c:
        with c.cursor() as cur:
            cur.execute(
                "UPDATE worker_leases SET owner=%s, fence=%s, lease_version=%s, expires_at=%s WHERE resource_id=%s",
                (worker, cached_fence, cached_version + 1, now + LEASE_TTL, resource_id),
            )
            rows = cur.rowcount
        c.commit()
    return {"updated_rows": rows, "lease": snapshot(dsn, resource_id)}


def safe_compare_and_renew(dsn, resource_id, worker, expected_fence, expected_version, now):
    # Current owner can renew only while its exact ownership epoch is still current
    # and has not expired. A stale heartbeat becomes a zero-row safety result.
    with db(dsn) as c:
        with c.cursor() as cur:
            cur.execute(
                """
                UPDATE worker_leases
                   SET expires_at=%s,
                       lease_version=lease_version+1
                 WHERE resource_id=%s
                   AND owner=%s
                   AND fence=%s
                   AND lease_version=%s
                   AND expires_at >= %s
                """,
                (now + LEASE_TTL, resource_id, worker, expected_fence, expected_version, now),
            )
            rows = cur.rowcount
        c.commit()
    return {"updated_rows": rows, "lease": snapshot(dsn, resource_id)}


def run(*args, check=True):
    return subprocess.run(args, text=True, capture_output=True, check=check)


def req_json(method, path, headers=None):
    r = urllib.request.Request(
        BASE_URL + path,
        method=method,
        data=b"{}" if method == "POST" else None,
        headers={"Content-Type": "application/json", **(headers or {})},
    )
    try:
        with urllib.request.urlopen(r, timeout=5) as resp:
            return {"http_status": resp.status, "payload": json.loads(resp.read().decode())}
    except urllib.error.HTTPError as exc:
        return {"http_status": exc.code, "payload": json.loads(exc.read().decode())}


def start_service():
    run("docker", "rm", "-f", CONTAINER, check=False)
    run("docker", "volume", "rm", "-f", VOLUME, check=False)
    run("docker", "volume", "create", VOLUME)
    run(
        "docker", "run", "-d", "--name", CONTAINER,
        "-p", "18086:8080",
        "-e", "STATE_DB=/state/resource.db",
        "-v", f"{VOLUME}:/state",
        "-v", f"{SERVICE}:/app/external_service.py:ro",
        IMAGE, "python", "/app/external_service.py", "--host", "0.0.0.0", "--port", "8080",
    )
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
    return req_json(
        "POST",
        "/effects",
        {
            "X-Resource-Id": resource_id,
            "X-Worker": worker,
            "X-Fencing-Token": str(fence),
            "X-Enforce-Fence": "1" if enforce else "0",
        },
    )


def remote_status(resource_id):
    return req_json("GET", f"/status/{resource_id}")["payload"]


def unsafe_delayed_heartbeat(dsn):
    rid = "unsafe-renewal-resource"
    reset_lease(dsn, rid)
    a = acquire_initial(dsn, rid, "worker-A", T0)
    b = takeover_if_expired(dsn, rid, "worker-B", TAKEOVER_TIME)
    b_write = post(rid, "worker-B", b["fence"], False)
    late = unsafe_blind_heartbeat(dsn, rid, "worker-A", a["fence"], a["lease_version"], LATE_HEARTBEAT_TIME)
    a_write = post(rid, "worker-A", a["fence"], False)
    return {
        "resource_id": rid,
        "worker_a_initial": a,
        "worker_b_after_takeover": b,
        "worker_b_write": b_write,
        "late_heartbeat": late,
        "worker_a_resurrected_write": a_write,
        "final_lease": snapshot(dsn, rid),
        "final_remote": remote_status(rid),
    }


def safe_compare_renewal(dsn):
    rid = "safe-renewal-resource"
    reset_lease(dsn, rid)
    a = acquire_initial(dsn, rid, "worker-A", T0)
    b = takeover_if_expired(dsn, rid, "worker-B", TAKEOVER_TIME)
    b_write = post(rid, "worker-B", b["fence"], True)
    late = safe_compare_and_renew(dsn, rid, "worker-A", a["fence"], a["lease_version"], LATE_HEARTBEAT_TIME)
    a_write_made = False
    if late["updated_rows"] == 1:
        a_write_made = True
        post(rid, "worker-A", a["fence"], True)
    return {
        "resource_id": rid,
        "worker_a_initial": a,
        "worker_b_after_takeover": b,
        "worker_b_write": b_write,
        "late_heartbeat": late,
        "worker_a_write_made": a_write_made,
        "final_lease": snapshot(dsn, rid),
        "final_remote": remote_status(rid),
    }


def resource_fence_defense(dsn):
    rid = "resource-fence-defense"
    reset_lease(dsn, rid)
    a = acquire_initial(dsn, rid, "worker-A", T0)
    b = takeover_if_expired(dsn, rid, "worker-B", TAKEOVER_TIME)
    b_write = post(rid, "worker-B", b["fence"], True)
    late = unsafe_blind_heartbeat(dsn, rid, "worker-A", a["fence"], a["lease_version"], LATE_HEARTBEAT_TIME)
    a_write = post(rid, "worker-A", a["fence"], True)
    return {
        "resource_id": rid,
        "worker_a_initial": a,
        "worker_b_after_takeover": b,
        "worker_b_write": b_write,
        "late_heartbeat": late,
        "worker_a_resurrected_write": a_write,
        "final_lease": snapshot(dsn, rid),
        "final_remote": remote_status(rid),
    }


def valid_current_heartbeat(dsn):
    rid = "valid-heartbeat-resource"
    reset_lease(dsn, rid)
    a = acquire_initial(dsn, rid, "worker-A", T0)
    renewed = safe_compare_and_renew(dsn, rid, "worker-A", a["fence"], a["lease_version"], T0 + 30)
    write = post(rid, "worker-A", a["fence"], True)
    return {
        "resource_id": rid,
        "worker_a_initial": a,
        "renewed": renewed,
        "worker_a_write": write,
        "final_lease": snapshot(dsn, rid),
        "final_remote": remote_status(rid),
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dsn", default=os.environ.get("DATABASE_URL", "postgresql://resonance:resonance@127.0.0.1:5432/resonance"))
    p.add_argument("--out", default="benchmark-results/lease-renewal-race-v1.0")
    args = p.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    init_schema(args.dsn)
    health = start_service()
    try:
        unsafe = unsafe_delayed_heartbeat(args.dsn)
        safe = safe_compare_renewal(args.dsn)
        fence_defense = resource_fence_defense(args.dsn)
        valid = valid_current_heartbeat(args.dsn)
        with db(args.dsn) as c:
            with c.cursor() as cur:
                cur.execute("SHOW server_version")
                pg = str(cur.fetchone()[0])
            c.commit()
        digest = run("docker", "image", "inspect", IMAGE, "--format", "{{index .RepoDigests 0}}").stdout.strip()

        checks = [
            {
                "id": "takeover_advances_fence_and_current_heartbeat_can_renew",
                "points": 2,
                "pass": unsafe["worker_b_after_takeover"]["fence"] > unsafe["worker_a_initial"]["fence"]
                and valid["renewed"]["updated_rows"] == 1
                and valid["final_lease"]["owner"] == "worker-A"
                and valid["final_lease"]["expires_at"] == T0 + 30 + LEASE_TTL,
                "evidence": {"takeover": [unsafe["worker_a_initial"], unsafe["worker_b_after_takeover"]], "valid_renewal": valid},
            },
            {
                "id": "blind_late_heartbeat_resurrects_superseded_owner",
                "points": 2,
                "pass": unsafe["late_heartbeat"]["updated_rows"] == 1
                and unsafe["final_lease"]["owner"] == "worker-A"
                and unsafe["final_lease"]["fence"] == unsafe["worker_a_initial"]["fence"]
                and unsafe["worker_b_after_takeover"]["owner"] == "worker-B",
                "evidence": unsafe,
            },
            {
                "id": "resurrected_stale_worker_duplicates_effect_without_resource_fence",
                "points": 2,
                "pass": unsafe["final_remote"]["effect_count"] == 2 and unsafe["final_remote"]["status"] == "conflict",
                "evidence": unsafe["final_remote"],
            },
            {
                "id": "compare_and_renew_rejects_late_heartbeat_and_preserves_new_owner",
                "points": 2,
                "pass": safe["late_heartbeat"]["updated_rows"] == 0
                and safe["final_lease"]["owner"] == "worker-B"
                and safe["final_lease"]["fence"] == safe["worker_b_after_takeover"]["fence"]
                and not safe["worker_a_write_made"]
                and safe["final_remote"]["effect_count"] == 1,
                "evidence": safe,
            },
            {
                "id": "resource_side_fencing_blocks_stale_worker_even_if_coordinator_is_corrupted",
                "points": 2,
                "pass": fence_defense["late_heartbeat"]["updated_rows"] == 1
                and fence_defense["final_lease"]["owner"] == "worker-A"
                and fence_defense["worker_a_resurrected_write"]["http_status"] == 409
                and fence_defense["worker_a_resurrected_write"]["payload"].get("delivery") == "fenced_out"
                and fence_defense["final_remote"]["effect_count"] == 1,
                "evidence": fence_defense,
            },
        ]
        score = sum(x["points"] for x in checks if x["pass"])
        result = {
            "benchmark": "RESONANCE Lease Renewal Race / Delayed Heartbeat",
            "benchmark_version": "1.0",
            "executed_at": datetime.now(timezone.utc).isoformat(),
            "protocol": "RESONANCE Transactional Trust Protocol v1.0",
            "database": {"server_version": pg},
            "lease_model": {"ttl_seconds": LEASE_TTL, "initial_time": T0, "takeover_time": TAKEOVER_TIME, "late_heartbeat_time": LATE_HEARTBEAT_TIME},
            "http_service": health,
            "http_service_image": IMAGE,
            "http_service_image_digest": digest,
            "unsafe_delayed_heartbeat": unsafe,
            "safe_compare_and_renew": safe,
            "resource_fence_defense": fence_defense,
            "valid_current_heartbeat": valid,
            "checks": checks,
            "score": score,
            "max_score": 10,
            "classification": "Delayed-heartbeat lease protocol passes" if score == 10 else "Protocol incomplete",
            "invariants": [
                "A late heartbeat must not resurrect a superseded ownership epoch.",
                "Lease renewal must compare the current owner, fencing token, lease version, and expiry in the renewal mutation.",
                "A zero-row compare-and-renew is a stale-owner safety result, not permission to overwrite the lease.",
                "Resource-side fencing remains the final protection if coordinator state is corrupted by stale renewal.",
            ],
            "external_safety_certification": False,
            "vulnerability_claim": False,
        }
        (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        (out / "RESULT.md").write_text(
            f"# Lease Renewal Race / Delayed Heartbeat v1.0\n\n"
            f"Score: **{score}/10**\n\n"
            f"Unsafe effects after late heartbeat: **{unsafe['final_remote']['effect_count']}**\n\n"
            f"CAS-renew effects: **{safe['final_remote']['effect_count']}**\n\n"
            f"Late heartbeat CAS rows: **{safe['late_heartbeat']['updated_rows']}**\n\n"
            f"Resource-fenced stale write: **HTTP {fence_defense['worker_a_resurrected_write']['http_status']} / {fence_defense['worker_a_resurrected_write']['payload'].get('delivery')}**\n"
        )
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if score == 10 else 1
    finally:
        run("docker", "rm", "-f", CONTAINER, check=False)
        run("docker", "volume", "rm", "-f", VOLUME, check=False)


if __name__ == "__main__":
    raise SystemExit(main())
