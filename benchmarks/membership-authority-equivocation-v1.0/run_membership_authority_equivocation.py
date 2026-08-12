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

CONTAINER = "resonance-external-membership-authority-equivocation"
VOLUME = "resonance-membership-authority-equivocation-v1"
IMAGE = os.environ.get("HTTP_SERVICE_IMAGE", "python:3.12-slim")
BASE = os.environ.get("EXTERNAL_BASE_URL", "http://127.0.0.1:18101")
SERVICE = Path("benchmarks/dependency-aware-applicability-v1.0/external_service.py").resolve()

AUTHORITY_NS = "resonance-proof-authority"
MEMBERSHIP_NS = "resonance-witness-membership"
HEAD_KEY = b"resonance-authority-head-demo-key-v1"
HEAD_KEY_ID = "authority-head-demo-key-v1"
MEMBERSHIP_KEY = b"resonance-membership-authority-demo-key-v1"
MEMBERSHIP_KEY_ID = "membership-authority-demo-key-v1"
RECOVERY_KEY = b"resonance-membership-recovery-authority-demo-key-v1"
RECOVERY_KEY_ID = "membership-recovery-authority-demo-key-v1"
WITNESS_KEYS = {
    f"W{i}": (f"resonance-membership-equivocation-w{i}-demo-key-v1".encode(), f"membership-equivocation-w{i}-demo-key-v1")
    for i in range(1, 13)
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
        and payload.get("authority_namespace") == AUTHORITY_NS
        and hmac.compare_digest(head.get("mac", ""), mac(HEAD_KEY, payload))
    )


def sign_membership(payload, recovery=False):
    key = RECOVERY_KEY if recovery else MEMBERSHIP_KEY
    key_id = RECOVERY_KEY_ID if recovery else MEMBERSHIP_KEY_ID
    return {"alg": "HMAC-SHA256", "key_id": key_id, "payload": payload, "mac": mac(key, payload)}


def membership_authentic(record, allow_recovery=True):
    payload = record.get("payload", {})
    key_id = record.get("key_id")
    if key_id == MEMBERSHIP_KEY_ID:
        key = MEMBERSHIP_KEY
    elif allow_recovery and key_id == RECOVERY_KEY_ID:
        key = RECOVERY_KEY
    else:
        return False
    return (
        record.get("alg") == "HMAC-SHA256"
        and payload.get("membership_namespace") == MEMBERSHIP_NS
        and hmac.compare_digest(record.get("mac", ""), mac(key, payload))
    )


def primary_membership_authentic(record):
    return record.get("key_id") == MEMBERSHIP_KEY_ID and membership_authentic(record, allow_recovery=False)


def recovery_membership_authentic(record):
    payload = record.get("payload", {})
    return (
        record.get("alg") == "HMAC-SHA256"
        and record.get("key_id") == RECOVERY_KEY_ID
        and payload.get("membership_namespace") == MEMBERSHIP_NS
        and hmac.compare_digest(record.get("mac", ""), mac(RECOVERY_KEY, payload))
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
        and payload.get("authority_namespace") == AUTHORITY_NS
        and hmac.compare_digest(statement.get("mac", ""), mac(key, payload))
    )


RULE = {"rule_id": "cap-equivalence-r2", "generation": 9}
RULE["digest"] = sha(RULE)
H9 = sign_head(
    {
        "authority_namespace": AUTHORITY_NS,
        "generation": 9,
        "rule_id": RULE["rule_id"],
        "rule_digest": RULE["digest"],
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
        "predecessor_membership_digest": None,
    }
)
M1_DIGEST = sha(M1["payload"])

M2_A = sign_membership(
    {
        "membership_namespace": MEMBERSHIP_NS,
        "set_id": "set-B",
        "set_epoch": 2,
        "members": ["W4", "W5", "W6"],
        "threshold": 2,
        "issued_for_generation": 9,
        "predecessor_membership_digest": M1_DIGEST,
    }
)
M2_B = sign_membership(
    {
        "membership_namespace": MEMBERSHIP_NS,
        "set_id": "set-C",
        "set_epoch": 2,
        "members": ["W7", "W8", "W9"],
        "threshold": 2,
        "issued_for_generation": 9,
        "predecessor_membership_digest": M1_DIGEST,
    }
)
M2_A_DIGEST = sha(M2_A["payload"])
M2_B_DIGEST = sha(M2_B["payload"])

M3 = sign_membership(
    {
        "membership_namespace": MEMBERSHIP_NS,
        "set_id": "set-D",
        "set_epoch": 3,
        "members": ["W10", "W11", "W12"],
        "threshold": 2,
        "issued_for_generation": 9,
        "predecessor_membership_digests": sorted([M2_A_DIGEST, M2_B_DIGEST]),
        "resolves_equivocation_digests": sorted([M2_A_DIGEST, M2_B_DIGEST]),
        "recovery_reason": "membership_authority_same_epoch_equivocation",
    },
    recovery=True,
)


def statement(witness_id, membership, head, round_number):
    mp = membership["payload"]
    hp = head["payload"]
    return sign_witness(
        witness_id,
        {
            "authority_namespace": AUTHORITY_NS,
            "witness_id": witness_id,
            "witness_set_id": mp["set_id"],
            "witness_set_epoch": mp["set_epoch"],
            "membership_digest": sha(mp),
            "round": round_number,
            "generation": hp["generation"],
            "head_digest": sha(head),
        },
    )


QC_A = {"certificate_id": "QC-epoch2-branch-A", "statements": [statement("W4", M2_A, H9, 80), statement("W5", M2_A, H9, 80)]}
QC_B = {"certificate_id": "QC-epoch2-branch-B", "statements": [statement("W7", M2_B, H9, 80), statement("W8", M2_B, H9, 80)]}
QC_RECOVERY = {"certificate_id": "QC-epoch3-recovery", "statements": [statement("W10", M3, H9, 81), statement("W11", M3, H9, 81)]}


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
    authentic = bool(statements) and all(witness_authentic(s) for s in statements)
    members_valid = all(s in mp.get("members", []) for s in distinct)
    threshold = int(mp.get("threshold", 0))
    valid = (
        membership_authentic(membership)
        and authentic
        and len(signers) == len(distinct)
        and members_valid
        and same_set
        and same_round
        and same_head
        and same_generation
        and len(distinct) >= threshold
    )
    return {
        "valid": valid,
        "certificate_id": certificate.get("certificate_id"),
        "membership_authentic": membership_authentic(membership),
        "membership_key_id": membership.get("key_id"),
        "set_id": mp.get("set_id"),
        "set_epoch": mp.get("set_epoch"),
        "membership_digest": membership_digest,
        "threshold": threshold,
        "signers": distinct,
        "all_authentic": authentic,
        "members_valid": members_valid,
        "same_set": same_set,
        "same_round": same_round,
        "same_head": same_head,
        "same_generation": same_generation,
        "round": payloads[0].get("round") if payloads else None,
        "head_digest": payloads[0].get("head_digest") if payloads else None,
        "generation": payloads[0].get("generation") if payloads else None,
    }


def detect_membership_equivocation(left, right):
    lp = left.get("payload", {})
    rp = right.get("payload", {})
    same_authority = left.get("key_id") == right.get("key_id") == MEMBERSHIP_KEY_ID
    same_namespace = lp.get("membership_namespace") == rp.get("membership_namespace") == MEMBERSHIP_NS
    same_epoch = lp.get("set_epoch") == rp.get("set_epoch")
    same_predecessor = lp.get("predecessor_membership_digest") == rp.get("predecessor_membership_digest")
    left_authentic = primary_membership_authentic(left)
    right_authentic = primary_membership_authentic(right)
    left_digest = sha(lp)
    right_digest = sha(rp)
    different_digest = left_digest != right_digest
    equivocation = all([same_authority, same_namespace, same_epoch, same_predecessor, left_authentic, right_authentic, different_digest])
    return {
        "equivocation": equivocation,
        "reason": "membership_authority_equivocation_detected" if equivocation else "no_membership_equivocation",
        "same_authority": same_authority,
        "same_namespace": same_namespace,
        "same_epoch": same_epoch,
        "same_predecessor": same_predecessor,
        "left_authentic": left_authentic,
        "right_authentic": right_authentic,
        "left_set_id": lp.get("set_id"),
        "right_set_id": rp.get("set_id"),
        "set_epoch": lp.get("set_epoch") if same_epoch else None,
        "left_digest": left_digest,
        "right_digest": right_digest,
        "different_digest": different_digest,
        "issuer_key_id": left.get("key_id") if same_authority else None,
    }


def db(dsn):
    return psycopg.connect(dsn, autocommit=False, row_factory=dict_row)


def init(conn):
    conn.execute("CREATE TABLE IF NOT EXISTS mae_replica(region TEXT PRIMARY KEY, rule_id TEXT, rule_digest TEXT, status TEXT, generation INT)")
    conn.execute("CREATE TABLE IF NOT EXISTS mae_state(resource_id TEXT PRIMARY KEY, owner TEXT, fence INT, global_version INT, output_value INT)")
    conn.execute("CREATE TABLE IF NOT EXISTS mae_artifacts(resource_id TEXT PRIMARY KEY, artifact_digest TEXT, state TEXT DEFAULT 'READY', adopted_by TEXT, adopted_fence INT)")
    conn.execute("DELETE FROM mae_replica")
    conn.execute("INSERT INTO mae_replica VALUES('region-B',%s,%s,'ACTIVE',9)", (RULE["rule_id"], RULE["digest"]))
    conn.commit()


def reset_resource(conn, resource_id):
    conn.execute("DELETE FROM mae_artifacts WHERE resource_id=%s", (resource_id,))
    conn.execute("DELETE FROM mae_state WHERE resource_id=%s", (resource_id,))
    conn.execute("INSERT INTO mae_state VALUES(%s,'worker-B',2,101,30)", (resource_id,))
    artifact_digest = sha({"resource_id": resource_id, "artifact_id": "artifact-v1", "output_value": 30})
    conn.execute("INSERT INTO mae_artifacts(resource_id,artifact_digest) VALUES(%s,%s)", (resource_id, artifact_digest))
    conn.commit()
    return artifact_digest


def replica_matches(conn, head):
    replica = conn.execute("SELECT * FROM mae_replica WHERE region='region-B'").fetchone()
    hp = head.get("payload", {})
    checks = {
        "head_authentic": head_authentic(head),
        "replica_generation": replica is not None and replica["generation"] == hp.get("generation"),
        "replica_rule": replica is not None and replica["rule_id"] == hp.get("rule_id") and replica["rule_digest"] == hp.get("rule_digest"),
        "replica_active": replica is not None and replica["status"] == "ACTIVE",
    }
    return checks, dict(replica) if replica else None


def isolated_verdict(conn, certificate, membership, head):
    qc = validate_certificate(certificate, membership)
    checks, replica = replica_matches(conn, head)
    binds_head = qc["head_digest"] == sha(head) and qc["generation"] == head.get("payload", {}).get("generation")
    accept = qc["valid"] and all(checks.values()) and binds_head
    return {
        "accept": accept,
        "reason": "isolated_membership_branch_authorized" if accept else "isolated_branch_or_head_conflict",
        "certificate": qc,
        "checks": {**checks, "quorum_binds_head": binds_head},
        "replica": replica,
    }


def conflict_guard_verdict(conn, certificate, membership, other_membership, head):
    qc = validate_certificate(certificate, membership)
    checks, replica = replica_matches(conn, head)
    binds_head = qc["head_digest"] == sha(head) and qc["generation"] == head.get("payload", {}).get("generation")
    conflict = detect_membership_equivocation(membership, other_membership)
    if conflict["equivocation"]:
        accept = False
        reason = "membership_authority_equivocation_detected"
    else:
        accept = qc["valid"] and all(checks.values()) and binds_head
        reason = "non_conflicting_membership_authorized" if accept else "membership_or_head_conflict"
    return {
        "accept": accept,
        "reason": reason,
        "certificate": qc,
        "equivocation": conflict,
        "checks": {**checks, "quorum_binds_head": binds_head},
        "replica": replica,
        "quarantine_issuer": MEMBERSHIP_KEY_ID if conflict["equivocation"] else None,
    }


def recovery_verdict(conn, certificate, recovery_membership, disputed_left, disputed_right, head):
    qc = validate_certificate(certificate, recovery_membership)
    checks, replica = replica_matches(conn, head)
    rp = recovery_membership.get("payload", {})
    expected = sorted([sha(disputed_left["payload"]), sha(disputed_right["payload"])])
    binds_conflicts = sorted(rp.get("resolves_equivocation_digests", [])) == expected and sorted(rp.get("predecessor_membership_digests", [])) == expected
    higher_epoch = rp.get("set_epoch", 0) > max(disputed_left["payload"].get("set_epoch", 0), disputed_right["payload"].get("set_epoch", 0))
    binds_head = qc["head_digest"] == sha(head) and qc["generation"] == head.get("payload", {}).get("generation")
    recovery_auth = recovery_membership_authentic(recovery_membership)
    accept = recovery_auth and binds_conflicts and higher_epoch and qc["valid"] and all(checks.values()) and binds_head
    return {
        "accept": accept,
        "reason": "equivocation_resolved_by_fresh_recovery_membership" if accept else "recovery_membership_not_authorized",
        "certificate": qc,
        "recovery_membership_authentic": recovery_auth,
        "binds_all_conflicting_digests": binds_conflicts,
        "higher_epoch": higher_epoch,
        "checks": {**checks, "quorum_binds_head": binds_head},
        "replica": replica,
    }


def adopt(conn, resource_id, verdict):
    if not verdict["accept"]:
        return {"updated_rows": 0, "reason": verdict["reason"]}
    cur = conn.execute(
        "UPDATE mae_artifacts a SET state='ADOPTED',adopted_by=s.owner,adopted_fence=s.fence FROM mae_state s WHERE a.resource_id=s.resource_id AND a.resource_id=%s AND a.state='READY' RETURNING a.resource_id",
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
    state = conn.execute("SELECT * FROM mae_state WHERE resource_id=%s", (resource_id,)).fetchone()
    artifact = conn.execute("SELECT * FROM mae_artifacts WHERE resource_id=%s", (resource_id,)).fetchone()
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
    parser.add_argument("--out", default="benchmark-results/membership-authority-equivocation-v1.0")
    args = parser.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    dsn = os.environ.get("DATABASE_URL", "postgresql://resonance:resonance@127.0.0.1:5432/resonance")
    health = start_service()

    with db(dsn) as conn:
        init(conn)
        qc_a = validate_certificate(QC_A, M2_A)
        qc_b = validate_certificate(QC_B, M2_B)
        conflict = detect_membership_equivocation(M2_A, M2_B)

        unsafe = run_case(conn, "unsafe-membership-fork", isolated_verdict(conn, QC_B, M2_B, H9), "unsafe-membership-fork")
        safe_a = run_case(conn, "safe-branch-a-held", conflict_guard_verdict(conn, QC_A, M2_A, M2_B, H9), "safe-branch-a-held")
        safe_b = run_case(conn, "safe-branch-b-held", conflict_guard_verdict(conn, QC_B, M2_B, M2_A, H9), "safe-branch-b-held")
        recovery = run_case(conn, "fresh-recovery-membership", recovery_verdict(conn, QC_RECOVERY, M3, M2_A, M2_B, H9), "fresh-recovery-membership")

        checks = [
            {
                "id": "same_authority_same_epoch_membership_branches_are_both_authentic_and_locally_valid",
                "pass": primary_membership_authentic(M2_A) and primary_membership_authentic(M2_B) and qc_a["valid"] and qc_b["valid"] and M2_A["payload"]["set_epoch"] == M2_B["payload"]["set_epoch"] == 2 and M2_A_DIGEST != M2_B_DIGEST,
                "points": 2,
                "evidence": {"M2_A": M2_A, "M2_B": M2_B, "QC_A": qc_a, "QC_B": qc_b},
            },
            {
                "id": "isolated_verifier_accepts_one_authentic_fork_branch_and_commits_one_effect",
                "pass": unsafe["verdict"]["accept"] and unsafe["adoption"]["updated_rows"] == 1 and unsafe["remote"].get("effect_count") == 1,
                "points": 2,
                "evidence": unsafe,
            },
            {
                "id": "cross_view_comparison_detects_same_epoch_membership_authority_equivocation",
                "pass": conflict["equivocation"] and conflict["reason"] == "membership_authority_equivocation_detected" and conflict["same_authority"] and conflict["same_epoch"] and conflict["different_digest"],
                "points": 2,
                "evidence": conflict,
            },
            {
                "id": "safe_verifier_holds_both_disputed_membership_branches_before_consequence",
                "pass": (not safe_a["verdict"]["accept"]) and (not safe_b["verdict"]["accept"]) and safe_a["verdict"]["reason"] == "membership_authority_equivocation_detected" and safe_b["verdict"]["reason"] == "membership_authority_equivocation_detected" and safe_a["remote"].get("effect_count") == 0 and safe_b["remote"].get("effect_count") == 0,
                "points": 2,
                "evidence": {"branch_A": safe_a, "branch_B": safe_b},
            },
            {
                "id": "higher_epoch_recovery_membership_binds_both_conflicts_and_restores_liveness_once",
                "pass": recovery["verdict"]["accept"] and recovery["verdict"]["recovery_membership_authentic"] and recovery["verdict"]["binds_all_conflicting_digests"] and recovery["verdict"]["higher_epoch"] and recovery["adoption"]["updated_rows"] == 1 and recovery["remote"].get("effect_count") == 1,
                "points": 2,
                "evidence": recovery,
            },
        ]

        score = sum(c["points"] for c in checks if c["pass"])
        result = {
            "benchmark": "RESONANCE Membership Authority Equivocation / Same-Epoch Fork",
            "benchmark_version": "1.0",
            "protocol": "RESONANCE Transactional Trust Protocol v1.0",
            "executed_at": datetime.now(timezone.utc).isoformat(),
            "database": {"server_version": conn.info.server_version},
            "http_service_image": IMAGE,
            "http_service": health,
            "authentication_fixtures": {
                "authority_head": {"algorithm": "HMAC-SHA256", "key_id": HEAD_KEY_ID, "production_pki": False},
                "membership_authority": {"algorithm": "HMAC-SHA256", "key_id": MEMBERSHIP_KEY_ID, "production_pki": False},
                "recovery_authority": {"algorithm": "HMAC-SHA256", "key_id": RECOVERY_KEY_ID, "production_pki": False},
            },
            "memberships": {"M1": M1, "M2_A": M2_A, "M2_B": M2_B, "M3": M3},
            "head": H9,
            "certificates": {"QC_A": QC_A, "QC_B": QC_B, "QC_RECOVERY": QC_RECOVERY},
            "equivocation": conflict,
            "checks": checks,
            "invariants": [
                "SAME AUTHORITY + SAME MEMBERSHIP EPOCH + DIFFERENT AUTHENTIC MEMBERSHIP DIGESTS = EQUIVOCATION EVIDENCE.",
                "AUTHENTIC MEMBERSHIP RECORD DOES NOT IMPLY UNIQUE MEMBERSHIP HISTORY.",
                "MEMBERSHIP-AUTHORITY EQUIVOCATION MUST HOLD ALL DISPUTED BRANCHES AND QUARANTINE THE EQUIVOCATING ISSUER BEFORE CONSEQUENCE.",
                "RECOVERY REQUIRES A FRESH HIGHER-EPOCH MEMBERSHIP FROM NON-EQUIVOCATING AUTHORITY OR EXPLICIT GOVERNANCE RESOLUTION BINDING ALL CONFLICTING BRANCH DIGESTS.",
            ],
            "score": score,
            "max_score": 10,
            "classification": "Membership authority equivocation protocol passes" if score == 10 else "Membership authority equivocation protocol incomplete",
            "external_safety_certification": False,
            "vulnerability_claim": False,
        }

    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    md = [
        "# RESONANCE Membership Authority Equivocation / Same-Epoch Fork v1.0",
        "",
        f"**Score:** {score}/10",
        "",
        f"**Classification:** {result['classification']}",
        "",
    ]
    for check in checks:
        md.append(f"- {'PASS' if check['pass'] else 'FAIL'} — {check['id']} ({check['points']}/2)")
    md += ["", "> SAME AUTHORITY + SAME EPOCH + TWO AUTHENTIC MEMBERSHIPS = EQUIVOCATION EVIDENCE.", ""]
    (out / "RESULT.md").write_text("\n".join(md))
    print(json.dumps(result, indent=2, sort_keys=True))
    if score != 10:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
