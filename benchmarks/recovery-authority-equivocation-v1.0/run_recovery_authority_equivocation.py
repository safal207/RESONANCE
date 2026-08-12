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

CONTAINER = "resonance-external-recovery-authority-equivocation"
VOLUME = "resonance-recovery-authority-equivocation-v1"
IMAGE = os.environ.get("HTTP_SERVICE_IMAGE", "python:3.12-slim")
BASE = os.environ.get("EXTERNAL_BASE_URL", "http://127.0.0.1:18101")
SERVICE = Path("benchmarks/dependency-aware-applicability-v1.0/external_service.py").resolve()

AUTHORITY_NS = "resonance-proof-authority"
MEMBERSHIP_NS = "resonance-witness-membership"
HEAD_KEY = b"resonance-authority-head-demo-key-v1"
HEAD_KEY_ID = "authority-head-demo-key-v1"
RECOVERY_KEY = b"resonance-membership-recovery-authority-demo-key-v1"
RECOVERY_KEY_ID = "membership-recovery-authority-demo-key-v1"
GOVERNANCE_KEY = b"resonance-membership-governance-resolution-demo-key-v1"
GOVERNANCE_KEY_ID = "membership-governance-resolution-demo-key-v1"
WITNESS_KEYS = {
    f"W{i}": (f"resonance-recovery-equivocation-w{i}-demo-key-v1".encode(), f"recovery-equivocation-w{i}-demo-key-v1")
    for i in range(1, 19)
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


def sign_recovery(payload):
    return sign(RECOVERY_KEY, RECOVERY_KEY_ID, payload)


def recovery_authentic(record):
    return authentic(record, RECOVERY_KEY, RECOVERY_KEY_ID, "membership_namespace", MEMBERSHIP_NS)


def sign_governance(payload):
    return sign(GOVERNANCE_KEY, GOVERNANCE_KEY_ID, payload)


def governance_authentic(record):
    return authentic(record, GOVERNANCE_KEY, GOVERNANCE_KEY_ID, "membership_namespace", MEMBERSHIP_NS)


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
H9 = sign_head({"authority_namespace": AUTHORITY_NS, "generation": 9, "rule_id": RULE["rule_id"], "rule_digest": RULE["digest"], "status": "ACTIVE"})

# Frozen disputed membership-authority fork from the prior layer. Only the digests are needed here.
M2_A_DIGEST = "sha256:aa0ad1f938ebde6911b5678bd40aaf0df1f2294c8925e8658b088f2c70557402"
M2_B_DIGEST = "sha256:b1586f4db5d001f30c64587bfdc960b625748d55048d30b94f350ddeebeca24c"
DISPUTED = sorted([M2_A_DIGEST, M2_B_DIGEST])

R3_A = sign_recovery({
    "membership_namespace": MEMBERSHIP_NS,
    "record_type": "recovery-resolution",
    "set_id": "set-D",
    "set_epoch": 3,
    "members": ["W10", "W11", "W12"],
    "threshold": 2,
    "issued_for_generation": 9,
    "resolves_membership_equivocation_digests": DISPUTED,
    "predecessor_membership_digests": DISPUTED,
    "recovery_reason": "membership_authority_same_epoch_equivocation",
})
R3_B = sign_recovery({
    "membership_namespace": MEMBERSHIP_NS,
    "record_type": "recovery-resolution",
    "set_id": "set-E",
    "set_epoch": 3,
    "members": ["W13", "W14", "W15"],
    "threshold": 2,
    "issued_for_generation": 9,
    "resolves_membership_equivocation_digests": DISPUTED,
    "predecessor_membership_digests": DISPUTED,
    "recovery_reason": "membership_authority_same_epoch_equivocation",
})
R3_A_DIGEST = sha(R3_A["payload"])
R3_B_DIGEST = sha(R3_B["payload"])

R4 = sign_governance({
    "membership_namespace": MEMBERSHIP_NS,
    "record_type": "governance-recovery-resolution",
    "set_id": "set-F",
    "set_epoch": 4,
    "members": ["W16", "W17", "W18"],
    "threshold": 2,
    "issued_for_generation": 9,
    "predecessor_resolution_digests": sorted([R3_A_DIGEST, R3_B_DIGEST]),
    "resolves_recovery_equivocation_digests": sorted([R3_A_DIGEST, R3_B_DIGEST]),
    "recovery_reason": "recovery_authority_same_epoch_equivocation",
})


def statement(witness_id, membership, round_number):
    mp = membership["payload"]
    return sign_witness(witness_id, {
        "authority_namespace": AUTHORITY_NS,
        "witness_id": witness_id,
        "witness_set_id": mp["set_id"],
        "witness_set_epoch": mp["set_epoch"],
        "membership_digest": sha(mp),
        "round": round_number,
        "generation": 9,
        "head_digest": sha(H9),
    })


QC_A = {"certificate_id": "QC-recovery-epoch3-A", "statements": [statement("W10", R3_A, 90), statement("W11", R3_A, 90)]}
QC_B = {"certificate_id": "QC-recovery-epoch3-B", "statements": [statement("W13", R3_B, 90), statement("W14", R3_B, 90)]}
QC_FINAL = {"certificate_id": "QC-governance-epoch4", "statements": [statement("W16", R4, 91), statement("W17", R4, 91)]}


def record_authentic(record):
    return recovery_authentic(record) or governance_authentic(record)


def validate_certificate(certificate, membership):
    mp = membership.get("payload", {})
    statements = certificate.get("statements", [])
    payloads = [s.get("payload", {}) for s in statements]
    signers = [p.get("witness_id") for p in payloads]
    distinct = sorted(set(signers))
    membership_digest = sha(mp)
    same_set = bool(payloads) and all(
        p.get("witness_set_id") == mp.get("set_id")
        and p.get("witness_set_epoch") == mp.get("set_epoch")
        and p.get("membership_digest") == membership_digest
        for p in payloads
    )
    same_round = bool(payloads) and len({p.get("round") for p in payloads}) == 1
    same_head = bool(payloads) and len({p.get("head_digest") for p in payloads}) == 1
    same_generation = bool(payloads) and len({p.get("generation") for p in payloads}) == 1
    all_authentic = bool(statements) and all(witness_authentic(s) for s in statements)
    members_valid = all(s in mp.get("members", []) for s in distinct)
    threshold = int(mp.get("threshold", 0))
    valid = record_authentic(membership) and all_authentic and len(signers) == len(distinct) and members_valid and same_set and same_round and same_head and same_generation and len(distinct) >= threshold
    return {
        "valid": valid,
        "certificate_id": certificate.get("certificate_id"),
        "record_authentic": record_authentic(membership),
        "record_key_id": membership.get("key_id"),
        "set_id": mp.get("set_id"),
        "set_epoch": mp.get("set_epoch"),
        "membership_digest": membership_digest,
        "threshold": threshold,
        "signers": distinct,
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


def detect_recovery_equivocation(left, right):
    lp, rp = left.get("payload", {}), right.get("payload", {})
    left_digest, right_digest = sha(lp), sha(rp)
    same_authority = left.get("key_id") == right.get("key_id") == RECOVERY_KEY_ID
    same_namespace = lp.get("membership_namespace") == rp.get("membership_namespace") == MEMBERSHIP_NS
    same_epoch = lp.get("set_epoch") == rp.get("set_epoch")
    same_dispute = sorted(lp.get("resolves_membership_equivocation_digests", [])) == sorted(rp.get("resolves_membership_equivocation_digests", [])) == DISPUTED
    same_predecessors = sorted(lp.get("predecessor_membership_digests", [])) == sorted(rp.get("predecessor_membership_digests", [])) == DISPUTED
    left_authentic, right_authentic = recovery_authentic(left), recovery_authentic(right)
    different_digest = left_digest != right_digest
    equivocation = all([same_authority, same_namespace, same_epoch, same_dispute, same_predecessors, left_authentic, right_authentic, different_digest])
    return {
        "equivocation": equivocation,
        "reason": "recovery_authority_equivocation_detected" if equivocation else "no_recovery_equivocation",
        "same_authority": same_authority,
        "same_namespace": same_namespace,
        "same_epoch": same_epoch,
        "same_dispute_set": same_dispute,
        "same_predecessors": same_predecessors,
        "left_authentic": left_authentic,
        "right_authentic": right_authentic,
        "left_set_id": lp.get("set_id"),
        "right_set_id": rp.get("set_id"),
        "recovery_epoch": lp.get("set_epoch") if same_epoch else None,
        "left_digest": left_digest,
        "right_digest": right_digest,
        "different_digest": different_digest,
        "issuer_key_id": left.get("key_id") if same_authority else None,
    }


def http_json(method, path, headers=None):
    req = urllib.request.Request(BASE + path, method=method, headers=headers or {})
    with urllib.request.urlopen(req, timeout=5) as r:
        return r.status, json.loads(r.read().decode())


def start_service():
    subprocess.run(["docker", "rm", "-f", CONTAINER], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["docker", "volume", "rm", "-f", VOLUME], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["docker", "volume", "create", VOLUME], check=True, stdout=subprocess.DEVNULL)
    subprocess.run([
        "docker", "run", "-d", "--name", CONTAINER, "-p", "18101:8080", "-v", f"{VOLUME}:/state", "-v", f"{SERVICE}:/app/external_service.py:ro", IMAGE,
        "python", "/app/external_service.py", "--port", "8080",
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
    conn.execute("CREATE TABLE IF NOT EXISTS rae_state(resource_id TEXT PRIMARY KEY, owner TEXT, fence INT, global_version INT, output_value INT)")
    conn.execute("CREATE TABLE IF NOT EXISTS rae_artifacts(resource_id TEXT PRIMARY KEY, artifact_digest TEXT, state TEXT DEFAULT 'READY', adopted_by TEXT, adopted_fence INT)")
    conn.commit()


def reset_resource(conn, resource_id):
    conn.execute("DELETE FROM rae_artifacts WHERE resource_id=%s", (resource_id,))
    conn.execute("DELETE FROM rae_state WHERE resource_id=%s", (resource_id,))
    conn.execute("INSERT INTO rae_state VALUES(%s,'worker-B',2,101,30)", (resource_id,))
    artifact_digest = sha({"resource_id": resource_id, "artifact_id": "artifact-v1", "output_value": 30})
    conn.execute("INSERT INTO rae_artifacts(resource_id,artifact_digest) VALUES(%s,%s)", (resource_id, artifact_digest))
    conn.commit()
    return artifact_digest


def isolated_verdict(certificate, membership):
    qc = validate_certificate(certificate, membership)
    binds_head = qc["head_digest"] == sha(H9) and qc["generation"] == 9
    accept = qc["valid"] and head_authentic(H9) and binds_head
    return {"accept": accept, "reason": "isolated_recovery_branch_authorized" if accept else "recovery_branch_or_head_conflict", "certificate": qc, "checks": {"head_authentic": head_authentic(H9), "quorum_binds_head": binds_head}}


def safe_verdict(certificate, membership, sibling):
    qc = validate_certificate(certificate, membership)
    conflict = detect_recovery_equivocation(membership, sibling)
    binds_head = qc["head_digest"] == sha(H9) and qc["generation"] == 9
    if conflict["equivocation"]:
        return {"accept": False, "reason": "recovery_authority_equivocation_detected", "certificate": qc, "equivocation": conflict, "checks": {"head_authentic": head_authentic(H9), "quorum_binds_head": binds_head}, "quarantine_issuer": RECOVERY_KEY_ID}
    accept = qc["valid"] and head_authentic(H9) and binds_head
    return {"accept": accept, "reason": "non_conflicting_recovery_authorized" if accept else "recovery_or_head_conflict", "certificate": qc, "equivocation": conflict, "checks": {"head_authentic": head_authentic(H9), "quorum_binds_head": binds_head}}


def final_recovery_verdict(certificate):
    qc = validate_certificate(certificate, R4)
    p = R4["payload"]
    binds_both = sorted(p.get("resolves_recovery_equivocation_digests", [])) == sorted([R3_A_DIGEST, R3_B_DIGEST]) and sorted(p.get("predecessor_resolution_digests", [])) == sorted([R3_A_DIGEST, R3_B_DIGEST])
    higher_epoch = p.get("set_epoch") == 4
    binds_head = qc["head_digest"] == sha(H9) and qc["generation"] == 9
    accept = governance_authentic(R4) and qc["valid"] and binds_both and higher_epoch and head_authentic(H9) and binds_head
    return {"accept": accept, "reason": "recovery_equivocation_resolved_by_governance_epoch4" if accept else "governance_recovery_conflict", "certificate": qc, "governance_record_authentic": governance_authentic(R4), "binds_all_conflicting_recovery_digests": binds_both, "higher_epoch": higher_epoch, "checks": {"head_authentic": head_authentic(H9), "quorum_binds_head": binds_head}}


def attempt(conn, resource_id, verdict, phase):
    artifact = conn.execute("SELECT * FROM rae_artifacts WHERE resource_id=%s", (resource_id,)).fetchone()
    if not verdict["accept"]:
        return {"verdict": verdict, "adoption": {"updated_rows": 0, "reason": verdict["reason"]}, "write": None, "remote": http_json("GET", f"/status/{resource_id}")[1]}
    cur = conn.execute("UPDATE rae_artifacts SET state='ADOPTED', adopted_by='worker-B', adopted_fence=2 WHERE resource_id=%s AND state='READY'", (resource_id,))
    conn.commit()
    if cur.rowcount != 1:
        return {"verdict": verdict, "adoption": {"updated_rows": cur.rowcount, "reason": "adoption_conflict"}, "write": None, "remote": http_json("GET", f"/status/{resource_id}")[1]}
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
    return {"verdict": verdict, "adoption": {"updated_rows": 1, "reason": "adopted"}, "write": {"http_status": status, "payload": payload}, "remote": http_json("GET", f"/status/{resource_id}")[1]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    dsn = os.environ["DATABASE_URL"]
    health = start_service()
    try:
        with db(dsn) as conn:
            init_db(conn)
            qa, qb = validate_certificate(QC_A, R3_A), validate_certificate(QC_B, R3_B)
            conflict = detect_recovery_equivocation(R3_A, R3_B)

            reset_resource(conn, "unsafe-recovery-fork")
            unsafe = attempt(conn, "unsafe-recovery-fork", isolated_verdict(QC_B, R3_B), "unsafe-recovery-fork")

            reset_resource(conn, "safe-recovery-branch-a")
            safe_a = attempt(conn, "safe-recovery-branch-a", safe_verdict(QC_A, R3_A, R3_B), "safe-recovery-branch-a")
            reset_resource(conn, "safe-recovery-branch-b")
            safe_b = attempt(conn, "safe-recovery-branch-b", safe_verdict(QC_B, R3_B, R3_A), "safe-recovery-branch-b")

            reset_resource(conn, "fresh-governance-recovery")
            final = attempt(conn, "fresh-governance-recovery", final_recovery_verdict(QC_FINAL), "fresh-governance-recovery")

        checks = [
            {"id": "same_recovery_authority_same_epoch_branches_are_both_authentic_and_locally_valid", "pass": recovery_authentic(R3_A) and recovery_authentic(R3_B) and qa["valid"] and qb["valid"], "points": 2, "evidence": {"R3_A": R3_A, "R3_B": R3_B, "QC_A": qa, "QC_B": qb}},
            {"id": "isolated_verifier_accepts_one_authentic_recovery_branch_and_commits_one_effect", "pass": unsafe["verdict"]["accept"] and unsafe["adoption"]["updated_rows"] == 1 and unsafe["write"]["http_status"] == 200 and unsafe["remote"]["effect_count"] == 1, "points": 2, "evidence": unsafe},
            {"id": "cross_view_comparison_detects_same_epoch_recovery_authority_equivocation", "pass": conflict["equivocation"], "points": 2, "evidence": conflict},
            {"id": "safe_verifier_holds_both_disputed_recovery_branches_before_consequence", "pass": (not safe_a["verdict"]["accept"]) and (not safe_b["verdict"]["accept"]) and safe_a["remote"]["effect_count"] == 0 and safe_b["remote"]["effect_count"] == 0, "points": 2, "evidence": {"branch_A": safe_a, "branch_B": safe_b}},
            {"id": "higher_epoch_governance_resolution_binds_both_recovery_forks_and_restores_liveness_once", "pass": final["verdict"]["accept"] and final["verdict"]["binds_all_conflicting_recovery_digests"] and final["adoption"]["updated_rows"] == 1 and final["write"]["http_status"] == 200 and final["remote"]["effect_count"] == 1, "points": 2, "evidence": final},
        ]
        score = sum(c["points"] for c in checks if c["pass"])
        result = {
            "protocol": "RESONANCE Transactional Trust Protocol v1.0",
            "benchmark": "RESONANCE Recovery Authority Equivocation / Conflicting Resolution Fork",
            "benchmark_version": "1.0",
            "executed_at": datetime.now(timezone.utc).isoformat(),
            "score": score,
            "max_score": 10,
            "classification": "Recovery authority equivocation protocol passes" if score == 10 else "Recovery authority equivocation protocol incomplete",
            "head": H9,
            "disputed_membership_digests": DISPUTED,
            "recovery_records": {"R3_A": R3_A, "R3_B": R3_B, "R4": R4},
            "recovery_equivocation": conflict,
            "certificates": {"QC_A": QC_A, "QC_B": QC_B, "QC_FINAL": QC_FINAL},
            "checks": checks,
            "http_service": health,
            "http_service_image": IMAGE,
            "database": {"server_version": 170006},
            "authentication_fixtures": {
                "authority_head": {"algorithm": "HMAC-SHA256", "key_id": HEAD_KEY_ID, "production_pki": False},
                "recovery_authority": {"algorithm": "HMAC-SHA256", "key_id": RECOVERY_KEY_ID, "production_pki": False},
                "governance_resolution_authority": {"algorithm": "HMAC-SHA256", "key_id": GOVERNANCE_KEY_ID, "production_pki": False},
            },
            "invariants": [
                "AUTHENTIC RECOVERY RECORD DOES NOT IMPLY UNIQUE RECOVERY HISTORY.",
                "SAME RECOVERY AUTHORITY + SAME RECOVERY EPOCH + SAME DISPUTE SET + DIFFERENT AUTHENTIC RESOLUTION DIGESTS = EQUIVOCATION EVIDENCE.",
                "RECOVERY-AUTHORITY EQUIVOCATION MUST HOLD ALL DISPUTED RESOLUTION BRANCHES AND QUARANTINE THE EQUIVOCATING RECOVERY ISSUER BEFORE CONSEQUENCE.",
                "RECOVERY FROM RECOVERY-EQUIVOCATION REQUIRES A HIGHER-EPOCH INDEPENDENT RESOLUTION THAT BINDS EVERY CONFLICTING RECOVERY DIGEST.",
            ],
            "external_safety_certification": False,
            "vulnerability_claim": False,
        }
        (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        md = [
            "# Recovery Authority Equivocation / Conflicting Resolution Fork v1.0",
            "",
            f"Score: **{score}/10**",
            "",
            f"Classification: **{result['classification']}**",
            "",
            "## Checks",
        ]
        for c in checks:
            md.append(f"- {'PASS' if c['pass'] else 'FAIL'} — {c['id']} ({c['points']}/2)")
        (out / "RESULT.md").write_text("\n".join(md) + "\n")
        print(json.dumps(result, indent=2, sort_keys=True))
        if score != 10:
            raise SystemExit(1)
    finally:
        stop_service()


if __name__ == "__main__":
    main()
