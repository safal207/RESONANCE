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

CONTAINER = "resonance-external-authority-head-authenticity"
VOLUME = "resonance-authority-head-authenticity-v1"
IMAGE = os.environ.get("HTTP_SERVICE_IMAGE", "python:3.12-slim")
BASE_URL = os.environ.get("EXTERNAL_BASE_URL", "http://127.0.0.1:18096")
SERVICE = Path("benchmarks/dependency-aware-applicability-v1.0/external_service.py").resolve()

AUTHORITY_NAMESPACE = "resonance-proof-authority"
HEAD_KEY_ID = "authority-head-demo-key-v1"
HEAD_KEY = b"resonance-authority-head-demo-secret-v1"


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
        CREATE TABLE IF NOT EXISTS aha_state(
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
        CREATE TABLE IF NOT EXISTS aha_artifacts(
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
        CREATE TABLE IF NOT EXISTS aha_authority_replica(
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


def reset_replica(conn):
    conn.execute("DELETE FROM aha_authority_replica")
    r1 = RULES["R1"]
    conn.execute(
        "INSERT INTO aha_authority_replica(region,rule_id,rule_digest,status,generation,successor_rule_id) VALUES('region-B',%s,%s,'ACTIVE',7,NULL)",
        (r1["rule_id"], r1["digest"]),
    )
    conn.commit()


def set_replica_r1_revoked(conn):
    r1 = RULES["R1"]
    r2 = RULES["R2"]
    conn.execute(
        "UPDATE aha_authority_replica SET status='REVOKED',generation=8,successor_rule_id=%s WHERE region='region-B' AND rule_id=%s",
        (r2["rule_id"], r1["rule_id"]),
    )
    conn.commit()


def set_replica_r2_active(conn):
    r2 = RULES["R2"]
    conn.execute(
        """INSERT INTO aha_authority_replica(region,rule_id,rule_digest,status,generation,successor_rule_id)
           VALUES('region-B',%s,%s,'ACTIVE',9,NULL)
           ON CONFLICT(region,rule_id) DO UPDATE SET rule_digest=EXCLUDED.rule_digest,status='ACTIVE',generation=9,successor_rule_id=NULL""",
        (r2["rule_id"], r2["digest"]),
    )
    conn.commit()


def reset_resource(conn, resource_id, price=20, limit=30, tax_rate=8):
    conn.execute("DELETE FROM aha_artifacts WHERE resource_id=%s", (resource_id,))
    conn.execute("DELETE FROM aha_state WHERE resource_id=%s", (resource_id,))
    conn.execute(
        "INSERT INTO aha_state(resource_id,owner,fence,global_version,price,limit_value,tax_rate,current_model_version,current_model_digest) VALUES(%s,'worker-B',2,101,%s,%s,%s,'model-v2',%s)",
        (resource_id, price, limit, tax_rate, MODELS["model-v2"]["digest"]),
    )
    conn.commit()


def get_state(conn, resource_id):
    return conn.execute("SELECT * FROM aha_state WHERE resource_id=%s", (resource_id,)).fetchone()


def get_artifact(conn, resource_id, artifact_id):
    return conn.execute("SELECT * FROM aha_artifacts WHERE resource_id=%s AND artifact_id=%s", (resource_id, artifact_id)).fetchone()


def make_artifact(conn, resource_id, artifact_id):
    s = get_state(conn, resource_id)
    output = calc("model-v1", s["price"], s["limit_value"], s["tax_rate"])
    digest = artifact_digest(resource_id, artifact_id, "model-v1", s["price"], s["limit_value"], s["tax_rate"], output)
    conn.execute(
        """INSERT INTO aha_artifacts(resource_id,artifact_id,model_version,model_digest,dependency_fingerprint,input_values_fingerprint,output_value,artifact_digest)
           VALUES(%s,%s,'model-v1',%s,%s,%s,%s,%s)""",
        (resource_id, artifact_id, MODELS["model-v1"]["digest"], dep_fp("model-v1", s["price"], s["limit_value"], s["tax_rate"]), values_fp(s["price"], s["limit_value"], s["tax_rate"]), output, digest),
    )
    conn.commit()
    return get_artifact(conn, resource_id, artifact_id)


def replica_rule(conn, rule_id):
    return conn.execute("SELECT * FROM aha_authority_replica WHERE region='region-B' AND rule_id=%s", (rule_id,)).fetchone()


def proof_predicate(s):
    return s["tax_rate"] >= 0 and 2 * s["price"] >= s["limit_value"]


def issue_proof(conn, resource_id, artifact_id, rule_key="R1", generation=7):
    s = get_state(conn, resource_id)
    a = get_artifact(conn, resource_id, artifact_id)
    rule = RULES[rule_key]
    proof = {
        "rule_id": rule["rule_id"],
        "rule_digest": rule["digest"],
        "rule_generation": generation,
        "issued_status": "ACTIVE",
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


def head_payload(generation, rule_key, status, successor_rule_id=None):
    rule = RULES[rule_key]
    return {
        "authority_namespace": AUTHORITY_NAMESPACE,
        "generation": generation,
        "rule_id": rule["rule_id"],
        "rule_digest": rule["digest"],
        "status": status,
        "successor_rule_id": successor_rule_id,
    }


def sign_head(payload):
    msg = canonical(payload).encode()
    mac = hmac.new(HEAD_KEY, msg, hashlib.sha256).hexdigest()
    return {"alg": "HMAC-SHA256", "key_id": HEAD_KEY_ID, "payload": payload, "mac": mac}


def verify_head(attestation):
    if attestation.get("alg") != "HMAC-SHA256" or attestation.get("key_id") != HEAD_KEY_ID:
        return False
    payload = attestation.get("payload")
    if not isinstance(payload, dict) or payload.get("authority_namespace") != AUTHORITY_NAMESPACE:
        return False
    expected = hmac.new(HEAD_KEY, canonical(payload).encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, str(attestation.get("mac", "")))


def forged_lower_head(authentic_head):
    forged = json.loads(json.dumps(authentic_head))
    forged["payload"]["generation"] = 7
    forged["payload"]["status"] = "ACTIVE"
    forged["payload"]["successor_rule_id"] = None
    # Intentionally keep the generation-8 MAC. The claim changed; authentication must fail.
    return forged


def static_checks(s, a, proof):
    return {
        "from_model": proof["from_model_version"] == a["model_version"] and proof["from_model_digest"] == a["model_digest"],
        "to_model": proof["to_model_version"] == s["current_model_version"] and proof["to_model_digest"] == s["current_model_digest"],
        "artifact": proof["artifact_digest"] == a["artifact_digest"],
        "values": proof["current_values_fingerprint"] == values_fp(s["price"], s["limit_value"], s["tax_rate"]),
        "predicate": bool(proof["predicate_holds"]) and proof_predicate(s),
    }


def verdict(conn, resource_id, artifact_id, proof, head_attestation, authenticate_head=True):
    s = get_state(conn, resource_id)
    a = get_artifact(conn, resource_id, artifact_id)
    rep = replica_rule(conn, proof["rule_id"])
    head_ok = verify_head(head_attestation) if authenticate_head else True
    claimed = head_attestation.get("payload", {})
    checks = static_checks(s, a, proof)
    checks.update({
        "authority_head_authentic": head_ok,
        "replica_exists": rep is not None,
        "rule_digest": rep is not None and rep["rule_digest"] == proof["rule_digest"],
        "rule_active": rep is not None and rep["status"] == "ACTIVE",
        "rule_generation": rep is not None and rep["generation"] == proof["rule_generation"],
        "authority_view_fresh": head_ok and rep is not None and rep["generation"] >= int(claimed.get("generation", 10**9)),
    })
    if all(checks.values()):
        return {"accept": True, "reason": "proof_authorized_with_current_view", "checks": checks, "replica": dict(rep), "head": claimed}
    if authenticate_head and not head_ok:
        reason = "authority_head_authentication_failed"
    elif head_ok and rep is not None and rep["generation"] < int(claimed.get("generation", 10**9)):
        reason = "stale_authority_view"
    elif rep is not None and rep["status"] == "REVOKED":
        reason = "compatibility_proof_revoked"
    elif rep is not None and rep["generation"] != proof["rule_generation"]:
        reason = "compatibility_proof_authority_conflict"
    else:
        reason = "compatibility_proof_binding_conflict"
    return {"accept": False, "reason": reason, "checks": checks, "replica": dict(rep) if rep else None, "head": claimed}


def adopt(conn, resource_id, artifact_id, proof, decision):
    if not decision["accept"]:
        return {"updated_rows": 0, "reason": decision["reason"]}
    cur = conn.execute(
        """UPDATE aha_artifacts a SET state='ADOPTED',adopted_by=s.owner,adopted_fence=s.fence,proof_digest=%s
           FROM aha_state s WHERE a.resource_id=s.resource_id AND a.resource_id=%s AND a.artifact_id=%s AND a.state='READY'
           RETURNING a.artifact_id""",
        (proof["proof_digest"], resource_id, artifact_id),
    )
    rows = cur.rowcount
    conn.commit()
    return {"updated_rows": rows, "reason": "adopted" if rows else "compare_and_adopt_conflict"}


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


def run(dsn, out_dir):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    with db(dsn) as conn:
        init_schema(conn)
        reset_replica(conn)
        health = start_service()
        checks = []
        try:
            # 1. Synchronized control with authentic generation-7 head.
            r1 = "authentic-active-control"
            reset_resource(conn, r1)
            a1 = make_artifact(conn, r1, "artifact-v1-control")
            p1 = issue_proof(conn, r1, a1["artifact_id"], "R1", 7)
            h7 = sign_head(head_payload(7, "R1", "ACTIVE"))
            v1 = verdict(conn, r1, a1["artifact_id"], p1, h7, True)
            ad1 = adopt(conn, r1, a1["artifact_id"], p1, v1)
            w1 = commit_artifact(conn, r1, a1["artifact_id"], "authentic-head-control")
            rem1 = remote(r1)
            ok1 = verify_head(h7) and v1["accept"] and ad1["updated_rows"] == 1 and rem1["effect_count"] == 1 and rem1["effects"][0]["output_value"] == 30
            checks.append({"id": "authentic_current_head_authorizes_synchronized_active_replica", "pass": ok1, "points": 2, "evidence": {"head": h7, "verdict": v1, "adoption": ad1, "write": w1, "remote": rem1}})

            # Origin advances to generation 8 / R1 revoked. Region B intentionally remains at gen 7 / ACTIVE.
            h8 = sign_head(head_payload(8, "R1", "REVOKED", RULES["R2"]["rule_id"]))
            forged_h7 = forged_lower_head(h8)

            # 2. Unsafe verifier trusts the forged generation claim without authenticating it.
            r2 = "unsafe-forged-watermark"
            reset_resource(conn, r2)
            a2 = make_artifact(conn, r2, "artifact-v1-forged")
            p2 = issue_proof(conn, r2, a2["artifact_id"], "R1", 7)
            v2 = verdict(conn, r2, a2["artifact_id"], p2, forged_h7, False)
            ad2 = adopt(conn, r2, a2["artifact_id"], p2, v2)
            w2 = commit_artifact(conn, r2, a2["artifact_id"], "unsafe-forged-head")
            rem2 = remote(r2)
            ok2 = (not verify_head(forged_h7)) and v2["accept"] and ad2["updated_rows"] == 1 and rem2["effect_count"] == 1
            checks.append({"id": "unauthenticated_forged_head_makes_stale_replica_look_fresh_and_commit", "pass": ok2, "points": 2, "evidence": {"authentic_head_8": h8, "forged_head": forged_h7, "forged_head_authenticates": verify_head(forged_h7), "verdict": v2, "adoption": ad2, "write": w2, "remote": rem2}})

            # 3. Safe verifier rejects the exact same forged head before consequence.
            r3 = "safe-forged-watermark"
            reset_resource(conn, r3)
            a3 = make_artifact(conn, r3, "artifact-v1-safe-forged")
            p3 = issue_proof(conn, r3, a3["artifact_id"], "R1", 7)
            v3 = verdict(conn, r3, a3["artifact_id"], p3, forged_h7, True)
            ad3 = adopt(conn, r3, a3["artifact_id"], p3, v3)
            rem3 = remote(r3)
            ok3 = (not v3["accept"]) and v3["reason"] == "authority_head_authentication_failed" and ad3["updated_rows"] == 0 and rem3["effect_count"] == 0
            checks.append({"id": "authenticated_verifier_rejects_forged_head_with_zero_effects", "pass": ok3, "points": 2, "evidence": {"forged_head": forged_h7, "verdict": v3, "adoption": ad3, "remote": rem3}})

            # 4. Authentic current head reveals the same replica is stale; propagation then converges it to REVOKED.
            r4 = "authentic-current-head"
            reset_resource(conn, r4)
            a4 = make_artifact(conn, r4, "artifact-v1-authentic-current")
            p4 = issue_proof(conn, r4, a4["artifact_id"], "R1", 7)
            stale_v = verdict(conn, r4, a4["artifact_id"], p4, h8, True)
            stale_ad = adopt(conn, r4, a4["artifact_id"], p4, stale_v)
            before = remote(r4)
            set_replica_r1_revoked(conn)
            revoked_v = verdict(conn, r4, a4["artifact_id"], p4, h8, True)
            revoked_ad = adopt(conn, r4, a4["artifact_id"], p4, revoked_v)
            after = remote(r4)
            ok4 = verify_head(h8) and stale_v["reason"] == "stale_authority_view" and stale_ad["updated_rows"] == 0 and before["effect_count"] == 0 and revoked_v["reason"] == "compatibility_proof_revoked" and revoked_ad["updated_rows"] == 0 and after["effect_count"] == 0
            checks.append({"id": "authentic_generation_8_head_exposes_stale_view_then_propagation_converges_to_revoked", "pass": ok4, "points": 2, "evidence": {"head": h8, "stale_verdict": stale_v, "stale_adoption": stale_ad, "after_propagation_verdict": revoked_v, "after_propagation_adoption": revoked_ad, "remote": after}})

            # 5. Fresh successor R2 at authentic generation 9 succeeds.
            set_replica_r2_active(conn)
            r5 = "successor-authentic-head"
            reset_resource(conn, r5)
            a5 = make_artifact(conn, r5, "artifact-v1-successor")
            p5 = issue_proof(conn, r5, a5["artifact_id"], "R2", 9)
            h9 = sign_head(head_payload(9, "R2", "ACTIVE"))
            v5 = verdict(conn, r5, a5["artifact_id"], p5, h9, True)
            ad5 = adopt(conn, r5, a5["artifact_id"], p5, v5)
            w5 = commit_artifact(conn, r5, a5["artifact_id"], "successor-authentic-head")
            rem5 = remote(r5)
            ok5 = verify_head(h9) and v5["accept"] and ad5["updated_rows"] == 1 and rem5["effect_count"] == 1 and rem5["effects"][0]["output_value"] == 30
            checks.append({"id": "fresh_successor_proof_with_authentic_generation_9_head_succeeds", "pass": ok5, "points": 2, "evidence": {"head": h9, "proof": p5, "verdict": v5, "adoption": ad5, "write": w5, "remote": rem5}})

            score = sum(c["points"] for c in checks if c["pass"])
            result = {
                "benchmark": "RESONANCE Authority Head Authenticity / Forged Freshness Watermark",
                "benchmark_version": "1.0",
                "protocol": "RESONANCE Transactional Trust Protocol v1.0",
                "executed_at": datetime.now(timezone.utc).isoformat(),
                "database": {"server_version": conn.info.server_version // 10000 if False else conn.execute("SHOW server_version").fetchone()["server_version"]},
                "http_service": health,
                "http_service_image": IMAGE,
                "authentication_fixture": {"algorithm": "HMAC-SHA256", "key_id": HEAD_KEY_ID, "production_pki": False},
                "models": MODELS,
                "rules": RULES,
                "checks": checks,
                "score": score,
                "max_score": 10,
                "classification": "Authority head authenticity protocol passes" if score == 10 else "Authority head authenticity protocol incomplete",
                "invariants": [
                    "FRESHNESS CLAIM DOES NOT IMPLY AUTHENTIC FRESHNESS EVIDENCE.",
                    "AUTHORITY HEAD IDENTITY, DOMAIN, GENERATION, AND CONTENT MUST BE AUTHENTICATED BEFORE THEY CAN FENCE A CONSEQUENCE.",
                    "AN UNAUTHENTICATED OR TAMPERED AUTHORITY HEAD MUST FAIL CLOSED BEFORE REGIONAL FRESHNESS IS EVALUATED.",
                    "AUTHENTIC HEAD EVIDENCE CAN FENCE A STALE REPLICA, BUT AUTHENTIC OLD-HEAD REPLAY REQUIRES AN ADDITIONAL MONOTONICITY MECHANISM.",
                ],
                "external_safety_certification": False,
                "vulnerability_claim": False,
            }
            (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
            summary = [
                "# Authority Head Authenticity v1.0",
                "",
                f"Score: **{score}/10**",
                "",
            ]
            for c in checks:
                summary.append(f"- {'PASS' if c['pass'] else 'FAIL'} · {c['id']} · {c['points'] if c['pass'] else 0}/{c['points']}")
            summary += ["", f"Classification: **{result['classification']}**", ""]
            (out / "RESULT.md").write_text("\n".join(summary))
            print(json.dumps(result, indent=2, sort_keys=True))
            if score != 10:
                raise SystemExit(1)
            return result
        finally:
            stop_service()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dsn", default=os.environ.get("DATABASE_URL", "postgresql://resonance:resonance@127.0.0.1:5432/resonance"))
    p.add_argument("--out", default="benchmark-results/authority-head-authenticity-v1.0")
    args = p.parse_args()
    run(args.dsn, args.out)


if __name__ == "__main__":
    main()
