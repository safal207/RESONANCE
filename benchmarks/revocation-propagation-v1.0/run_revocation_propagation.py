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
from psycopg.rows import dict_row

CONTAINER = "resonance-external-revocation-propagation"
VOLUME = "resonance-revocation-propagation-v1"
IMAGE = os.environ.get("HTTP_SERVICE_IMAGE", "python:3.12-slim")
BASE_URL = os.environ.get("EXTERNAL_BASE_URL", "http://127.0.0.1:18095")
SERVICE = Path("benchmarks/dependency-aware-applicability-v1.0/external_service.py").resolve()


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def sha(obj):
    return "sha256:" + hashlib.sha256(canonical(obj).encode()).hexdigest()


MODELS = {
    "model-v1": {"version": "model-v1", "dependencies": ["price", "limit"], "formula_id": "min_limit_2x_price"},
    "model-v2": {"version": "model-v2", "dependencies": ["price", "limit", "tax_rate"], "formula_id": "min_limit_2x_price_plus_tax"},
}
for model in MODELS.values():
    model["digest"] = sha({k: model[k] for k in ("version", "dependencies", "formula_id")})

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


def db(dsn):
    return psycopg.connect(dsn, autocommit=False, row_factory=dict_row)


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
        CREATE TABLE IF NOT EXISTS rp_state(
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
        CREATE TABLE IF NOT EXISTS rp_artifacts(
          resource_id TEXT NOT NULL,
          artifact_id TEXT NOT NULL,
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
    conn.execute("""
        CREATE TABLE IF NOT EXISTS rp_authority_head(
          singleton BOOLEAN PRIMARY KEY DEFAULT TRUE CHECK(singleton),
          generation INTEGER NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS rp_authority_origin(
          rule_id TEXT PRIMARY KEY,
          rule_digest TEXT NOT NULL,
          status TEXT NOT NULL,
          generation INTEGER NOT NULL,
          successor_rule_id TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS rp_authority_replica(
          region TEXT NOT NULL,
          rule_id TEXT NOT NULL,
          rule_digest TEXT NOT NULL,
          status TEXT NOT NULL,
          generation INTEGER NOT NULL,
          successor_rule_id TEXT,
          PRIMARY KEY(region, rule_id)
        )
    """)
    conn.commit()


def reset_authority(conn):
    conn.execute("DELETE FROM rp_authority_replica")
    conn.execute("DELETE FROM rp_authority_origin")
    conn.execute("DELETE FROM rp_authority_head")
    conn.execute("INSERT INTO rp_authority_head(singleton,generation) VALUES(TRUE,7)")
    r1 = RULES["R1"]
    conn.execute(
        "INSERT INTO rp_authority_origin(rule_id,rule_digest,status,generation,successor_rule_id) VALUES(%s,%s,'ACTIVE',7,NULL)",
        (r1["rule_id"], r1["digest"]),
    )
    for region in ("region-A", "region-B"):
        conn.execute(
            "INSERT INTO rp_authority_replica(region,rule_id,rule_digest,status,generation,successor_rule_id) VALUES(%s,%s,%s,'ACTIVE',7,NULL)",
            (region, r1["rule_id"], r1["digest"]),
        )
    conn.commit()


def reset_resource(conn, resource_id, price=20, limit=30, tax_rate=8):
    conn.execute("DELETE FROM rp_artifacts WHERE resource_id=%s", (resource_id,))
    conn.execute("DELETE FROM rp_state WHERE resource_id=%s", (resource_id,))
    conn.execute(
        "INSERT INTO rp_state(resource_id,owner,fence,global_version,price,limit_value,tax_rate,current_model_version,current_model_digest) VALUES(%s,'worker-B',2,101,%s,%s,%s,'model-v2',%s)",
        (resource_id, price, limit, tax_rate, MODELS["model-v2"]["digest"]),
    )
    conn.commit()


def get_state(conn, resource_id):
    return conn.execute("SELECT * FROM rp_state WHERE resource_id=%s", (resource_id,)).fetchone()


def make_artifact(conn, resource_id, artifact_id):
    s = get_state(conn, resource_id)
    output = calc("model-v1", s["price"], s["limit_value"], s["tax_rate"])
    digest = artifact_digest(resource_id, artifact_id, "model-v1", s["price"], s["limit_value"], s["tax_rate"], output)
    conn.execute(
        """INSERT INTO rp_artifacts(resource_id,artifact_id,model_version,model_digest,dependency_fingerprint,input_values_fingerprint,output_value,artifact_digest)
           VALUES(%s,%s,'model-v1',%s,%s,%s,%s,%s)""",
        (resource_id, artifact_id, MODELS["model-v1"]["digest"], dep_fp("model-v1", s["price"], s["limit_value"], s["tax_rate"]), values_fp(s["price"], s["limit_value"], s["tax_rate"]), output, digest),
    )
    conn.commit()
    return get_artifact(conn, resource_id, artifact_id)


def get_artifact(conn, resource_id, artifact_id):
    return conn.execute("SELECT * FROM rp_artifacts WHERE resource_id=%s AND artifact_id=%s", (resource_id, artifact_id)).fetchone()


def origin_rule(conn, rule_id):
    return conn.execute("SELECT * FROM rp_authority_origin WHERE rule_id=%s", (rule_id,)).fetchone()


def replica_rule(conn, region, rule_id):
    return conn.execute("SELECT * FROM rp_authority_replica WHERE region=%s AND rule_id=%s", (region, rule_id)).fetchone()


def head_generation(conn):
    return conn.execute("SELECT generation FROM rp_authority_head WHERE singleton=TRUE").fetchone()["generation"]


def proof_predicate(s):
    return s["tax_rate"] >= 0 and 2 * s["price"] >= s["limit_value"]


def issue_proof(conn, resource_id, artifact_id, rule_key="R1"):
    s = get_state(conn, resource_id)
    a = get_artifact(conn, resource_id, artifact_id)
    rule = RULES[rule_key]
    auth = origin_rule(conn, rule["rule_id"])
    proof = {
        "rule_id": rule["rule_id"],
        "rule_digest": rule["digest"],
        "rule_generation": auth["generation"],
        "issued_status": auth["status"],
        "from_model_version": a["model_version"],
        "from_model_digest": a["model_digest"],
        "to_model_version": s["current_model_version"],
        "to_model_digest": s["current_model_digest"],
        "artifact_digest": a["artifact_digest"],
        "current_values_fingerprint": values_fp(s["price"], s["limit_value"], s["tax_rate"]),
        "predicate_holds": proof_predicate(s),
    }
    proof["proof_digest"] = sha(proof)
    return proof


def revoke_origin_r1(conn):
    r1 = RULES["R1"]
    r2 = RULES["R2"]
    conn.execute("UPDATE rp_authority_head SET generation=8 WHERE singleton=TRUE")
    conn.execute(
        "UPDATE rp_authority_origin SET status='REVOKED',generation=8,successor_rule_id=%s WHERE rule_id=%s",
        (r2["rule_id"], r1["rule_id"]),
    )
    conn.execute(
        "INSERT INTO rp_authority_origin(rule_id,rule_digest,status,generation,successor_rule_id) VALUES(%s,%s,'PENDING',8,NULL) ON CONFLICT(rule_id) DO UPDATE SET rule_digest=EXCLUDED.rule_digest,status='PENDING',generation=8,successor_rule_id=NULL",
        (r2["rule_id"], r2["digest"]),
    )
    conn.commit()


def activate_successor(conn):
    r2 = RULES["R2"]
    conn.execute("UPDATE rp_authority_head SET generation=9 WHERE singleton=TRUE")
    conn.execute("UPDATE rp_authority_origin SET status='ACTIVE',generation=9 WHERE rule_id=%s", (r2["rule_id"],))
    conn.commit()


def sync_region(conn, region):
    rows = conn.execute("SELECT * FROM rp_authority_origin").fetchall()
    for row in rows:
        conn.execute(
            """INSERT INTO rp_authority_replica(region,rule_id,rule_digest,status,generation,successor_rule_id)
               VALUES(%s,%s,%s,%s,%s,%s)
               ON CONFLICT(region,rule_id) DO UPDATE SET rule_digest=EXCLUDED.rule_digest,status=EXCLUDED.status,generation=EXCLUDED.generation,successor_rule_id=EXCLUDED.successor_rule_id""",
            (region, row["rule_id"], row["rule_digest"], row["status"], row["generation"], row["successor_rule_id"]),
        )
    conn.commit()


def static_checks(s, a, proof):
    return {
        "from_model": proof["from_model_version"] == a["model_version"] and proof["from_model_digest"] == a["model_digest"],
        "to_model": proof["to_model_version"] == s["current_model_version"] and proof["to_model_digest"] == s["current_model_digest"],
        "artifact": proof["artifact_digest"] == a["artifact_digest"],
        "values": proof["current_values_fingerprint"] == values_fp(s["price"], s["limit_value"], s["tax_rate"]),
        "predicate": bool(proof["predicate_holds"]) and proof_predicate(s),
    }


def regional_verdict(conn, region, resource_id, artifact_id, proof, require_head_freshness=False):
    s = get_state(conn, resource_id)
    a = get_artifact(conn, resource_id, artifact_id)
    rep = replica_rule(conn, region, proof["rule_id"])
    checks = static_checks(s, a, proof)
    checks.update({
        "replica_exists": rep is not None,
        "rule_digest": rep is not None and rep["rule_digest"] == proof["rule_digest"],
        "rule_active": rep is not None and rep["status"] == "ACTIVE",
        "rule_generation": rep is not None and rep["generation"] == proof["rule_generation"],
    })
    if require_head_freshness:
        checks["authority_view_fresh"] = rep is not None and rep["generation"] >= head_generation(conn)
    if all(checks.values()):
        return {"accept": True, "reason": "regional_proof_authorized", "region": region, "replica": dict(rep), "checks": checks}
    if require_head_freshness and not checks.get("authority_view_fresh", False):
        reason = "stale_authority_view"
    elif rep is not None and rep["status"] == "REVOKED":
        reason = "compatibility_proof_revoked"
    elif rep is not None and rep["generation"] != proof["rule_generation"]:
        reason = "compatibility_proof_authority_conflict"
    else:
        reason = "compatibility_proof_binding_conflict"
    return {"accept": False, "reason": reason, "region": region, "replica": dict(rep) if rep else None, "checks": checks}


def adopt_from_verdict(conn, resource_id, artifact_id, proof, verdict):
    if not verdict["accept"]:
        return {"updated_rows": 0, "reason": verdict["reason"]}
    cur = conn.execute(
        """UPDATE rp_artifacts a SET state='ADOPTED',adopted_by=s.owner,adopted_fence=s.fence,proof_digest=%s
           FROM rp_state s WHERE a.resource_id=s.resource_id AND a.resource_id=%s AND a.artifact_id=%s AND a.state='READY'
           RETURNING a.artifact_id""",
        (proof["proof_digest"], resource_id, artifact_id),
    )
    rows = cur.rowcount
    conn.commit()
    return {"updated_rows": rows, "reason": "adopted_from_regional_view" if rows else "compare_and_adopt_conflict"}


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
    s = get_state(conn, resource_id)
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


def result_doc(result):
    lines = [
        "# RESONANCE Revocation Propagation / Stale Proof Registry Split-Brain",
        "",
        f"Score: **{result['score']}/{result['max_score']}**",
        "",
        f"Classification: **{result['classification']}**",
        "",
        "## Invariants",
    ]
    lines.extend(f"- {x}" for x in result["invariants"])
    lines += ["", "## Checks"]
    lines.extend(f"- {'PASS' if c['pass'] else 'FAIL'} — {c['id']} ({c['points']}/2)" for c in result["checks"])
    return "\n".join(lines) + "\n"


def run(dsn, out_dir):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    with db(dsn) as conn:
        init_schema(conn)
        health = start_service()
        checks = []
        try:
            # 1. Synchronized active control.
            reset_authority(conn)
            r1 = "synced-active-control"
            reset_resource(conn, r1)
            a1 = make_artifact(conn, r1, "artifact-v1-control")
            p1 = issue_proof(conn, r1, a1["artifact_id"], "R1")
            v1 = regional_verdict(conn, "region-B", r1, a1["artifact_id"], p1, require_head_freshness=True)
            ad1 = adopt_from_verdict(conn, r1, a1["artifact_id"], p1, v1)
            w1 = commit_artifact(conn, r1, a1["artifact_id"], "synced-active")
            rem1 = remote(r1)
            c1 = v1["accept"] and ad1["updated_rows"] == 1 and rem1["effect_count"] == 1 and rem1["effects"][0]["output_value"] == 30
            checks.append({"id": "synchronized_active_replica_authorizes_current_proof", "pass": c1, "points": 2, "evidence": {"proof": p1, "verdict": v1, "adoption": ad1, "write": w1, "remote": rem1}})

            # 2. Origin revokes, A syncs, B stays stale: same proof gets divergent verdicts and B commits unsafely.
            reset_authority(conn)
            r2 = "split-brain-unsafe"
            reset_resource(conn, r2)
            a2 = make_artifact(conn, r2, "artifact-v1-split")
            p2 = issue_proof(conn, r2, a2["artifact_id"], "R1")
            revoke_origin_r1(conn)
            sync_region(conn, "region-A")
            va = regional_verdict(conn, "region-A", r2, a2["artifact_id"], p2, require_head_freshness=False)
            vb = regional_verdict(conn, "region-B", r2, a2["artifact_id"], p2, require_head_freshness=False)
            ad2 = adopt_from_verdict(conn, r2, a2["artifact_id"], p2, vb)
            w2 = commit_artifact(conn, r2, a2["artifact_id"], "unsafe-stale-region")
            rem2 = remote(r2)
            c2 = (not va["accept"] and va["reason"] == "compatibility_proof_revoked" and vb["accept"] and ad2["updated_rows"] == 1 and rem2["effect_count"] == 1)
            checks.append({"id": "same_proof_splits_verdicts_and_stale_region_commits_after_origin_revocation", "pass": c2, "points": 2, "evidence": {"proof": p2, "origin_head": head_generation(conn), "region_A": va, "region_B": vb, "adoption": ad2, "write": w2, "remote": rem2}})

            # 3. Freshness floor blocks stale region even before revocation payload propagates.
            reset_authority(conn)
            r3 = "freshness-floor-safe"
            reset_resource(conn, r3)
            a3 = make_artifact(conn, r3, "artifact-v1-floor")
            p3 = issue_proof(conn, r3, a3["artifact_id"], "R1")
            revoke_origin_r1(conn)
            v3 = regional_verdict(conn, "region-B", r3, a3["artifact_id"], p3, require_head_freshness=True)
            ad3 = adopt_from_verdict(conn, r3, a3["artifact_id"], p3, v3)
            rem3 = remote(r3)
            c3 = (not v3["accept"] and v3["reason"] == "stale_authority_view" and ad3["updated_rows"] == 0 and rem3["effect_count"] == 0)
            checks.append({"id": "authoritative_generation_watermark_rejects_stale_replica_before_effect", "pass": c3, "points": 2, "evidence": {"proof": p3, "origin_head": head_generation(conn), "verdict": v3, "adoption": ad3, "remote": rem3}})

            # 4. Propagation converges stale region to revoked state.
            sync_region(conn, "region-B")
            v4 = regional_verdict(conn, "region-B", r3, a3["artifact_id"], p3, require_head_freshness=True)
            ad4 = adopt_from_verdict(conn, r3, a3["artifact_id"], p3, v4)
            rem4 = remote(r3)
            c4 = (not v4["accept"] and v4["reason"] == "compatibility_proof_revoked" and v4["replica"]["generation"] == 8 and ad4["updated_rows"] == 0 and rem4["effect_count"] == 0)
            checks.append({"id": "revocation_propagation_converges_regional_verdict_to_reject", "pass": c4, "points": 2, "evidence": {"verdict": v4, "adoption": ad4, "remote": rem4}})

            # 5. Fresh successor proof succeeds after generation 9 propagation.
            activate_successor(conn)
            sync_region(conn, "region-B")
            r5 = "successor-after-propagation"
            reset_resource(conn, r5)
            a5 = make_artifact(conn, r5, "artifact-v1-successor")
            p5 = issue_proof(conn, r5, a5["artifact_id"], "R2")
            v5 = regional_verdict(conn, "region-B", r5, a5["artifact_id"], p5, require_head_freshness=True)
            ad5 = adopt_from_verdict(conn, r5, a5["artifact_id"], p5, v5)
            w5 = commit_artifact(conn, r5, a5["artifact_id"], "successor-after-propagation")
            rem5 = remote(r5)
            c5 = v5["accept"] and v5["replica"]["generation"] == 9 and ad5["updated_rows"] == 1 and rem5["effect_count"] == 1 and rem5["effects"][0]["output_value"] == 30
            checks.append({"id": "fresh_successor_proof_succeeds_after_authority_propagation", "pass": c5, "points": 2, "evidence": {"proof": p5, "origin_head": head_generation(conn), "verdict": v5, "adoption": ad5, "write": w5, "remote": rem5}})

            score = sum(c["points"] for c in checks if c["pass"])
            result = {
                "benchmark": "RESONANCE Revocation Propagation / Stale Proof Registry Split-Brain",
                "benchmark_version": "1.0",
                "protocol": "RESONANCE Transactional Trust Protocol v1.0",
                "executed_at": datetime.now(timezone.utc).isoformat(),
                "database": {"server_version": conn.execute("SHOW server_version").fetchone()["server_version"]},
                "http_service": health,
                "http_service_image": IMAGE,
                "models": MODELS,
                "rules": RULES,
                "score": score,
                "max_score": 10,
                "classification": "Revocation propagation protocol passes" if score == 10 else "Revocation propagation protocol needs review",
                "invariants": [
                    "VALIDATION AGAINST A STALE AUTHORITY VIEW DOES NOT IMPLY CURRENT AUTHORIZATION.",
                    "REVOCATION PROPAGATION IS PART OF THE CONSEQUENCE SAFETY BOUNDARY.",
                    "REGIONAL AUTHORITY VIEWS MUST PROVE CURRENTNESS AGAINST A MONOTONIC AUTHORITATIVE GENERATION OR HOLD.",
                    "SPLIT-BRAIN AUTHORITY VERDICTS REQUIRE FAIL-CLOSED RECONCILIATION BEFORE CONSEQUENCE.",
                ],
                "checks": checks,
                "external_safety_certification": False,
                "vulnerability_claim": False,
            }
            (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
            (out / "RESULT.md").write_text(result_doc(result))
            print(json.dumps(result, indent=2, sort_keys=True))
            if score != 10:
                raise SystemExit(1)
        finally:
            stop_service()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="benchmark-results/revocation-propagation-v1.0")
    args = parser.parse_args()
    dsn = os.environ.get("DATABASE_URL", "postgresql://resonance:resonance@127.0.0.1:5432/resonance")
    run(dsn, args.out)


if __name__ == "__main__":
    main()
