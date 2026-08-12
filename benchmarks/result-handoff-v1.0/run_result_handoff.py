from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import psycopg

CONTAINER = "resonance-external-result-handoff"
VOLUME = "resonance-result-handoff-v1"
IMAGE = os.environ.get("HTTP_SERVICE_IMAGE", "python:3.12-slim")
BASE_URL = os.environ.get("EXTERNAL_BASE_URL", "http://127.0.0.1:18088")
SERVICE = Path("benchmarks/result-handoff-v1.0/external_service.py").resolve()
LEASE_TTL = 60
T0 = 1000
START_TIME = 1020
TAKEOVER_TIME = 1070
FINISH_TIME = 1080
CONTROL_FINISH = 1050


def db(dsn):
    return psycopg.connect(dsn, autocommit=False)


def init_schema(dsn):
    with db(dsn) as c:
        with c.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS worker_leases(
                  resource_id text PRIMARY KEY,
                  owner text NOT NULL,
                  fence bigint NOT NULL,
                  lease_version bigint NOT NULL,
                  expires_at bigint NOT NULL
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS result_artifacts(
                  artifact_id text PRIMARY KEY,
                  resource_id text NOT NULL,
                  payload text NOT NULL,
                  artifact_digest text NOT NULL,
                  producer text NOT NULL,
                  producer_fence bigint NOT NULL,
                  producer_version bigint NOT NULL,
                  state text NOT NULL,
                  adopted_by text,
                  adopted_fence bigint,
                  adopted_version bigint
                )
            """)
        c.commit()


def reset(dsn, resource_id):
    with db(dsn) as c:
        with c.cursor() as cur:
            cur.execute("DELETE FROM result_artifacts WHERE resource_id=%s", (resource_id,))
            cur.execute("DELETE FROM worker_leases WHERE resource_id=%s", (resource_id,))
        c.commit()


def lease(dsn, resource_id):
    with db(dsn) as c:
        with c.cursor() as cur:
            cur.execute("SELECT owner, fence, lease_version, expires_at FROM worker_leases WHERE resource_id=%s", (resource_id,))
            row = cur.fetchone()
        c.commit()
    return None if row is None else {"owner": row[0], "fence": int(row[1]), "lease_version": int(row[2]), "expires_at": int(row[3])}


def artifact(dsn, artifact_id):
    with db(dsn) as c:
        with c.cursor() as cur:
            cur.execute("SELECT artifact_id, resource_id, payload, artifact_digest, producer, producer_fence, producer_version, state, adopted_by, adopted_fence, adopted_version FROM result_artifacts WHERE artifact_id=%s", (artifact_id,))
            row = cur.fetchone()
        c.commit()
    if row is None:
        return None
    keys = ["artifact_id", "resource_id", "payload", "artifact_digest", "producer", "producer_fence", "producer_version", "state", "adopted_by", "adopted_fence", "adopted_version"]
    out = dict(zip(keys, row))
    for k in ("producer_fence", "producer_version", "adopted_fence", "adopted_version"):
        if out[k] is not None:
            out[k] = int(out[k])
    return out


def acquire(dsn, resource_id, worker, now):
    with db(dsn) as c:
        with c.cursor() as cur:
            cur.execute("INSERT INTO worker_leases(resource_id, owner, fence, lease_version, expires_at) VALUES (%s,%s,1,1,%s)", (resource_id, worker, now + LEASE_TTL))
        c.commit()
    return lease(dsn, resource_id)


def takeover(dsn, resource_id, worker, now):
    with db(dsn) as c:
        with c.cursor() as cur:
            cur.execute("SELECT owner, fence, lease_version, expires_at FROM worker_leases WHERE resource_id=%s FOR UPDATE", (resource_id,))
            row = cur.fetchone()
            if row is None or now <= int(row[3]):
                raise RuntimeError("lease not expired")
            cur.execute("UPDATE worker_leases SET owner=%s, fence=%s, lease_version=%s, expires_at=%s WHERE resource_id=%s", (worker, int(row[1]) + 1, int(row[2]) + 1, now + LEASE_TTL, resource_id))
        c.commit()
    return lease(dsn, resource_id)


def authorize(dsn, resource_id, worker, expected_fence, expected_version, now):
    observed = lease(dsn, resource_id)
    ok = bool(observed and observed["owner"] == worker and observed["fence"] == expected_fence and observed["lease_version"] == expected_version and observed["expires_at"] >= now)
    return {"authorized": ok, "decision_time": now, "expected_fence": expected_fence, "expected_version": expected_version, "observed": observed}


def digest_payload(payload):
    return hashlib.sha256(payload.encode()).hexdigest()


def produce(dsn, artifact_id, resource_id, payload, worker, fence, version):
    digest = digest_payload(payload)
    with db(dsn) as c:
        with c.cursor() as cur:
            cur.execute("INSERT INTO result_artifacts(artifact_id, resource_id, payload, artifact_digest, producer, producer_fence, producer_version, state) VALUES (%s,%s,%s,%s,%s,%s,%s,'READY')", (artifact_id, resource_id, payload, digest, worker, fence, version))
        c.commit()
    return artifact(dsn, artifact_id)


def adopt(dsn, artifact_id, resource_id, expected_digest, adopter, adopter_fence, adopter_version, now):
    # Adoption is one CAS-style transaction: verify current owner epoch and exact immutable artifact digest,
    # then move READY -> ADOPTED under that same current epoch.
    with db(dsn) as c:
        with c.cursor() as cur:
            cur.execute("SELECT owner, fence, lease_version, expires_at FROM worker_leases WHERE resource_id=%s FOR UPDATE", (resource_id,))
            l = cur.fetchone()
            current = bool(l and l[0] == adopter and int(l[1]) == adopter_fence and int(l[2]) == adopter_version and int(l[3]) >= now)
            rows = 0
            if current:
                cur.execute("""
                    UPDATE result_artifacts
                       SET state='ADOPTED', adopted_by=%s, adopted_fence=%s, adopted_version=%s
                     WHERE artifact_id=%s AND resource_id=%s AND state='READY' AND artifact_digest=%s
                """, (adopter, adopter_fence, adopter_version, artifact_id, resource_id, expected_digest))
                rows = cur.rowcount
        c.commit()
    return {"updated_rows": rows, "artifact": artifact(dsn, artifact_id), "current_owner_epoch": lease(dsn, resource_id)}


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
    run("docker", "run", "-d", "--name", CONTAINER, "-p", "18088:8080", "-v", f"{VOLUME}:/state", "-v", f"{SERVICE}:/app/external_service.py:ro", IMAGE, "python", "/app/external_service.py", "--host", "0.0.0.0", "--port", "8080")
    for _ in range(40):
        try:
            h = req_json("GET", "/health")
            if h["http_status"] == 200:
                return h["payload"]
        except Exception:
            pass
        time.sleep(0.25)
    raise RuntimeError("service not healthy")


def publish(resource_id, worker, fence, artifact_digest, phase, enforce):
    return req_json("POST", "/effects", {
        "X-Resource-Id": resource_id,
        "X-Worker": worker,
        "X-Fencing-Token": str(fence),
        "X-Artifact-Digest": artifact_digest,
        "X-Phase": phase,
        "X-Enforce-Fence": "1" if enforce else "0",
    })


def remote(resource_id):
    return req_json("GET", f"/status/{resource_id}")["payload"]


def unsafe_implicit_publish(dsn):
    rid = "unsafe-handoff-resource"
    aid = "artifact-unsafe"
    reset(dsn, rid)
    a = acquire(dsn, rid, "worker-A", T0)
    start = authorize(dsn, rid, "worker-A", a["fence"], a["lease_version"], START_TIME)
    b = takeover(dsn, rid, "worker-B", TAKEOVER_TIME)
    art = produce(dsn, aid, rid, "computed-result-v1", "worker-A", a["fence"], a["lease_version"])
    stale_auto = publish(rid, "worker-A", a["fence"], art["artifact_digest"], "stale-auto-publish", False)
    adoption = adopt(dsn, aid, rid, art["artifact_digest"], "worker-B", b["fence"], b["lease_version"], FINISH_TIME)
    current_publish = publish(rid, "worker-B", b["fence"], art["artifact_digest"], "current-owner-publish", False)
    return {"resource_id": rid, "start_authorization": start, "worker_b_after_takeover": b, "artifact": art, "stale_auto_publish": stale_auto, "adoption": adoption, "current_owner_publish": current_publish, "final_remote": remote(rid)}


def safe_explicit_adoption(dsn):
    rid = "safe-handoff-resource"
    aid = "artifact-safe"
    reset(dsn, rid)
    a = acquire(dsn, rid, "worker-A", T0)
    start = authorize(dsn, rid, "worker-A", a["fence"], a["lease_version"], START_TIME)
    b = takeover(dsn, rid, "worker-B", TAKEOVER_TIME)
    art = produce(dsn, aid, rid, "computed-result-v1", "worker-A", a["fence"], a["lease_version"])
    before = remote(rid)
    adoption = adopt(dsn, aid, rid, art["artifact_digest"], "worker-B", b["fence"], b["lease_version"], FINISH_TIME)
    b_publish = publish(rid, "worker-B", b["fence"], art["artifact_digest"], "adopted-result-commit", True)
    stale_a_attempt = publish(rid, "worker-A", a["fence"], art["artifact_digest"], "stale-producer-commit", True)
    return {"resource_id": rid, "start_authorization": start, "worker_b_after_takeover": b, "artifact_before_adoption": art, "remote_before_adoption": before, "adoption": adoption, "current_owner_publish": b_publish, "stale_producer_attempt": stale_a_attempt, "final_remote": remote(rid)}


def digest_mismatch_rejected(dsn):
    rid = "digest-mismatch-resource"
    aid = "artifact-digest-mismatch"
    reset(dsn, rid)
    a = acquire(dsn, rid, "worker-A", T0)
    b = takeover(dsn, rid, "worker-B", TAKEOVER_TIME)
    art = produce(dsn, aid, rid, "computed-result-v1", "worker-A", a["fence"], a["lease_version"])
    bad = adopt(dsn, aid, rid, "0" * 64, "worker-B", b["fence"], b["lease_version"], FINISH_TIME)
    return {"artifact": art, "adoption_with_wrong_digest": bad, "final_remote": remote(rid)}


def valid_current_control(dsn):
    rid = "valid-handoff-control"
    aid = "artifact-control"
    reset(dsn, rid)
    a = acquire(dsn, rid, "worker-A", T0)
    start = authorize(dsn, rid, "worker-A", a["fence"], a["lease_version"], START_TIME)
    art = produce(dsn, aid, rid, "computed-result-current", "worker-A", a["fence"], a["lease_version"])
    self_adopt = adopt(dsn, aid, rid, art["artifact_digest"], "worker-A", a["fence"], a["lease_version"], CONTROL_FINISH)
    write = publish(rid, "worker-A", a["fence"], art["artifact_digest"], "current-owner-result-commit", True)
    return {"start_authorization": start, "artifact": art, "adoption": self_adopt, "write": write, "final_remote": remote(rid)}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dsn", default=os.environ.get("DATABASE_URL", "postgresql://resonance:resonance@127.0.0.1:5432/resonance"))
    p.add_argument("--out", default="benchmark-results/result-handoff-v1.0")
    args = p.parse_args()
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    init_schema(args.dsn)
    health = start_service()
    try:
        unsafe = unsafe_implicit_publish(args.dsn)
        safe = safe_explicit_adoption(args.dsn)
        mismatch = digest_mismatch_rejected(args.dsn)
        control = valid_current_control(args.dsn)
        with db(args.dsn) as c:
            with c.cursor() as cur:
                cur.execute("SHOW server_version")
                pg = str(cur.fetchone()[0])
            c.commit()
        image_digest = run("docker", "image", "inspect", IMAGE, "--format", "{{index .RepoDigests 0}}").stdout.strip()
        checks = [
            {"id": "stale_worker_was_legitimately_authorized_at_start_and_artifact_survived_takeover", "points": 2, "pass": unsafe["start_authorization"]["authorized"] and unsafe["worker_b_after_takeover"]["fence"] == 2 and unsafe["artifact"]["producer_fence"] == 1 and unsafe["artifact"]["state"] == "READY", "evidence": {"start": unsafe["start_authorization"], "takeover": unsafe["worker_b_after_takeover"], "artifact": unsafe["artifact"]}},
            {"id": "implicit_stale_publish_plus_current_owner_publish_duplicates_consequence", "points": 2, "pass": unsafe["stale_auto_publish"]["http_status"] == 200 and unsafe["current_owner_publish"]["http_status"] == 200 and unsafe["final_remote"]["effect_count"] == 2 and unsafe["final_remote"]["effects"][0]["artifact_digest"] == unsafe["final_remote"]["effects"][1]["artifact_digest"], "evidence": unsafe},
            {"id": "explicit_current_owner_adoption_binds_same_digest_and_current_epoch", "points": 2, "pass": safe["remote_before_adoption"]["effect_count"] == 0 and safe["adoption"]["updated_rows"] == 1 and safe["adoption"]["artifact"]["state"] == "ADOPTED" and safe["adoption"]["artifact"]["adopted_by"] == "worker-B" and safe["adoption"]["artifact"]["adopted_fence"] == 2 and safe["adoption"]["artifact"]["artifact_digest"] == safe["artifact_before_adoption"]["artifact_digest"], "evidence": safe},
            {"id": "only_current_owner_commit_survives_and_stale_producer_is_fenced", "points": 2, "pass": safe["current_owner_publish"]["http_status"] == 200 and safe["stale_producer_attempt"]["http_status"] == 409 and safe["stale_producer_attempt"]["payload"].get("delivery") == "fenced_out" and safe["final_remote"]["effect_count"] == 1 and safe["final_remote"]["effects"][0]["worker"] == "worker-B", "evidence": safe},
            {"id": "digest_mismatch_is_not_adopted_and_current_owner_control_still_commits", "points": 2, "pass": mismatch["adoption_with_wrong_digest"]["updated_rows"] == 0 and mismatch["adoption_with_wrong_digest"]["artifact"]["state"] == "READY" and mismatch["final_remote"]["effect_count"] == 0 and control["adoption"]["updated_rows"] == 1 and control["write"]["http_status"] == 200 and control["final_remote"]["effect_count"] == 1, "evidence": {"mismatch": mismatch, "control": control}},
        ]
        score = sum(x["points"] for x in checks if x["pass"])
        result = {
            "benchmark": "RESONANCE Result Handoff / Stale Work Salvage",
            "benchmark_version": "1.0",
            "executed_at": datetime.now(timezone.utc).isoformat(),
            "protocol": "RESONANCE Transactional Trust Protocol v1.0",
            "database": {"server_version": pg},
            "lease_model": {"ttl_seconds": LEASE_TTL, "start_time": START_TIME, "takeover_time": TAKEOVER_TIME, "finish_time": FINISH_TIME},
            "http_service": health,
            "http_service_image": IMAGE,
            "http_service_image_digest": image_digest,
            "unsafe_implicit_publish": unsafe,
            "safe_explicit_adoption": safe,
            "digest_mismatch": mismatch,
            "valid_current_control": control,
            "checks": checks,
            "score": score,
            "max_score": 10,
            "classification": "Result-handoff adoption protocol passes" if score == 10 else "Protocol incomplete",
            "invariants": [
                "STALE EXECUTOR MAY PRODUCE DATA; ONLY CURRENT AUTHORITY MAY ADOPT THE CONSEQUENCE.",
                "RESULT ADOPTION MUST BIND THE EXACT ARTIFACT DIGEST AND PRODUCER EPOCH TO THE CURRENT OWNER EPOCH.",
                "READY ARTIFACT IS DATA, NOT COMMIT AUTHORITY.",
                "THE CONSEQUENTIAL COMMIT MUST PRESENT THE ADOPTER'S CURRENT FENCING TOKEN, NOT THE PRODUCER'S STALE TOKEN.",
            ],
            "vulnerability_claim": False,
            "external_safety_certification": False,
        }
        (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True))
        (out / "RESULT.md").write_text(f"# RESONANCE Result Handoff / Stale Work Salvage\n\nScore: **{score}/10**\n\nUnsafe effects: **{unsafe['final_remote']['effect_count']}**  \nSafe effects: **{safe['final_remote']['effect_count']}**  \nStale producer final attempt: **HTTP {safe['stale_producer_attempt']['http_status']} / {safe['stale_producer_attempt']['payload'].get('delivery')}**\n")
        print(json.dumps(result, indent=2, sort_keys=True))
        if score != 10:
            raise SystemExit(1)
    finally:
        run("docker", "rm", "-f", CONTAINER, check=False)


if __name__ == "__main__":
    main()
