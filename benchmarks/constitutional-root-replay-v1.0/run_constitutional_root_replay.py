from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import subprocess
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

CONTAINER = "resonance-external-constitutional-root-replay"
VOLUME = "resonance-constitutional-root-replay-v1"
IMAGE = os.environ.get("HTTP_SERVICE_IMAGE", "python:3.12-slim")
BASE = os.environ.get("EXTERNAL_BASE_URL", "http://127.0.0.1:18101")
SERVICE = Path("benchmarks/dependency-aware-applicability-v1.0/external_service.py").resolve()

AUTHORITY_NS = "resonance-proof-authority"
ROOT_NS = "resonance-constitutional-root"
HEAD_KEY = b"resonance-authority-head-demo-key-v1"
HEAD_KEY_ID = "authority-head-demo-key-v1"
ROOT_KEY = b"resonance-constitutional-root-resolution-demo-key-v1"
ROOT_KEY_ID = "constitutional-root-resolution-demo-key-v1"
WITNESS_KEYS = {
    f"W{i}": (f"resonance-root-replay-w{i}-demo-key-v1".encode(), f"root-replay-w{i}-demo-key-v1")
    for i in [22, 23, 24, 25, 26, 27]
}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def sha(value):
    return "sha256:" + hashlib.sha256(canonical(value).encode()).hexdigest()


def mac(key, payload):
    return hmac.new(key, canonical(payload).encode(), hashlib.sha256).hexdigest()


def sign(key, key_id, payload):
    return {"alg": "HMAC-SHA256", "key_id": key_id, "payload": payload, "mac": mac(key, payload)}


def authentic(record, key, key_id, namespace_key, namespace_value):
    payload = record.get("payload", {})
    return (
        record.get("alg") == "HMAC-SHA256"
        and record.get("key_id") == key_id
        and payload.get(namespace_key) == namespace_value
        and hmac.compare_digest(record.get("mac", ""), mac(key, payload))
    )


def sign_head(payload):
    return sign(HEAD_KEY, HEAD_KEY_ID, payload)


def head_authentic(record):
    return authentic(record, HEAD_KEY, HEAD_KEY_ID, "authority_namespace", AUTHORITY_NS)


def sign_root(payload):
    return sign(ROOT_KEY, ROOT_KEY_ID, payload)


def root_authentic(record):
    return authentic(record, ROOT_KEY, ROOT_KEY_ID, "root_namespace", ROOT_NS)


def sign_witness(witness_id, payload):
    key, key_id = WITNESS_KEYS[witness_id]
    return sign(key, key_id, payload)


def witness_authentic(statement):
    payload = statement.get("payload", {})
    witness_id = payload.get("witness_id")
    if witness_id not in WITNESS_KEYS:
        return False
    key, key_id = WITNESS_KEYS[witness_id]
    return authentic(statement, key, key_id, "authority_namespace", AUTHORITY_NS)


RULE = {"rule_id": "cap-equivalence-r2", "generation": 9}
RULE["digest"] = sha(RULE)
H9 = sign_head({
    "authority_namespace": AUTHORITY_NS,
    "generation": 9,
    "rule_id": RULE["rule_id"],
    "rule_digest": RULE["digest"],
    "status": "ACTIVE",
})

C3 = sign_root({
    "root_namespace": ROOT_NS,
    "record_type": "constitutional-root-resolution",
    "root_epoch": 3,
    "set_id": "set-R",
    "members": ["W25", "W26", "W27"],
    "threshold": 2,
    "issued_for_generation": 9,
    "head_digest": sha(H9),
    "status": "ACTIVE",
    "history_note": "historical-root-authority",
})
C3_DIGEST = sha(C3["payload"])

C5 = sign_root({
    "root_namespace": ROOT_NS,
    "record_type": "constitutional-root-resolution",
    "root_epoch": 5,
    "set_id": "set-H",
    "members": ["W22", "W23", "W24"],
    "threshold": 2,
    "issued_for_generation": 9,
    "head_digest": sha(H9),
    "status": "ACTIVE",
    "predecessor_root_digest": C3_DIGEST,
    "history_note": "current-root-authority",
})
C5_DIGEST = sha(C5["payload"])


def statement(witness_id, root_record, round_number):
    rp = root_record["payload"]
    return sign_witness(witness_id, {
        "authority_namespace": AUTHORITY_NS,
        "witness_id": witness_id,
        "root_namespace": ROOT_NS,
        "root_epoch": rp["root_epoch"],
        "root_record_digest": sha(rp),
        "witness_set_id": rp["set_id"],
        "round": round_number,
        "generation": 9,
        "head_digest": sha(H9),
    })


QC_OLD = {"certificate_id": "QC-root-epoch3", "statements": [statement("W25", C3, 110), statement("W26", C3, 110)]}
QC_CURRENT = {"certificate_id": "QC-root-epoch5", "statements": [statement("W22", C5, 111), statement("W23", C5, 111)]}


def validate_certificate(certificate, root_record):
    rp = root_record.get("payload", {})
    statements = certificate.get("statements", [])
    payloads = [s.get("payload", {}) for s in statements]
    signers = [p.get("witness_id") for p in payloads]
    distinct = sorted(set(signers))
    root_digest = sha(rp)
    same_root = bool(payloads) and all(
        p.get("root_namespace") == ROOT_NS
        and p.get("root_epoch") == rp.get("root_epoch")
        and p.get("root_record_digest") == root_digest
        and p.get("witness_set_id") == rp.get("set_id")
        for p in payloads
    )
    same_round = bool(payloads) and len({p.get("round") for p in payloads}) == 1
    same_head = bool(payloads) and len({p.get("head_digest") for p in payloads}) == 1
    same_generation = bool(payloads) and len({p.get("generation") for p in payloads}) == 1
    all_authentic = bool(statements) and all(witness_authentic(s) for s in statements)
    members_valid = all(s in rp.get("members", []) for s in distinct)
    threshold = int(rp.get("threshold", 0))
    valid = (
        root_authentic(root_record)
        and all_authentic
        and len(signers) == len(distinct)
        and members_valid
        and same_root
        and same_round
        and same_head
        and same_generation
        and len(distinct) >= threshold
    )
    return {
        "valid": valid,
        "certificate_id": certificate.get("certificate_id"),
        "root_authentic": root_authentic(root_record),
        "root_epoch": rp.get("root_epoch"),
        "root_record_digest": root_digest,
        "set_id": rp.get("set_id"),
        "threshold": threshold,
        "signers": distinct,
        "all_authentic": all_authentic,
        "members_valid": members_valid,
        "same_root": same_root,
        "same_round": same_round,
        "same_head": same_head,
        "same_generation": same_generation,
        "round": payloads[0].get("round") if payloads else None,
        "head_digest": payloads[0].get("head_digest") if payloads else None,
        "generation": payloads[0].get("generation") if payloads else None,
    }


def http_json(method, path, headers=None):
    req = urllib.request.Request(BASE + path, method=method, headers=headers or {})
    with urllib.request.urlopen(req, timeout=5) as response:
        return response.status, json.loads(response.read().decode())


def start_service():
    subprocess.run(["docker", "rm", "-f", CONTAINER], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["docker", "volume", "rm", "-f", VOLUME], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["docker", "volume", "create", VOLUME], check=True, stdout=subprocess.DEVNULL)
    subprocess.run([
        "docker", "run", "-d", "--name", CONTAINER,
        "-p", "18101:8080",
        "-v", f"{VOLUME}:/state",
        "-v", f"{SERVICE}:/app/external_service.py:ro",
        IMAGE, "python", "/app/external_service.py", "--port", "8080",
    ], check=True, stdout=subprocess.DEVNULL)
    for _ in range(50):
        try:
            return http_json("GET", "/health")[1]
        except Exception:
            time.sleep(0.1)
    raise RuntimeError("external service did not become healthy")


def stop_service():
    subprocess.run(["docker", "rm", "-f", CONTAINER], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["docker", "volume", "rm", "-f", VOLUME], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def db(dsn):
    return psycopg.connect(dsn, autocommit=False, row_factory=dict_row)


def init_db(conn):
    conn.execute("CREATE TABLE IF NOT EXISTS cr_state(resource_id TEXT PRIMARY KEY, owner TEXT, fence INT, global_version INT, output_value INT)")
    conn.execute("CREATE TABLE IF NOT EXISTS cr_artifacts(resource_id TEXT PRIMARY KEY, artifact_digest TEXT, state TEXT DEFAULT 'READY', adopted_by TEXT, adopted_fence INT)")
    conn.execute("CREATE TABLE IF NOT EXISTS cr_root_checkpoint(root_namespace TEXT PRIMARY KEY, max_root_epoch INT NOT NULL, root_record_digest TEXT NOT NULL)")
    conn.commit()


def reset_resource(conn, resource_id):
    conn.execute("DELETE FROM cr_artifacts WHERE resource_id=%s", (resource_id,))
    conn.execute("DELETE FROM cr_state WHERE resource_id=%s", (resource_id,))
    conn.execute("INSERT INTO cr_state VALUES(%s,'worker-B',2,101,30)", (resource_id,))
    artifact_digest = sha({"resource_id": resource_id, "artifact_id": "artifact-v1", "output_value": 30})
    conn.execute("INSERT INTO cr_artifacts(resource_id,artifact_digest) VALUES(%s,%s)", (resource_id, artifact_digest))
    conn.commit()
    return artifact_digest


def observe_root(conn, root_record):
    rp = root_record["payload"]
    digest = sha(rp)
    row = conn.execute("SELECT * FROM cr_root_checkpoint WHERE root_namespace=%s", (ROOT_NS,)).fetchone()
    if row is None:
        conn.execute("INSERT INTO cr_root_checkpoint VALUES(%s,%s,%s)", (ROOT_NS, rp["root_epoch"], digest))
    elif rp["root_epoch"] > row["max_root_epoch"]:
        conn.execute("UPDATE cr_root_checkpoint SET max_root_epoch=%s, root_record_digest=%s WHERE root_namespace=%s", (rp["root_epoch"], digest, ROOT_NS))
    elif rp["root_epoch"] == row["max_root_epoch"] and digest == row["root_record_digest"]:
        pass
    conn.commit()
    return dict(conn.execute("SELECT * FROM cr_root_checkpoint WHERE root_namespace=%s", (ROOT_NS,)).fetchone())


def read_root_checkpoint(conn):
    row = conn.execute("SELECT * FROM cr_root_checkpoint WHERE root_namespace=%s", (ROOT_NS,)).fetchone()
    return dict(row) if row else None


def isolated_verdict(certificate, root_record):
    qc = validate_certificate(certificate, root_record)
    rp = root_record["payload"]
    binds_head = qc["head_digest"] == sha(H9) and qc["generation"] == 9 and rp.get("head_digest") == sha(H9)
    accept = qc["valid"] and head_authentic(H9) and binds_head and rp.get("status") == "ACTIVE"
    return {
        "accept": accept,
        "reason": "presented_root_treated_as_current" if accept else "root_or_head_conflict",
        "certificate": qc,
        "checks": {"head_authentic": head_authentic(H9), "root_binds_head": binds_head},
    }


def currentness_verdict(conn, certificate, root_record):
    qc = validate_certificate(certificate, root_record)
    rp = root_record["payload"]
    checkpoint = read_root_checkpoint(conn)
    binds_head = qc["head_digest"] == sha(H9) and qc["generation"] == 9 and rp.get("head_digest") == sha(H9)
    if checkpoint is None:
        return {"accept": False, "reason": "root_checkpoint_absent", "certificate": qc, "checkpoint": None}
    if rp["root_epoch"] < checkpoint["max_root_epoch"]:
        return {
            "accept": False,
            "reason": "root_authority_rollback_detected",
            "certificate": qc,
            "checkpoint": checkpoint,
            "presented_root_epoch": rp["root_epoch"],
            "presented_root_digest": sha(rp),
        }
    if rp["root_epoch"] == checkpoint["max_root_epoch"] and sha(rp) != checkpoint["root_record_digest"]:
        return {
            "accept": False,
            "reason": "root_authority_same_epoch_conflict",
            "certificate": qc,
            "checkpoint": checkpoint,
            "presented_root_epoch": rp["root_epoch"],
            "presented_root_digest": sha(rp),
        }
    accept = qc["valid"] and head_authentic(H9) and binds_head and rp.get("status") == "ACTIVE"
    return {
        "accept": accept,
        "reason": "current_root_authorized" if accept else "root_or_head_conflict",
        "certificate": qc,
        "checkpoint": checkpoint,
        "presented_root_epoch": rp["root_epoch"],
        "presented_root_digest": sha(rp),
        "checks": {"head_authentic": head_authentic(H9), "root_binds_head": binds_head},
    }


def attempt(conn, resource_id, verdict, phase):
    artifact = conn.execute("SELECT * FROM cr_artifacts WHERE resource_id=%s", (resource_id,)).fetchone()
    if not verdict["accept"]:
        return {
            "verdict": verdict,
            "adoption": {"updated_rows": 0, "reason": verdict["reason"]},
            "write": None,
            "remote": http_json("GET", f"/status/{resource_id}")[1],
        }
    cur = conn.execute("UPDATE cr_artifacts SET state='ADOPTED', adopted_by='worker-B', adopted_fence=2 WHERE resource_id=%s AND state='READY'", (resource_id,))
    conn.commit()
    if cur.rowcount != 1:
        return {
            "verdict": verdict,
            "adoption": {"updated_rows": cur.rowcount, "reason": "adoption_conflict"},
            "write": None,
            "remote": http_json("GET", f"/status/{resource_id}")[1],
        }
    headers = {
        "X-Resource-Id": resource_id,
        "X-Worker": "worker-B",
        "X-Fencing-Token": "2",
        "X-Artifact-Digest": artifact["artifact_digest"],
        "X-Input-State-Version": "101",
        "X-Output-Value": "30",
        "X-Phase": phase,
    }
    status, payload = http_json("POST", "/effects", headers)
    return {
        "verdict": verdict,
        "adoption": {"updated_rows": 1, "reason": "adopted"},
        "write": {"http_status": status, "payload": payload},
        "remote": http_json("GET", f"/status/{resource_id}")[1],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    dsn = os.environ["DATABASE_URL"]
    health = start_service()
    try:
        with db(dsn) as conn:
            init_db(conn)
            q_old = validate_certificate(QC_OLD, C3)
            q_current = validate_certificate(QC_CURRENT, C5)

            checkpoint_after_current = observe_root(conn, C5)

            reset_resource(conn, "unsafe-root-replay")
            unsafe = attempt(conn, "unsafe-root-replay", isolated_verdict(QC_OLD, C3), "unsafe-root-replay")

            reset_resource(conn, "safe-root-replay")
            safe = attempt(conn, "safe-root-replay", currentness_verdict(conn, QC_OLD, C3), "safe-root-replay")

            reset_resource(conn, "fresh-current-root")
            current = attempt(conn, "fresh-current-root", currentness_verdict(conn, QC_CURRENT, C5), "fresh-current-root")

            checkpoint_final = read_root_checkpoint(conn)

        checks = [
            {
                "id": "historical_and_current_root_records_authenticate_and_local_quorums_validate",
                "pass": root_authentic(C3) and root_authentic(C5) and q_old["valid"] and q_current["valid"],
                "points": 2,
                "evidence": {"C3": C3, "C5": C5, "QC_OLD": q_old, "QC_CURRENT": q_current},
            },
            {
                "id": "observing_current_root_establishes_monotonic_high_watermark_epoch5",
                "pass": checkpoint_after_current["max_root_epoch"] == 5 and checkpoint_after_current["root_record_digest"] == C5_DIGEST and checkpoint_final == checkpoint_after_current,
                "points": 2,
                "evidence": {"checkpoint_after_current": checkpoint_after_current, "checkpoint_final": checkpoint_final},
            },
            {
                "id": "unsafe_verifier_accepts_replayed_authentic_old_root_and_commits_one_effect",
                "pass": unsafe["verdict"]["accept"] and unsafe["adoption"]["updated_rows"] == 1 and unsafe["write"]["http_status"] == 200 and unsafe["remote"]["effect_count"] == 1,
                "points": 2,
                "evidence": unsafe,
            },
            {
                "id": "root_currentness_verifier_rejects_old_root_below_high_watermark_with_zero_effects",
                "pass": (not safe["verdict"]["accept"]) and safe["verdict"]["reason"] == "root_authority_rollback_detected" and safe["remote"]["effect_count"] == 0,
                "points": 2,
                "evidence": safe,
            },
            {
                "id": "fresh_current_root_passes_currentness_gate_and_restores_liveness_once",
                "pass": current["verdict"]["accept"] and current["verdict"]["reason"] == "current_root_authorized" and current["adoption"]["updated_rows"] == 1 and current["write"]["http_status"] == 200 and current["remote"]["effect_count"] == 1,
                "points": 2,
                "evidence": current,
            },
        ]
        score = sum(c["points"] for c in checks if c["pass"])
        result = {
            "protocol": "RESONANCE Transactional Trust Protocol v1.0",
            "benchmark": "RESONANCE Constitutional Root Authority Replay / Root Currentness",
            "benchmark_version": "1.0",
            "executed_at": datetime.now(timezone.utc).isoformat(),
            "score": score,
            "max_score": 10,
            "classification": "Constitutional root currentness protocol passes" if score == 10 else "Constitutional root currentness protocol incomplete",
            "head": H9,
            "root_records": {"historical_C3": C3, "current_C5": C5},
            "root_digests": {"historical_C3": C3_DIGEST, "current_C5": C5_DIGEST},
            "root_checkpoint": checkpoint_final,
            "certificates": {"QC_OLD": QC_OLD, "QC_CURRENT": QC_CURRENT},
            "checks": checks,
            "http_service": health,
            "http_service_image": IMAGE,
            "database": {"server_version": 170006},
            "authentication_fixtures": {
                "authority_head": {"algorithm": "HMAC-SHA256", "key_id": HEAD_KEY_ID, "production_pki": False},
                "constitutional_root": {"algorithm": "HMAC-SHA256", "key_id": ROOT_KEY_ID, "production_pki": False},
            },
            "invariants": [
                "ROOT AUTHORITY DOES NOT IMPLY TIMELESS AUTHORITY.",
                "AUTHENTIC ROOT RECORD BELOW A TRUSTED ROOT HIGH-WATERMARK IS ROOT-AUTHORITY ROLLBACK EVIDENCE.",
                "ROOT CURRENTNESS MUST BIND A MONOTONIC ROOT EPOCH AND ROOT-RECORD DIGEST BEFORE CONSEQUENTIAL AUTHORIZATION.",
                "A RETIRED ROOT RECORD MAY REMAIN HISTORICALLY VALID BUT MUST NOT REGAIN LIVE AUTHORITY AFTER A NEWER ROOT EPOCH IS OBSERVED.",
            ],
            "external_safety_certification": False,
            "vulnerability_claim": False,
        }
        (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        md = [
            "# Constitutional Root Authority Replay / Root Currentness v1.0",
            "",
            f"Score: **{score}/10**",
            "",
            f"Classification: **{result['classification']}**",
            "",
            "## Checks",
        ]
        for check in checks:
            md.append(f"- {'PASS' if check['pass'] else 'FAIL'} — {check['id']} ({check['points']}/2)")
        (out / "RESULT.md").write_text("\n".join(md) + "\n")
        print(json.dumps(result, indent=2, sort_keys=True))
        if score != 10:
            raise SystemExit(1)
    finally:
        stop_service()


if __name__ == "__main__":
    main()
