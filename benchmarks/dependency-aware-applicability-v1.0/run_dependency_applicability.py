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

CONTAINER = "resonance-external-dependency-applicability"
VOLUME = "resonance-dependency-applicability-v1"
IMAGE = os.environ.get("HTTP_SERVICE_IMAGE", "python:3.12-slim")
BASE_URL = os.environ.get("EXTERNAL_BASE_URL", "http://127.0.0.1:18090")
SERVICE = Path("benchmarks/dependency-aware-applicability-v1.0/external_service.py").resolve()


def db(dsn):
    return psycopg.connect(dsn, autocommit=False)


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def sha(obj):
    return "sha256:" + hashlib.sha256(canonical(obj).encode()).hexdigest()


def dependency_fp(price, spend_limit):
    return sha({"price": int(price), "limit": int(spend_limit)})


def expected_output(price, spend_limit):
    return min(int(spend_limit), 2 * int(price))


def init_schema(dsn):
    with db(dsn) as c:
        with c.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS business_state(
                  resource_id text PRIMARY KEY,
                  global_version bigint NOT NULL,
                  price bigint NOT NULL,
                  spend_limit bigint NOT NULL,
                  theme text NOT NULL,
                  owner text NOT NULL,
                  fence bigint NOT NULL
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
                  dependency_fingerprint text NOT NULL,
                  input_price bigint NOT NULL,
                  input_limit bigint NOT NULL,
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
            cur.execute("DELETE FROM result_artifacts WHERE resource_id=%s", (rid,))
            cur.execute("DELETE FROM business_state WHERE resource_id=%s", (rid,))
        c.commit()


def seed(dsn, rid):
    reset(dsn, rid)
    with db(dsn) as c:
        with c.cursor() as cur:
            cur.execute("INSERT INTO business_state(resource_id,global_version,price,spend_limit,theme,owner,fence) VALUES (%s,100,10,30,'light','worker-B',2)", (rid,))
        c.commit()
    return state(dsn, rid)


def state(dsn, rid):
    with db(dsn) as c:
        with c.cursor() as cur:
            cur.execute("SELECT global_version,price,spend_limit,theme,owner,fence FROM business_state WHERE resource_id=%s", (rid,))
            r = cur.fetchone()
        c.commit()
    out = {"global_version": int(r[0]), "price": int(r[1]), "limit": int(r[2]), "theme": r[3], "owner": r[4], "fence": int(r[5])}
    out["dependency_fingerprint"] = dependency_fp(out["price"], out["limit"])
    out["expected_output"] = expected_output(out["price"], out["limit"])
    return out


def mutate(dsn, rid, *, price=None, spend_limit=None, theme=None):
    with db(dsn) as c:
        with c.cursor() as cur:
            sets = ["global_version=global_version+1"]
            vals = []
            if price is not None:
                sets.append("price=%s"); vals.append(price)
            if spend_limit is not None:
                sets.append("spend_limit=%s"); vals.append(spend_limit)
            if theme is not None:
                sets.append("theme=%s"); vals.append(theme)
            vals.append(rid)
            cur.execute(f"UPDATE business_state SET {', '.join(sets)} WHERE resource_id=%s", vals)
        c.commit()
    return state(dsn, rid)


def produce(dsn, aid, rid, producer, producer_fence):
    s = state(dsn, rid)
    payload = {
        "dependency_fingerprint": s["dependency_fingerprint"],
        "input_global_version": s["global_version"],
        "input_price": s["price"],
        "input_limit": s["limit"],
        "output_value": s["expected_output"],
        "producer": producer,
        "producer_fence": producer_fence,
    }
    digest = sha(payload)
    with db(dsn) as c:
        with c.cursor() as cur:
            cur.execute("""
                INSERT INTO result_artifacts(
                  artifact_id,resource_id,artifact_digest,producer,producer_fence,input_global_version,
                  dependency_fingerprint,input_price,input_limit,input_theme,output_value,state
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'READY')
            """, (aid,rid,digest,producer,producer_fence,s["global_version"],s["dependency_fingerprint"],s["price"],s["limit"],s["theme"],s["expected_output"]))
        c.commit()
    return artifact(dsn, aid)


def artifact(dsn, aid):
    with db(dsn) as c:
        with c.cursor() as cur:
            cur.execute("SELECT artifact_id,resource_id,artifact_digest,producer,producer_fence,input_global_version,dependency_fingerprint,input_price,input_limit,input_theme,output_value,state,adopted_by,adopted_fence FROM result_artifacts WHERE artifact_id=%s", (aid,))
            r = cur.fetchone()
        c.commit()
    keys = ["artifact_id","resource_id","artifact_digest","producer","producer_fence","input_global_version","dependency_fingerprint","input_price","input_limit","input_theme","output_value","state","adopted_by","adopted_fence"]
    out = dict(zip(keys, r))
    for k in ("producer_fence","input_global_version","input_price","input_limit","output_value","adopted_fence"):
        if out[k] is not None: out[k] = int(out[k])
    return out


def adopt(dsn, aid, rid, mode):
    with db(dsn) as c:
        with c.cursor() as cur:
            cur.execute("SELECT global_version,price,spend_limit,theme,owner,fence FROM business_state WHERE resource_id=%s FOR UPDATE", (rid,))
            s = cur.fetchone()
            cur.execute("SELECT input_global_version,dependency_fingerprint,state FROM result_artifacts WHERE artifact_id=%s FOR UPDATE", (aid,))
            a = cur.fetchone()
            current_fp = dependency_fp(s[1], s[2])
            current_owner = s[4] == "worker-B" and int(s[5]) == 2
            applicable = True
            reason = "adopted"
            if mode == "global" and int(a[0]) != int(s[0]):
                applicable = False; reason = "global_version_conflict"
            elif mode == "dependency" and a[1] != current_fp:
                applicable = False; reason = "dependency_conflict"
            rows = 0
            if current_owner and applicable and a[2] == "READY":
                cur.execute("UPDATE result_artifacts SET state='ADOPTED', adopted_by='worker-B', adopted_fence=2 WHERE artifact_id=%s AND state='READY'", (aid,))
                rows = cur.rowcount
        c.commit()
    return {"mode": mode, "updated_rows": rows, "reason": reason, "current_state": state(dsn, rid), "artifact": artifact(dsn, aid)}


def run(*args, check=True):
    return subprocess.run(args, text=True, capture_output=True, check=check)


def req_json(method, path, headers=None):
    r = urllib.request.Request(BASE_URL + path, method=method, data=b"{}" if method == "POST" else None, headers={"Content-Type":"application/json", **(headers or {})})
    try:
        with urllib.request.urlopen(r, timeout=5) as resp:
            return {"http_status": resp.status, "payload": json.loads(resp.read().decode())}
    except urllib.error.HTTPError as exc:
        return {"http_status": exc.code, "payload": json.loads(exc.read().decode())}


def start_service():
    run("docker","rm","-f",CONTAINER,check=False)
    run("docker","volume","rm","-f",VOLUME,check=False)
    run("docker","volume","create",VOLUME)
    run("docker","run","-d","--name",CONTAINER,"-p","18090:8080","-v",f"{VOLUME}:/state","-v",f"{SERVICE}:/app/external_service.py:ro",IMAGE,"python","/app/external_service.py","--host","0.0.0.0","--port","8080")
    for _ in range(40):
        try:
            h = req_json("GET","/health")
            if h["http_status"] == 200: return h["payload"]
        except Exception: pass
        time.sleep(0.25)
    raise RuntimeError("service not healthy")


def publish(rid, art, phase):
    return req_json("POST","/effects",{
        "X-Resource-Id": rid, "X-Worker":"worker-B", "X-Fencing-Token":"2",
        "X-Artifact-Digest":art["artifact_digest"], "X-Input-State-Version":str(art["input_global_version"]),
        "X-Output-Value":str(art["output_value"]), "X-Phase":phase,
    })


def remote(rid):
    return req_json("GET",f"/status/{rid}")["payload"]


def irrelevant_drift(dsn):
    rid="irrelevant-drift"; seed(dsn,rid)
    art=produce(dsn,"artifact-irrelevant",rid,"worker-A",1)
    before=state(dsn,rid); after=mutate(dsn,rid,theme="dark")
    global_attempt=adopt(dsn,art["artifact_id"],rid,"global")
    dep_attempt=adopt(dsn,art["artifact_id"],rid,"dependency")
    write=publish(rid,dep_attempt["artifact"],"irrelevant-drift-current") if dep_attempt["updated_rows"]==1 else None
    return {"before":before,"after":after,"artifact":art,"global_guard":global_attempt,"dependency_guard":dep_attempt,"write":write,"final_remote":remote(rid)}


def blind_relevant_drift(dsn):
    rid="blind-relevant-drift"; seed(dsn,rid)
    art=produce(dsn,"artifact-blind-price",rid,"worker-A",1)
    before=state(dsn,rid); after=mutate(dsn,rid,price=20)
    adoption=adopt(dsn,art["artifact_id"],rid,"blind")
    write=publish(rid,adoption["artifact"],"blind-relevant-drift")
    return {"before":before,"after":after,"artifact":art,"adoption":adoption,"write":write,"final_remote":remote(rid)}


def safe_relevant_drift(dsn):
    rid="safe-relevant-drift"; seed(dsn,rid)
    old=produce(dsn,"artifact-safe-old",rid,"worker-A",1)
    before=state(dsn,rid); after=mutate(dsn,rid,price=20)
    reject=adopt(dsn,old["artifact_id"],rid,"dependency")
    remote_after_reject=remote(rid)
    fresh=produce(dsn,"artifact-safe-fresh",rid,"worker-B",2)
    fresh_adoption=adopt(dsn,fresh["artifact_id"],rid,"dependency")
    write=publish(rid,fresh_adoption["artifact"],"fresh-dependency-recompute")
    return {"before":before,"after":after,"old_artifact":old,"stale_adoption":reject,"remote_after_reject":remote_after_reject,"fresh_artifact":fresh,"fresh_adoption":fresh_adoption,"write":write,"final_remote":remote(rid)}


def limit_dependency_guard(dsn):
    rid="limit-dependency-drift"; seed(dsn,rid)
    art=produce(dsn,"artifact-limit-old",rid,"worker-A",1)
    before=state(dsn,rid); after=mutate(dsn,rid,spend_limit=15)
    reject=adopt(dsn,art["artifact_id"],rid,"dependency")
    return {"before":before,"after":after,"artifact":art,"adoption":reject,"final_remote":remote(rid)}


def main():
    p=argparse.ArgumentParser(); p.add_argument("--dsn",default=os.environ.get("DATABASE_URL","postgresql://resonance:resonance@127.0.0.1:5432/resonance")); p.add_argument("--out",default="benchmark-results/dependency-aware-applicability-v1.0"); a=p.parse_args()
    out=Path(a.out); out.mkdir(parents=True,exist_ok=True); init_schema(a.dsn); health=start_service()
    try:
        irrelevant=irrelevant_drift(a.dsn)
        blind=blind_relevant_drift(a.dsn)
        safe=safe_relevant_drift(a.dsn)
        limit=limit_dependency_guard(a.dsn)
        with db(a.dsn) as c:
            with c.cursor() as cur: cur.execute("SHOW server_version"); pg=str(cur.fetchone()[0])
            c.commit()
        image_digest=run("docker","image","inspect",IMAGE,"--format","{{index .RepoDigests 0}}").stdout.strip()
        checks=[
            {"id":"irrelevant_drift_preserves_dependency_fingerprint_and_remains_applicable","points":2,"pass":irrelevant["before"]["global_version"]==100 and irrelevant["after"]["global_version"]==101 and irrelevant["before"]["dependency_fingerprint"]==irrelevant["after"]["dependency_fingerprint"] and irrelevant["dependency_guard"]["updated_rows"]==1 and irrelevant["final_remote"]["effect_count"]==1 and irrelevant["final_remote"]["effects"][0]["output_value"]==20,"evidence":irrelevant},
            {"id":"strict_global_version_guard_rejects_still_applicable_artifact","points":2,"pass":irrelevant["global_guard"]["updated_rows"]==0 and irrelevant["global_guard"]["reason"]=="global_version_conflict" and irrelevant["after"]["expected_output"]==irrelevant["artifact"]["output_value"],"evidence":{"artifact":irrelevant["artifact"],"after":irrelevant["after"],"global_guard":irrelevant["global_guard"]}},
            {"id":"blind_adoption_after_relevant_price_drift_commits_stale_result","points":2,"pass":blind["before"]["dependency_fingerprint"]!=blind["after"]["dependency_fingerprint"] and blind["adoption"]["updated_rows"]==1 and blind["final_remote"]["effect_count"]==1 and blind["final_remote"]["effects"][0]["output_value"]==20 and blind["after"]["expected_output"]==30,"evidence":blind},
            {"id":"dependency_guard_rejects_price_and_limit_drift","points":2,"pass":safe["stale_adoption"]["updated_rows"]==0 and safe["stale_adoption"]["reason"]=="dependency_conflict" and safe["remote_after_reject"]["effect_count"]==0 and limit["adoption"]["updated_rows"]==0 and limit["adoption"]["reason"]=="dependency_conflict" and limit["after"]["expected_output"]==15,"evidence":{"price_drift":safe["stale_adoption"],"limit_drift":limit}},
            {"id":"recompute_on_current_dependencies_commits_one_current_effect","points":2,"pass":safe["fresh_adoption"]["updated_rows"]==1 and safe["write"]["http_status"]==200 and safe["final_remote"]["effect_count"]==1 and safe["final_remote"]["effects"][0]["output_value"]==30 and safe["fresh_artifact"]["dependency_fingerprint"]==safe["after"]["dependency_fingerprint"],"evidence":safe},
        ]
        score=sum(x["points"] for x in checks if x["pass"])
        result={"benchmark":"RESONANCE Dependency-Aware Applicability / Relevant vs Irrelevant State Drift","benchmark_version":"1.0","protocol":"RESONANCE Transactional Trust Protocol v1.0","executed_at":datetime.now(timezone.utc).isoformat(),"database":{"server_version":pg},"http_service":health,"http_service_image":IMAGE,"http_service_image_digest":image_digest,"score":score,"max_score":10,"classification":"Dependency-aware applicability protocol passes" if score==10 else "Dependency-aware applicability protocol incomplete","checks":checks,"irrelevant_drift":irrelevant,"blind_relevant_drift":blind,"safe_relevant_drift":safe,"limit_dependency_guard":limit,"invariants":["STATE CHANGED DOES NOT IMPLY RELEVANT STATE CHANGED.","APPLICABILITY SHOULD BIND TO THE STATE SUBGRAPH THAT CAUSALLY JUSTIFIED THE RESULT.","GLOBAL VERSION MISMATCH MAY BE A CONSERVATIVE SIGNAL, NOT PROOF OF INVALIDITY.","DEPENDENCY FINGERPRINT MISMATCH REQUIRES REVALIDATION, RECOMPUTATION, OR DOMAIN PROOF BEFORE CONSEQUENCE."],"vulnerability_claim":False,"external_safety_certification":False}
        (out/"result.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
        md=["# Dependency-Aware Applicability v1.0","",f"Score: **{score}/10**","",f"- Irrelevant drift: global {irrelevant['before']['global_version']} → {irrelevant['after']['global_version']}; dependency fingerprint unchanged; dependency-aware adoption rows={irrelevant['dependency_guard']['updated_rows']}.",f"- Strict global-version guard on same artifact: rows={irrelevant['global_guard']['updated_rows']} / {irrelevant['global_guard']['reason']}.",f"- Relevant price drift: expected output {blind['before']['expected_output']} → {blind['after']['expected_output']}; blind commit output={blind['final_remote']['effects'][0]['output_value']}.",f"- Dependency-aware stale adoption: rows={safe['stale_adoption']['updated_rows']} / {safe['stale_adoption']['reason']}; effects before recompute={safe['remote_after_reject']['effect_count']}.",f"- Fresh recompute: output={safe['fresh_artifact']['output_value']}; final effects={safe['final_remote']['effect_count']}.",f"- Limit drift guard: expected output {limit['before']['expected_output']} → {limit['after']['expected_output']}; rows={limit['adoption']['updated_rows']}.","","**STATE CHANGED ≠ RELEVANT STATE CHANGED.**"]
        (out/"RESULT.md").write_text("\n".join(md)+"\n")
        print(json.dumps(result,indent=2,sort_keys=True))
        if score!=10: raise SystemExit(1)
    finally:
        run("docker","rm","-f",CONTAINER,check=False)
        run("docker","volume","rm","-f",VOLUME,check=False)

if __name__=="__main__": main()
