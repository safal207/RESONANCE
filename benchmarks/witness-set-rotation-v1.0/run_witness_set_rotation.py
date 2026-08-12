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

CONTAINER = "resonance-external-witness-set-rotation"
VOLUME = "resonance-witness-set-rotation-v1"
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
    "W1": (b"resonance-rotation-w1-demo-key-v1", "rotation-w1-demo-key-v1"),
    "W2": (b"resonance-rotation-w2-demo-key-v1", "rotation-w2-demo-key-v1"),
    "W3": (b"resonance-rotation-w3-demo-key-v1", "rotation-w3-demo-key-v1"),
    "W4": (b"resonance-rotation-w4-demo-key-v1", "rotation-w4-demo-key-v1"),
    "W5": (b"resonance-rotation-w5-demo-key-v1", "rotation-w5-demo-key-v1"),
    "W6": (b"resonance-rotation-w6-demo-key-v1", "rotation-w6-demo-key-v1"),
}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def sha(value):
    return "sha256:" + hashlib.sha256(canonical(value).encode()).hexdigest()


def mac(key, payload):
    return hmac.new(key, canonical(payload).encode(), hashlib.sha256).hexdigest()


def sign_head(payload):
    return {"alg": "HMAC-SHA256", "key_id": HEAD_KEY_ID, "payload": payload, "mac": mac(HEAD_KEY, payload)}


def head_authentic(head):
    payload = head.get("payload", {})
    return (
        head.get("alg") == "HMAC-SHA256"
        and head.get("key_id") == HEAD_KEY_ID
        and payload.get("authority_namespace") == NS
        and hmac.compare_digest(head.get("mac", ""), mac(HEAD_KEY, payload))
    )


def sign_membership(payload):
    return {
        "alg": "HMAC-SHA256",
        "key_id": MEMBERSHIP_KEY_ID,
        "payload": payload,
        "mac": mac(MEMBERSHIP_KEY, payload),
    }


def membership_authentic(record):
    payload = record.get("payload", {})
    return (
        record.get("alg") == "HMAC-SHA256"
        and record.get("key_id") == MEMBERSHIP_KEY_ID
        and payload.get("membership_namespace") == MEMBERSHIP_NS
        and hmac.compare_digest(record.get("mac", ""), mac(MEMBERSHIP_KEY, payload))
    )


def sign_witness(witness_id, payload):
    key, key_id = WITNESS_KEYS[witness_id]
    return {"alg": "HMAC-SHA256", "key_id": key_id, "payload": payload, "mac": mac(key, payload)}


def witness_authentic(statement):
    payload = statement.get("payload", {})
    witness_id = payload.get("witness_id")
    if witness_id not in WITNESS_KEYS:
        return False
    key, key_id = WITNESS_KEYS[witness_id]
    return (
        statement.get("alg") == "HMAC-SHA256"
        and statement.get("key_id") == key_id
        and payload.get("authority_namespace") == NS
        and hmac.compare_digest(statement.get("mac", ""), mac(key, payload))
    )


RULES = {
    "R1": {"rule_id": "cap-equivalence-r1", "generation": 7},
    "R2": {"rule_id": "cap-equivalence-r2", "generation": 9},
}
for rule in RULES.values():
    rule["digest"] = sha(rule)

H7 = sign_head(
    {
        "authority_namespace": NS,
        "generation": 7,
        "rule_id": RULES["R1"]["rule_id"],
        "rule_digest": RULES["R1"]["digest"],
        "status": "ACTIVE",
    }
)
H9 = sign_head(
    {
        "authority_namespace": NS,
        "generation": 9,
        "rule_id": RULES["R2"]["rule_id"],
        "rule_digest": RULES["R2"]["digest"],
        "status": "ACTIVE",
    }
)

M1 = sign_membership(
    {
        "membership_namespace": MEMBERSHIP_NS,
        "set_id": "set-A",
        "set_epoch": 1,
        "members": ["W1", "W2", "W3"],
        "threshold": 2,
        "issued_for_generation": 7,
        "successor_set_id": None,
    }
)
M2 = sign_membership(
    {
        "membership_namespace": MEMBERSHIP_NS,
        "set_id": "set-B",
        "set_epoch": 2,
        "members": ["W4", "W5", "W6"],
        "threshold": 2,
        "issued_for_generation": 9,
        "successor_of_set_id": "set-A",
    }
)


def statement(witness_id, membership, head, round_number):
    mp = membership["payload"]
    hp = head["payload"]
    return sign_witness(
        witness_id,
        {
            "authority_namespace": NS,
            "witness_id": witness_id,
            "witness_set_id": mp["set_id"],
            "witness_set_epoch": mp["set_epoch"],
            "membership_digest": sha(mp),
            "round": round_number,
            "generation": hp["generation"],
            "head_digest": sha(head),
            "statement": "highest authenticated authority head observed for witness-set round",
        },
    )


QC_OLD = {
    "certificate_id": "QC-old-epoch1",
    "statements": [statement("W1", M1, H7, 60), statement("W2", M1, H7, 60)],
}
QC_CURRENT = {
    "certificate_id": "QC-current-epoch2",
    "statements": [statement("W4", M2, H9, 61), statement("W5", M2, H9, 61)],
}


def validate_certificate(certificate, membership, quarantined=None):
    quarantined = set(quarantined or [])
    mp = membership.get("payload", {})
    statements = certificate.get("statements", [])
    payloads = [s.get("payload", {}) for s in statements]
    signers = [p.get("witness_id") for p in payloads]
    distinct_signers = sorted(set(signers))
    active_signers = sorted(s for s in distinct_signers if s not in quarantined)
    expected_membership_digest = sha(mp)
    same_set = bool(payloads) and all(
        p.get("witness_set_id") == mp.get("set_id")
        and p.get("witness_set_epoch") == mp.get("set_epoch")
        and p.get("membership_digest") == expected_membership_digest
        for p in payloads
    )
    same_round = bool(payloads) and len({p.get("round") for p in payloads}) == 1
    same_head = bool(payloads) and len({p.get("head_digest") for p in payloads}) == 1
    same_generation = bool(payloads) and len({p.get("generation") for p in payloads}) == 1
    all_authentic = bool(statements) and all(witness_authentic(s) for s in statements)
    members_valid = all(s in mp.get("members", []) for s in distinct_signers)
    threshold = int(mp.get("threshold", 0))
    valid = (
        membership_authentic(membership)
        and all_authentic
        and len(distinct_signers) == len(signers)
        and members_valid
        and same_set
        and same_round
        and same_head
        and same_generation
        and len(active_signers) >= threshold
    )
    return {
        "valid": valid,
        "certificate_id": certificate.get("certificate_id"),
        "membership_authentic": membership_authentic(membership),
        "set_id": mp.get("set_id"),
        "set_epoch": mp.get("set_epoch"),
        "membership_digest": expected_membership_digest,
        "threshold": threshold,
        "members": mp.get("members", []),
        "signers": distinct_signers,
        "active_signers": active_signers,
        "all_authentic": all_authentic,
        "members_valid": members_valid,
        "same_set": same_set,
        "same_round": same_round,
        "same_head": same_head,
        "same_generation": same_generation,
        "round": payloads[0].get("round") if payloads else None,
        "head_digest": payloads[0].get("head_digest") if payloads else None,
        "generation": payloads[0].get("generation") if payloads else None,
    }


def current_membership_check(certificate, historical_membership, current_membership):
    historical = validate_certificate(certificate, historical_membership)
    cp = current_membership.get("payload", {})
    same_current_set = (
        historical["set_id"] == cp.get("set_id")
        and historical["set_epoch"] == cp.get("set_epoch")
        and historical["membership_digest"] == sha(cp)
        and historical["threshold"] == cp.get("threshold")
    )
    return {
        "accept": historical["valid"] and membership_authentic(current_membership) and same_current_set,
        "reason": "current_witness_set_authorized" if historical["valid"] and membership_authentic(current_membership) and same_current_set else "witness_set_authority_conflict",
        "historical_certificate": historical,
        "current_membership_authentic": membership_authentic(current_membership),
        "current_set_id": cp.get("set_id"),
        "current_set_epoch": cp.get("set_epoch"),
        "current_membership_digest": sha(cp),
        "current_threshold": cp.get("threshold"),
        "same_current_set": same_current_set,
    }


def db(dsn):
    return psycopg.connect(dsn, autocommit=False, row_factory=dict_row)


def init(conn):
    conn.execute("CREATE TABLE IF NOT EXISTS wr_replica(region TEXT PRIMARY KEY, rule_id TEXT, rule_digest TEXT, status TEXT, generation INT)")
    conn.execute("CREATE TABLE IF NOT EXISTS wr_state(resource_id TEXT PRIMARY KEY, owner TEXT, fence INT, global_version INT, output_value INT)")
    conn.execute("CREATE TABLE IF NOT EXISTS wr_artifacts(resource_id TEXT PRIMARY KEY, artifact_digest TEXT, state TEXT DEFAULT 'READY', adopted_by TEXT, adopted_fence INT)")
    conn.commit()


def set_replica(conn, generation):
    rule = RULES["R1" if generation == 7 else "R2"]
    conn.execute("DELETE FROM wr_replica")
    conn.execute(
        "INSERT INTO wr_replica(region,rule_id,rule_digest,status,generation) VALUES('region-B',%s,%s,'ACTIVE',%s)",
        (rule["rule_id"], rule["digest"], generation),
    )
    conn.commit()


def reset_resource(conn, resource_id):
    conn.execute("DELETE FROM wr_artifacts WHERE resource_id=%s", (resource_id,))
    conn.execute("DELETE FROM wr_state WHERE resource_id=%s", (resource_id,))
    conn.execute("INSERT INTO wr_state VALUES(%s,'worker-B',2,101,30)", (resource_id,))
    artifact_digest = sha({"resource_id": resource_id, "artifact_id": "artifact-v1", "output_value": 30})
    conn.execute("INSERT INTO wr_artifacts(resource_id,artifact_digest) VALUES(%s,%s)", (resource_id, artifact_digest))
    conn.commit()
    return artifact_digest


def replica_matches(conn, head):
    replica = conn.execute("SELECT * FROM wr_replica WHERE region='region-B'").fetchone()
    hp = head.get("payload", {})
    checks = {
        "head_authentic": head_authentic(head),
        "replica_generation": replica is not None and replica["generation"] == hp.get("generation"),
        "replica_rule": replica is not None and replica["rule_id"] == hp.get("rule_id") and replica["rule_digest"] == hp.get("rule_digest"),
        "replica_active": replica is not None and replica["status"] == "ACTIVE",
    }
    return checks, dict(replica) if replica else None


def unsafe_verdict(conn, certificate, historical_membership, head):
    qc = validate_certificate(certificate, historical_membership)
    checks, replica = replica_matches(conn, head)
    binds_head = qc["head_digest"] == sha(head) and qc["generation"] == head.get("payload", {}).get("generation")
    accept = qc["valid"] and all(checks.values()) and binds_head
    return {
        "accept": accept,
        "reason": "historical_membership_quorum_authorized" if accept else "historical_quorum_or_head_conflict",
        "certificate": qc,
        "checks": {**checks, "quorum_binds_head": binds_head},
        "replica": replica,
    }


def safe_verdict(conn, certificate, historical_membership, current_membership, head):
    current = current_membership_check(certificate, historical_membership, current_membership)
    checks, replica = replica_matches(conn, head)
    qc = current["historical_certificate"]
    binds_head = qc["head_digest"] == sha(head) and qc["generation"] == head.get("payload", {}).get("generation")
    if not current["accept"]:
        reason = "witness_set_authority_conflict"
        accept = False
    else:
        accept = all(checks.values()) and binds_head
        reason = "current_membership_quorum_authorized" if accept else "current_quorum_or_head_conflict"
    return {
        "accept": accept,
        "reason": reason,
        "membership": current,
        "checks": {**checks, "quorum_binds_head": binds_head},
        "replica": replica,
    }


def adopt(conn, resource_id, verdict):
    if not verdict["accept"]:
        return {"updated_rows": 0, "reason": verdict["reason"]}
    cur = conn.execute(
        "UPDATE wr_artifacts a SET state='ADOPTED',adopted_by=s.owner,adopted_fence=s.fence FROM wr_state s WHERE a.resource_id=s.resource_id AND a.resource_id=%s AND a.state='READY' RETURNING a.resource_id",
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
    subprocess.run(
        ["docker", "run", "-d", "--name", CONTAINER, "-p", f"{port}:8080", "-v", f"{VOLUME}:/state", "-v", f"{SERVICE}:/app/external_service.py:ro", IMAGE, "python", "/app/external_service.py"],
        check=True,
        stdout=subprocess.DEVNULL,
    )
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
    state = conn.execute("SELECT * FROM wr_state WHERE resource_id=%s", (resource_id,)).fetchone()
    artifact = conn.execute("SELECT * FROM wr_artifacts WHERE resource_id=%s", (resource_id,)).fetchone()
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
    parser.add_argument("--out", default="benchmark-results/witness-set-rotation-v1.0")
    args = parser.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    dsn = os.environ.get("DATABASE_URL", "postgresql://resonance:resonance@127.0.0.1:5432/resonance")
    health = start_service()

    with db(dsn) as conn:
        init(conn)

        old_validation = validate_certificate(QC_OLD, M1)
        rotation_compare = current_membership_check(QC_OLD, M1, M2)

        set_replica(conn, 7)
        unsafe = run_case(conn, "unsafe-old-membership", unsafe_verdict(conn, QC_OLD, M1, H7), "unsafe-old-membership")

        set_replica(conn, 7)
        safe_old = run_case(conn, "safe-current-membership", safe_verdict(conn, QC_OLD, M1, M2, H7), "safe-current-membership")

        set_replica(conn, 9)
        safe_current = run_case(conn, "fresh-current-membership", safe_verdict(conn, QC_CURRENT, M2, M2, H9), "fresh-current-membership")

        checks = [
            {
                "id": "historical_quorum_remains_cryptographically_valid_after_rotation",
                "pass": old_validation["valid"] and membership_authentic(M1) and membership_authentic(M2) and M2["payload"]["set_epoch"] > M1["payload"]["set_epoch"],
                "points": 2,
                "evidence": {"old_certificate": old_validation, "M1": M1, "M2": M2},
            },
            {
                "id": "unsafe_verifier_accepts_old_membership_quorum_and_commits_one_effect",
                "pass": unsafe["verdict"]["accept"] and unsafe["adoption"]["updated_rows"] == 1 and unsafe["remote"].get("effect_count") == 1,
                "points": 2,
                "evidence": unsafe,
            },
            {
                "id": "current_membership_authority_exposes_epoch_and_digest_mismatch",
                "pass": not rotation_compare["accept"] and rotation_compare["reason"] == "witness_set_authority_conflict" and not rotation_compare["same_current_set"],
                "points": 2,
                "evidence": rotation_compare,
            },
            {
                "id": "safe_verifier_rejects_old_membership_quorum_before_consequence",
                "pass": not safe_old["verdict"]["accept"] and safe_old["verdict"]["reason"] == "witness_set_authority_conflict" and safe_old["adoption"]["updated_rows"] == 0 and safe_old["remote"].get("effect_count") == 0,
                "points": 2,
                "evidence": safe_old,
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
            "benchmark": "RESONANCE Witness-Set Rotation / Membership Epoch Confusion",
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
            "heads": {"H7": H7, "H9": H9},
            "certificates": {"QC_OLD": QC_OLD, "QC_CURRENT": QC_CURRENT},
            "checks": checks,
            "invariants": [
                "VALID QUORUM FOR AN OLD MEMBERSHIP DOES NOT IMPLY CURRENT QUORUM AUTHORITY.",
                "QUORUM CERTIFICATE MUST BIND WITNESS-SET IDENTITY, EPOCH, MEMBERSHIP DIGEST, THRESHOLD POLICY, ROUND, HEAD, AND DISTINCT SIGNERS.",
                "ADOPTION MUST RESOLVE CURRENT WITNESS-SET AUTHORITY AND REJECT SUPERSEDED MEMBERSHIP BEFORE CONSEQUENCE.",
                "MEMBERSHIP ROTATION REQUIRES FRESH CURRENT-SET QUORUM EVIDENCE; OLD MEMBERS REMAIN HISTORICAL EVIDENCE, NOT LIVE AUTHORITY.",
            ],
            "score": score,
            "max_score": 10,
            "classification": "Witness-set rotation protocol passes" if score == 10 else "Witness-set rotation protocol incomplete",
            "external_safety_certification": False,
            "vulnerability_claim": False,
        }

    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    md = [
        "# RESONANCE Witness-Set Rotation / Membership Epoch Confusion v1.0",
        "",
        f"**Score:** {score}/10",
        "",
        f"**Classification:** {result['classification']}",
        "",
    ]
    for check in checks:
        md.append(f"- {'PASS' if check['pass'] else 'FAIL'} — {check['id']} ({check['points']}/2)")
    md += ["", "> VALID QUORUM FOR AN OLD MEMBERSHIP ≠ CURRENT QUORUM AUTHORITY.", ""]
    (out / "RESULT.md").write_text("\n".join(md))
    print(json.dumps(result, indent=2, sort_keys=True))
    if score != 10:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
