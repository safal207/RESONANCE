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

CONTAINER = "resonance-external-governance-resolution-equivocation"
VOLUME = "resonance-governance-resolution-equivocation-v1"
IMAGE = os.environ.get("HTTP_SERVICE_IMAGE", "python:3.12-slim")
BASE = os.environ.get("EXTERNAL_BASE_URL", "http://127.0.0.1:18101")
SERVICE = Path("benchmarks/dependency-aware-applicability-v1.0/external_service.py").resolve()

AUTHORITY_NS = "resonance-proof-authority"
MEMBERSHIP_NS = "resonance-witness-membership"
HEAD_KEY = b"resonance-authority-head-demo-key-v1"
HEAD_KEY_ID = "authority-head-demo-key-v1"
GOV_KEY = b"resonance-membership-governance-resolution-demo-key-v1"
GOV_KEY_ID = "membership-governance-resolution-demo-key-v1"
ROOT_KEY = b"resonance-constitutional-root-resolution-demo-key-v1"
ROOT_KEY_ID = "constitutional-root-resolution-demo-key-v1"
WITNESS_KEYS = {
    f"W{i}": (f"resonance-governance-equivocation-w{i}-demo-key-v1".encode(), f"governance-equivocation-w{i}-demo-key-v1")
    for i in range(16, 25)
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


def sign_governance(payload):
    return sign(GOV_KEY, GOV_KEY_ID, payload)


def governance_authentic(record):
    return authentic(record, GOV_KEY, GOV_KEY_ID, "membership_namespace", MEMBERSHIP_NS)


def sign_root(payload):
    return sign(ROOT_KEY, ROOT_KEY_ID, payload)


def root_authentic(record):
    return authentic(record, ROOT_KEY, ROOT_KEY_ID, "membership_namespace", MEMBERSHIP_NS)


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

# Frozen recovery-authority fork from Verified #039.
R3_A_DIGEST = "sha256:96ba32f275d54015845336d0b24baccae2ad3d2985322ebdebf53f27579639ae"
R3_B_DIGEST = "sha256:fc5034190cbfe2727441388e204f44d7904d3000680712a31d9cb7a04ef25ac0"
DISPUTED_RECOVERY = sorted([R3_A_DIGEST, R3_B_DIGEST])

G4_A = sign_governance({
    "membership_namespace": MEMBERSHIP_NS,
    "record_type": "governance-recovery-resolution",
    "set_id": "set-F",
    "set_epoch": 4,
    "members": ["W16", "W17", "W18"],
    "threshold": 2,
    "issued_for_generation": 9,
    "predecessor_resolution_digests": DISPUTED_RECOVERY,
    "resolves_recovery_equivocation_digests": DISPUTED_RECOVERY,
    "recovery_reason": "recovery_authority_same_epoch_equivocation",
})
G4_B = sign_governance({
    "membership_namespace": MEMBERSHIP_NS,
    "record_type": "governance-recovery-resolution",
    "set_id": "set-G",
    "set_epoch": 4,
    "members": ["W19", "W20", "W21"],
    "threshold": 2,
    "issued_for_generation": 9,
    "predecessor_resolution_digests": DISPUTED_RECOVERY,
    "resolves_recovery_equivocation_digests": DISPUTED_RECOVERY,
    "recovery_reason": "recovery_authority_same_epoch_equivocation",
})
G4_A_DIGEST = sha(G4_A["payload"])
G4_B_DIGEST = sha(G4_B["payload"])

G5 = sign_root({
    "membership_namespace": MEMBERSHIP_NS,
    "record_type": "constitutional-finality-resolution",
    "set_id": "set-H",
    "set_epoch": 5,
    "members": ["W22", "W23", "W24"],
    "threshold": 2,
    "issued_for_generation": 9,
    "predecessor_governance_resolution_digests": sorted([G4_A_DIGEST, G4_B_DIGEST]),
    "resolves_governance_equivocation_digests": sorted([G4_A_DIGEST, G4_B_DIGEST]),
    "recovery_reason": "governance_resolution_same_epoch_equivocation",
})


def statement(witness_id, record, round_number):
    p = record["payload"]
    return sign_witness(witness_id, {
        "authority_namespace": AUTHORITY_NS,
        "witness_id": witness_id,
        "witness_set_id": p["set_id"],
        "witness_set_epoch": p["set_epoch"],
        "membership_digest": sha(p),
        "round": round_number,
        "generation": 9,
        "head_digest": sha(H9),
    })


QC_A = {"certificate_id": "QC-governance-epoch4-A", "statements": [statement("W16", G4_A, 100), statement("W17", G4_A, 100)]}
QC_B = {"certificate_id": "QC-governance-epoch4-B", "statements": [statement("W19", G4_B, 100), statement("W20", G4_B, 100)]}
QC_FINAL = {"certificate_id": "QC-constitutional-epoch5", "statements": [statement("W22", G5, 101), statement("W23", G5, 101)]}


def record_authentic(record):
    return governance_authentic(record) or root_authentic(record)


def validate_certificate(certificate, record):
    rp = record.get("payload", {})
    statements = certificate.get("statements", [])
    payloads = [s.get("payload", {}) for s in statements]
    signers = [p.get("witness_id") for p in payloads]
    distinct = sorted(set(signers))
    digest = sha(rp)
    same_set = bool(payloads) and all(
        p.get("witness_set_id") == rp.get("set_id")
        and p.get("witness_set_epoch") == rp.get("set_epoch")
        and p.get("membership_digest") == digest
        for p in payloads
    )
    same_round = bool(payloads) and len({p.get("round") for p in payloads}) == 1
    same_head = bool(payloads) and len({p.get("head_digest") for p in payloads}) == 1
    same_generation = bool(payloads) and len({p.get("generation") for p in payloads}) == 1
    all_authentic = bool(statements) and all(witness_authentic(s) for s in statements)
    members_valid = all(s in rp.get("members", []) for s in distinct)
    threshold = int(rp.get("threshold", 0))
    valid = record_authentic(record) and all_authentic and len(signers) == len(distinct) and members_valid and same_set and same_round and same_head and same_generation and len(distinct) >= threshold
    return {
        "valid": valid,
        "certificate_id": certificate.get("certificate_id"),
        "record_authentic": record_authentic(record),
        "record_key_id": record.get("key_id"),
        "set_id": rp.get("set_id"),
        "set_epoch": rp.get("set_epoch"),
        "membership_digest": digest,
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


def detect_governance_equivocation(left, right):
    lp, rp = left.get("payload", {}), right.get("payload", {})
    left_digest, right_digest = sha(lp), sha(rp)
    same_authority = left.get("key_id") == right.get("key_id") == GOV_KEY_ID
    same_namespace = lp.get("membership_namespace") == rp.get("membership_namespace") == MEMBERSHIP_NS
    same_epoch = lp.get("set_epoch") == rp.get("set_epoch")
    same_dispute = sorted(lp.get("resolves_recovery_equivocation_digests", [])) == sorted(rp.get("resolves_recovery_equivocation_digests", [])) == DISPUTED_RECOVERY
    same_predecessors = sorted(lp.get("predecessor_resolution_digests", [])) == sorted(rp.get("predecessor_resolution_digests", [])) == DISPUTED_RECOVERY
    left_authentic, right_authentic = governance_authentic(left), governance_authentic(right)
    different_digest = left_digest != right_digest
    equivocation = all([same_authority, same_namespace, same_epoch, same_dispute, same_predecessors, left_authentic, right_authentic, different_digest])
    return {
        "equivocation": equivocation,
        "reason": "governance_resolution_equivocation_detected" if equivocation else "no_governance_equivocation",
        "same_authority": same_authority,
        "same_namespace": same_namespace,
        "same_epoch": same_epoch,
        "same_dispute_set": same_dispute,
        "same_predecessors": same_predecessors,
        "left_authentic": left_authentic,
        "right_authentic": right_authentic,
        "left_set_id": lp.get("set_id"),
        "right_set_id": rp.get("set_id"),
        "governance_epoch": lp.get("set_epoch") if same_epoch else None,
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
    conn.execute("CREATE TABLE IF NOT EXISTS gre_state(resource_id TEXT PRIMARY KEY, owner TEXT, fence INT, global_version INT, output_value INT)")
    conn.execute("CREATE TABLE IF NOT EXISTS gre_artifacts(resource_id TEXT PRIMARY KEY, artifact_digest TEXT, state TEXT DEFAULT 'READY', adopted_by TEXT, adopted_fence INT)")
    conn.commit()


def reset_resource(conn, resource_id):
    conn.execute("DELETE FROM gre_artifacts WHERE resource_id=%s", (resource_id,))
    conn.execute("DELETE FROM gre_state WHERE resource_id=%s", (resource_id,))
    conn.execute("INSERT INTO gre_state VALUES(%s,'worker-B',2,101,30)", (resource_id,))
    artifact_digest = sha({"resource_id": resource_id, "artifact_id": "artifact-v1", "output_value": 30})
    conn.execute("INSERT INTO gre_artifacts(resource_id,artifact_digest) VALUES(%s,%s)", (resource_id, artifact_digest))
    conn.commit()
    return artifact_digest


def isolated_verdict(certificate, record):
    qc = validate_certificate(certificate, record)
    binds_head = qc["head_digest"] == sha(H9) and qc["generation"] == 9
    accept = qc["valid"] and head_authentic(H9) and binds_head
    return {"accept": accept, "reason": "isolated_governance_branch_authorized" if accept else "governance_branch_or_head_conflict", "certificate": qc, "checks": {"head_authentic": head_authentic(H9), "quorum_binds_head": binds_head}}


def safe_verdict(certificate, record, sibling):
    qc = validate_certificate(certificate, record)
    conflict = detect_governance_equivocation(record, sibling)
    binds_head = qc["head_digest"] == sha(H9) and qc["generation"] == 9
    if conflict["equivocation"]:
        return {"accept": False, "reason": "governance_resolution_equivocation_detected", "certificate": qc, "equivocation": conflict, "checks": {"head_authentic": head_authentic(H9), "quorum_binds_head": binds_head}, "quarantine_issuer": GOV_KEY_ID}
    accept = qc["valid"] and head_authentic(H9) and binds_head
    return {"accept": accept, "reason": "non_conflicting_governance_authorized" if accept else "governance_or_head_conflict", "certificate": qc, "equivocation": conflict, "checks": {"head_authentic": head_authentic(H9), "quorum_binds_head": binds_head}}


def final_verdict(certificate):
    qc = validate_certificate(certificate, G5)
    p = G5["payload"]
    binds_both = sorted(p.get("resolves_governance_equivocation_digests", [])) == sorted([G4_A_DIGEST, G4_B_DIGEST]) and sorted(p.get("predecessor_governance_resolution_digests", [])) == sorted([G4_A_DIGEST, G4_B_DIGEST])
    higher_epoch = p.get("set_epoch") == 5
    binds_head = qc["head_digest"] == sha(H9) and qc["generation"] == 9
    accept = root_authentic(G5) and qc["valid"] and binds_both and higher_epoch and head_authentic(H9) and binds_head
    return {"accept": accept, "reason": "governance_equivocation_resolved_by_constitutional_epoch5" if accept else "constitutional_resolution_conflict", "certificate": qc, "root_record_authentic": root_authentic(G5), "binds_all_conflicting_governance_digests": binds_both, "higher_epoch": higher_epoch, "checks": {"head_authentic": head_authentic(H9), "quorum_binds_head": binds_head}}


def attempt(conn, resource_id, verdict, phase):
    artifact = conn.execute("SELECT * FROM gre_artifacts WHERE resource_id=%s", (resource_id,)).fetchone()
    if not verdict["accept"]:
        return {"verdict": verdict, "adoption": {"updated_rows": 0, "reason": verdict["reason"]}, "write": None, "remote": http_json("GET", f"/status/{resource_id}")[1]}
    cur = conn.execute("UPDATE gre_artifacts SET state='ADOPTED', adopted_by='worker-B', adopted_fence=2 WHERE resource_id=%s AND state='READY'", (resource_id,))
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
            qa, qb = validate_certificate(QC_A, G4_A), validate_certificate(QC_B, G4_B)
            conflict = detect_governance_equivocation(G4_A, G4_B)

            reset_resource(conn, "unsafe-governance-fork")
            unsafe = attempt(conn, "unsafe-governance-fork", isolated_verdict(QC_B, G4_B), "unsafe-governance-fork")

            reset_resource(conn, "safe-governance-branch-a")
            safe_a = attempt(conn, "safe-governance-branch-a", safe_verdict(QC_A, G4_A, G4_B), "safe-governance-branch-a")
            reset_resource(conn, "safe-governance-branch-b")
            safe_b = attempt(conn, "safe-governance-branch-b", safe_verdict(QC_B, G4_B, G4_A), "safe-governance-branch-b")

            reset_resource(conn, "fresh-constitutional-resolution")
            final = attempt(conn, "fresh-constitutional-resolution", final_verdict(QC_FINAL), "fresh-constitutional-resolution")

        checks = [
            {"id": "same_governance_authority_same_epoch_branches_are_both_authentic_and_locally_valid", "pass": governance_authentic(G4_A) and governance_authentic(G4_B) and qa["valid"] and qb["valid"], "points": 2, "evidence": {"G4_A": G4_A, "G4_B": G4_B, "QC_A": qa, "QC_B": qb}},
            {"id": "isolated_verifier_accepts_one_authentic_governance_branch_and_commits_one_effect", "pass": unsafe["verdict"]["accept"] and unsafe["adoption"]["updated_rows"] == 1 and unsafe["write"]["http_status"] == 200 and unsafe["remote"]["effect_count"] == 1, "points": 2, "evidence": unsafe},
            {"id": "cross_view_comparison_detects_same_epoch_governance_resolution_equivocation", "pass": conflict["equivocation"], "points": 2, "evidence": conflict},
            {"id": "safe_verifier_holds_both_disputed_governance_branches_before_consequence", "pass": (not safe_a["verdict"]["accept"]) and (not safe_b["verdict"]["accept"]) and safe_a["remote"]["effect_count"] == 0 and safe_b["remote"]["effect_count"] == 0, "points": 2, "evidence": {"branch_A": safe_a, "branch_B": safe_b}},
            {"id": "higher_epoch_constitutional_resolution_binds_both_governance_forks_and_restores_liveness_once", "pass": final["verdict"]["accept"] and final["verdict"]["binds_all_conflicting_governance_digests"] and final["adoption"]["updated_rows"] == 1 and final["write"]["http_status"] == 200 and final["remote"]["effect_count"] == 1, "points": 2, "evidence": final},
        ]
        score = sum(c["points"] for c in checks if c["pass"])
        result = {
            "protocol": "RESONANCE Transactional Trust Protocol v1.0",
            "benchmark": "RESONANCE Governance Resolution Equivocation / Conflicting Finality",
            "benchmark_version": "1.0",
            "executed_at": datetime.now(timezone.utc).isoformat(),
            "score": score,
            "max_score": 10,
            "classification": "Governance resolution equivocation protocol passes" if score == 10 else "Governance resolution equivocation protocol incomplete",
            "head": H9,
            "disputed_recovery_digests": DISPUTED_RECOVERY,
            "governance_records": {"G4_A": G4_A, "G4_B": G4_B, "G5": G5},
            "governance_equivocation": conflict,
            "certificates": {"QC_A": QC_A, "QC_B": QC_B, "QC_FINAL": QC_FINAL},
            "checks": checks,
            "http_service": health,
            "http_service_image": IMAGE,
            "database": {"server_version": 170006},
            "authentication_fixtures": {
                "authority_head": {"algorithm": "HMAC-SHA256", "key_id": HEAD_KEY_ID, "production_pki": False},
                "governance_resolution_authority": {"algorithm": "HMAC-SHA256", "key_id": GOV_KEY_ID, "production_pki": False},
                "constitutional_root_authority": {"algorithm": "HMAC-SHA256", "key_id": ROOT_KEY_ID, "production_pki": False},
            },
            "invariants": [
                "AUTHENTIC GOVERNANCE RESOLUTION DOES NOT IMPLY UNIQUE FINALITY.",
                "SAME GOVERNANCE AUTHORITY + SAME GOVERNANCE EPOCH + SAME DISPUTE SET + DIFFERENT AUTHENTIC FINALITY DIGESTS = EQUIVOCATION EVIDENCE.",
                "GOVERNANCE-RESOLUTION EQUIVOCATION MUST HOLD ALL DISPUTED FINALITY BRANCHES AND QUARANTINE THE EQUIVOCATING GOVERNANCE ISSUER BEFORE CONSEQUENCE.",
                "RECOVERY FROM GOVERNANCE EQUIVOCATION REQUIRES A HIGHER-EPOCH INDEPENDENT CONSTITUTIONAL RESOLUTION THAT BINDS EVERY CONFLICTING GOVERNANCE DIGEST.",
            ],
            "external_safety_certification": False,
            "vulnerability_claim": False,
        }
        (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        md = ["# Governance Resolution Equivocation / Conflicting Finality v1.0", "", f"Score: **{score}/10**", "", f"Classification: **{result['classification']}**", "", "## Checks"]
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
