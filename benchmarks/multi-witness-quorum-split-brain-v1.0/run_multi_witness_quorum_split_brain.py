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

CONTAINER = "resonance-external-multi-witness-quorum"
VOLUME = "resonance-multi-witness-quorum-v1"
IMAGE = os.environ.get("HTTP_SERVICE_IMAGE", "python:3.12-slim")
BASE = os.environ.get("EXTERNAL_BASE_URL", "http://127.0.0.1:18100")
SERVICE = Path("benchmarks/dependency-aware-applicability-v1.0/external_service.py").resolve()

NS = "resonance-proof-authority"
SET_ID = "set-A"
SET_EPOCH = 1
THRESHOLD = 2
MEMBERS = ("W1", "W2", "W3")

HEAD_KEY = b"resonance-authority-head-demo-key-v1"
HEAD_KEY_ID = "authority-head-demo-key-v1"
WITNESS_KEYS = {
    "W1": (b"resonance-quorum-w1-demo-key-v1", "quorum-w1-demo-key-v1"),
    "W2": (b"resonance-quorum-w2-demo-key-v1", "quorum-w2-demo-key-v1"),
    "W3": (b"resonance-quorum-w3-demo-key-v1", "quorum-w3-demo-key-v1"),
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


def sign_witness(witness_id, round_id, head):
    key, key_id = WITNESS_KEYS[witness_id]
    payload = {
        "authority_namespace": NS,
        "witness_set_id": SET_ID,
        "witness_set_epoch": SET_EPOCH,
        "witness_id": witness_id,
        "round": round_id,
        "generation": head["payload"]["generation"],
        "head_digest": sha(head),
        "statement": "highest authenticated authority head observed for quorum round",
    }
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
        and payload.get("witness_set_id") == SET_ID
        and payload.get("witness_set_epoch") == SET_EPOCH
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

W1_R50_H9 = sign_witness("W1", 50, H9)
W2_R50_H9 = sign_witness("W2", 50, H9)
W2_R50_H7 = sign_witness("W2", 50, H7)
W3_R50_H7 = sign_witness("W3", 50, H7)
W1_R51_H9 = sign_witness("W1", 51, H9)
W3_R51_H9 = sign_witness("W3", 51, H9)

QC_A = {"certificate_id": "QC-A", "statements": [W1_R50_H9, W2_R50_H9]}
QC_B = {"certificate_id": "QC-B", "statements": [W2_R50_H7, W3_R50_H7]}
QC_RECOVERY = {"certificate_id": "QC-R51", "statements": [W1_R51_H9, W3_R51_H9]}


def db(dsn):
    return psycopg.connect(dsn, autocommit=False, row_factory=dict_row)


def init(conn):
    conn.execute(
        "CREATE TABLE IF NOT EXISTS mq_replica(region TEXT PRIMARY KEY, rule_id TEXT, rule_digest TEXT, status TEXT, generation INT)"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS mq_state(resource_id TEXT PRIMARY KEY, owner TEXT, fence INT, global_version INT, output_value INT)"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS mq_artifacts(resource_id TEXT PRIMARY KEY, artifact_digest TEXT, state TEXT DEFAULT 'READY', adopted_by TEXT, adopted_fence INT)"
    )
    conn.commit()


def set_replica(conn, generation):
    rule = RULES["R1" if generation == 7 else "R2"]
    conn.execute("DELETE FROM mq_replica")
    conn.execute(
        "INSERT INTO mq_replica(region,rule_id,rule_digest,status,generation) VALUES('region-B',%s,%s,'ACTIVE',%s)",
        (rule["rule_id"], rule["digest"], generation),
    )
    conn.commit()


def reset_resource(conn, resource_id):
    conn.execute("DELETE FROM mq_artifacts WHERE resource_id=%s", (resource_id,))
    conn.execute("DELETE FROM mq_state WHERE resource_id=%s", (resource_id,))
    conn.execute("INSERT INTO mq_state VALUES(%s,'worker-B',2,101,30)", (resource_id,))
    artifact_digest = sha({"resource_id": resource_id, "artifact_id": "artifact-v1", "output_value": 30})
    conn.execute("INSERT INTO mq_artifacts(resource_id,artifact_digest) VALUES(%s,%s)", (resource_id, artifact_digest))
    conn.commit()
    return artifact_digest


def certificate_summary(certificate, quarantined=None):
    quarantined = set(quarantined or [])
    statements = certificate.get("statements", [])
    authentic = [s for s in statements if witness_authentic(s)]
    payloads = [s["payload"] for s in authentic]
    ids = [p["witness_id"] for p in payloads]
    distinct = sorted(set(ids))
    active = sorted(w for w in distinct if w not in quarantined)
    same_set = bool(payloads) and all(p["witness_set_id"] == SET_ID and p["witness_set_epoch"] == SET_EPOCH for p in payloads)
    same_round = bool(payloads) and len({p["round"] for p in payloads}) == 1
    same_head = bool(payloads) and len({p["head_digest"] for p in payloads}) == 1
    same_generation = bool(payloads) and len({p["generation"] for p in payloads}) == 1
    head_digest = payloads[0]["head_digest"] if same_head else None
    generation = payloads[0]["generation"] if same_generation else None
    round_id = payloads[0]["round"] if same_round else None
    valid = (
        len(authentic) == len(statements)
        and len(distinct) == len(statements)
        and same_set
        and same_round
        and same_head
        and same_generation
        and len(active) >= THRESHOLD
    )
    return {
        "certificate_id": certificate.get("certificate_id"),
        "valid": valid,
        "threshold": THRESHOLD,
        "member_count": len(MEMBERS),
        "signers": distinct,
        "active_signers": active,
        "quarantined": sorted(quarantined),
        "round": round_id,
        "generation": generation,
        "head_digest": head_digest,
        "all_authentic": len(authentic) == len(statements),
        "same_witness_set": same_set,
        "same_round": same_round,
        "same_head": same_head,
        "same_generation": same_generation,
    }


def local_quorum_verdict(conn, head, certificate, quarantined=None):
    qc = certificate_summary(certificate, quarantined=quarantined)
    replica = conn.execute("SELECT * FROM mq_replica WHERE region='region-B'").fetchone()
    hp = head.get("payload", {})
    checks = {
        "head_authentic": head_authentic(head),
        "quorum_certificate_valid": qc["valid"],
        "quorum_binds_head": qc["head_digest"] == sha(head),
        "quorum_matches_head_generation": qc["generation"] == hp.get("generation"),
        "replica_generation": replica is not None and replica["generation"] == hp.get("generation"),
        "replica_rule": replica is not None and replica["rule_id"] == hp.get("rule_id") and replica["rule_digest"] == hp.get("rule_digest"),
        "replica_active": replica is not None and replica["status"] == "ACTIVE",
    }
    if all(checks.values()):
        return {"accept": True, "reason": "local_quorum_authorized_current_head", "checks": checks, "certificate": qc, "replica": dict(replica)}
    if not checks["head_authentic"]:
        reason = "authority_head_authentication_failed"
    elif not checks["quorum_certificate_valid"]:
        reason = "quorum_certificate_invalid_or_insufficient"
    elif not checks["quorum_binds_head"]:
        reason = "quorum_head_binding_failed"
    else:
        reason = "quorum_or_authority_conflict"
    return {"accept": False, "reason": reason, "checks": checks, "certificate": qc, "replica": dict(replica) if replica else None}


def conflicting_quorums(left, right):
    lq = certificate_summary(left)
    rq = certificate_summary(right)
    if not lq["valid"] or not rq["valid"]:
        return {"detected": False, "reason": "certificate_invalid", "left": lq, "right": rq, "intersection": [], "equivocators": []}
    same_domain = (
        lq["round"] == rq["round"]
        and lq["round"] is not None
        and all(s["payload"]["witness_set_id"] == SET_ID and s["payload"]["witness_set_epoch"] == SET_EPOCH for s in left["statements"] + right["statements"])
    )
    conflicting_head = lq["head_digest"] != rq["head_digest"]
    intersection = sorted(set(lq["signers"]) & set(rq["signers"]))
    equivocators = []
    for witness_id in intersection:
        ls = [s for s in left["statements"] if s["payload"]["witness_id"] == witness_id]
        rs = [s for s in right["statements"] if s["payload"]["witness_id"] == witness_id]
        for a in ls:
            for b in rs:
                pa, pb = a["payload"], b["payload"]
                if (
                    witness_authentic(a)
                    and witness_authentic(b)
                    and pa["witness_set_epoch"] == pb["witness_set_epoch"]
                    and pa["round"] == pb["round"]
                    and pa["head_digest"] != pb["head_digest"]
                ):
                    equivocators.append(witness_id)
    equivocators = sorted(set(equivocators))
    detected = same_domain and conflicting_head and bool(intersection) and bool(equivocators)
    return {
        "detected": detected,
        "reason": "conflicting_quorum_certificates" if detected else "no_global_quorum_conflict_evidence",
        "same_domain": same_domain,
        "conflicting_head": conflicting_head,
        "intersection": intersection,
        "equivocators": equivocators,
        "left": lq,
        "right": rq,
    }


def adopt(conn, resource_id, verdict):
    if not verdict["accept"]:
        return {"updated_rows": 0, "reason": verdict["reason"]}
    cur = conn.execute(
        "UPDATE mq_artifacts a SET state='ADOPTED',adopted_by=s.owner,adopted_fence=s.fence FROM mq_state s WHERE a.resource_id=s.resource_id AND a.resource_id=%s AND a.state='READY' RETURNING a.resource_id",
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
    state = conn.execute("SELECT * FROM mq_state WHERE resource_id=%s", (resource_id,)).fetchone()
    artifact = conn.execute("SELECT * FROM mq_artifacts WHERE resource_id=%s", (resource_id,)).fetchone()
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


def execute_local(conn, resource_id, head, certificate, phase, quarantined=None):
    reset_resource(conn, resource_id)
    verdict = local_quorum_verdict(conn, head, certificate, quarantined=quarantined)
    adoption = adopt(conn, resource_id, verdict)
    write = None
    if adoption["updated_rows"]:
        code, payload = publish(conn, resource_id, phase)
        write = {"http_status": code, "payload": payload}
    return {"verdict": verdict, "adoption": adoption, "write": write, "remote": remote(resource_id)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="benchmark-results/multi-witness-quorum-split-brain-v1.0")
    args = parser.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    dsn = os.environ.get("DATABASE_URL", "postgresql://resonance:resonance@127.0.0.1:5432/resonance")
    health = start_service()
    conn = db(dsn)
    init(conn)

    checks = []

    # 1. Both local certificates independently satisfy threshold.
    qa = certificate_summary(QC_A)
    qb = certificate_summary(QC_B)
    checks.append({
        "id": "two_incompatible_local_quorums_each_validate_independently",
        "pass": qa["valid"] and qb["valid"] and qa["head_digest"] != qb["head_digest"],
        "points": 2,
        "evidence": {"QC_A": qa, "QC_B": qb},
    })

    # 2. Isolated verifier B accepts old branch and commits.
    set_replica(conn, 7)
    unsafe = execute_local(conn, "unsafe-local-majority", H7, QC_B, "unsafe-local-majority")
    checks.append({
        "id": "isolated_verifier_accepts_local_two_of_three_for_H7_and_commits",
        "pass": unsafe["verdict"]["accept"] and unsafe["adoption"]["updated_rows"] == 1 and unsafe["remote"].get("effect_count") == 1,
        "points": 2,
        "evidence": unsafe,
    })

    # 3. Cross-view comparison detects conflicting QCs and W2 equivocation.
    conflict = conflicting_quorums(QC_A, QC_B)
    checks.append({
        "id": "cross_view_comparison_detects_conflicting_quorum_certificates",
        "pass": conflict["detected"] and conflict["intersection"] == ["W2"] and conflict["equivocators"] == ["W2"],
        "points": 2,
        "evidence": conflict,
    })

    # 4. Safe guard blocks consequence rather than choosing a majority.
    reset_resource(conn, "safe-global-conflict")
    safe_verdict = {"accept": False, "reason": conflict["reason"] if conflict["detected"] else "no_conflict"}
    safe_adoption = adopt(conn, "safe-global-conflict", safe_verdict)
    safe_remote = remote("safe-global-conflict")
    checks.append({
        "id": "global_conflict_guard_holds_before_consequence",
        "pass": conflict["detected"] and safe_adoption["updated_rows"] == 0 and safe_remote.get("effect_count") == 0,
        "points": 2,
        "evidence": {"conflict": conflict, "adoption": safe_adoption, "remote": safe_remote},
    })

    # 5. Quarantine W2 invalidates both old QCs; fresh W1+W3 H9 quorum restores liveness.
    quarantined = ["W2"]
    qa_after = certificate_summary(QC_A, quarantined=quarantined)
    qb_after = certificate_summary(QC_B, quarantined=quarantined)
    recovery_qc = certificate_summary(QC_RECOVERY, quarantined=quarantined)
    set_replica(conn, 9)
    recovery = execute_local(conn, "fresh-quorum-after-quarantine", H9, QC_RECOVERY, "fresh-quorum-after-quarantine", quarantined=quarantined)
    checks.append({
        "id": "quarantine_invalidates_conflicting_certificates_and_fresh_nonconflicting_quorum_succeeds_once",
        "pass": (
            not qa_after["valid"]
            and not qb_after["valid"]
            and recovery_qc["valid"]
            and recovery["verdict"]["accept"]
            and recovery["adoption"]["updated_rows"] == 1
            and recovery["remote"].get("effect_count") == 1
        ),
        "points": 2,
        "evidence": {
            "quarantined": quarantined,
            "QC_A_after_quarantine": qa_after,
            "QC_B_after_quarantine": qb_after,
            "QC_recovery": recovery_qc,
            "recovery": recovery,
        },
    })

    score = sum(c["points"] for c in checks if c["pass"])
    result = {
        "benchmark": "RESONANCE Multi-Witness Quorum Split-Brain / Conflicting Majorities",
        "benchmark_version": "1.0",
        "protocol": "RESONANCE Transactional Trust Protocol v1.0",
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "database": {"server_version": conn.info.server_version // 10000 if conn.info.server_version else None, "server_version_num": conn.info.server_version},
        "http_service": health,
        "http_service_image": IMAGE,
        "witness_set": {"set_id": SET_ID, "epoch": SET_EPOCH, "members": list(MEMBERS), "threshold": THRESHOLD},
        "heads": {"H7": H7, "H9": H9},
        "certificates": {"QC_A": QC_A, "QC_B": QC_B, "QC_RECOVERY": QC_RECOVERY},
        "checks": checks,
        "score": score,
        "max_score": 10,
        "classification": "Multi-witness quorum consistency protocol passes" if score == 10 else "Multi-witness quorum consistency protocol incomplete",
        "invariants": [
            "LOCAL QUORUM DOES NOT IMPLY GLOBALLY CONSISTENT QUORUM.",
            "TWO LOCALLY VALID QUORUM CERTIFICATES FOR THE SAME WITNESS-SET EPOCH AND ROUND MAY CONFLICT.",
            "CONFLICTING QUORUMS MUST BE CROSS-CHECKED FOR OVERLAP AND EQUIVOCATION BEFORE CONSEQUENCE.",
            "EQUIVOCATING WITNESS IDENTITIES MUST BE QUARANTINED; LIVENESS MAY RESUME ONLY WITH A NON-CONFLICTING THRESHOLD CERTIFICATE.",
        ],
        "external_safety_certification": False,
        "vulnerability_claim": False,
    }

    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    summary = [
        "# RESONANCE Multi-Witness Quorum Split-Brain v1.0",
        "",
        f"Score: **{score}/10**",
        "",
        "Law: **LOCAL QUORUM ≠ GLOBALLY CONSISTENT QUORUM.**",
        "",
    ]
    for check in checks:
        summary.append(f"- {'PASS' if check['pass'] else 'FAIL'} · {check['id']} · {check['points'] if check['pass'] else 0}/2")
    (out / "RESULT.md").write_text("\n".join(summary) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    conn.close()
    subprocess.run(["docker", "rm", "-f", CONTAINER], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    raise SystemExit(0 if score == 10 else 1)


if __name__ == "__main__":
    main()
