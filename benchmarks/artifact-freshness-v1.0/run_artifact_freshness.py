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

CONTAINER = "resonance-external-artifact-freshness"
VOLUME = "resonance-artifact-freshness-v1"
IMAGE = os.environ.get("HTTP_SERVICE_IMAGE", "python:3.12-slim")
BASE_URL = os.environ.get("EXTERNAL_BASE_URL", "http://127.0.0.1:18089")
SERVICE = Path("benchmarks/artifact-freshness-v1.0/external_service.py").resolve()
LEASE_TTL = 60
T0 = 1000
START_TIME = 1020
STATE_ADVANCE_TIME = 1065
TAKEOVER_TIME = 1070
FINISH_TIME = 1080
ADOPTION_TIME = 1085


def db(dsn):
    return psycopg.connect(dsn, autocommit=False)


def canonical_snapshot(version: int, value: int) -> str:
    return json.dumps({"value": value, "version": version}, sort_keys=True, separators=(",", ":"))


def sha256_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode()).hexdigest()


def snapshot_digest(version: int, value: int) -> str:
    return sha256_text(canonical_snapshot(version, value))


def artifact_payload(input_version: int, input_digest: str, output_value: int) -> str:
    return json.dumps({"input_snapshot_digest": input_digest, "input_state_version": input_version, "output_value": output_value}, sort_keys=True, separators=(",", ":"))


def init_schema(dsn):
    with db(dsn) as c:
        with c.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS freshness_state(
                  resource_id text PRIMARY KEY,
                  state_version bigint NOT NULL,
                  state_value bigint NOT NULL
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS freshness_leases(
                  resource_id text PRIMARY KEY,
                  owner text NOT NULL,
                  fence bigint NOT NULL,
                  lease_version bigint NOT NULL,
                  expires_at bigint NOT NULL
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS freshness_artifacts(
                  artifact_id text PRIMARY KEY,
                  resource_id text NOT NULL,
                  payload text NOT NULL,
                  artifact_digest text NOT NULL,
                  input_state_version bigint NOT NULL,
                  input_snapshot_digest text NOT NULL,
                  output_value bigint NOT NULL,
                  producer text NOT NULL,
                  producer_fence bigint NOT NULL,
                  producer_lease_version bigint NOT NULL,
                  produced_at bigint NOT NULL,
                  state text NOT NULL,
                  adopted_by text,
                  adopted_fence bigint,
                  adopted_lease_version bigint
                )
            """)
        c.commit()


def reset(dsn, resource_id):
    with db(dsn) as c:
        with c.cursor() as cur:
            cur.execute("DELETE FROM freshness_artifacts WHERE resource_id=%s", (resource_id,))
            cur.execute("DELETE FROM freshness_leases WHERE resource_id=%s", (resource_id,))
            cur.execute("DELETE FROM freshness_state WHERE resource_id=%s", (resource_id,))
        c.commit()


def set_state(dsn, resource_id, version, value):
    with db(dsn) as c:
        with c.cursor() as cur:
            cur.execute("INSERT INTO freshness_state(resource_id, state_version, state_value) VALUES (%s,%s,%s) ON CONFLICT(resource_id) DO UPDATE SET state_version=EXCLUDED.state_version, state_value=EXCLUDED.state_value", (resource_id, version, value))
        c.commit()
    return get_state(dsn, resource_id)


def get_state(dsn, resource_id):
    with db(dsn) as c:
        with c.cursor() as cur:
            cur.execute("SELECT state_version, state_value FROM freshness_state WHERE resource_id=%s", (resource_id,))
            row = cur.fetchone()
        c.commit()
    if row is None:
        return None
    version, value = int(row[0]), int(row[1])
    return {"version": version, "value": value, "snapshot_digest": snapshot_digest(version, value), "expected_output": value * 2}


def get_lease(dsn, resource_id):
    with db(dsn) as c:
        with c.cursor() as cur:
            cur.execute("SELECT owner, fence, lease_version, expires_at FROM freshness_leases WHERE resource_id=%s", (resource_id,))
            row = cur.fetchone()
        c.commit()
    return None if row is None else {"owner": row[0], "fence": int(row[1]), "lease_version": int(row[2]), "expires_at": int(row[3])}


def acquire(dsn, resource_id, worker, now):
    with db(dsn) as c:
        with c.cursor() as cur:
            cur.execute("INSERT INTO freshness_leases(resource_id, owner, fence, lease_version, expires_at) VALUES (%s,%s,1,1,%s)", (resource_id, worker, now + LEASE_TTL))
        c.commit()
    return get_lease(dsn, resource_id)


def takeover(dsn, resource_id, worker, now):
    with db(dsn) as c:
        with c.cursor() as cur:
            cur.execute("SELECT owner, fence, lease_version, expires_at FROM freshness_leases WHERE resource_id=%s FOR UPDATE", (resource_id,))
            row = cur.fetchone()
            if row is None or now <= int(row[3]):
                raise RuntimeError("lease not expired")
            cur.execute("UPDATE freshness_leases SET owner=%s, fence=%s, lease_version=%s, expires_at=%s WHERE resource_id=%s", (worker, int(row[1]) + 1, int(row[2]) + 1, now + LEASE_TTL, resource_id))
        c.commit()
    return get_lease(dsn, resource_id)


def authorize(dsn, resource_id, worker, fence, lease_version, now):
    l = get_lease(dsn, resource_id)
    ok = bool(l and l["owner"] == worker and l["fence"] == fence and l["lease_version"] == lease_version and l["expires_at"] >= now)
    return {"authorized": ok, "decision_time": now, "observed": l, "expected_fence": fence, "expected_lease_version": lease_version}


def get_artifact(dsn, artifact_id):
    with db(dsn) as c:
        with c.cursor() as cur:
            cur.execute("SELECT artifact_id, resource_id, payload, artifact_digest, input_state_version, input_snapshot_digest, output_value, producer, producer_fence, producer_lease_version, produced_at, state, adopted_by, adopted_fence, adopted_lease_version FROM freshness_artifacts WHERE artifact_id=%s", (artifact_id,))
            row = cur.fetchone()
        c.commit()
    if row is None:
        return None
    keys = ["artifact_id", "resource_id", "payload", "artifact_digest", "input_state_version", "input_snapshot_digest", "output_value", "producer", "producer_fence", "producer_lease_version", "produced_at", "state", "adopted_by", "adopted_fence", "adopted_lease_version"]
    out = dict(zip(keys, row))
    for k in ("input_state_version", "output_value", "producer_fence", "producer_lease_version", "produced_at", "adopted_fence", "adopted_lease_version"):
        if out[k] is not None:
            out[k] = int(out[k])
    out["integrity_valid"] = sha256_text(out["payload"]) == out["artifact_digest"]
    return out


def produce_from_snapshot(dsn, artifact_id, resource_id, snapshot, worker, fence, lease_version, produced_at):
    output = int(snapshot["value"]) * 2
    payload = artifact_payload(int(snapshot["version"]), snapshot["snapshot_digest"], output)
    digest = sha256_text(payload)
    with db(dsn) as c:
        with c.cursor() as cur:
            cur.execute("""
                INSERT INTO freshness_artifacts(
                  artifact_id, resource_id, payload, artifact_digest,
                  input_state_version, input_snapshot_digest, output_value,
                  producer, producer_fence, producer_lease_version, produced_at, state
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'READY')
            """, (artifact_id, resource_id, payload, digest, snapshot["version"], snapshot["snapshot_digest"], output, worker, fence, lease_version, produced_at))
        c.commit()
    return get_artifact(dsn, artifact_id)


def adopt(dsn, artifact_id, resource_id, adopter, fence, lease_version, now, enforce_applicability):
    with db(dsn) as c:
        with c.cursor() as cur:
            cur.execute("SELECT owner, fence, lease_version, expires_at FROM freshness_leases WHERE resource_id=%s FOR UPDATE", (resource_id,))
            l = cur.fetchone()
            current_owner = bool(l and l[0] == adopter and int(l[1]) == fence and int(l[2]) == lease_version and int(l[3]) >= now)
            cur.execute("SELECT state_version, state_value FROM freshness_state WHERE resource_id=%s FOR UPDATE", (resource_id,))
            s = cur.fetchone()
            current_state = None if s is None else {"version": int(s[0]), "value": int(s[1]), "snapshot_digest": snapshot_digest(int(s[0]), int(s[1]))}
            rows = 0
            reason = "not_current_owner"
            if current_owner:
                reason = "artifact_mismatch"
                if enforce_applicability:
                    cur.execute("""
                        UPDATE freshness_artifacts
                           SET state='ADOPTED', adopted_by=%s, adopted_fence=%s, adopted_lease_version=%s
                         WHERE artifact_id=%s AND resource_id=%s AND state='READY'
                           AND input_state_version=%s AND input_snapshot_digest=%s
                    """, (adopter, fence, lease_version, artifact_id, resource_id, current_state["version"], current_state["snapshot_digest"]))
                else:
                    cur.execute("""
                        UPDATE freshness_artifacts
                           SET state='ADOPTED', adopted_by=%s, adopted_fence=%s, adopted_lease_version=%s
                         WHERE artifact_id=%s AND resource_id=%s AND state='READY'
                    """, (adopter, fence, lease_version, artifact_id, resource_id))
                rows = cur.rowcount
                reason = "adopted" if rows == 1 else "applicability_conflict"
        c.commit()
    return {"updated_rows": rows, "reason": reason, "artifact": get_artifact(dsn, artifact_id), "current_state": get_state(dsn, resource_id), "current_lease": get_lease(dsn, resource_id), "applicability_enforced": enforce_applicability}


def run(*args, check=True):
    return subprocess.run(args, text=True, capture_output=True, check=check)


def req_json(method, path, headers=None):
    request = urllib.request.Request(BASE_URL + path, method=method, data=b"{}" if method == "POST" else None, headers={"Content-Type": "application/json", **(headers or {})})
    try:
        with urllib.request.urlopen(request, timeout=5) as resp:
            return {"http_status": resp.status, "payload": json.loads(resp.read().decode())}
    except urllib.error.HTTPError as exc:
        return {"http_status": exc.code, "payload": json.loads(exc.read().decode())}


def start_service():
    run("docker", "rm", "-f", CONTAINER, check=False)
    run("docker", "volume", "rm", "-f", VOLUME, check=False)
    run("docker", "volume", "create", VOLUME)
    run("docker", "run", "-d", "--name", CONTAINER, "-p", "18089:8080", "-v", f"{VOLUME}:/state", "-v", f"{SERVICE}:/app/external_service.py:ro", IMAGE, "python", "/app/external_service.py", "--host", "0.0.0.0", "--port", "8080")
    for _ in range(40):
        try:
            h = req_json("GET", "/health")
            if h["http_status"] == 200:
                return h["payload"]
        except Exception:
            pass
        time.sleep(0.25)
    raise RuntimeError("service not healthy")


def publish(resource_id, worker, fence, art, phase):
    return req_json("POST", "/effects", {
        "X-Resource-Id": resource_id,
        "X-Worker": worker,
        "X-Fencing-Token": str(fence),
        "X-Artifact-Digest": art["artifact_digest"],
        "X-Input-State-Version": str(art["input_state_version"]),
        "X-Output-Value": str(art["output_value"]),
        "X-Phase": phase,
    })


def remote(resource_id):
    return req_json("GET", f"/status/{resource_id}")["payload"]


def prepare_stale_case(dsn, rid, aid):
    reset(dsn, rid)
    s100 = set_state(dsn, rid, 100, 10)
    a = acquire(dsn, rid, "worker-A", T0)
    start = authorize(dsn, rid, "worker-A", a["fence"], a["lease_version"], START_TIME)
    captured = dict(s100)
    s101 = set_state(dsn, rid, 101, 20)
    b = takeover(dsn, rid, "worker-B", TAKEOVER_TIME)
    art = produce_from_snapshot(dsn, aid, rid, captured, "worker-A", a["fence"], a["lease_version"], FINISH_TIME)
    return {"state_v100": s100, "captured_input": captured, "start": start, "state_v101": s101, "worker_a": a, "worker_b": b, "artifact": art}


def unsafe_stale_adoption(dsn):
    rid = "unsafe-artifact-freshness"
    case = prepare_stale_case(dsn, rid, "artifact-v100-unsafe")
    adoption = adopt(dsn, case["artifact"]["artifact_id"], rid, "worker-B", case["worker_b"]["fence"], case["worker_b"]["lease_version"], ADOPTION_TIME, False)
    write = publish(rid, "worker-B", case["worker_b"]["fence"], adoption["artifact"], "blind-current-owner-adoption")
    final = remote(rid)
    return {**case, "adoption": adoption, "write": write, "final_remote": final, "current_expected_output": case["state_v101"]["expected_output"]}


def safe_reject_recompute(dsn):
    rid = "safe-artifact-freshness"
    case = prepare_stale_case(dsn, rid, "artifact-v100-safe")
    rejected = adopt(dsn, case["artifact"]["artifact_id"], rid, "worker-B", case["worker_b"]["fence"], case["worker_b"]["lease_version"], ADOPTION_TIME, True)
    before = remote(rid)
    current = get_state(dsn, rid)
    fresh = produce_from_snapshot(dsn, "artifact-v101-recomputed", rid, current, "worker-B", case["worker_b"]["fence"], case["worker_b"]["lease_version"], ADOPTION_TIME + 1)
    adopted = adopt(dsn, fresh["artifact_id"], rid, "worker-B", case["worker_b"]["fence"], case["worker_b"]["lease_version"], ADOPTION_TIME + 2, True)
    write = publish(rid, "worker-B", case["worker_b"]["fence"], adopted["artifact"], "fresh-recomputed-adoption")
    return {**case, "stale_adoption": rejected, "remote_after_reject": before, "fresh_artifact": fresh, "fresh_adoption": adopted, "write": write, "final_remote": remote(rid), "current_state": current}


def same_version_digest_guard(dsn):
    rid = "same-version-digest-guard"
    reset(dsn, rid)
    s100 = set_state(dsn, rid, 100, 10)
    a = acquire(dsn, rid, "worker-A", T0)
    art = produce_from_snapshot(dsn, "artifact-same-version", rid, s100, "worker-A", a["fence"], a["lease_version"], START_TIME)
    # Deliberately broken state-version discipline: content changes without a version increment.
    mutated = set_state(dsn, rid, 100, 11)
    adoption = adopt(dsn, art["artifact_id"], rid, "worker-A", a["fence"], a["lease_version"], START_TIME + 1, True)
    return {"original_state": s100, "mutated_same_version_state": mutated, "artifact": art, "adoption": adoption, "final_remote": remote(rid)}


def unchanged_control(dsn):
    rid = "unchanged-state-control"
    reset(dsn, rid)
    state = set_state(dsn, rid, 100, 10)
    a = acquire(dsn, rid, "worker-A", T0)
    art = produce_from_snapshot(dsn, "artifact-current-control", rid, state, "worker-A", a["fence"], a["lease_version"], START_TIME)
    adoption = adopt(dsn, art["artifact_id"], rid, "worker-A", a["fence"], a["lease_version"], START_TIME + 1, True)
    write = publish(rid, "worker-A", a["fence"], adoption["artifact"], "unchanged-current-state")
    return {"state": state, "artifact": art, "adoption": adoption, "write": write, "final_remote": remote(rid)}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dsn", default=os.environ.get("DATABASE_URL", "postgresql://resonance:resonance@127.0.0.1:5432/resonance"))
    p.add_argument("--out", default="benchmark-results/artifact-freshness-v1.0")
    args = p.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    init_schema(args.dsn)
    health = start_service()
    try:
        unsafe = unsafe_stale_adoption(args.dsn)
        safe = safe_reject_recompute(args.dsn)
        digest_guard = same_version_digest_guard(args.dsn)
        control = unchanged_control(args.dsn)
        with db(args.dsn) as c:
            with c.cursor() as cur:
                cur.execute("SHOW server_version")
                pg = str(cur.fetchone()[0])
            c.commit()
        image_digest = run("docker", "image", "inspect", IMAGE, "--format", "{{index .RepoDigests 0}}").stdout.strip()

        checks = [
            {"id": "artifact_integrity_and_provenance_remain_valid_after_state_advance", "points": 2, "pass": unsafe["start"]["authorized"] and unsafe["artifact"]["integrity_valid"] and unsafe["artifact"]["input_state_version"] == 100 and unsafe["state_v101"]["version"] == 101 and unsafe["artifact"]["producer"] == "worker-A", "evidence": {"start": unsafe["start"], "artifact": unsafe["artifact"], "current_state": unsafe["state_v101"]}},
            {"id": "blind_current_owner_adoption_commits_stale_but_valid_result", "points": 2, "pass": unsafe["adoption"]["updated_rows"] == 1 and unsafe["write"]["http_status"] == 200 and unsafe["final_remote"]["effect_count"] == 1 and unsafe["final_remote"]["effects"][0]["output_value"] == 20 and unsafe["current_expected_output"] == 40, "evidence": unsafe},
            {"id": "applicability_binding_rejects_stale_version_and_same_version_snapshot_mismatch", "points": 2, "pass": safe["stale_adoption"]["updated_rows"] == 0 and safe["remote_after_reject"]["effect_count"] == 0 and digest_guard["adoption"]["updated_rows"] == 0 and digest_guard["original_state"]["version"] == digest_guard["mutated_same_version_state"]["version"] and digest_guard["original_state"]["snapshot_digest"] != digest_guard["mutated_same_version_state"]["snapshot_digest"], "evidence": {"version_advance": safe["stale_adoption"], "same_version_digest_guard": digest_guard}},
            {"id": "recompute_on_current_state_adopts_and_commits_current_result_once", "points": 2, "pass": safe["fresh_artifact"]["input_state_version"] == 101 and safe["fresh_artifact"]["output_value"] == 40 and safe["fresh_adoption"]["updated_rows"] == 1 and safe["write"]["http_status"] == 200 and safe["final_remote"]["effect_count"] == 1 and safe["final_remote"]["effects"][0]["output_value"] == 40, "evidence": safe},
            {"id": "unchanged_current_state_control_succeeds", "points": 2, "pass": control["artifact"]["integrity_valid"] and control["adoption"]["updated_rows"] == 1 and control["write"]["http_status"] == 200 and control["final_remote"]["effect_count"] == 1 and control["final_remote"]["effects"][0]["output_value"] == control["state"]["expected_output"], "evidence": control},
        ]
        score = sum(c["points"] for c in checks if c["pass"])
        result = {
            "benchmark": "RESONANCE Artifact Freshness / Stale-but-Valid Result",
            "benchmark_version": "1.0",
            "protocol": "RESONANCE Transactional Trust Protocol v1.0",
            "executed_at": datetime.now(timezone.utc).isoformat(),
            "database": {"server_version": pg},
            "http_service": health,
            "http_service_image": IMAGE,
            "http_service_image_digest": image_digest,
            "score": score,
            "max_score": 10,
            "classification": "Artifact applicability protocol passes" if score == 10 else "Artifact applicability protocol failed",
            "invariants": [
                "INTEGRITY + PROVENANCE DOES NOT IMPLY CURRENT APPLICABILITY.",
                "RESULT ADOPTION MUST BIND THE INPUT STATE VERSION OR EQUIVALENT SNAPSHOT IDENTITY THAT JUSTIFIED COMPUTATION.",
                "STATE ADVANCE AFTER INPUT CAPTURE IS AN APPLICABILITY TRANSITION.",
                "STALE-BUT-VALID ARTIFACT REQUIRES REVALIDATION, RECOMPUTATION, OR EXPLICIT DOMAIN PROOF BEFORE CONSEQUENCE."
            ],
            "unsafe_stale_adoption": unsafe,
            "safe_reject_recompute": safe,
            "same_version_digest_guard": digest_guard,
            "unchanged_state_control": control,
            "checks": checks,
            "vulnerability_claim": False,
            "external_safety_certification": False,
        }
        (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
        lines = [
            "# RESONANCE Artifact Freshness / Stale-but-Valid Result v1.0",
            "",
            f"Score: **{score}/10**",
            "",
            f"Unsafe: integrity-valid artifact from state v100 produced output 20; current state v101 requires output 40; blind adoption committed stale output with effect_count={unsafe['final_remote']['effect_count']}.",
            f"Safe: stale adoption rows={safe['stale_adoption']['updated_rows']}; remote effects before recompute={safe['remote_after_reject']['effect_count']}; recomputed v101 output={safe['fresh_artifact']['output_value']}; final effects={safe['final_remote']['effect_count']}.",
            f"Same-version digest guard: original={digest_guard['original_state']['snapshot_digest']}, mutated={digest_guard['mutated_same_version_state']['snapshot_digest']}, adoption rows={digest_guard['adoption']['updated_rows']}.",
            "",
            "## Checks",
        ]
        for c in checks:
            lines.append(f"- {'PASS' if c['pass'] else 'FAIL'} · {c['id']} · {c['points'] if c['pass'] else 0}/{c['points']}")
        (out / "RESULT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(json.dumps(result, indent=2, sort_keys=True))
        if score != 10:
            raise SystemExit(1)
    finally:
        run("docker", "rm", "-f", CONTAINER, check=False)
        run("docker", "volume", "rm", "-f", VOLUME, check=False)


if __name__ == "__main__":
    main()
