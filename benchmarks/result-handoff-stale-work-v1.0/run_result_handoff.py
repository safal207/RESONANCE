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
SERVICE = Path("benchmarks/result-handoff-stale-work-v1.0/external_service.py").resolve()
LEASE_TTL = 60
T0 = 1_000
START_TIME = 1_020
TAKEOVER_TIME = 1_070
FINISH_TIME = 1_080
ADOPTION_TIME = 1_085
CONTROL_FINISH = 1_050


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
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS result_artifacts(
                  resource_id text NOT NULL,
                  artifact_digest text NOT NULL,
                  payload text NOT NULL,
                  producer_worker text NOT NULL,
                  producer_fence bigint NOT NULL,
                  producer_lease_version bigint NOT NULL,
                  produced_at bigint NOT NULL,
                  status text NOT NULL,
                  adopted_by text,
                  adopted_fence bigint,
                  adopted_lease_version bigint,
                  adoption_id text,
                  adoption_version bigint NOT NULL DEFAULT 0,
                  PRIMARY KEY(resource_id, artifact_digest)
                )
                """
            )
        c.commit()


def reset_resource(dsn, resource_id):
    with db(dsn) as c:
        with c.cursor() as cur:
            cur.execute("DELETE FROM result_artifacts WHERE resource_id=%s", (resource_id,))
            cur.execute("DELETE FROM worker_leases WHERE resource_id=%s", (resource_id,))
        c.commit()


def lease_snapshot(dsn, resource_id):
    with db(dsn) as c:
        with c.cursor() as cur:
            cur.execute("SELECT owner, fence, lease_version, expires_at FROM worker_leases WHERE resource_id=%s", (resource_id,))
            row = cur.fetchone()
        c.commit()
    if row is None:
        return None
    return {"owner": str(row[0]), "fence": int(row[1]), "lease_version": int(row[2]), "expires_at": int(row[3])}


def artifact_snapshot(dsn, resource_id, digest):
    with db(dsn) as c:
        with c.cursor() as cur:
            cur.execute(
                "SELECT artifact_digest, payload, producer_worker, producer_fence, producer_lease_version, produced_at, status, "
                "adopted_by, adopted_fence, adopted_lease_version, adoption_id, adoption_version "
                "FROM result_artifacts WHERE resource_id=%s AND artifact_digest=%s",
                (resource_id, digest),
            )
            row = cur.fetchone()
        c.commit()
    if row is None:
        return None
    return {
        "artifact_digest": str(row[0]), "payload": str(row[1]), "producer_worker": str(row[2]),
        "producer_fence": int(row[3]), "producer_lease_version": int(row[4]), "produced_at": int(row[5]),
        "status": str(row[6]), "adopted_by": row[7], "adopted_fence": int(row[8]) if row[8] is not None else None,
        "adopted_lease_version": int(row[9]) if row[9] is not None else None, "adoption_id": row[10],
        "adoption_version": int(row[11]),
    }


def acquire_initial(dsn, resource_id, worker, now):
    with db(dsn) as c:
        with c.cursor() as cur:
            cur.execute(
                "INSERT INTO worker_leases(resource_id, owner, fence, lease_version, expires_at) VALUES (%s,%s,1,1,%s)",
                (resource_id, worker, now + LEASE_TTL),
            )
        c.commit()
    return lease_snapshot(dsn, resource_id)


def takeover_if_expired(dsn, resource_id, worker, now):
    with db(dsn) as c:
        with c.cursor() as cur:
            cur.execute("SELECT owner, fence, lease_version, expires_at FROM worker_leases WHERE resource_id=%s FOR UPDATE", (resource_id,))
            row = cur.fetchone()
            if row is None or now <= int(row[3]):
                raise RuntimeError("lease missing or not expired")
            cur.execute(
                "UPDATE worker_leases SET owner=%s, fence=%s, lease_version=%s, expires_at=%s WHERE resource_id=%s",
                (worker, int(row[1]) + 1, int(row[2]) + 1, now + LEASE_TTL, resource_id),
            )
        c.commit()
    return lease_snapshot(dsn, resource_id)


def authorize(dsn, resource_id, worker, expected_fence, expected_version, now):
    observed = lease_snapshot(dsn, resource_id)
    allowed = bool(
        observed and observed["owner"] == worker and observed["fence"] == expected_fence
        and observed["lease_version"] == expected_version and observed["expires_at"] >= now
    )
    return {"authorized": allowed, "decision_time": now, "expected_fence": expected_fence, "expected_version": expected_version, "observed": observed}


def digest_for(resource_id, payload):
    return "sha256:" + hashlib.sha256((resource_id + "\n" + payload).encode()).hexdigest()


def produce_artifact(dsn, resource_id, payload, producer, producer_fence, producer_version, now):
    digest = digest_for(resource_id, payload)
    with db(dsn) as c:
        with c.cursor() as cur:
            cur.execute(
                "INSERT INTO result_artifacts(resource_id, artifact_digest, payload, producer_worker, producer_fence, producer_lease_version, produced_at, status) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s,'PRODUCED')",
                (resource_id, digest, payload, producer, producer_fence, producer_version, now),
            )
        c.commit()
    return artifact_snapshot(dsn, resource_id, digest)


def adopt_artifact(dsn, resource_id, digest, producer, producer_fence, adopter, adopter_fence, adopter_version, now):
    adoption_id = f"{resource_id}:adopt:{adopter}:f{adopter_fence}:{digest[-12:]}"
    with db(dsn) as c:
        with c.cursor() as cur:
            cur.execute(
                """
                UPDATE result_artifacts ra
                   SET status='ADOPTED', adopted_by=%s, adopted_fence=%s, adopted_lease_version=%s,
                       adoption_id=%s, adoption_version=adoption_version+1
                 WHERE ra.resource_id=%s
                   AND ra.artifact_digest=%s
                   AND ra.status='PRODUCED'
                   AND ra.producer_worker=%s
                   AND ra.producer_fence=%s
                   AND EXISTS (
                       SELECT 1 FROM worker_leases wl
                        WHERE wl.resource_id=ra.resource_id
                          AND wl.owner=%s
                          AND wl.fence=%s
                          AND wl.lease_version=%s
                          AND wl.expires_at >= %s
                   )
                """,
                (adopter, adopter_fence, adopter_version, adoption_id, resource_id, digest, producer, producer_fence,
                 adopter, adopter_fence, adopter_version, now),
            )
            rows = cur.rowcount
        c.commit()
    return {"updated_rows": rows, "adoption_id": adoption_id if rows == 1 else None, "artifact": artifact_snapshot(dsn, resource_id, digest)}


def run(*args, check=True):
    return subprocess.run(args, text=True, capture_output=True, check=check)


def req_json(method, path, headers=None):
    r = urllib.request.Request(BASE_URL + path, method=method, data=b"{}" if method == "POST" else None,
                               headers={"Content-Type": "application/json", **(headers or {})})
    try:
        with urllib.request.urlopen(r, timeout=5) as resp:
            return {"http_status": resp.status, "payload": json.loads(resp.read().decode())}
    except urllib.error.HTTPError as exc:
        return {"http_status": exc.code, "payload": json.loads(exc.read().decode())}


def start_service():
    run("docker", "rm", "-f", CONTAINER, check=False)
    run("docker", "volume", "rm", "-f", VOLUME, check=False)
    run("docker", "volume", "create", VOLUME)
    run("docker", "run", "-d", "--name", CONTAINER, "-p", "18088:8080",
        "-e", "STATE_DB=/state/resource.db", "-v", f"{VOLUME}:/state", "-v", f"{SERVICE}:/app/external_service.py:ro",
        IMAGE, "python", "/app/external_service.py", "--host", "0.0.0.0", "--port", "8080")
    for _ in range(40):
        try:
            h = req_json("GET", "/health")
            if h["http_status"] == 200:
                return h["payload"]
        except Exception:
            pass
        time.sleep(0.25)
    raise RuntimeError("external service not healthy")


def post_effect(resource_id, worker, fence, digest, producer, producer_fence, adoption_id, phase, enforce):
    return req_json("POST", "/effects", {
        "X-Resource-Id": resource_id,
        "X-Worker": worker,
        "X-Fencing-Token": str(fence),
        "X-Artifact-Digest": digest,
        "X-Producer-Worker": producer,
        "X-Producer-Fence": str(producer_fence),
        "X-Adoption-Id": adoption_id or "",
        "X-Phase": phase,
        "X-Enforce-Fence": "1" if enforce else "0",
    })


def remote_status(resource_id):
    return req_json("GET", f"/status/{resource_id}")["payload"]


def prepare_stale_result(dsn, rid):
    reset_resource(dsn, rid)
    a = acquire_initial(dsn, rid, "worker-A", T0)
    start = authorize(dsn, rid, "worker-A", a["fence"], a["lease_version"], START_TIME)
    b = takeover_if_expired(dsn, rid, "worker-B", TAKEOVER_TIME)
    artifact = produce_artifact(dsn, rid, "calculation-output-v1", "worker-A", a["fence"], a["lease_version"], FINISH_TIME)
    return a, start, b, artifact


def unsafe_auto_publish_then_adopt(dsn):
    rid = "unsafe-result-handoff"
    a, start, b, artifact = prepare_stale_result(dsn, rid)
    stale_publish = post_effect(rid, "worker-A", a["fence"], artifact["artifact_digest"], "worker-A", a["fence"], None,
                                "stale-auto-publish", False)
    adoption = adopt_artifact(dsn, rid, artifact["artifact_digest"], "worker-A", a["fence"], "worker-B", b["fence"], b["lease_version"], ADOPTION_TIME)
    b_publish = post_effect(rid, "worker-B", b["fence"], artifact["artifact_digest"], "worker-A", a["fence"], adoption["adoption_id"],
                            "current-owner-adopted-commit", True)
    return {"resource_id": rid, "worker_a_initial": a, "start_authorization": start, "worker_b_after_takeover": b,
            "artifact": artifact, "stale_auto_publish": stale_publish, "adoption": adoption, "worker_b_publish": b_publish,
            "final_remote": remote_status(rid)}


def safe_handoff(dsn):
    rid = "safe-result-handoff"
    a, start, b, artifact = prepare_stale_result(dsn, rid)
    before = remote_status(rid)
    adoption = adopt_artifact(dsn, rid, artifact["artifact_digest"], "worker-A", a["fence"], "worker-B", b["fence"], b["lease_version"], ADOPTION_TIME)
    b_publish = post_effect(rid, "worker-B", b["fence"], artifact["artifact_digest"], "worker-A", a["fence"], adoption["adoption_id"],
                            "adopted-result-commit", True)
    stale_attempt = post_effect(rid, "worker-A", a["fence"], artifact["artifact_digest"], "worker-A", a["fence"], None,
                                "stale-producer-late-publish", True)
    return {"resource_id": rid, "worker_a_initial": a, "start_authorization": start, "worker_b_after_takeover": b,
            "artifact_before_adoption": artifact, "remote_before_adoption": before, "adoption": adoption,
            "worker_b_publish": b_publish, "stale_producer_attempt": stale_attempt,
            "final_artifact": artifact_snapshot(dsn, rid, artifact["artifact_digest"]), "final_remote": remote_status(rid)}


def tampered_digest_rejected(dsn):
    rid = "tampered-result-handoff"
    a, start, b, artifact = prepare_stale_result(dsn, rid)
    fake_digest = artifact["artifact_digest"][:-1] + ("0" if artifact["artifact_digest"][-1] != "0" else "1")
    bad = adopt_artifact(dsn, rid, fake_digest, "worker-A", a["fence"], "worker-B", b["fence"], b["lease_version"], ADOPTION_TIME)
    good = adopt_artifact(dsn, rid, artifact["artifact_digest"], "worker-A", a["fence"], "worker-B", b["fence"], b["lease_version"], ADOPTION_TIME)
    publish = post_effect(rid, "worker-B", b["fence"], artifact["artifact_digest"], "worker-A", a["fence"], good["adoption_id"],
                          "exact-digest-adopted-commit", True)
    return {"resource_id": rid, "artifact": artifact, "fake_digest": fake_digest, "bad_adoption": bad, "good_adoption": good,
            "worker_b_publish": publish, "final_remote": remote_status(rid)}


def valid_current_owner_control(dsn):
    rid = "valid-result-control"
    reset_resource(dsn, rid)
    a = acquire_initial(dsn, rid, "worker-A", T0)
    start = authorize(dsn, rid, "worker-A", a["fence"], a["lease_version"], START_TIME)
    artifact = produce_artifact(dsn, rid, "calculation-output-v1", "worker-A", a["fence"], a["lease_version"], CONTROL_FINISH)
    adoption = adopt_artifact(dsn, rid, artifact["artifact_digest"], "worker-A", a["fence"], "worker-A", a["fence"], a["lease_version"], CONTROL_FINISH)
    publish = post_effect(rid, "worker-A", a["fence"], artifact["artifact_digest"], "worker-A", a["fence"], adoption["adoption_id"],
                          "valid-self-adopted-commit", True)
    return {"resource_id": rid, "start_authorization": start, "artifact": artifact, "adoption": adoption,
            "publish": publish, "final_remote": remote_status(rid)}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dsn", default=os.environ.get("DATABASE_URL", "postgresql://resonance:resonance@127.0.0.1:5432/resonance"))
    p.add_argument("--out", default="benchmark-results/result-handoff-stale-work-v1.0")
    args = p.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    init_schema(args.dsn)
    health = start_service()
    try:
        unsafe = unsafe_auto_publish_then_adopt(args.dsn)
        safe = safe_handoff(args.dsn)
        tamper = tampered_digest_rejected(args.dsn)
        control = valid_current_owner_control(args.dsn)
        with db(args.dsn) as c:
            with c.cursor() as cur:
                cur.execute("SHOW server_version")
                pg = str(cur.fetchone()[0])
            c.commit()
        digest = run("docker", "image", "inspect", IMAGE, "--format", "{{index .RepoDigests 0}}").stdout.strip()

        checks = [
            {"id": "stale_worker_result_is_preserved_as_immutable_data_with_producer_epoch", "points": 2,
             "pass": safe["start_authorization"]["authorized"] and safe["worker_b_after_takeover"]["fence"] > safe["worker_a_initial"]["fence"]
                     and safe["artifact_before_adoption"]["status"] == "PRODUCED"
                     and safe["artifact_before_adoption"]["producer_fence"] == safe["worker_a_initial"]["fence"]
                     and safe["remote_before_adoption"]["effect_count"] == 0,
             "evidence": {"start": safe["start_authorization"], "takeover": safe["worker_b_after_takeover"], "artifact": safe["artifact_before_adoption"]}},
            {"id": "stale_auto_publish_then_current_owner_adoption_duplicates_same_artifact", "points": 2,
             "pass": unsafe["stale_auto_publish"]["http_status"] == 200 and unsafe["adoption"]["updated_rows"] == 1
                     and unsafe["worker_b_publish"]["http_status"] == 200 and unsafe["final_remote"]["effect_count"] == 2
                     and len({e["artifact_digest"] for e in unsafe["final_remote"]["effects"]}) == 1,
             "evidence": unsafe},
            {"id": "current_owner_explicit_adoption_commits_stale_result_once", "points": 2,
             "pass": safe["adoption"]["updated_rows"] == 1 and safe["final_artifact"]["status"] == "ADOPTED"
                     and safe["final_artifact"]["adopted_by"] == "worker-B" and safe["final_artifact"]["adopted_fence"] == safe["worker_b_after_takeover"]["fence"]
                     and safe["worker_b_publish"]["http_status"] == 200 and safe["final_remote"]["effect_count"] == 1,
             "evidence": safe},
            {"id": "digest_binding_and_resource_fence_block_wrong_or_stale_adoption_paths", "points": 2,
             "pass": tamper["bad_adoption"]["updated_rows"] == 0 and tamper["good_adoption"]["updated_rows"] == 1
                     and tamper["final_remote"]["effect_count"] == 1
                     and safe["stale_producer_attempt"]["http_status"] == 409
                     and safe["stale_producer_attempt"]["payload"].get("delivery") == "fenced_out",
             "evidence": {"tamper": tamper, "stale_attempt": safe["stale_producer_attempt"]}},
            {"id": "current_owner_can_adopt_its_own_valid_result_and_commit", "points": 2,
             "pass": control["start_authorization"]["authorized"] and control["adoption"]["updated_rows"] == 1
                     and control["publish"]["http_status"] == 200 and control["final_remote"]["effect_count"] == 1,
             "evidence": control},
        ]
        score = sum(x["points"] for x in checks if x["pass"])
        result = {
            "benchmark": "RESONANCE Result Handoff / Stale Work Salvage",
            "benchmark_version": "1.0",
            "executed_at": datetime.now(timezone.utc).isoformat(),
            "protocol": "RESONANCE Transactional Trust Protocol v1.0",
            "database": {"server_version": pg},
            "lease_model": {"ttl_seconds": LEASE_TTL, "initial_time": T0, "start_time": START_TIME, "takeover_time": TAKEOVER_TIME, "finish_time": FINISH_TIME, "adoption_time": ADOPTION_TIME},
            "http_service": health,
            "http_service_image": IMAGE,
            "http_service_image_digest": digest,
            "unsafe_auto_publish": unsafe,
            "safe_handoff": safe,
            "tampered_digest": tamper,
            "valid_current_owner_control": control,
            "checks": checks,
            "score": score,
            "max_score": 10,
            "classification": "Stale-work handoff protocol passes" if score == 10 else "Protocol incomplete",
            "invariants": [
                "STALE EXECUTOR MAY PRODUCE DATA; ONLY CURRENT AUTHORITY MAY ADOPT THE CONSEQUENCE.",
                "RESULT HANDOFF MUST BIND ARTIFACT DIGEST + PRODUCER EPOCH + CURRENT ADOPTER EPOCH.",
                "ADOPTION IS A NEW AUTHORITY TRANSITION, NOT A RETROACTIVE EXTENSION OF PRODUCER AUTHORITY.",
                "THE CONSEQUENTIAL COMMIT MUST PRESENT THE CURRENT ADOPTER FENCING TOKEN."
            ],
            "vulnerability_claim": False,
            "external_safety_certification": False,
        }
        (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        lines = ["# RESONANCE Result Handoff / Stale Work Salvage", "", f"Score: **{score}/10**", ""]
        for x in checks:
            lines.append(f"- {'PASS' if x['pass'] else 'FAIL'} — {x['id']} ({x['points']} pts)")
        lines += ["", "## Core result", "", "STALE EXECUTOR MAY PRODUCE DATA; ONLY CURRENT AUTHORITY MAY ADOPT THE CONSEQUENCE.", ""]
        (out / "RESULT.md").write_text("\n".join(lines))
        print(json.dumps(result, indent=2, sort_keys=True))
        if score != 10:
            raise SystemExit(1)
    finally:
        run("docker", "rm", "-f", CONTAINER, check=False)


if __name__ == "__main__":
    main()
