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

CONTAINER = "resonance-external-model-compatibility"
VOLUME = "resonance-model-compatibility-v1"
IMAGE = os.environ.get("HTTP_SERVICE_IMAGE", "python:3.12-slim")
BASE_URL = os.environ.get("EXTERNAL_BASE_URL", "http://127.0.0.1:18093")
SERVICE = Path("benchmarks/dependency-aware-applicability-v1.0/external_service.py").resolve()


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def sha(obj):
    return "sha256:" + hashlib.sha256(canonical(obj).encode()).hexdigest()


MODELS = {
    "model-v1": {
        "version": "model-v1",
        "dependencies": ["price", "limit"],
        "formula_id": "min_limit_2x_price",
    },
    "model-v2": {
        "version": "model-v2",
        "dependencies": ["price", "limit", "tax_rate"],
        "formula_id": "min_limit_2x_price_plus_tax",
    },
}
for model in MODELS.values():
    model["digest"] = sha({k: model[k] for k in ("version", "dependencies", "formula_id")})

PROOF_RULE = {
    "rule_id": "cap-dominates-tax-extension-v1",
    "from_model": "model-v1",
    "to_model": "model-v2",
    "predicate": "tax_rate >= 0 AND 2*price >= limit",
    "semantic_claim": "both models evaluate to limit",
}
PROOF_RULE["digest"] = sha(PROOF_RULE)


def db(dsn):
    return psycopg.connect(dsn, autocommit=False)


def calc(model_version, price, limit, tax_rate):
    if model_version == "model-v1":
        return min(limit, 2 * price)
    if model_version == "model-v2":
        return min(limit, 2 * price + tax_rate)
    raise ValueError(model_version)


def values_fp(price, limit, tax_rate):
    return sha({"price": price, "limit": limit, "tax_rate": tax_rate})


def dep_fp(model_version, price, limit, tax_rate):
    vals = {"price": price, "limit": limit, "tax_rate": tax_rate}
    return sha({k: vals[k] for k in MODELS[model_version]["dependencies"]})


def artifact_digest(resource_id, artifact_id, model_version, price, limit, tax_rate, output):
    return sha({
        "resource_id": resource_id,
        "artifact_id": artifact_id,
        "model_version": model_version,
        "model_digest": MODELS[model_version]["digest"],
        "dependency_fingerprint": dep_fp(model_version, price, limit, tax_rate),
        "output": output,
    })


def init_schema(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS compatibility_state(
          resource_id TEXT PRIMARY KEY,
          owner TEXT NOT NULL,
          fence INTEGER NOT NULL,
          global_version INTEGER NOT NULL,
          price INTEGER NOT NULL,
          limit_value INTEGER NOT NULL,
          tax_rate INTEGER NOT NULL,
          current_model_version TEXT NOT NULL,
          current_model_digest TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS compatibility_artifacts(
          resource_id TEXT NOT NULL,
          artifact_id TEXT NOT NULL,
          producer TEXT NOT NULL,
          producer_fence INTEGER NOT NULL,
          model_version TEXT NOT NULL,
          model_digest TEXT NOT NULL,
          dependency_fingerprint TEXT NOT NULL,
          input_values_fingerprint TEXT NOT NULL,
          output_value INTEGER NOT NULL,
          artifact_digest TEXT NOT NULL,
          state TEXT NOT NULL DEFAULT 'READY',
          adopted_by TEXT,
          adopted_fence INTEGER,
          proof_digest TEXT,
          PRIMARY KEY(resource_id, artifact_id)
        )
    """)
    conn.commit()


def reset_resource(conn, resource_id, price, limit, tax_rate, model_version="model-v1"):
    conn.execute("DELETE FROM compatibility_artifacts WHERE resource_id=%s", (resource_id,))
    conn.execute("DELETE FROM compatibility_state WHERE resource_id=%s", (resource_id,))
    conn.execute(
        "INSERT INTO compatibility_state(resource_id, owner, fence, global_version, price, limit_value, tax_rate, current_model_version, current_model_digest) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
        (resource_id, "worker-B", 2, 100, price, limit, tax_rate, model_version, MODELS[model_version]["digest"]),
    )
    conn.commit()


def advance_model(conn, resource_id, to_model="model-v2"):
    conn.execute(
        "UPDATE compatibility_state SET current_model_version=%s, current_model_digest=%s, global_version=global_version+1 WHERE resource_id=%s",
        (to_model, MODELS[to_model]["digest"], resource_id),
    )
    conn.commit()


def current(conn, resource_id):
    row = conn.execute("SELECT * FROM compatibility_state WHERE resource_id=%s", (resource_id,)).fetchone()
    cols = [d.name for d in conn.execute("SELECT * FROM compatibility_state LIMIT 0").description]
    return dict(zip(cols, row))


def make_artifact(conn, resource_id, artifact_id, model_version, producer="worker-A", producer_fence=1):
    s = current(conn, resource_id)
    price, limit, tax_rate = s["price"], s["limit_value"], s["tax_rate"]
    output = calc(model_version, price, limit, tax_rate)
    digest = artifact_digest(resource_id, artifact_id, model_version, price, limit, tax_rate, output)
    conn.execute(
        """INSERT INTO compatibility_artifacts(resource_id, artifact_id, producer, producer_fence, model_version, model_digest, dependency_fingerprint, input_values_fingerprint, output_value, artifact_digest)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        (resource_id, artifact_id, producer, producer_fence, model_version, MODELS[model_version]["digest"], dep_fp(model_version, price, limit, tax_rate), values_fp(price, limit, tax_rate), output, digest),
    )
    conn.commit()
    return get_artifact(conn, resource_id, artifact_id)


def get_artifact(conn, resource_id, artifact_id):
    cur = conn.execute("SELECT * FROM compatibility_artifacts WHERE resource_id=%s AND artifact_id=%s", (resource_id, artifact_id))
    row = cur.fetchone()
    return dict(zip([d.name for d in cur.description], row))


def proof_predicate(s):
    return s["tax_rate"] >= 0 and 2 * s["price"] >= s["limit_value"]


def build_proof(s, artifact, *, to_digest=None, artifact_digest_override=None):
    proof = {
        "rule_id": PROOF_RULE["rule_id"],
        "rule_digest": PROOF_RULE["digest"],
        "from_model_version": artifact["model_version"],
        "from_model_digest": artifact["model_digest"],
        "to_model_version": s["current_model_version"],
        "to_model_digest": to_digest or s["current_model_digest"],
        "artifact_digest": artifact_digest_override or artifact["artifact_digest"],
        "current_values_fingerprint": values_fp(s["price"], s["limit_value"], s["tax_rate"]),
        "predicate_holds": proof_predicate(s),
    }
    proof["proof_digest"] = sha(proof)
    return proof


def unsafe_global_adopt(conn, resource_id, artifact_id):
    # Deliberately unsafe: treats a global v1→v2 compatibility claim as enough.
    cur = conn.execute(
        """UPDATE compatibility_artifacts a
           SET state='ADOPTED', adopted_by=s.owner, adopted_fence=s.fence, proof_digest='GLOBAL_COMPATIBILITY_FLAG'
           FROM compatibility_state s
           WHERE a.resource_id=s.resource_id AND a.resource_id=%s AND a.artifact_id=%s
             AND a.state='READY' AND a.model_version='model-v1' AND s.current_model_version='model-v2'
           RETURNING a.artifact_id""",
        (resource_id, artifact_id),
    )
    rows = cur.rowcount
    conn.commit()
    return {"updated_rows": rows, "reason": "adopted_global_claim" if rows else "not_adopted"}


def proof_adopt(conn, resource_id, artifact_id, proof):
    s = current(conn, resource_id)
    a = get_artifact(conn, resource_id, artifact_id)
    checks = {
        "rule_identity": proof.get("rule_digest") == PROOF_RULE["digest"],
        "from_model": proof.get("from_model_version") == a["model_version"] and proof.get("from_model_digest") == a["model_digest"],
        "to_model": proof.get("to_model_version") == s["current_model_version"] and proof.get("to_model_digest") == s["current_model_digest"],
        "artifact_binding": proof.get("artifact_digest") == a["artifact_digest"],
        "current_values": proof.get("current_values_fingerprint") == values_fp(s["price"], s["limit_value"], s["tax_rate"]),
        "predicate": bool(proof.get("predicate_holds")) and proof_predicate(s),
        "transition": a["model_version"] == "model-v1" and s["current_model_version"] == "model-v2",
    }
    if not all(checks.values()):
        reason = "compatibility_scope_conflict" if not checks["predicate"] else "compatibility_proof_binding_conflict"
        return {"updated_rows": 0, "reason": reason, "checks": checks}
    cur = conn.execute(
        """UPDATE compatibility_artifacts a
           SET state='ADOPTED', adopted_by=s.owner, adopted_fence=s.fence, proof_digest=%s
           FROM compatibility_state s
           WHERE a.resource_id=s.resource_id AND a.resource_id=%s AND a.artifact_id=%s AND a.state='READY'
             AND s.owner='worker-B' AND s.fence=2 AND s.current_model_version='model-v2' AND s.current_model_digest=%s
             AND a.model_version='model-v1' AND a.model_digest=%s AND a.artifact_digest=%s
           RETURNING a.artifact_id""",
        (proof["proof_digest"], resource_id, artifact_id, proof["to_model_digest"], proof["from_model_digest"], proof["artifact_digest"]),
    )
    rows = cur.rowcount
    conn.commit()
    return {"updated_rows": rows, "reason": "adopted_with_compatibility_proof" if rows else "compare_and_adopt_conflict", "checks": checks}


def direct_current_adopt(conn, resource_id, artifact_id):
    cur = conn.execute(
        """UPDATE compatibility_artifacts a
           SET state='ADOPTED', adopted_by=s.owner, adopted_fence=s.fence, proof_digest='CURRENT_MODEL'
           FROM compatibility_state s
           WHERE a.resource_id=s.resource_id AND a.resource_id=%s AND a.artifact_id=%s AND a.state='READY'
             AND a.model_version=s.current_model_version AND a.model_digest=s.current_model_digest
           RETURNING a.artifact_id""",
        (resource_id, artifact_id),
    )
    rows = cur.rowcount
    conn.commit()
    return {"updated_rows": rows, "reason": "adopted_current_model" if rows else "current_model_conflict"}


def http_json(method, path, headers=None):
    req = urllib.request.Request(BASE_URL + path, method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())


def start_service():
    subprocess.run(["docker", "rm", "-f", CONTAINER], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["docker", "volume", "rm", "-f", VOLUME], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["docker", "volume", "create", VOLUME], check=True, stdout=subprocess.DEVNULL)
    port = BASE_URL.rsplit(":", 1)[-1]
    subprocess.run([
        "docker", "run", "-d", "--name", CONTAINER, "-p", f"{port}:8080",
        "-v", f"{VOLUME}:/state", "-v", f"{SERVICE}:/app/external_service.py:ro",
        IMAGE, "python", "/app/external_service.py", "--port", "8080"
    ], check=True, stdout=subprocess.DEVNULL)
    for _ in range(40):
        try:
            status, payload = http_json("GET", "/health")
            if status == 200:
                return payload
        except Exception:
            pass
        time.sleep(0.25)
    raise RuntimeError("external service failed to start")


def stop_service():
    subprocess.run(["docker", "rm", "-f", CONTAINER], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def commit_artifact(conn, resource_id, artifact_id, phase):
    a = get_artifact(conn, resource_id, artifact_id)
    if a["state"] != "ADOPTED":
        return {"http_status": None, "payload": {"delivery": "not_adopted"}}
    s = current(conn, resource_id)
    headers = {
        "X-Resource-Id": resource_id,
        "X-Worker": a["adopted_by"],
        "X-Fencing-Token": str(a["adopted_fence"]),
        "X-Artifact-Digest": a["artifact_digest"],
        "X-Input-State-Version": str(s["global_version"]),
        "X-Output-Value": str(a["output_value"]),
        "X-Phase": phase,
    }
    status, payload = http_json("POST", "/effects", headers=headers)
    return {"http_status": status, "payload": payload}


def remote(resource_id):
    return http_json("GET", "/status/" + resource_id)[1]


def run(dsn, out_dir):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    with db(dsn) as conn:
        init_schema(conn)
        health = start_service()
        checks = []
        try:
            # 1. Scoped compatibility: old v1 artifact remains semantically valid under v2.
            r1 = "compatible-scope"
            reset_resource(conn, r1, price=20, limit=30, tax_rate=8)
            a1 = make_artifact(conn, r1, "artifact-v1-compatible", "model-v1")
            advance_model(conn, r1)
            s1 = current(conn, r1)
            p1 = build_proof(s1, a1)
            ad1 = proof_adopt(conn, r1, a1["artifact_id"], p1)
            w1 = commit_artifact(conn, r1, a1["artifact_id"], "compatibility-proof")
            rem1 = remote(r1)
            c1 = ad1["updated_rows"] == 1 and a1["output_value"] == 30 and calc("model-v2", 20, 30, 8) == 30 and rem1["effect_count"] == 1 and rem1["effects"][0]["output_value"] == 30
            checks.append({"id": "scoped_proof_reuses_old_artifact_when_models_are_equivalent_for_current_state", "pass": c1, "points": 2, "evidence": {"proof": p1, "adoption": ad1, "write": w1, "remote": rem1}})

            # 2. Unsafe global compatibility claim accepts an actually incompatible artifact.
            r2 = "unsafe-global-compatibility"
            reset_resource(conn, r2, price=10, limit=30, tax_rate=8)
            a2 = make_artifact(conn, r2, "artifact-v1-unsafe", "model-v1")
            advance_model(conn, r2)
            ad2 = unsafe_global_adopt(conn, r2, a2["artifact_id"])
            w2 = commit_artifact(conn, r2, a2["artifact_id"], "unsafe-global-compatibility")
            rem2 = remote(r2)
            c2 = ad2["updated_rows"] == 1 and a2["output_value"] == 20 and calc("model-v2", 10, 30, 8) == 28 and rem2["effect_count"] == 1 and rem2["effects"][0]["output_value"] == 20
            checks.append({"id": "global_compatibility_flag_commits_stale_result_outside_proven_scope", "pass": c2, "points": 2, "evidence": {"adoption": ad2, "write": w2, "remote": rem2, "current_expected_output": 28}})

            # 3. Safe out-of-scope rejection followed by recompute under v2.
            r3 = "safe-out-of-scope"
            reset_resource(conn, r3, price=10, limit=30, tax_rate=8)
            old3 = make_artifact(conn, r3, "artifact-v1-reject", "model-v1")
            advance_model(conn, r3)
            s3 = current(conn, r3)
            p3 = build_proof(s3, old3)
            ad3 = proof_adopt(conn, r3, old3["artifact_id"], p3)
            before3 = remote(r3)
            fresh3 = make_artifact(conn, r3, "artifact-v2-current", "model-v2", producer="worker-B", producer_fence=2)
            ad3b = direct_current_adopt(conn, r3, fresh3["artifact_id"])
            w3 = commit_artifact(conn, r3, fresh3["artifact_id"], "recompute-current-model")
            rem3 = remote(r3)
            c3 = ad3["updated_rows"] == 0 and ad3["reason"] == "compatibility_scope_conflict" and before3["effect_count"] == 0 and fresh3["output_value"] == 28 and ad3b["updated_rows"] == 1 and rem3["effect_count"] == 1 and rem3["effects"][0]["output_value"] == 28
            checks.append({"id": "out_of_scope_old_artifact_is_rejected_then_current_model_recompute_commits_once", "pass": c3, "points": 2, "evidence": {"proof": p3, "stale_adoption": ad3, "remote_after_reject": before3, "fresh_adoption": ad3b, "write": w3, "remote": rem3}})

            # 4. Proof binding tamper: semantic predicate true, but target/artifact identities are wrong.
            r4 = "proof-binding-tamper"
            reset_resource(conn, r4, price=20, limit=30, tax_rate=8)
            a4 = make_artifact(conn, r4, "artifact-v1-tamper", "model-v1")
            advance_model(conn, r4)
            s4 = current(conn, r4)
            bad_target = build_proof(s4, a4, to_digest="sha256:" + "0" * 64)
            bad_artifact = build_proof(s4, a4, artifact_digest_override="sha256:" + "f" * 64)
            ad4a = proof_adopt(conn, r4, a4["artifact_id"], bad_target)
            ad4b = proof_adopt(conn, r4, a4["artifact_id"], bad_artifact)
            rem4 = remote(r4)
            c4 = ad4a["updated_rows"] == 0 and ad4b["updated_rows"] == 0 and ad4a["reason"] == "compatibility_proof_binding_conflict" and ad4b["reason"] == "compatibility_proof_binding_conflict" and rem4["effect_count"] == 0
            checks.append({"id": "compatibility_proof_must_bind_exact_model_and_artifact_identity", "pass": c4, "points": 2, "evidence": {"wrong_target_model": ad4a, "wrong_artifact": ad4b, "remote": rem4}})

            # 5. Current-model control.
            r5 = "current-model-control"
            reset_resource(conn, r5, price=10, limit=30, tax_rate=8, model_version="model-v2")
            a5 = make_artifact(conn, r5, "artifact-v2-control", "model-v2", producer="worker-B", producer_fence=2)
            ad5 = direct_current_adopt(conn, r5, a5["artifact_id"])
            w5 = commit_artifact(conn, r5, a5["artifact_id"], "current-model-control")
            rem5 = remote(r5)
            c5 = ad5["updated_rows"] == 1 and a5["output_value"] == 28 and rem5["effect_count"] == 1 and rem5["effects"][0]["output_value"] == 28
            checks.append({"id": "current_model_artifact_commits_normally_without_compatibility_proof", "pass": c5, "points": 2, "evidence": {"adoption": ad5, "write": w5, "remote": rem5}})
        finally:
            stop_service()

        score = sum(c["points"] for c in checks if c["pass"])
        result = {
            "benchmark": "RESONANCE Model Compatibility Proof / Backward-Compatible Migration",
            "benchmark_version": "1.0",
            "protocol": "RESONANCE Transactional Trust Protocol v1.0",
            "executed_at": datetime.now(timezone.utc).isoformat(),
            "database": {"server_version": conn.execute("SHOW server_version").fetchone()[0]},
            "http_service": health,
            "http_service_image": IMAGE,
            "models": MODELS,
            "compatibility_rule": PROOF_RULE,
            "checks": checks,
            "score": score,
            "max_score": 10,
            "classification": "Model compatibility proof protocol passes" if score == 10 else "Model compatibility proof protocol incomplete",
            "invariants": [
                "MODEL VERSION MISMATCH DOES NOT BY ITSELF PROVE INCOMPATIBILITY; COMPATIBILITY MUST BE PROVED.",
                "COMPATIBILITY PROOF MUST BE SCOPED TO EXACT MODEL IDENTITIES, ARTIFACT IDENTITY, AND CURRENT STATE.",
                "A GLOBAL COMPATIBILITY FLAG IS NOT EQUIVALENCE EVIDENCE FOR EVERY ARTIFACT.",
                "FAILED OR UNKNOWN COMPATIBILITY PROOF REQUIRES HOLD, REVALIDATION, OR RECOMPUTATION BEFORE CONSEQUENCE.",
            ],
            "external_safety_certification": False,
            "vulnerability_claim": False,
        }
        (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        md = [
            "# RESONANCE Model Compatibility Proof v1.0",
            "",
            f"Score: **{score}/10**",
            "",
            "| Check | Result | Points |",
            "|---|---:|---:|",
        ]
        for c in checks:
            md.append(f"| `{c['id']}` | {'PASS' if c['pass'] else 'FAIL'} | {c['points'] if c['pass'] else 0}/2 |")
        md += ["", f"Classification: **{result['classification']}**", "", "> MODEL VERSION MISMATCH ≠ AUTOMATIC INCOMPATIBILITY — COMPATIBILITY ITSELF MUST BE PROVED."]
        (out / "RESULT.md").write_text("\n".join(md) + "\n")
        print(json.dumps(result, indent=2, sort_keys=True))
        if score != 10:
            raise SystemExit(1)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--dsn", default=os.environ.get("DATABASE_URL", "postgresql://resonance:resonance@127.0.0.1:5432/resonance"))
    p.add_argument("--out", default="benchmark-results/model-compatibility-proof-v1.0")
    args = p.parse_args()
    run(args.dsn, args.out)
