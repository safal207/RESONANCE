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

CONTAINER = "resonance-external-checkpoint-storage-rollback"
VOLUME = "resonance-checkpoint-storage-rollback-v1"
IMAGE = os.environ.get("HTTP_SERVICE_IMAGE", "python:3.12-slim")
BASE = os.environ.get("EXTERNAL_BASE_URL", "http://127.0.0.1:18098")
SERVICE = Path("benchmarks/dependency-aware-applicability-v1.0/external_service.py").resolve()

HEAD_KEY = b"resonance-authority-head-demo-key-v1"
HEAD_KEY_ID = "authority-head-demo-key-v1"
WITNESS_KEY = b"resonance-checkpoint-witness-demo-key-v1"
WITNESS_KEY_ID = "checkpoint-witness-demo-key-v1"
NS = "resonance-proof-authority"
WITNESS_ID = "witness-A"


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def sha(value):
    return "sha256:" + hashlib.sha256(canonical(value).encode()).hexdigest()


def head_mac(payload):
    return hmac.new(HEAD_KEY, canonical(payload).encode(), hashlib.sha256).hexdigest()


def witness_mac(payload):
    return hmac.new(WITNESS_KEY, canonical(payload).encode(), hashlib.sha256).hexdigest()


def sign_head(payload):
    return {"alg": "HMAC-SHA256", "key_id": HEAD_KEY_ID, "payload": payload, "mac": head_mac(payload)}


def sign_witness(payload):
    return {"alg": "HMAC-SHA256", "key_id": WITNESS_KEY_ID, "payload": payload, "mac": witness_mac(payload)}


def head_authentic(head):
    return (
        head.get("alg") == "HMAC-SHA256"
        and head.get("key_id") == HEAD_KEY_ID
        and head.get("payload", {}).get("authority_namespace") == NS
        and hmac.compare_digest(head.get("mac", ""), head_mac(head.get("payload", {})))
    )


def witness_authentic(witness):
    return (
        witness.get("alg") == "HMAC-SHA256"
        and witness.get("key_id") == WITNESS_KEY_ID
        and witness.get("payload", {}).get("authority_namespace") == NS
        and witness.get("payload", {}).get("witness_id") == WITNESS_ID
        and hmac.compare_digest(witness.get("mac", ""), witness_mac(witness.get("payload", {})))
    )


MODELS = {
    "model-v1": {"version": "model-v1", "dependencies": ["price", "limit"], "formula_id": "min_limit_2x_price"},
    "model-v2": {"version": "model-v2", "dependencies": ["price", "limit", "tax_rate"], "formula_id": "min_limit_2x_price_plus_tax"},
}
for model in MODELS.values():
    model["digest"] = sha(model)

RULES = {
    "R1": {
        "rule_id": "cap-equivalence-r1",
        "from_model": "model-v1",
        "to_model": "model-v2",
        "predicate": "tax_rate >= 0 AND 2*price >= limit",
        "semantic_claim": "both models evaluate to limit",
    },
    "R2": {
        "rule_id": "cap-equivalence-r2",
        "from_model": "model-v1",
        "to_model": "model-v2",
        "predicate": "tax_rate >= 0 AND 2*price >= limit",
        "semantic_claim": "both models evaluate to limit",
        "supersedes": "cap-equivalence-r1",
    },
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
        "successor_rule_id": None,
    }
)
H9 = sign_head(
    {
        "authority_namespace": NS,
        "generation": 9,
        "rule_id": RULES["R2"]["rule_id"],
        "rule_digest": RULES["R2"]["digest"],
        "status": "ACTIVE",
        "successor_rule_id": None,
    }
)
W9 = sign_witness(
    {
        "authority_namespace": NS,
        "witness_id": WITNESS_ID,
        "generation": 9,
        "head_digest": sha(H9),
        "statement": "highest authenticated authority head observed",
    }
)


def db(dsn):
    return psycopg.connect(dsn, autocommit=False, row_factory=dict_row)


def init(conn):
    conn.execute(
        "CREATE TABLE IF NOT EXISTS csr_state(resource_id TEXT PRIMARY KEY, owner TEXT, fence INT, global_version INT, price INT, limit_value INT, tax_rate INT, current_model_version TEXT, current_model_digest TEXT)"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS csr_artifacts(resource_id TEXT, artifact_id TEXT, model_version TEXT, model_digest TEXT, input_values_fingerprint TEXT, output_value INT, artifact_digest TEXT, state TEXT DEFAULT 'READY', adopted_by TEXT, adopted_fence INT, proof_digest TEXT, PRIMARY KEY(resource_id, artifact_id))"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS csr_replica(region TEXT, rule_id TEXT, rule_digest TEXT, status TEXT, generation INT, PRIMARY KEY(region, rule_id))"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS csr_checkpoint(verifier_id TEXT PRIMARY KEY, max_authenticated_generation INT, head_digest TEXT, updated_at TIMESTAMPTZ DEFAULT now())"
    )
    conn.commit()


def reset_replica(conn, generation):
    conn.execute("DELETE FROM csr_replica")
    rule = RULES["R1" if generation == 7 else "R2"]
    conn.execute(
        "INSERT INTO csr_replica VALUES('region-B', %s, %s, 'ACTIVE', %s)",
        (rule["rule_id"], rule["digest"], generation),
    )
    conn.commit()


def checkpoint(conn, generation, head):
    conn.execute(
        "INSERT INTO csr_checkpoint(verifier_id,max_authenticated_generation,head_digest) VALUES('verifier-B',%s,%s) ON CONFLICT(verifier_id) DO UPDATE SET max_authenticated_generation=GREATEST(csr_checkpoint.max_authenticated_generation,EXCLUDED.max_authenticated_generation),head_digest=CASE WHEN EXCLUDED.max_authenticated_generation>=csr_checkpoint.max_authenticated_generation THEN EXCLUDED.head_digest ELSE csr_checkpoint.head_digest END,updated_at=now()",
        (generation, sha(head)),
    )
    conn.commit()


def checkpoint_row(conn):
    row = conn.execute(
        "SELECT verifier_id,max_authenticated_generation,head_digest FROM csr_checkpoint WHERE verifier_id='verifier-B'"
    ).fetchone()
    return dict(row) if row else {"verifier_id": "verifier-B", "max_authenticated_generation": 0, "head_digest": None}


def cp(conn):
    return checkpoint_row(conn)["max_authenticated_generation"]


def restore_checkpoint(conn, snapshot):
    conn.execute("DELETE FROM csr_checkpoint WHERE verifier_id='verifier-B'")
    conn.execute(
        "INSERT INTO csr_checkpoint(verifier_id,max_authenticated_generation,head_digest) VALUES(%s,%s,%s)",
        (snapshot["verifier_id"], snapshot["max_authenticated_generation"], snapshot["head_digest"]),
    )
    conn.commit()


def reconstruct_from_witness(conn, witness):
    if not witness_authentic(witness):
        return {"reconstructed": False, "reason": "witness_authentication_failed", "checkpoint": checkpoint_row(conn)}
    payload = witness["payload"]
    if payload["head_digest"] != sha(H9):
        return {"reconstructed": False, "reason": "witness_head_binding_failed", "checkpoint": checkpoint_row(conn)}
    checkpoint(conn, payload["generation"], H9)
    return {"reconstructed": True, "reason": "checkpoint_reconstructed_from_witness", "checkpoint": checkpoint_row(conn)}


def storage_guard(conn, witness):
    local = checkpoint_row(conn)
    authentic = witness_authentic(witness)
    payload = witness.get("payload", {})
    binding = authentic and payload.get("head_digest") == sha(H9)
    witness_generation = payload.get("generation", -1) if authentic else -1
    not_rolled_back = binding and local["max_authenticated_generation"] >= witness_generation
    if not authentic:
        reason = "witness_authentication_failed"
    elif not binding:
        reason = "witness_head_binding_failed"
    elif not not_rolled_back:
        reason = "checkpoint_storage_rollback_detected"
    else:
        reason = "checkpoint_storage_current"
    return {
        "accept": bool(not_rolled_back),
        "reason": reason,
        "local_checkpoint": local,
        "witness": witness,
        "witness_authentic": authentic,
        "witness_head_binding": binding,
        "witness_generation": witness_generation,
    }


def reset_resource(conn, rid):
    conn.execute("DELETE FROM csr_artifacts WHERE resource_id=%s", (rid,))
    conn.execute("DELETE FROM csr_state WHERE resource_id=%s", (rid,))
    conn.execute(
        "INSERT INTO csr_state VALUES(%s,'worker-B',2,101,20,30,8,'model-v2',%s)",
        (rid, MODELS["model-v2"]["digest"]),
    )
    conn.commit()


def values_fp(state):
    return sha({"price": state["price"], "limit": state["limit_value"], "tax_rate": state["tax_rate"]})


def make_artifact(conn, rid):
    state = conn.execute("SELECT * FROM csr_state WHERE resource_id=%s", (rid,)).fetchone()
    output = min(state["limit_value"], 2 * state["price"])
    digest = sha(
        {
            "resource_id": rid,
            "artifact_id": "artifact-v1",
            "model_version": "model-v1",
            "model_digest": MODELS["model-v1"]["digest"],
            "output": output,
        }
    )
    conn.execute(
        "INSERT INTO csr_artifacts(resource_id,artifact_id,model_version,model_digest,input_values_fingerprint,output_value,artifact_digest) VALUES(%s,'artifact-v1','model-v1',%s,%s,%s,%s)",
        (rid, MODELS["model-v1"]["digest"], values_fp(state), output, digest),
    )
    conn.commit()
    return conn.execute("SELECT * FROM csr_artifacts WHERE resource_id=%s", (rid,)).fetchone()


def proof(conn, rid, rule_key):
    state = conn.execute("SELECT * FROM csr_state WHERE resource_id=%s", (rid,)).fetchone()
    artifact = conn.execute("SELECT * FROM csr_artifacts WHERE resource_id=%s", (rid,)).fetchone()
    rule = RULES[rule_key]
    generation = 7 if rule_key == "R1" else 9
    value = {
        "rule_id": rule["rule_id"],
        "rule_digest": rule["digest"],
        "rule_generation": generation,
        "from_model_version": artifact["model_version"],
        "from_model_digest": artifact["model_digest"],
        "to_model_version": state["current_model_version"],
        "to_model_digest": state["current_model_digest"],
        "artifact_digest": artifact["artifact_digest"],
        "current_values_fingerprint": values_fp(state),
        "predicate_holds": state["tax_rate"] >= 0 and 2 * state["price"] >= state["limit_value"],
    }
    value["proof_digest"] = sha(value)
    return value


def verdict(conn, rid, proof_value, head, enforce_head_rollback):
    state = conn.execute("SELECT * FROM csr_state WHERE resource_id=%s", (rid,)).fetchone()
    artifact = conn.execute("SELECT * FROM csr_artifacts WHERE resource_id=%s", (rid,)).fetchone()
    head_payload = head["payload"]
    replica = conn.execute(
        "SELECT * FROM csr_replica WHERE region='region-B' AND rule_id=%s", (proof_value["rule_id"],)
    ).fetchone()
    authentic = head_authentic(head)
    high = cp(conn)
    checks = {
        "authority_head_authentic": authentic,
        "from_model": proof_value["from_model_version"] == artifact["model_version"] and proof_value["from_model_digest"] == artifact["model_digest"],
        "to_model": proof_value["to_model_version"] == state["current_model_version"] and proof_value["to_model_digest"] == state["current_model_digest"],
        "artifact": proof_value["artifact_digest"] == artifact["artifact_digest"],
        "values": proof_value["current_values_fingerprint"] == values_fp(state),
        "predicate": bool(proof_value["predicate_holds"]),
        "replica_exists": replica is not None,
        "head_matches_rule": head_payload.get("rule_id") == proof_value["rule_id"] and head_payload.get("rule_digest") == proof_value["rule_digest"],
        "rule_active": replica is not None and replica["status"] == "ACTIVE",
        "rule_generation": replica is not None and replica["generation"] == proof_value["rule_generation"],
        "authority_view_fresh": replica is not None and replica["generation"] >= head_payload.get("generation", 10**9),
    }
    if enforce_head_rollback:
        checks["head_not_rolled_back"] = authentic and head_payload.get("generation", -1) >= high
    if all(checks.values()):
        return {
            "accept": True,
            "reason": "proof_authorized_with_current_head",
            "checks": checks,
            "checkpoint_generation": high,
            "head": head_payload,
            "replica": dict(replica),
        }
    if not authentic:
        reason = "authority_head_authentication_failed"
    elif enforce_head_rollback and not checks.get("head_not_rolled_back", False):
        reason = "authority_head_rollback_detected"
    elif not checks["authority_view_fresh"]:
        reason = "stale_authority_view"
    else:
        reason = "proof_authority_conflict"
    return {
        "accept": False,
        "reason": reason,
        "checks": checks,
        "checkpoint_generation": high,
        "head": head_payload,
        "replica": dict(replica) if replica else None,
    }


def adopt(conn, rid, proof_value, verdict_value):
    if not verdict_value["accept"]:
        return {"updated_rows": 0, "reason": verdict_value["reason"]}
    cursor = conn.execute(
        "UPDATE csr_artifacts a SET state='ADOPTED',adopted_by=s.owner,adopted_fence=s.fence,proof_digest=%s FROM csr_state s WHERE a.resource_id=s.resource_id AND a.resource_id=%s AND a.state='READY' RETURNING a.artifact_id",
        (proof_value["proof_digest"], rid),
    )
    count = cursor.rowcount
    conn.commit()
    return {"updated_rows": count, "reason": "adopted" if count else "compare_and_adopt_conflict"}


def http(method, path, headers=None):
    request = urllib.request.Request(BASE + path, method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            return response.status, json.loads(response.read().decode())
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read().decode())


def start_service():
    subprocess.run(["docker", "rm", "-f", CONTAINER], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["docker", "volume", "rm", "-f", VOLUME], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["docker", "volume", "create", VOLUME], check=True, stdout=subprocess.DEVNULL)
    port = BASE.rsplit(":", 1)[-1]
    subprocess.run(
        [
            "docker",
            "run",
            "-d",
            "--name",
            CONTAINER,
            "-p",
            f"{port}:8080",
            "-v",
            f"{VOLUME}:/state",
            "-v",
            f"{SERVICE}:/app/external_service.py:ro",
            IMAGE,
            "python",
            "/app/external_service.py",
        ],
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


def publish(conn, rid, phase):
    artifact = conn.execute("SELECT * FROM csr_artifacts WHERE resource_id=%s", (rid,)).fetchone()
    state = conn.execute("SELECT * FROM csr_state WHERE resource_id=%s", (rid,)).fetchone()
    headers = {
        "X-Resource-Id": rid,
        "X-Worker": state["owner"],
        "X-Fencing-Token": str(state["fence"]),
        "X-Artifact-Digest": artifact["artifact_digest"],
        "X-Input-State-Version": str(state["global_version"]),
        "X-Output-Value": str(artifact["output_value"]),
        "X-Phase": phase,
    }
    return http("POST", "/effects", headers)


def remote(rid):
    return http("GET", f"/status/{rid}")[1]


def scenario(conn, rid, rule_key, head, enforce_head_rollback, phase):
    reset_resource(conn, rid)
    artifact = make_artifact(conn, rid)
    proof_value = proof(conn, rid, rule_key)
    verdict_value = verdict(conn, rid, proof_value, head, enforce_head_rollback)
    adoption = adopt(conn, rid, proof_value, verdict_value)
    write = None
    if adoption["updated_rows"]:
        code, payload = publish(conn, rid, phase)
        write = {"http_status": code, "payload": payload}
    return {
        "artifact": dict(artifact),
        "proof": proof_value,
        "head": head,
        "head_authentic": head_authentic(head),
        "verdict": verdict_value,
        "adoption": adoption,
        "write": write,
        "remote": remote(rid),
    }


def guarded_storage_scenario(conn, rid, witness):
    reset_resource(conn, rid)
    artifact = make_artifact(conn, rid)
    proof_value = proof(conn, rid, "R1")
    guard = storage_guard(conn, witness)
    adoption = {"updated_rows": 0, "reason": guard["reason"]}
    return {
        "artifact": dict(artifact),
        "proof": proof_value,
        "head": H7,
        "head_authentic": head_authentic(H7),
        "storage_guard": guard,
        "adoption": adoption,
        "write": None,
        "remote": remote(rid),
    }


def check(check_id, ok, evidence):
    return {"id": check_id, "pass": bool(ok), "points": 2 if ok else 0, "evidence": evidence}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    dsn = os.environ["DATABASE_URL"]

    service = start_service()
    conn = db(dsn)
    init(conn)
    conn.execute("DELETE FROM csr_checkpoint")
    conn.commit()

    reset_replica(conn, 7)
    checkpoint(conn, 7, H7)
    backup_snapshot_7 = checkpoint_row(conn)
    baseline = scenario(conn, "baseline-head7", "R1", H7, True, "baseline-head7")

    checkpoint(conn, 9, H9)
    pre_restore_checkpoint = checkpoint_row(conn)
    witness_before_restore = {
        "authentic": witness_authentic(W9),
        "generation": W9["payload"]["generation"],
        "head_digest_matches_h9": W9["payload"]["head_digest"] == sha(H9),
    }

    restore_checkpoint(conn, backup_snapshot_7)
    reset_replica(conn, 7)
    post_restore_checkpoint = checkpoint_row(conn)

    unsafe = scenario(conn, "unsafe-restored-local-state", "R1", H7, True, "unsafe-restored-local-state")

    guarded = guarded_storage_scenario(conn, "safe-storage-guard", W9)
    reconstruction = reconstruct_from_witness(conn, W9)
    reconstructed_h7 = scenario(conn, "reconstructed-replay-h7", "R1", H7, True, "reconstructed-replay-h7")

    reset_replica(conn, 9)
    fresh = scenario(conn, "fresh-head9-after-reconstruction", "R2", H9, True, "fresh-head9-after-reconstruction")

    checks = [
        check(
            "generation7_checkpoint_control_succeeds_before_advance",
            baseline["head_authentic"]
            and baseline["verdict"]["accept"]
            and baseline["write"]["http_status"] == 200
            and baseline["remote"].get("effect_count") == 1,
            {"backup_snapshot": backup_snapshot_7, "scenario": baseline},
        ),
        check(
            "local_checkpoint_really_advances_to9_then_restores_to7_while_witness_stays9",
            pre_restore_checkpoint["max_authenticated_generation"] == 9
            and post_restore_checkpoint["max_authenticated_generation"] == 7
            and witness_before_restore["authentic"]
            and witness_before_restore["generation"] == 9
            and witness_before_restore["head_digest_matches_h9"],
            {
                "pre_restore_checkpoint": pre_restore_checkpoint,
                "restored_snapshot": backup_snapshot_7,
                "post_restore_checkpoint": post_restore_checkpoint,
                "witness": W9,
                "witness_status": witness_before_restore,
            },
        ),
        check(
            "local_only_verifier_accepts_authentic_h7_after_storage_restore",
            unsafe["head_authentic"]
            and unsafe["verdict"]["accept"]
            and unsafe["verdict"]["checkpoint_generation"] == 7
            and unsafe["write"]["http_status"] == 200
            and unsafe["remote"].get("effect_count") == 1,
            unsafe,
        ),
        check(
            "witness_guard_detects_storage_rollback_then_reconstructs_checkpoint_with_zero_effects",
            guarded["storage_guard"]["reason"] == "checkpoint_storage_rollback_detected"
            and guarded["adoption"]["updated_rows"] == 0
            and guarded["remote"].get("effect_count") == 0
            and reconstruction["reconstructed"]
            and reconstruction["checkpoint"]["max_authenticated_generation"] == 9
            and reconstructed_h7["verdict"]["reason"] == "authority_head_rollback_detected"
            and reconstructed_h7["adoption"]["updated_rows"] == 0
            and reconstructed_h7["remote"].get("effect_count") == 0,
            {
                "guarded": guarded,
                "reconstruction": reconstruction,
                "post_reconstruction_h7": reconstructed_h7,
            },
        ),
        check(
            "fresh_authentic_h9_succeeds_once_after_reconstruction",
            fresh["head_authentic"]
            and fresh["verdict"]["accept"]
            and fresh["verdict"]["checkpoint_generation"] == 9
            and fresh["write"]["http_status"] == 200
            and fresh["remote"].get("effect_count") == 1,
            fresh,
        ),
    ]

    result = {
        "benchmark": "RESONANCE Checkpoint Storage Rollback / Restored Verifier State",
        "benchmark_version": "1.0",
        "protocol": "RESONANCE Transactional Trust Protocol v1.0",
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "database": {"server_version": conn.execute("SHOW server_version").fetchone()["server_version"]},
        "http_service": service,
        "http_service_image": IMAGE,
        "authentication_fixtures": {
            "authority_head": {"algorithm": "HMAC-SHA256", "key_id": HEAD_KEY_ID, "production_pki": False},
            "checkpoint_witness": {"algorithm": "HMAC-SHA256", "key_id": WITNESS_KEY_ID, "witness_id": WITNESS_ID, "production_pki": False},
        },
        "restore_fixture": {
            "type": "explicit verifier-local checkpoint row restore from previously captured snapshot",
            "snapshot_generation": 7,
            "pre_restore_generation": 9,
            "post_restore_generation": post_restore_checkpoint["max_authenticated_generation"],
        },
        "heads": {"H7": H7, "H9": H9},
        "external_witness": W9,
        "checks": checks,
        "score": sum(item["points"] for item in checks),
        "max_score": 10,
        "classification": "Checkpoint rollback resistance protocol passes" if all(item["pass"] for item in checks) else "Checkpoint rollback resistance protocol fails",
        "invariants": [
            "DURABLE CHECKPOINT DOES NOT IMPLY ROLLBACK-RESISTANT CHECKPOINT.",
            "VERIFIER STATE RECOVERY MUST NOT MOVE TRUST HISTORY BACKWARD.",
            "A LOCAL CHECKPOINT BELOW AN AUTHENTICATED INDEPENDENT HIGH-WATERMARK IS STORAGE-ROLLBACK EVIDENCE.",
            "AFTER CHECKPOINT ROLLBACK, RECONSTRUCT TRUST STATE FROM INDEPENDENT EVIDENCE BEFORE AUTHORIZING CONSEQUENCE.",
        ],
        "external_safety_certification": False,
        "vulnerability_claim": False,
    }

    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    summary = [
        "# RESULT — RESONANCE Checkpoint Storage Rollback / Restored Verifier State v1.0",
        "",
        f"Score: **{result['score']}/{result['max_score']}**",
        "",
        f"Classification: **{result['classification']}**",
        "",
    ]
    for item in checks:
        summary.append(f"- {'PASS' if item['pass'] else 'FAIL'} · {item['id']} · {item['points']}/2")
    summary += [
        "",
        "Core law: **DURABLE CHECKPOINT ≠ ROLLBACK-RESISTANT CHECKPOINT.**",
        "",
        "This benchmark is an experimental verification fixture, not production safety certification or a vulnerability claim.",
        "",
    ]
    (out / "RESULT.md").write_text("\n".join(summary))
    print(json.dumps(result, indent=2, sort_keys=True))
    conn.close()

    if result["score"] != result["max_score"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
