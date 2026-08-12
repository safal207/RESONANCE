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

CONTAINER = "resonance-external-incomplete-causal-graph"
VOLUME = "resonance-incomplete-causal-graph-v1"
IMAGE = os.environ.get("HTTP_SERVICE_IMAGE", "python:3.12-slim")
BASE_URL = os.environ.get("EXTERNAL_BASE_URL", "http://127.0.0.1:18091")
SERVICE = Path("benchmarks/dependency-aware-applicability-v1.0/external_service.py").resolve()
AUTHORITATIVE_DEPS = ("price", "limit", "tax_rate")
INCOMPLETE_DEPS = ("price", "limit")


def db(dsn):
    return psycopg.connect(dsn, autocommit=False)


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def sha(obj):
    return "sha256:" + hashlib.sha256(canonical(obj).encode()).hexdigest()


def manifest_digest(deps):
    return sha({"dependencies": list(deps)})


def dependency_fp(s, deps):
    return sha({k: s[k] for k in deps})


def expected_output(s):
    return min(int(s["limit"]), 2 * int(s["price"]) + int(s["tax_rate"]))


def init_schema(dsn):
    with db(dsn) as c:
        with c.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS causal_business_state(
                  resource_id text PRIMARY KEY,
                  global_version bigint NOT NULL,
                  price bigint NOT NULL,
                  spend_limit bigint NOT NULL,
                  tax_rate bigint NOT NULL,
                  theme text NOT NULL,
                  owner text NOT NULL,
                  fence bigint NOT NULL
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS causal_artifacts(
                  artifact_id text PRIMARY KEY,
                  resource_id text NOT NULL,
                  artifact_digest text NOT NULL,
                  producer text NOT NULL,
                  producer_fence bigint NOT NULL,
                  input_global_version bigint NOT NULL,
                  dependency_manifest text NOT NULL,
                  dependency_manifest_digest text NOT NULL,
                  dependency_fingerprint text NOT NULL,
                  input_price bigint NOT NULL,
                  input_limit bigint NOT NULL,
                  input_tax_rate bigint NOT NULL,
                  input_theme text NOT NULL,
                  output_value bigint NOT NULL,
                  state text NOT NULL,
                  adopted_by text,
                  adopted_fence bigint
                )
            """)
        c.commit()


def reset(dsn, rid):
    with db(dsn) as c:
        with c.cursor() as cur:
            cur.execute("DELETE FROM causal_artifacts WHERE resource_id=%s", (rid,))
            cur.execute("DELETE FROM causal_business_state WHERE resource_id=%s", (rid,))
        c.commit()


def seed(dsn, rid):
    reset(dsn, rid)
    with db(dsn) as c:
        with c.cursor() as cur:
            cur.execute("""
                INSERT INTO causal_business_state(resource_id,global_version,price,spend_limit,tax_rate,theme,owner,fence)
                VALUES (%s,100,10,30,2,'light','worker-B',2)
            """, (rid,))
        c.commit()
    return state(dsn, rid)


def state(dsn, rid):
    with db(dsn) as c:
        with c.cursor() as cur:
            cur.execute("SELECT global_version,price,spend_limit,tax_rate,theme,owner,fence FROM causal_business_state WHERE resource_id=%s", (rid,))
            r = cur.fetchone()
        c.commit()
    out = {
        "global_version": int(r[0]), "price": int(r[1]), "limit": int(r[2]),
        "tax_rate": int(r[3]), "theme": r[4], "owner": r[5], "fence": int(r[6])
    }
    out["declared_incomplete_fingerprint"] = dependency_fp(out, INCOMPLETE_DEPS)
    out["authoritative_fingerprint"] = dependency_fp(out, AUTHORITATIVE_DEPS)
    out["expected_output"] = expected_output(out)
    return out


def mutate(dsn, rid, *, tax_rate=None, theme=None):
    with db(dsn) as c:
        with c.cursor() as cur:
            sets = ["global_version=global_version+1"]
            vals = []
            if tax_rate is not None:
                sets.append("tax_rate=%s"); vals.append(tax_rate)
            if theme is not None:
                sets.append("theme=%s"); vals.append(theme)
            vals.append(rid)
            cur.execute(f"UPDATE causal_business_state SET {', '.join(sets)} WHERE resource_id=%s", vals)
        c.commit()
    return state(dsn, rid)


def produce(dsn, aid, rid, producer, producer_fence, deps):
    s = state(dsn, rid)
    fp = dependency_fp(s, deps)
    md = manifest_digest(deps)
    payload = {
        "dependency_manifest": list(deps), "dependency_manifest_digest": md,
        "dependency_fingerprint": fp, "input_global_version": s["global_version"],
        "output_value": s["expected_output"], "producer": producer, "producer_fence": producer_fence,
    }
    digest = sha(payload)
    with db(dsn) as c:
        with c.cursor() as cur:
            cur.execute("""
                INSERT INTO causal_artifacts(
                  artifact_id,resource_id,artifact_digest,producer,producer_fence,input_global_version,
                  dependency_manifest,dependency_manifest_digest,dependency_fingerprint,
                  input_price,input_limit,input_tax_rate,input_theme,output_value,state
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'READY')
            """, (aid,rid,digest,producer,producer_fence,s["global_version"],canonical(list(deps)),md,fp,
                  s["price"],s["limit"],s["tax_rate"],s["theme"],s["expected_output"]))
        c.commit()
    return artifact(dsn, aid)


def artifact(dsn, aid):
    with db(dsn) as c:
        with c.cursor() as cur:
            cur.execute("""
                SELECT artifact_id,resource_id,artifact_digest,producer,producer_fence,input_global_version,
                       dependency_manifest,dependency_manifest_digest,dependency_fingerprint,input_price,input_limit,
                       input_tax_rate,input_theme,output_value,state,adopted_by,adopted_fence
                FROM causal_artifacts WHERE artifact_id=%s
            """, (aid,))
            r = cur.fetchone()
        c.commit()
    keys = ["artifact_id","resource_id","artifact_digest","producer","producer_fence","input_global_version",
            "dependency_manifest","dependency_manifest_digest","dependency_fingerprint","input_price","input_limit",
            "input_tax_rate","input_theme","output_value","state","adopted_by","adopted_fence"]
    out = dict(zip(keys, r))
    out["dependency_manifest"] = json.loads(out["dependency_manifest"])
    for k in ("producer_fence","input_global_version","input_price","input_limit","input_tax_rate","output_value","adopted_fence"):
        if out[k] is not None: out[k] = int(out[k])
    return out


def adopt(dsn, aid, rid, mode):
    with db(dsn) as c:
        with c.cursor() as cur:
            cur.execute("SELECT global_version,price,spend_limit,tax_rate,theme,owner,fence FROM causal_business_state WHERE resource_id=%s FOR UPDATE", (rid,))
            srow = cur.fetchone()
            current = {"global_version":int(srow[0]),"price":int(srow[1]),"limit":int(srow[2]),"tax_rate":int(srow[3]),"theme":srow[4],"owner":srow[5],"fence":int(srow[6])}
            cur.execute("SELECT dependency_manifest,dependency_manifest_digest,dependency_fingerprint,state FROM causal_artifacts WHERE artifact_id=%s FOR UPDATE", (aid,))
            a = cur.fetchone()
            deps = tuple(json.loads(a[0]))
            applicable = True
            reason = "adopted"
            if mode == "declared_only":
                if a[2] != dependency_fp(current, deps):
                    applicable = False; reason = "declared_dependency_conflict"
            elif mode == "contract":
                if a[1] != manifest_digest(AUTHORITATIVE_DEPS):
                    applicable = False; reason = "dependency_manifest_conflict"
                elif a[2] != dependency_fp(current, AUTHORITATIVE_DEPS):
                    applicable = False; reason = "dependency_value_conflict"
            rows = 0
            if current["owner"] == "worker-B" and current["fence"] == 2 and applicable and a[3] == "READY":
                cur.execute("UPDATE causal_artifacts SET state='ADOPTED', adopted_by='worker-B', adopted_fence=2 WHERE artifact_id=%s AND state='READY'", (aid,))
                rows = cur.rowcount
        c.commit()
    return {"mode":mode,"updated_rows":rows,"reason":reason,"current_state":state(dsn,rid),"artifact":artifact(dsn,aid)}


def run(*args, check=True):
    return subprocess.run(args, text=True, capture_output=True, check=check)


def req_json(method, path, headers=None):
    r = urllib.request.Request(BASE_URL + path, method=method, data=b"{}" if method == "POST" else None,
                               headers={"Content-Type":"application/json", **(headers or {})})
    try:
        with urllib.request.urlopen(r, timeout=5) as resp:
            return {"http_status":resp.status,"payload":json.loads(resp.read().decode())}
    except urllib.error.HTTPError as exc:
        return {"http_status":exc.code,"payload":json.loads(exc.read().decode())}


def start_service():
    run("docker","rm","-f",CONTAINER,check=False)
    run("docker","volume","rm","-f",VOLUME,check=False)
    run("docker","volume","create",VOLUME)
    run("docker","run","-d","--name",CONTAINER,"-p","18091:8080","-v",f"{VOLUME}:/state",
        "-v",f"{SERVICE}:/app/external_service.py:ro",IMAGE,"python","/app/external_service.py","--host","0.0.0.0","--port","8080")
    for _ in range(40):
        try:
            h=req_json("GET","/health")
            if h["http_status"]==200: return h["payload"]
        except Exception: pass
        time.sleep(0.25)
    raise RuntimeError("service not healthy")


def publish(rid, art, phase):
    return req_json("POST","/effects",{
        "X-Resource-Id":rid,"X-Worker":"worker-B","X-Fencing-Token":"2",
        "X-Artifact-Digest":art["artifact_digest"],"X-Input-State-Version":str(art["input_global_version"]),
        "X-Output-Value":str(art["output_value"]),"X-Phase":phase,
    })


def remote(rid):
    return req_json("GET",f"/status/{rid}")["payload"]


def omitted_drift(dsn):
    rid="omitted-tax-drift"; before=seed(dsn,rid)
    art=produce(dsn,"artifact-incomplete",rid,"worker-A",1,INCOMPLETE_DEPS)
    after=mutate(dsn,rid,tax_rate=8)
    return {"before":before,"after":after,"artifact":art}


def unsafe_declared_only(dsn):
    rid="unsafe-incomplete"; before=seed(dsn,rid)
    art=produce(dsn,"artifact-unsafe",rid,"worker-A",1,INCOMPLETE_DEPS)
    after=mutate(dsn,rid,tax_rate=8)
    adoption=adopt(dsn,art["artifact_id"],rid,"declared_only")
    write=publish(rid,adoption["artifact"],"unsafe-incomplete-manifest") if adoption["updated_rows"]==1 else None
    return {"before":before,"after":after,"artifact":art,"adoption":adoption,"write":write,"final_remote":remote(rid)}


def safe_contract(dsn):
    rid="safe-complete-contract"; before=seed(dsn,rid)
    old=produce(dsn,"artifact-safe-incomplete",rid,"worker-A",1,INCOMPLETE_DEPS)
    after=mutate(dsn,rid,tax_rate=8)
    reject=adopt(dsn,old["artifact_id"],rid,"contract")
    remote_after_reject=remote(rid)
    fresh=produce(dsn,"artifact-safe-complete",rid,"worker-B",2,AUTHORITATIVE_DEPS)
    accept=adopt(dsn,fresh["artifact_id"],rid,"contract")
    write=publish(rid,accept["artifact"],"complete-causal-recompute") if accept["updated_rows"]==1 else None
    return {"before":before,"after":after,"old_artifact":old,"stale_adoption":reject,"remote_after_reject":remote_after_reject,
            "fresh_artifact":fresh,"fresh_adoption":accept,"write":write,"final_remote":remote(rid)}


def irrelevant_control(dsn):
    rid="complete-irrelevant-control"; before=seed(dsn,rid)
    art=produce(dsn,"artifact-complete-control",rid,"worker-B",2,AUTHORITATIVE_DEPS)
    after=mutate(dsn,rid,theme="dark")
    adoption=adopt(dsn,art["artifact_id"],rid,"contract")
    write=publish(rid,adoption["artifact"],"complete-irrelevant-control") if adoption["updated_rows"]==1 else None
    return {"before":before,"after":after,"artifact":art,"adoption":adoption,"write":write,"final_remote":remote(rid)}


def main():
    p=argparse.ArgumentParser(); p.add_argument("--dsn",default=os.environ.get("DATABASE_URL","postgresql://resonance:resonance@127.0.0.1:5432/resonance")); p.add_argument("--out",default="benchmark-results/incomplete-causal-graph-v1.0"); a=p.parse_args()
    out=Path(a.out); out.mkdir(parents=True,exist_ok=True); init_schema(a.dsn); health=start_service()
    try:
        omitted=omitted_drift(a.dsn); unsafe=unsafe_declared_only(a.dsn); safe=safe_contract(a.dsn); control=irrelevant_control(a.dsn)
        with db(a.dsn) as c:
            with c.cursor() as cur: cur.execute("SHOW server_version"); pg=str(cur.fetchone()[0])
            c.commit()
        image_digest=run("docker","image","inspect",IMAGE,"--format","{{index .RepoDigests 0}}").stdout.strip()
        checks=[
            {"id":"omitted_tax_drift_preserves_incomplete_fingerprint_while_output_changes","points":2,"pass":omitted["before"]["declared_incomplete_fingerprint"]==omitted["after"]["declared_incomplete_fingerprint"] and omitted["before"]["authoritative_fingerprint"]!=omitted["after"]["authoritative_fingerprint"] and omitted["before"]["expected_output"]==22 and omitted["after"]["expected_output"]==28,"evidence":omitted},
            {"id":"declared_only_guard_accepts_incomplete_model_and_commits_stale_output","points":2,"pass":unsafe["adoption"]["updated_rows"]==1 and unsafe["adoption"]["reason"]=="adopted" and unsafe["write"]["http_status"]==200 and unsafe["final_remote"]["effect_count"]==1 and unsafe["final_remote"]["effects"][0]["output_value"]==22 and unsafe["after"]["expected_output"]==28,"evidence":unsafe},
            {"id":"authoritative_dependency_manifest_rejects_omitted_causal_input","points":2,"pass":safe["stale_adoption"]["updated_rows"]==0 and safe["stale_adoption"]["reason"]=="dependency_manifest_conflict" and safe["remote_after_reject"]["effect_count"]==0,"evidence":{"artifact":safe["old_artifact"],"after":safe["after"],"adoption":safe["stale_adoption"],"remote":safe["remote_after_reject"]}},
            {"id":"complete_recompute_commits_current_output_once","points":2,"pass":safe["fresh_adoption"]["updated_rows"]==1 and safe["fresh_artifact"]["dependency_manifest"]==list(AUTHORITATIVE_DEPS) and safe["fresh_artifact"]["output_value"]==28 and safe["final_remote"]["effect_count"]==1 and safe["final_remote"]["effects"][0]["output_value"]==28,"evidence":safe},
            {"id":"complete_model_preserves_applicability_across_irrelevant_theme_drift","points":2,"pass":control["before"]["global_version"]==100 and control["after"]["global_version"]==101 and control["before"]["authoritative_fingerprint"]==control["after"]["authoritative_fingerprint"] and control["adoption"]["updated_rows"]==1 and control["final_remote"]["effect_count"]==1 and control["final_remote"]["effects"][0]["output_value"]==22,"evidence":control},
        ]
        score=sum(x["points"] for x in checks if x["pass"])
        result={"benchmark":"RESONANCE Missing Dependency / Incomplete Causal Graph","benchmark_version":"1.0","protocol":"RESONANCE Transactional Trust Protocol v1.0","executed_at":datetime.now(timezone.utc).isoformat(),"database":{"server_version":pg},"http_service":health,"http_service_image":IMAGE,"http_service_image_digest":image_digest,"authoritative_dependency_contract":list(AUTHORITATIVE_DEPS),"incomplete_declared_dependencies":list(INCOMPLETE_DEPS),"omitted_dependency_drift":omitted,"unsafe_declared_only":unsafe,"safe_authoritative_contract":safe,"irrelevant_control":control,"checks":checks,"score":score,"max_score":10,"classification":"Incomplete causal graph protocol passes" if score==10 else "Incomplete causal graph protocol failed","invariants":["A CORRECT FINGERPRINT OVER AN INCOMPLETE DEPENDENCY SET IS STILL UNSAFE.","DEPENDENCY-SET IDENTITY IS PART OF APPLICABILITY EVIDENCE.","ADOPTION MUST VALIDATE THE DEPENDENCY MANIFEST, NOT ONLY THE FINGERPRINT VALUES.","OMITTED OR UNKNOWN CAUSAL INPUT REQUIRES REVALIDATION, RECOMPUTATION, OR HOLD BEFORE CONSEQUENCE."],"vulnerability_claim":False,"external_safety_certification":False}
        (out/"result.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
        (out/"RESULT.md").write_text(f"# Incomplete Causal Graph v1.0\n\nScore: **{score}/10**\n\n- incomplete fingerprint unchanged under tax drift: **{omitted['before']['declared_incomplete_fingerprint']==omitted['after']['declared_incomplete_fingerprint']}**\n- real output: **22 → 28**\n- unsafe declared-only adoption rows: **{unsafe['adoption']['updated_rows']}**\n- unsafe committed output: **{unsafe['final_remote']['effects'][0]['output_value']}**\n- manifest-aware stale adoption rows: **{safe['stale_adoption']['updated_rows']}**\n- safe current output: **{safe['final_remote']['effects'][0]['output_value']}**\n")
        print(json.dumps(result,indent=2,sort_keys=True))
        if score != 10: raise SystemExit(1)
    finally:
        run("docker","rm","-f",CONTAINER,check=False)

if __name__ == "__main__":
    main()
