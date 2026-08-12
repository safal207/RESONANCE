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

CONTAINER = "resonance-external-witness-equivocation"
VOLUME = "resonance-witness-equivocation-v1"
IMAGE = os.environ.get("HTTP_SERVICE_IMAGE", "python:3.12-slim")
BASE = os.environ.get("EXTERNAL_BASE_URL", "http://127.0.0.1:18099")
SERVICE = Path("benchmarks/dependency-aware-applicability-v1.0/external_service.py").resolve()

NS = "resonance-proof-authority"
HEAD_KEY = b"resonance-authority-head-demo-key-v1"
HEAD_KEY_ID = "authority-head-demo-key-v1"
WITNESS_KEYS = {
    "witness-A": (b"resonance-witness-a-demo-key-v1", "witness-a-demo-key-v1"),
    "witness-B": (b"resonance-witness-b-demo-key-v1", "witness-b-demo-key-v1"),
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

WA42 = sign_witness(
    "witness-A",
    {
        "authority_namespace": NS,
        "witness_id": "witness-A",
        "witness_seq": 42,
        "previous_statement_digest": None,
        "generation": 7,
        "head_digest": sha(H7),
        "statement": "highest authenticated authority head observed",
    },
)
WA43_GOOD = sign_witness(
    "witness-A",
    {
        "authority_namespace": NS,
        "witness_id": "witness-A",
        "witness_seq": 43,
        "previous_statement_digest": sha(WA42),
        "generation": 9,
        "head_digest": sha(H9),
        "statement": "highest authenticated authority head observed",
    },
)
WA43_FORK = sign_witness(
    "witness-A",
    {
        "authority_namespace": NS,
        "witness_id": "witness-A",
        "witness_seq": 43,
        "previous_statement_digest": sha(WA42),
        "generation": 7,
        "head_digest": sha(H7),
        "statement": "highest authenticated authority head observed",
    },
)
WB11 = sign_witness(
    "witness-B",
    {
        "authority_namespace": NS,
        "witness_id": "witness-B",
        "witness_seq": 11,
        "previous_statement_digest": None,
        "generation": 9,
        "head_digest": sha(H9),
        "statement": "highest authenticated authority head observed",
    },
)


def db(dsn):
    return psycopg.connect(dsn, autocommit=False, row_factory=dict_row)


def init(conn):
    conn.execute(
        "CREATE TABLE IF NOT EXISTS we_checkpoint(verifier_id TEXT PRIMARY KEY, generation INT, head_digest TEXT, source TEXT, updated_at TIMESTAMPTZ DEFAULT now())"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS we_replica(region TEXT PRIMARY KEY, rule_id TEXT, rule_digest TEXT, status TEXT, generation INT)"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS we_state(resource_id TEXT PRIMARY KEY, owner TEXT, fence INT, global_version INT, output_value INT)"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS we_artifacts(resource_id TEXT PRIMARY KEY, artifact_digest TEXT, state TEXT DEFAULT 'READY', adopted_by TEXT, adopted_fence INT)"
    )
    conn.commit()


def set_checkpoint(conn, generation, head, source):
    conn.execute(
        "INSERT INTO we_checkpoint(verifier_id,generation,head_digest,source) VALUES('verifier-B',%s,%s,%s) ON CONFLICT(verifier_id) DO UPDATE SET generation=GREATEST(we_checkpoint.generation,EXCLUDED.generation),head_digest=CASE WHEN EXCLUDED.generation>=we_checkpoint.generation THEN EXCLUDED.head_digest ELSE we_checkpoint.head_digest END,source=CASE WHEN EXCLUDED.generation>=we_checkpoint.generation THEN EXCLUDED.source ELSE we_checkpoint.source END,updated_at=now()",
        (generation, sha(head), source),
    )
    conn.commit()


def checkpoint(conn):
    row = conn.execute("SELECT verifier_id,generation,head_digest,source FROM we_checkpoint WHERE verifier_id='verifier-B'").fetchone()
    return dict(row) if row else {"verifier_id": "verifier-B", "generation": 0, "head_digest": None, "source": None}


def set_replica(conn, generation):
    rule = RULES["R1" if generation == 7 else "R2"]
    conn.execute("DELETE FROM we_replica")
    conn.execute(
        "INSERT INTO we_replica(region,rule_id,rule_digest,status,generation) VALUES('region-B',%s,%s,'ACTIVE',%s)",
        (rule["rule_id"], rule["digest"], generation),
    )
    conn.commit()


def reset_resource(conn, resource_id):
    conn.execute("DELETE FROM we_artifacts WHERE resource_id=%s", (resource_id,))
    conn.execute("DELETE FROM we_state WHERE resource_id=%s", (resource_id,))
    conn.execute("INSERT INTO we_state VALUES(%s,'worker-B',2,101,30)", (resource_id,))
    artifact_digest = sha({"resource_id": resource_id, "artifact_id": "artifact-v1", "output_value": 30})
    conn.execute("INSERT INTO we_artifacts(resource_id,artifact_digest) VALUES(%s,%s)", (resource_id, artifact_digest))
    conn.commit()
    return artifact_digest


def local_statement_verdict(conn, head, statement):
    cp = checkpoint(conn)
    replica = conn.execute("SELECT * FROM we_replica WHERE region='region-B'").fetchone()
    hp = head.get("payload", {})
    wp = statement.get("payload", {})
    checks = {
        "head_authentic": head_authentic(head),
        "witness_authentic": witness_authentic(statement),
        "witness_head_binding": wp.get("head_digest") == sha(head),
        "witness_not_below_local_checkpoint": wp.get("generation", -1) >= cp["generation"],
        "head_not_below_local_checkpoint": hp.get("generation", -1) >= cp["generation"],
        "witness_matches_head_generation": wp.get("generation") == hp.get("generation"),
        "replica_generation": replica is not None and replica["generation"] == hp.get("generation"),
        "replica_rule": replica is not None and replica["rule_id"] == hp.get("rule_id") and replica["rule_digest"] == hp.get("rule_digest"),
        "replica_active": replica is not None and replica["status"] == "ACTIVE",
    }
    if all(checks.values()):
        return {"accept": True, "reason": "witness_authorized_current_head", "checks": checks, "checkpoint": cp, "replica": dict(replica)}
    if not checks["head_authentic"]:
        reason = "authority_head_authentication_failed"
    elif not checks["witness_authentic"]:
        reason = "witness_authentication_failed"
    elif not checks["witness_head_binding"]:
        reason = "witness_head_binding_failed"
    elif not checks["head_not_below_local_checkpoint"]:
        reason = "authority_head_rollback_detected"
    else:
        reason = "witness_or_authority_conflict"
    return {"accept": False, "reason": reason, "checks": checks, "checkpoint": cp, "replica": dict(replica) if replica else None}


def witness_equivocation(left, right):
    lp = left.get("payload", {})
    rp = right.get("payload", {})
    authentic = witness_authentic(left) and witness_authentic(right)
    same_slot = (
        lp.get("witness_id") == rp.get("witness_id")
        and lp.get("witness_seq") == rp.get("witness_seq")
        and lp.get("previous_statement_digest") == rp.get("previous_statement_digest")
    )
    different_statements = sha(left) != sha(right)
    detected = authentic and same_slot and different_statements
    return {
        "detected": detected,
        "reason": "witness_equivocation_detected" if detected else "no_equivocation_evidence",
        "both_authentic": authentic,
        "same_witness_id": lp.get("witness_id") == rp.get("witness_id"),
        "same_witness_seq": lp.get("witness_seq") == rp.get("witness_seq"),
        "same_parent": lp.get("previous_statement_digest") == rp.get("previous_statement_digest"),
        "left_digest": sha(left),
        "right_digest": sha(right),
        "left_generation": lp.get("generation"),
        "right_generation": rp.get("generation"),
    }


def reconstruct_from_witness_b(conn):
    payload = WB11["payload"]
    if not witness_authentic(WB11):
        return {"reconstructed": False, "reason": "witness_b_authentication_failed", "checkpoint": checkpoint(conn)}
    if payload["head_digest"] != sha(H9):
        return {"reconstructed": False, "reason": "witness_b_head_binding_failed", "checkpoint": checkpoint(conn)}
    set_checkpoint(conn, payload["generation"], H9, "witness-B-after-witness-A-quarantine")
    return {"reconstructed": True, "reason": "checkpoint_reconstructed_from_independent_witness", "checkpoint": checkpoint(conn)}


def head_currentness(conn, head):
    cp = checkpoint(conn)
    auth = head_authentic(head)
    generation = head.get("payload", {}).get("generation", -1)
    if not auth:
        return {"accept": False, "reason": "authority_head_authentication_failed", "checkpoint": cp}
    if generation < cp["generation"]:
        return {"accept": False, "reason": "authority_head_rollback_detected", "checkpoint": cp}
    return {"accept": True, "reason": "authority_head_current", "checkpoint": cp}


def adopt(conn, resource_id, verdict):
    if not verdict["accept"]:
        return {"updated_rows": 0, "reason": verdict["reason"]}
    cur = conn.execute(
        "UPDATE we_artifacts a SET state='ADOPTED',adopted_by=s.owner,adopted_fence=s.fence FROM we_state s WHERE a.resource_id=s.resource_id AND a.resource_id=%s AND a.state='READY' RETURNING a.resource_id",
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
    state = conn.execute("SELECT * FROM we_state WHERE resource_id=%s", (resource_id,)).fetchone()
    artifact = conn.execute("SELECT * FROM we_artifacts WHERE resource_id=%s", (resource_id,)).fetchone()
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


def run_local(conn, resource_id, head, statement, phase):
    reset_resource(conn, resource_id)
    verdict = local_statement_verdict(conn, head, statement)
    adoption = adopt(conn, resource_id, verdict)
    write = None
    if adoption["updated_rows"]:
        code, payload = publish(conn, resource_id, phase)
        write = {"http_status": code, "payload": payload}
    return {
        "head": head,
        "witness": statement,
        "verdict": verdict,
        "adoption": adoption,
        "write": write,
        "remote": remote(resource_id),
    }


def run_gossip_guard(conn, resource_id):
    reset_resource(conn, resource_id)
    conflict = witness_equivocation(WA43_GOOD, WA43_FORK)
    verdict = {"accept": not conflict["detected"], "reason": conflict["reason"], "conflict": conflict}
    adoption = adopt(conn, resource_id, verdict)
    return {"conflict": conflict, "adoption": adoption, "remote": remote(resource_id), "quarantined_witness": "witness-A" if conflict["detected"] else None}


def check(check_id, ok, evidence):
    return {"id": check_id, "pass": bool(ok), "points": 2 if ok else 0, "evidence": evidence}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    service = start_service()
    conn = db(os.environ["DATABASE_URL"])
    init(conn)
    conn.execute("DELETE FROM we_checkpoint")
    conn.commit()
    set_checkpoint(conn, 7, H7, "WA42")
    set_replica(conn, 7)

    baseline = run_local(conn, "baseline-wa42", H7, WA42, "baseline-wa42")
    fork_evidence = witness_equivocation(WA43_GOOD, WA43_FORK)
    unsafe = run_local(conn, "unsafe-isolated-fork", H7, WA43_FORK, "unsafe-isolated-fork")
    guarded = run_gossip_guard(conn, "safe-gossip-guard")

    recovery = reconstruct_from_witness_b(conn)
    h7_after_recovery = head_currentness(conn, H7)
    set_replica(conn, 9)
    fresh = run_local(conn, "fresh-h9-after-witness-recovery", H9, WB11, "fresh-h9-after-witness-recovery")

    checks = [
        check(
            "baseline_witness_statement_authorizes_generation7_before_conflict",
            baseline["verdict"]["accept"] and baseline["adoption"]["updated_rows"] == 1 and baseline["write"]["http_status"] == 200 and baseline["remote"].get("effect_count") == 1,
            baseline,
        ),
        check(
            "same_witness_signs_two_authentic_conflicting_children_at_same_sequence",
            fork_evidence["detected"] and fork_evidence["both_authentic"] and fork_evidence["same_witness_seq"] and fork_evidence["same_parent"] and fork_evidence["left_generation"] == 9 and fork_evidence["right_generation"] == 7,
            {"WA43_good": WA43_GOOD, "WA43_fork": WA43_FORK, "equivocation": fork_evidence},
        ),
        check(
            "isolated_verifier_accepts_authentic_fork_and_commits_one_effect",
            unsafe["verdict"]["accept"] and unsafe["adoption"]["updated_rows"] == 1 and unsafe["write"]["http_status"] == 200 and unsafe["remote"].get("effect_count") == 1,
            unsafe,
        ),
        check(
            "gossip_detects_equivocation_and_quarantines_witness_before_consequence",
            guarded["conflict"]["detected"] and guarded["adoption"]["updated_rows"] == 0 and guarded["remote"].get("effect_count") == 0 and guarded["quarantined_witness"] == "witness-A",
            guarded,
        ),
        check(
            "independent_witness_reconstructs_generation9_then_h7_rejects_and_h9_succeeds_once",
            recovery["reconstructed"] and recovery["checkpoint"]["generation"] == 9 and h7_after_recovery["reason"] == "authority_head_rollback_detected" and fresh["verdict"]["accept"] and fresh["adoption"]["updated_rows"] == 1 and fresh["write"]["http_status"] == 200 and fresh["remote"].get("effect_count") == 1,
            {"recovery": recovery, "h7_after_recovery": h7_after_recovery, "fresh": fresh, "witness_B": WB11},
        ),
    ]

    result = {
        "benchmark": "RESONANCE Witness Rollback / Equivocation",
        "benchmark_version": "1.0",
        "protocol": "RESONANCE Transactional Trust Protocol v1.0",
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "database": {"server_version": conn.execute("SHOW server_version").fetchone()["server_version"]},
        "http_service": service,
        "http_service_image": IMAGE,
        "authentication_fixtures": {
            "authority_head": {"algorithm": "HMAC-SHA256", "key_id": HEAD_KEY_ID, "production_pki": False},
            "witness_A": {"algorithm": "HMAC-SHA256", "key_id": WITNESS_KEYS["witness-A"][1], "production_pki": False},
            "witness_B": {"algorithm": "HMAC-SHA256", "key_id": WITNESS_KEYS["witness-B"][1], "production_pki": False},
        },
        "heads": {"H7": H7, "H9": H9},
        "witness_history": {"WA42": WA42, "WA43_good": WA43_GOOD, "WA43_fork": WA43_FORK, "WB11": WB11},
        "checks": checks,
        "score": sum(item["points"] for item in checks),
        "max_score": 10,
        "classification": "Witness consistency protocol passes" if all(item["pass"] for item in checks) else "Witness consistency protocol fails",
        "invariants": [
            "INDEPENDENT WITNESS DOES NOT IMPLY CONSISTENT WITNESS.",
            "AUTHENTIC WITNESS STATEMENT DOES NOT IMPLY A UNIQUE WITNESS HISTORY.",
            "SAME WITNESS SEQUENCE AND PARENT WITH DIFFERENT AUTHENTIC CONTENT IS EQUIVOCATION EVIDENCE.",
            "EQUIVOCATING WITNESS MUST BE QUARANTINED; RECONSTRUCT TRUST FROM NON-CONFLICTING INDEPENDENT EVIDENCE BEFORE CONSEQUENCE.",
        ],
        "external_safety_certification": False,
        "vulnerability_claim": False,
    }

    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    (out / "RESULT.md").write_text(
        "# RESULT — Witness Rollback / Equivocation\n\n"
        f"Score: **{result['score']}/{result['max_score']}**\n\n"
        f"Classification: **{result['classification']}**\n\n"
        "Main law: **INDEPENDENT WITNESS ≠ CONSISTENT WITNESS**\n"
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    conn.close()
    subprocess.run(["docker", "rm", "-f", CONTAINER], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    if result["score"] != result["max_score"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
