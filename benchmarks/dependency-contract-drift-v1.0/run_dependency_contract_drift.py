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

CONTAINER = "resonance-external-dependency-contract-drift"
VOLUME = "resonance-dependency-contract-drift-v1"
IMAGE = os.environ.get("HTTP_SERVICE_IMAGE", "python:3.12-slim")
BASE_URL = os.environ.get("EXTERNAL_BASE_URL", "http://127.0.0.1:18092")
SERVICE = Path("benchmarks/dependency-aware-applicability-v1.0/external_service.py").resolve()

MODEL_V1 = {
    "version": "model-v1",
    "dependencies": ["price", "limit"],
    "formula_id": "min_limit_2x_price",
}
MODEL_V2 = {
    "version": "model-v2",
    "dependencies": ["price", "limit", "tax_rate"],
    "formula_id": "min_limit_2x_price_plus_tax",
}


def db(dsn):
    return psycopg.connect(dsn, autocommit=False)


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def sha(obj):
    return "sha256:" + hashlib.sha256(canonical(obj).encode()).hexdigest()


def model_digest(model):
    return sha({"version": model["version"], "dependencies": model["dependencies"], "formula_id": model["formula_id"]})


def value_fp(model, s):
    vals = {k: int(s[k]) for k in model["dependencies"]}
    return sha({"model_version": model["version"], "values": vals})


def expected_output(model_version, s):
    if model_version == "model-v1":
        return min(int(s["limit"]), 2 * int(s["price"]))
    if model_version == "model-v2":
        return min(int(s["limit"]), 2 * int(s["price"]) + int(s["tax_rate"]))
    raise ValueError(model_version)


def init_schema(dsn):
    with db(dsn) as c:
        with c.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS causal_models(
                  model_version text PRIMARY KEY,
                  model_digest text NOT NULL,
                  dependency_manifest jsonb NOT NULL,
                  formula_id text NOT NULL
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS business_state(
                  resource_id text PRIMARY KEY,
                  global_version bigint NOT NULL,
                  price bigint NOT NULL,
                  spend_limit bigint NOT NULL,
                  tax_rate bigint NOT NULL,
                  theme text NOT NULL,
                  owner text NOT NULL,
                  fence bigint NOT NULL,
                  current_model_version text NOT NULL REFERENCES causal_models(model_version)
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS result_artifacts(
                  artifact_id text PRIMARY KEY,
                  resource_id text NOT NULL,
                  artifact_digest text NOT NULL,
                  producer text NOT NULL,
                  producer_fence bigint NOT NULL,
                  input_global_version bigint NOT NULL,
                  model_version text NOT NULL,
                  model_digest text NOT NULL,
                  dependency_manifest jsonb NOT NULL,
                  dependency_fingerprint text NOT NULL,
                  input_price bigint NOT NULL,
                  input_limit bigint NOT NULL,
                  input_tax_rate bigint NOT NULL,
                  output_value bigint NOT NULL,
                  state text NOT NULL,
                  adopted_by text,
                  adopted_fence bigint
                )
            """)
            for m in (MODEL_V1, MODEL_V2):
                cur.execute(
                    "INSERT INTO causal_models(model_version,model_digest,dependency_manifest,formula_id) VALUES (%s,%s,%s::jsonb,%s) ON CONFLICT(model_version) DO UPDATE SET model_digest=EXCLUDED.model_digest, dependency_manifest=EXCLUDED.dependency_manifest, formula_id=EXCLUDED.formula_id",
                    (m["version"], model_digest(m), json.dumps(m["dependencies"]), m["formula_id"]),
                )
        c.commit()


def reset(dsn, rid):
    with db(dsn) as c:
        with c.cursor() as cur:
            cur.execute("DELETE FROM result_artifacts WHERE resource_id=%s", (rid,))
            cur.execute("DELETE FROM business_state WHERE resource_id=%s", (rid,))
        c.commit()


def seed(dsn, rid):
    reset(dsn, rid)
    with db(dsn) as c:
        with c.cursor() as cur:
            cur.execute("""
                INSERT INTO business_state(resource_id,global_version,price,spend_limit,tax_rate,theme,owner,fence,current_model_version)
                VALUES (%s,100,10,30,2,'light','worker-B',2,'model-v1')
            """, (rid,))
        c.commit()
    return state(dsn, rid)


def get_model(dsn, version):
    with db(dsn) as c:
        with c.cursor() as cur:
            cur.execute("SELECT model_version,model_digest,dependency_manifest,formula_id FROM causal_models WHERE model_version=%s", (version,))
            r = cur.fetchone()
        c.commit()
    return {"version": r[0], "digest": r[1], "dependencies": list(r[2]), "formula_id": r[3]}


def state(dsn, rid):
    with db(dsn) as c:
        with c.cursor() as cur:
            cur.execute("SELECT global_version,price,spend_limit,tax_rate,theme,owner,fence,current_model_version FROM business_state WHERE resource_id=%s", (rid,))
            r = cur.fetchone()
        c.commit()
    out = {
        "global_version": int(r[0]),
        "price": int(r[1]),
        "limit": int(r[2]),
        "tax_rate": int(r[3]),
        "theme": r[4],
        "owner": r[5],
        "fence": int(r[6]),
        "current_model_version": r[7],
    }
    m = get_model(dsn, out["current_model_version"])
    out["current_model_digest"] = m["digest"]
    out["current_model_dependencies"] = m["dependencies"]
    out["current_dependency_fingerprint"] = value_fp({"version": m["version"], "dependencies": m["dependencies"]}, out)
    out["expected_output"] = expected_output(m["version"], out)
    return out


def switch_model(dsn, rid, version):
    with db(dsn) as c:
        with c.cursor() as cur:
            cur.execute("UPDATE business_state SET current_model_version=%s, global_version=global_version+1 WHERE resource_id=%s", (version, rid))
        c.commit()
    return state(dsn, rid)


def produce(dsn, aid, rid, producer="worker-A", producer_fence=1):
    s = state(dsn, rid)
    m = get_model(dsn, s["current_model_version"])
    fp = value_fp({"version": m["version"], "dependencies": m["dependencies"]}, s)
    out = expected_output(m["version"], s)
    payload = {
        "resource_id": rid,
        "producer": producer,
        "producer_fence": producer_fence,
        "input_global_version": s["global_version"],
        "model_version": m["version"],
        "model_digest": m["digest"],
        "dependency_manifest": m["dependencies"],
        "dependency_fingerprint": fp,
        "input_price": s["price"],
        "input_limit": s["limit"],
        "input_tax_rate": s["tax_rate"],
        "output_value": out,
    }
    digest = sha(payload)
    with db(dsn) as c:
        with c.cursor() as cur:
            cur.execute("""
                INSERT INTO result_artifacts(
                  artifact_id,resource_id,artifact_digest,producer,producer_fence,input_global_version,
                  model_version,model_digest,dependency_manifest,dependency_fingerprint,
                  input_price,input_limit,input_tax_rate,output_value,state
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s,%s,%s,%s,%s,'READY')
            """, (
                aid,rid,digest,producer,producer_fence,s["global_version"],m["version"],m["digest"],json.dumps(m["dependencies"]),fp,
                s["price"],s["limit"],s["tax_rate"],out,
            ))
        c.commit()
    return artifact(dsn, aid)


def artifact(dsn, aid):
    with db(dsn) as c:
        with c.cursor() as cur:
            cur.execute("""
                SELECT artifact_id,resource_id,artifact_digest,producer,producer_fence,input_global_version,
                       model_version,model_digest,dependency_manifest,dependency_fingerprint,
                       input_price,input_limit,input_tax_rate,output_value,state,adopted_by,adopted_fence
                FROM result_artifacts WHERE artifact_id=%s
            """, (aid,))
            r = cur.fetchone()
        c.commit()
    keys = [
        "artifact_id","resource_id","artifact_digest","producer","producer_fence","input_global_version",
        "model_version","model_digest","dependency_manifest","dependency_fingerprint",
        "input_price","input_limit","input_tax_rate","output_value","state","adopted_by","adopted_fence"
    ]
    out = dict(zip(keys, r))
    out["dependency_manifest"] = list(out["dependency_manifest"])
    for k in ("producer_fence","input_global_version","input_price","input_limit","input_tax_rate","output_value","adopted_fence"):
        if out[k] is not None:
            out[k] = int(out[k])
    return out


def adopt(dsn, aid, rid, mode):
    with db(dsn) as c:
        with c.cursor() as cur:
            cur.execute("SELECT global_version,price,spend_limit,tax_rate,theme,owner,fence,current_model_version FROM business_state WHERE resource_id=%s FOR UPDATE", (rid,))
            sr = cur.fetchone()
            current = {
                "global_version": int(sr[0]), "price": int(sr[1]), "limit": int(sr[2]), "tax_rate": int(sr[3]),
                "theme": sr[4], "owner": sr[5], "fence": int(sr[6]), "current_model_version": sr[7],
            }
            cur.execute("SELECT model_version,model_digest,dependency_manifest,dependency_fingerprint,state FROM result_artifacts WHERE artifact_id=%s FOR UPDATE", (aid,))
            ar = cur.fetchone()
            artifact_model_version = ar[0]
            artifact_model_digest = ar[1]
            artifact_deps = list(ar[2])
            artifact_fp = ar[3]
            artifact_state = ar[4]
            applicable = True
            reason = "adopted"

            if mode == "artifact_bound":
                check_model = {"version": artifact_model_version, "dependencies": artifact_deps}
                if value_fp(check_model, current) != artifact_fp:
                    applicable = False
                    reason = "artifact_bound_value_conflict"
            elif mode == "current_model":
                current_model = get_model(dsn, current["current_model_version"])
                if artifact_model_version != current_model["version"] or artifact_model_digest != current_model["digest"]:
                    applicable = False
                    reason = "model_version_conflict"
                else:
                    check_model = {"version": current_model["version"], "dependencies": current_model["dependencies"]}
                    if value_fp(check_model, current) != artifact_fp:
                        applicable = False
                        reason = "dependency_conflict"
            else:
                raise ValueError(mode)

            rows = 0
            current_owner = current["owner"] == "worker-B" and current["fence"] == 2
            if current_owner and applicable and artifact_state == "READY":
                cur.execute("UPDATE result_artifacts SET state='ADOPTED', adopted_by='worker-B', adopted_fence=2 WHERE artifact_id=%s AND state='READY'", (aid,))
                rows = cur.rowcount
        c.commit()
    return {"mode": mode, "updated_rows": rows, "reason": reason, "current_state": state(dsn, rid), "artifact": artifact(dsn, aid)}


def run(*args, check=True):
    return subprocess.run(args, text=True, capture_output=True, check=check)


def req_json(method, path, headers=None):
    r = urllib.request.Request(BASE_URL + path, method=method, data=b"{}" if method == "POST" else None, headers={"Content-Type": "application/json", **(headers or {})})
    try:
        with urllib.request.urlopen(r, timeout=5) as resp:
            return {"http_status": resp.status, "payload": json.loads(resp.read().decode())}
    except urllib.error.HTTPError as exc:
        return {"http_status": exc.code, "payload": json.loads(exc.read().decode())}


def start_service():
    run("docker", "rm", "-f", CONTAINER, check=False)
    run("docker", "volume", "rm", "-f", VOLUME, check=False)
    run("docker", "volume", "create", VOLUME)
    run("docker", "run", "-d", "--name", CONTAINER, "-p", "18092:8080", "-v", f"{VOLUME}:/state", "-v", f"{SERVICE}:/app/external_service.py:ro", IMAGE, "python", "/app/external_service.py", "--host", "0.0.0.0", "--port", "8080")
    for _ in range(40):
        try:
            h = req_json("GET", "/health")
            if h["http_status"] == 200:
                return h["payload"]
        except Exception:
            pass
        time.sleep(0.25)
    raise RuntimeError("service not healthy")


def publish(rid, art, phase):
    return req_json("POST", "/effects", {
        "X-Resource-Id": rid,
        "X-Worker": "worker-B",
        "X-Fencing-Token": "2",
        "X-Artifact-Digest": art["artifact_digest"],
        "X-Input-State-Version": str(art["input_global_version"]),
        "X-Output-Value": str(art["output_value"]),
        "X-Phase": phase,
    })


def remote(rid):
    return req_json("GET", f"/status/{rid}")["payload"]


def model_drift_observation(dsn):
    rid = "model-drift-observation"
    before = seed(dsn, rid)
    art = produce(dsn, "artifact-observation-v1", rid)
    after = switch_model(dsn, rid, "model-v2")
    return {"before": before, "artifact": art, "after": after}


def unsafe_artifact_bound(dsn):
    rid = "unsafe-artifact-bound"
    before = seed(dsn, rid)
    art = produce(dsn, "artifact-unsafe-v1", rid)
    after = switch_model(dsn, rid, "model-v2")
    adoption = adopt(dsn, art["artifact_id"], rid, "artifact_bound")
    write = publish(rid, adoption["artifact"], "unsafe-artifact-bound") if adoption["updated_rows"] == 1 else None
    return {"before": before, "artifact": art, "after": after, "adoption": adoption, "write": write, "final_remote": remote(rid)}


def safe_current_model(dsn):
    rid = "safe-current-model"
    before = seed(dsn, rid)
    old = produce(dsn, "artifact-safe-v1", rid)
    after = switch_model(dsn, rid, "model-v2")
    reject = adopt(dsn, old["artifact_id"], rid, "current_model")
    remote_after_reject = remote(rid)
    fresh = produce(dsn, "artifact-safe-v2", rid, producer="worker-B", producer_fence=2)
    fresh_adoption = adopt(dsn, fresh["artifact_id"], rid, "current_model")
    write = publish(rid, fresh_adoption["artifact"], "current-model-recompute") if fresh_adoption["updated_rows"] == 1 else None
    return {
        "before": before,
        "old_artifact": old,
        "after": after,
        "stale_adoption": reject,
        "remote_after_reject": remote_after_reject,
        "fresh_artifact": fresh,
        "fresh_adoption": fresh_adoption,
        "write": write,
        "final_remote": remote(rid),
    }


def no_drift_control(dsn):
    rid = "no-model-drift-control"
    before = seed(dsn, rid)
    art = produce(dsn, "artifact-control-v1", rid, producer="worker-B", producer_fence=2)
    adoption = adopt(dsn, art["artifact_id"], rid, "current_model")
    write = publish(rid, adoption["artifact"], "no-model-drift-control") if adoption["updated_rows"] == 1 else None
    return {"before": before, "artifact": art, "adoption": adoption, "write": write, "final_remote": remote(rid)}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dsn", default=os.environ.get("DATABASE_URL", "postgresql://resonance:resonance@127.0.0.1:5432/resonance"))
    p.add_argument("--out", default="benchmark-results/dependency-contract-drift-v1.0")
    a = p.parse_args()
    outdir = Path(a.out)
    outdir.mkdir(parents=True, exist_ok=True)
    init_schema(a.dsn)
    health = start_service()
    try:
        obs = model_drift_observation(a.dsn)
        unsafe = unsafe_artifact_bound(a.dsn)
        safe = safe_current_model(a.dsn)
        control = no_drift_control(a.dsn)
        with db(a.dsn) as c:
            with c.cursor() as cur:
                cur.execute("SHOW server_version")
                pg = str(cur.fetchone()[0])
            c.commit()
        image_digest = run("docker", "image", "inspect", IMAGE, "--format", "{{index .RepoDigests 0}}").stdout.strip()

        checks = [
            {
                "id": "artifact_valid_under_v1_and_only_model_identity_changes_before_adoption",
                "points": 2,
                "pass": obs["before"]["current_model_version"] == "model-v1"
                        and obs["artifact"]["model_version"] == "model-v1"
                        and obs["artifact"]["output_value"] == 20
                        and obs["after"]["current_model_version"] == "model-v2"
                        and obs["before"]["price"] == obs["after"]["price"]
                        and obs["before"]["limit"] == obs["after"]["limit"]
                        and obs["before"]["tax_rate"] == obs["after"]["tax_rate"]
                        and obs["before"]["expected_output"] == 20
                        and obs["after"]["expected_output"] == 22,
                "evidence": obs,
            },
            {
                "id": "artifact_bound_validation_accepts_old_model_and_commits_stale_output",
                "points": 2,
                "pass": unsafe["adoption"]["updated_rows"] == 1
                        and unsafe["adoption"]["reason"] == "adopted"
                        and unsafe["write"]["http_status"] == 200
                        and unsafe["final_remote"]["effect_count"] == 1
                        and unsafe["final_remote"]["effects"][0]["output_value"] == 20
                        and unsafe["after"]["expected_output"] == 22,
                "evidence": unsafe,
            },
            {
                "id": "current_model_guard_rejects_old_model_identity_with_zero_effects",
                "points": 2,
                "pass": safe["stale_adoption"]["updated_rows"] == 0
                        and safe["stale_adoption"]["reason"] == "model_version_conflict"
                        and safe["remote_after_reject"]["effect_count"] == 0,
                "evidence": {"old_artifact": safe["old_artifact"], "after": safe["after"], "stale_adoption": safe["stale_adoption"], "remote": safe["remote_after_reject"]},
            },
            {
                "id": "recompute_under_v2_commits_current_output_once",
                "points": 2,
                "pass": safe["fresh_artifact"]["model_version"] == "model-v2"
                        and safe["fresh_artifact"]["output_value"] == 22
                        and safe["fresh_adoption"]["updated_rows"] == 1
                        and safe["write"]["http_status"] == 200
                        and safe["final_remote"]["effect_count"] == 1
                        and safe["final_remote"]["effects"][0]["output_value"] == 22,
                "evidence": safe,
            },
            {
                "id": "no_model_drift_control_allows_current_v1_artifact",
                "points": 2,
                "pass": control["before"]["current_model_version"] == "model-v1"
                        and control["adoption"]["updated_rows"] == 1
                        and control["write"]["http_status"] == 200
                        and control["final_remote"]["effect_count"] == 1
                        and control["final_remote"]["effects"][0]["output_value"] == 20,
                "evidence": control,
            },
        ]
        score = sum(c["points"] for c in checks if c["pass"])
        result = {
            "benchmark": "RESONANCE Dependency Contract Drift / Model Version Race",
            "benchmark_version": "1.0",
            "protocol": "RESONANCE Transactional Trust Protocol v1.0",
            "classification": "Dependency contract drift protocol passes" if score == 10 else "Dependency contract drift protocol incomplete",
            "score": score,
            "max_score": 10,
            "executed_at": datetime.now(timezone.utc).isoformat(),
            "models": {
                "v1": {**MODEL_V1, "digest": model_digest(MODEL_V1)},
                "v2": {**MODEL_V2, "digest": model_digest(MODEL_V2)},
            },
            "invariants": [
                "MODEL VALID THEN ≠ MODEL VALID NOW.",
                "ARTIFACT MUST BIND THE CAUSAL-MODEL IDENTITY THAT AUTHORIZED ITS COMPUTATION.",
                "ADOPTION MUST COMPARE ARTIFACT MODEL IDENTITY WITH THE CURRENT AUTHORITATIVE MODEL BEFORE VALUE FINGERPRINT.",
                "MODEL DRIFT OR UNKNOWN COMPATIBILITY REQUIRES HOLD, REVALIDATION, RECOMPUTATION, OR EXPLICIT COMPATIBILITY PROOF BEFORE CONSEQUENCE.",
            ],
            "database": {"server_version": pg},
            "http_service": health,
            "http_service_image": IMAGE,
            "http_service_image_digest": image_digest,
            "model_drift_observation": obs,
            "unsafe_artifact_bound": unsafe,
            "safe_current_model": safe,
            "no_drift_control": control,
            "checks": checks,
            "vulnerability_claim": False,
            "external_safety_certification": False,
        }
        (outdir / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        lines = [
            "# RESONANCE Dependency Contract Drift / Model Version Race v1.0",
            "",
            f"Score: **{score}/10**",
            "",
            "Core: **MODEL VALID THEN ≠ MODEL VALID NOW**",
            "",
            f"- model-v1 output at production: {obs['artifact']['output_value']}",
            f"- business inputs changed during model switch: false",
            f"- model-v2 current expected output: {obs['after']['expected_output']}",
            f"- unsafe artifact-bound commit: {unsafe['final_remote']['effects'][0]['output_value'] if unsafe['final_remote']['effect_count'] else 'none'}",
            f"- safe stale-model adoption rows: {safe['stale_adoption']['updated_rows']} ({safe['stale_adoption']['reason']})",
            f"- safe current-model final output: {safe['final_remote']['effects'][0]['output_value'] if safe['final_remote']['effect_count'] else 'none'}",
            "",
        ]
        for chk in checks:
            lines.append(f"- {'PASS' if chk['pass'] else 'FAIL'} — {chk['id']} ({chk['points']} pts)")
        (outdir / "RESULT.md").write_text("\n".join(lines) + "\n")
        print(json.dumps(result, indent=2, sort_keys=True))
        if score != 10:
            raise SystemExit(1)
    finally:
        run("docker", "rm", "-f", CONTAINER, check=False)
        run("docker", "volume", "rm", "-f", VOLUME, check=False)


if __name__ == "__main__":
    main()
