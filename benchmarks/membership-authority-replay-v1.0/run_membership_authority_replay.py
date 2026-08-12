from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import subprocess
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

CONTAINER = "resonance-external-membership-authority-replay"
VOLUME = "resonance-membership-authority-replay-v1"
IMAGE = os.environ.get("HTTP_SERVICE_IMAGE", "python:3.12-slim")
BASE = os.environ.get("EXTERNAL_BASE_URL", "http://127.0.0.1:18101")
SERVICE = Path("benchmarks/dependency-aware-applicability-v1.0/external_service.py").resolve()

NS = "resonance-proof-authority"
MEMBERSHIP_NS = "resonance-witness-membership"
HEAD_KEY = b"resonance-authority-head-demo-key-v1"
HEAD_KEY_ID = "authority-head-demo-key-v1"
MEMBERSHIP_KEY = b"resonance-membership-authority-demo-key-v1"
MEMBERSHIP_KEY_ID = "membership-authority-demo-key-v1"
WITNESS_KEYS = {
    "W1": (b"resonance-replay-w1-demo-key-v1", "replay-w1-demo-key-v1"),
    "W2": (b"resonance-replay-w2-demo-key-v1", "replay-w2-demo-key-v1"),
    "W3": (b"resonance-replay-w3-demo-key-v1", "replay-w3-demo-key-v1"),
    "W4": (b"resonance-replay-w4-demo-key-v1", "replay-w4-demo-key-v1"),
    "W5": (b"resonance-replay-w5-demo-key-v1", "replay-w5-demo-key-v1"),
    "W6": (b"resonance-replay-w6-demo-key-v1", "replay-w6-demo-key-v1"),
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


def head_authentic(head):
    return authentic(head, HEAD_KEY, HEAD_KEY_ID, "authority_namespace", NS)


def sign_membership(payload):
    return sign(MEMBERSHIP_KEY, MEMBERSHIP_KEY_ID, payload)


def membership_authentic(record):
    return authentic(record, MEMBERSHIP_KEY, MEMBERSHIP_KEY_ID, "membership_namespace", MEMBERSHIP_NS)


def sign_witness(witness_id, payload):
    key, key_id = WITNESS_KEYS[witness_id]
    return sign(key, key_id, payload)


def witness_authentic(statement):
    payload = statement.get("payload", {})
    wid = payload.get("witness_id")
    if wid not in WITNESS_KEYS:
        return False
    key, key_id = WITNESS_KEYS[wid]
    return authentic(statement, key, key_id, "authority_namespace", NS)


RULES = {
    "R1": {"rule_id": "cap-equivalence-r1", "generation": 7},
    "R2": {"rule_id": "cap-equivalence-r2", "generation": 9},
}
for rule in RULES.values():
    rule["digest"] = sha(rule)

H7 = sign_head({
    "authority_namespace": NS,
    "generation": 7,
    "rule_id": RULES["R1"]["rule_id"],
    "rule_digest": RULES["R1"]["digest"],
    "status": "ACTIVE",
})
H9 = sign_head({
    "authority_namespace": NS,
    "generation": 9,
    "rule_id": RULES["R2"]["rule_id"],
    "rule_digest": RULES["R2"]["digest"],
    "status": "ACTIVE",
})

M1_PAYLOAD = {
    "membership_namespace": MEMBERSHIP_NS,
    "set_id": "set-A",
    "set_epoch": 1,
    "members": ["W1", "W2", "W3"],
    "threshold": 2,
    "issued_for_generation": 7,
    "predecessor_membership_digest": None,
}
M1 = sign_membership(M1_PAYLOAD)
M2_PAYLOAD = {
    "membership_namespace": MEMBERSHIP_NS,
    "set_id": "set-B",
    "set_epoch": 2,
    "members": ["W4", "W5", "W6"],
    "threshold": 2,
    "issued_for_generation": 9,
    "predecessor_membership_digest": sha(M1_PAYLOAD),
}
M2 = sign_membership(M2_PAYLOAD)


def statement(witness_id, membership, head, round_number):
    mp = membership["payload"]
    hp = head["payload"]
    return sign_witness(witness_id, {
        "authority_namespace": NS,
        "witness_id": witness_id,
        "witness_set_id": mp["set_id"],
        "witness_set_epoch": mp["set_epoch"],
        "membership_digest": sha(mp),
        "round": round_number,
        "generation": hp["generation"],
        "head_digest": sha(head),
    })


QC_OLD = {"certificate_id": "QC-old-epoch1", "statements": [statement("W1", M1, H7, 70), statement("W2", M1, H7, 70)]}
QC_CURRENT = {"certificate_id": "QC-current-epoch2", "statements": [statement("W4", M2, H9, 71), statement("W5", M2, H9, 71)]}


def validate_certificate(certificate, membership):
    mp = membership.get("payload", {})
    statements = certificate.get("statements", [])
    payloads = [s.get("payload", {}) for s in statements]
    signers = [p.get("witness_id") for p in payloads]
    distinct = sorted(set(signers))
    md = sha(mp)
    same_set = bool(payloads) and all(
        p.get("witness_set_id") == mp.get("set_id")
        and p.get("witness_set_epoch") == mp.get("set_epoch")
        and p.get("membership_digest") == md
        for p in payloads
    )
    same_round = bool(payloads) and len({p.get("round") for p in payloads}) == 1
    same_head = bool(payloads) and len({p.get("head_digest") for p in payloads}) == 1
    same_generation = bool(payloads) and len({p.get("generation") for p in payloads}) == 1
    valid = (
        membership_authentic(membership)
        and bool(statements)
        and all(witness_authentic(s) for s in statements)
        and len(distinct) == len(signers)
        and all(s in mp.get("members", []) for s in distinct)
        and same_set and same_round and same_head and same_generation
        and len(distinct) >= int(mp.get("threshold", 0))
    )
    return {
        "valid": valid,
        "certificate_id": certificate.get("certificate_id"),
        "set_id": mp.get("set_id"),
        "set_epoch": mp.get("set_epoch"),
        "membership_digest": md,
        "threshold": mp.get("threshold"),
        "signers": distinct,
        "head_digest": payloads[0].get("head_digest") if payloads else None,
        "generation": payloads[0].get("generation") if payloads else None,
        "all_authentic": bool(statements) and all(witness_authentic(s) for s in statements),
        "membership_authentic": membership_authentic(membership),
    }


def db(dsn):
    return psycopg.connect(dsn, autocommit=False, row_factory=dict_row)


def init(conn):
    conn.execute("CREATE TABLE IF NOT EXISTS mar_replica(region TEXT PRIMARY KEY, rule_id TEXT, rule_digest TEXT, status TEXT, generation INT)")
    conn.execute("CREATE TABLE IF NOT EXISTS mar_membership_checkpoint(namespace TEXT PRIMARY KEY, max_set_epoch INT, set_id TEXT, membership_digest TEXT)")
    conn.execute("CREATE TABLE IF NOT EXISTS mar_state(resource_id TEXT PRIMARY KEY, owner TEXT, fence INT, global_version INT, output_value INT)")
    conn.execute("CREATE TABLE IF NOT EXISTS mar_artifacts(resource_id TEXT PRIMARY KEY, artifact_digest TEXT, state TEXT DEFAULT 'READY', adopted_by TEXT, adopted_fence INT)")
    conn.commit()


def establish_checkpoint(conn, membership):
    mp = membership["payload"]
    conn.execute(
        "INSERT INTO mar_membership_checkpoint(namespace,max_set_epoch,set_id,membership_digest) VALUES(%s,%s,%s,%s) ON CONFLICT(namespace) DO UPDATE SET max_set_epoch=GREATEST(mar_membership_checkpoint.max_set_epoch,EXCLUDED.max_set_epoch), set_id=CASE WHEN EXCLUDED.max_set_epoch>=mar_membership_checkpoint.max_set_epoch THEN EXCLUDED.set_id ELSE mar_membership_checkpoint.set_id END, membership_digest=CASE WHEN EXCLUDED.max_set_epoch>=mar_membership_checkpoint.max_set_epoch THEN EXCLUDED.membership_digest ELSE mar_membership_checkpoint.membership_digest END",
        (MEMBERSHIP_NS, mp["set_epoch"], mp["set_id"], sha(mp)),
    )
    conn.commit()
    return dict(conn.execute("SELECT * FROM mar_membership_checkpoint WHERE namespace=%s", (MEMBERSHIP_NS,)).fetchone())


def set_replica(conn, generation):
    rule = RULES["R1" if generation == 7 else "R2"]
    conn.execute("DELETE FROM mar_replica")
    conn.execute("INSERT INTO mar_replica VALUES('region-B',%s,%s,'ACTIVE',%s)", (rule["rule_id"], rule["digest"], generation))
    conn.commit()


def reset_resource(conn, resource_id):
    conn.execute("DELETE FROM mar_artifacts WHERE resource_id=%s", (resource_id,))
    conn.execute("DELETE FROM mar_state WHERE resource_id=%s", (resource_id,))
    conn.execute("INSERT INTO mar_state VALUES(%s,'worker-B',2,101,30)", (resource_id,))
    digest = sha({"resource_id": resource_id, "artifact_id": "artifact-v1", "output_value": 30})
    conn.execute("INSERT INTO mar_artifacts(resource_id,artifact_digest) VALUES(%s,%s)", (resource_id, digest))
    conn.commit()


def replica_matches(conn, head):
    replica = conn.execute("SELECT * FROM mar_replica WHERE region='region-B'").fetchone()
    hp = head["payload"]
    checks = {
        "head_authentic": head_authentic(head),
        "replica_generation": replica is not None and replica["generation"] == hp["generation"],
        "replica_rule": replica is not None and replica["rule_id"] == hp["rule_id"] and replica["rule_digest"] == hp["rule_digest"],
        "replica_active": replica is not None and replica["status"] == "ACTIVE",
    }
    return checks, dict(replica) if replica else None


def unsafe_verdict(conn, certificate, presented_membership, head):
    qc = validate_certificate(certificate, presented_membership)
    checks, replica = replica_matches(conn, head)
    binds = qc["head_digest"] == sha(head) and qc["generation"] == head["payload"]["generation"]
    accept = qc["valid"] and all(checks.values()) and binds
    return {
        "accept": accept,
        "reason": "presented_membership_treated_as_current" if accept else "presented_membership_or_head_conflict",
        "membership": presented_membership,
        "certificate": qc,
        "checks": {**checks, "quorum_binds_head": binds},
        "replica": replica,
    }


def safe_verdict(conn, certificate, presented_membership, head):
    qc = validate_certificate(certificate, presented_membership)
    mp = presented_membership["payload"]
    checkpoint = dict(conn.execute("SELECT * FROM mar_membership_checkpoint WHERE namespace=%s", (MEMBERSHIP_NS,)).fetchone())
    checks, replica = replica_matches(conn, head)
    binds = qc["head_digest"] == sha(head) and qc["generation"] == head["payload"]["generation"]
    membership_ok = membership_authentic(presented_membership)
    rollback = membership_ok and mp["set_epoch"] < checkpoint["max_set_epoch"]
    same_checkpoint = (
        membership_ok
        and mp["set_epoch"] == checkpoint["max_set_epoch"]
        and mp["set_id"] == checkpoint["set_id"]
        and sha(mp) == checkpoint["membership_digest"]
    )
    if rollback:
        reason = "membership_authority_rollback_detected"
        accept = False
    elif not same_checkpoint:
        reason = "membership_authority_conflict"
        accept = False
    else:
        accept = qc["valid"] and all(checks.values()) and binds
        reason = "current_membership_authorized" if accept else "current_membership_or_head_conflict"
    return {
        "accept": accept,
        "reason": reason,
        "checkpoint": checkpoint,
        "presented_membership_authentic": membership_ok,
        "presented_set_epoch": mp["set_epoch"],
        "presented_set_id": mp["set_id"],
        "rollback": rollback,
        "certificate": qc,
        "checks": {**checks, "quorum_binds_head": binds},
        "replica": replica,
    }


def adopt(conn, resource_id, verdict):
    if not verdict["accept"]:
        return {"updated_rows": 0, "reason": verdict["reason"]}
    cur = conn.execute(
        "UPDATE mar_artifacts a SET state='ADOPTED',adopted_by=s.owner,adopted_fence=s.fence FROM mar_state s WHERE a.resource_id=s.resource_id AND a.resource_id=%s AND a.state='READY' RETURNING a.resource_id",
        (resource_id,),
    )
    rows = cur.rowcount
    conn.commit()
    return {"updated_rows": rows, "reason": "adopted" if rows else "compare_and_adopt_conflict"}


def http(method, path, headers=None):
    req = urllib.request.Request(BASE + path, method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            return response.status, json.loads(response.read().decode())
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read().decode())


def start_service():
    subprocess.run(["docker", "rm", "-f", CONTAINER], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["docker", "volume", "rm", "-f", VOLUME], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["docker", "volume", "create", VOLUME], check=True, stdout=subprocess.DEVNULL)
    port = BASE.rsplit(":", 1)[-1]
    subprocess.run(["docker", "run", "-d", "--name", CONTAINER, "-p", f"{port}:8080", "-v", f"{VOLUME}:/state", "-v", f"{SERVICE}:/app/external_service.py:ro", IMAGE, "python", "/app/external_service.py"], check=True, stdout=subprocess.DEVNULL)
    for _ in range(50):
        try:
            code, payload = http("GET", "/health")
            if code == 200:
                return payload
        except Exception:
            pass
        time.sleep(0.1)
    raise RuntimeError("external service did not start")


def publish(conn, resource_id, phase):
    state = conn.execute("SELECT * FROM mar_state WHERE resource_id=%s", (resource_id,)).fetchone()
    artifact = conn.execute("SELECT * FROM mar_artifacts WHERE resource_id=%s", (resource_id,)).fetchone()
    headers = {
        "X-Resource-Id": resource_id,
        "X-Worker": state["owner"],
        "X-Fencing-Token": str(state["fence"]),
        "X-Artifact-Digest": artifact["artifact_digest"],
        "X-Input-State-Version": str(state["global_version"]),
        "X-Output-Value": str(state["output_value"]),
        "X-Phase": phase,
    }
    return http("POST", "/effects", headers)


def remote(resource_id):
    return http("GET", f"/status/{resource_id}")[1]


def run_case(conn, resource_id, verdict, phase):
    reset_resource(conn, resource_id)
    adoption = adopt(conn, resource_id, verdict)
    write = None
    if adoption["updated_rows"]:
        code, payload = publish(conn, resource_id, phase)
        write = {"http_status": code, "payload": payload}
    return {"verdict": verdict, "adoption": adoption, "write": write, "remote": remote(resource_id)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="benchmark-results/membership-authority-replay-v1.0")
    args = parser.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    dsn = os.environ.get("DATABASE_URL", "postgresql://resonance:resonance@127.0.0.1:5432/resonance")
    health = start_service()

    with db(dsn) as conn:
        init(conn)
        checkpoint = establish_checkpoint(conn, M2)
        successor_chain_valid = membership_authentic(M1) and membership_authentic(M2) and M2_PAYLOAD["predecessor_membership_digest"] == sha(M1_PAYLOAD) and M2_PAYLOAD["set_epoch"] > M1_PAYLOAD["set_epoch"]

        set_replica(conn, 7)
        unsafe = run_case(conn, "unsafe-membership-replay", unsafe_verdict(conn, QC_OLD, M1, H7), "unsafe-membership-replay")

        set_replica(conn, 7)
        safe_old = run_case(conn, "safe-membership-replay", safe_verdict(conn, QC_OLD, M1, H7), "safe-membership-replay")

        stale_crypto = {
            "membership_authentic": membership_authentic(M1),
            "old_quorum_valid": validate_certificate(QC_OLD, M1)["valid"],
            "head_authentic": head_authentic(H7),
            "presented_epoch": M1_PAYLOAD["set_epoch"],
            "trusted_epoch": checkpoint["max_set_epoch"],
        }

        set_replica(conn, 9)
        safe_current = run_case(conn, "fresh-current-membership", safe_verdict(conn, QC_CURRENT, M2, H9), "fresh-current-membership")

        checks = [
            {
                "id": "authenticated_successor_chain_establishes_monotonic_membership_checkpoint",
                "pass": successor_chain_valid and checkpoint["max_set_epoch"] == 2 and checkpoint["set_id"] == "set-B" and checkpoint["membership_digest"] == sha(M2_PAYLOAD),
                "points": 2,
                "evidence": {"M1": M1, "M2": M2, "checkpoint": checkpoint, "successor_chain_valid": successor_chain_valid},
            },
            {
                "id": "unsafe_verifier_accepts_replayed_authentic_membership_and_commits_one_effect",
                "pass": unsafe["verdict"]["accept"] and unsafe["adoption"]["updated_rows"] == 1 and unsafe["remote"].get("effect_count") == 1,
                "points": 2,
                "evidence": unsafe,
            },
            {
                "id": "safe_verifier_detects_membership_authority_rollback_before_consequence",
                "pass": not safe_old["verdict"]["accept"] and safe_old["verdict"]["reason"] == "membership_authority_rollback_detected" and safe_old["adoption"]["updated_rows"] == 0 and safe_old["remote"].get("effect_count") == 0,
                "points": 2,
                "evidence": safe_old,
            },
            {
                "id": "stale_membership_remains_cryptographically_valid_but_is_not_current",
                "pass": stale_crypto["membership_authentic"] and stale_crypto["old_quorum_valid"] and stale_crypto["head_authentic"] and stale_crypto["presented_epoch"] < stale_crypto["trusted_epoch"],
                "points": 2,
                "evidence": stale_crypto,
            },
            {
                "id": "fresh_current_membership_quorum_succeeds_exactly_once",
                "pass": safe_current["verdict"]["accept"] and safe_current["adoption"]["updated_rows"] == 1 and safe_current["remote"].get("effect_count") == 1,
                "points": 2,
                "evidence": safe_current,
            },
        ]

        score = sum(c["points"] for c in checks if c["pass"])
        result = {
            "benchmark": "RESONANCE Membership Authority Replay / Stale Rotation View",
            "benchmark_version": "1.0",
            "protocol": "RESONANCE Transactional Trust Protocol v1.0",
            "executed_at": datetime.now(timezone.utc).isoformat(),
            "database": {"server_version": conn.info.server_version},
            "http_service_image": IMAGE,
            "http_service": health,
            "authentication_fixtures": {
                "authority_head": {"algorithm": "HMAC-SHA256", "key_id": HEAD_KEY_ID, "production_pki": False},
                "membership_authority": {"algorithm": "HMAC-SHA256", "key_id": MEMBERSHIP_KEY_ID, "production_pki": False},
                "witnesses": {w: {"algorithm": "HMAC-SHA256", "key_id": kid, "production_pki": False} for w, (_, kid) in WITNESS_KEYS.items()},
            },
            "memberships": {"M1": M1, "M2": M2},
            "membership_checkpoint": checkpoint,
            "heads": {"H7": H7, "H9": H9},
            "certificates": {"QC_OLD": QC_OLD, "QC_CURRENT": QC_CURRENT},
            "checks": checks,
            "invariants": [
                "AUTHENTIC MEMBERSHIP RECORD DOES NOT IMPLY CURRENT MEMBERSHIP AUTHORITY.",
                "MEMBERSHIP CURRENTNESS MUST BIND TO A MONOTONIC SET-EPOCH / MEMBERSHIP-DIGEST CHECKPOINT OR EQUIVALENT ANTI-ROLLBACK EVIDENCE.",
                "AUTHENTIC MEMBERSHIP BELOW THE TRUSTED MEMBERSHIP HIGH-WATERMARK MUST FAIL CLOSED BEFORE CONSEQUENCE.",
                "FRESH CURRENT-MEMBERSHIP QUORUM EVIDENCE IS REQUIRED TO RESTORE LIVE AUTHORITY AFTER ROTATION.",
            ],
            "score": score,
            "max_score": 10,
            "classification": "Membership authority replay protocol passes" if score == 10 else "Membership authority replay protocol incomplete",
            "external_safety_certification": False,
            "vulnerability_claim": False,
        }

    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    md = ["# RESONANCE Membership Authority Replay / Stale Rotation View v1.0", "", f"**Score:** {score}/10", "", f"**Classification:** {result['classification']}", ""]
    for check in checks:
        md.append(f"- {'PASS' if check['pass'] else 'FAIL'} — {check['id']} ({check['points']}/2)")
    md += ["", "> AUTHENTIC MEMBERSHIP RECORD ≠ CURRENT MEMBERSHIP AUTHORITY.", ""]
    (out / "RESULT.md").write_text("\n".join(md))
    print(json.dumps(result, indent=2, sort_keys=True))
    if score != 10:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
