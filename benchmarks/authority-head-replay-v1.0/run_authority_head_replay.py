from __future__ import annotations

import argparse, hashlib, hmac, json, os, subprocess, time, urllib.error, urllib.request
from datetime import datetime, timezone
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

CONTAINER = "resonance-external-authority-head-replay"
VOLUME = "resonance-authority-head-replay-v1"
IMAGE = os.environ.get("HTTP_SERVICE_IMAGE", "python:3.12-slim")
BASE_URL = os.environ.get("EXTERNAL_BASE_URL", "http://127.0.0.1:18097")
SERVICE = Path("benchmarks/dependency-aware-applicability-v1.0/external_service.py").resolve()
KEY = b"resonance-authority-head-demo-key-v1"
KEY_ID = "authority-head-demo-key-v1"
NAMESPACE = "resonance-proof-authority"


def canonical(obj): return json.dumps(obj, sort_keys=True, separators=(",", ":"))
def sha(obj): return "sha256:" + hashlib.sha256(canonical(obj).encode()).hexdigest()
def mac(payload): return hmac.new(KEY, canonical(payload).encode(), hashlib.sha256).hexdigest()
def sign_head(payload): return {"alg":"HMAC-SHA256","key_id":KEY_ID,"payload":payload,"mac":mac(payload)}
def authenticate(head): return head.get("alg")=="HMAC-SHA256" and head.get("key_id")==KEY_ID and head.get("payload",{}).get("authority_namespace")==NAMESPACE and hmac.compare_digest(head.get("mac",""), mac(head.get("payload",{})))

MODELS = {
    "model-v1": {"version":"model-v1","dependencies":["price","limit"],"formula_id":"min_limit_2x_price"},
    "model-v2": {"version":"model-v2","dependencies":["price","limit","tax_rate"],"formula_id":"min_limit_2x_price_plus_tax"},
}
for m in MODELS.values(): m["digest"] = sha(m)
RULES = {
    "R1": {"rule_id":"cap-equivalence-r1","from_model":"model-v1","to_model":"model-v2","predicate":"tax_rate >= 0 AND 2*price >= limit","semantic_claim":"both models evaluate to limit"},
    "R2": {"rule_id":"cap-equivalence-r2","from_model":"model-v1","to_model":"model-v2","predicate":"tax_rate >= 0 AND 2*price >= limit","semantic_claim":"both models evaluate to limit","supersedes":"cap-equivalence-r1"},
}
for r in RULES.values(): r["digest"] = sha(r)

HEAD7_PAYLOAD = {"authority_namespace":NAMESPACE,"generation":7,"rule_id":RULES["R1"]["rule_id"],"rule_digest":RULES["R1"]["digest"],"status":"ACTIVE","successor_rule_id":None}
HEAD9_PAYLOAD = {"authority_namespace":NAMESPACE,"generation":9,"rule_id":RULES["R2"]["rule_id"],"rule_digest":RULES["R2"]["digest"],"status":"ACTIVE","successor_rule_id":None}
HEAD7 = sign_head(HEAD7_PAYLOAD)
HEAD9 = sign_head(HEAD9_PAYLOAD)


def db(dsn): return psycopg.connect(dsn, autocommit=False, row_factory=dict_row)

def calc(model, price, limit, tax_rate):
    return min(limit, 2*price) if model=="model-v1" else min(limit, 2*price + tax_rate)

def values_fp(p,l,t): return sha({"price":p,"limit":l,"tax_rate":t})
def dep_fp(model,p,l,t):
    vals={"price":p,"limit":l,"tax_rate":t}; return sha({k:vals[k] for k in MODELS[model]["dependencies"]})

def init_schema(conn):
    conn.execute("CREATE TABLE IF NOT EXISTS ahr_state(resource_id TEXT PRIMARY KEY,owner TEXT NOT NULL,fence INT NOT NULL,global_version INT NOT NULL,price INT NOT NULL,limit_value INT NOT NULL,tax_rate INT NOT NULL,current_model_version TEXT NOT NULL,current_model_digest TEXT NOT NULL)")
    conn.execute("CREATE TABLE IF NOT EXISTS ahr_artifacts(resource_id TEXT NOT NULL,artifact_id TEXT NOT NULL,model_version TEXT NOT NULL,model_digest TEXT NOT NULL,dependency_fingerprint TEXT NOT NULL,input_values_fingerprint TEXT NOT NULL,output_value INT NOT NULL,artifact_digest TEXT NOT NULL,state TEXT NOT NULL DEFAULT 'READY',adopted_by TEXT,adopted_fence INT,proof_digest TEXT,PRIMARY KEY(resource_id,artifact_id))")
    conn.execute("CREATE TABLE IF NOT EXISTS ahr_replica(region TEXT NOT NULL,rule_id TEXT NOT NULL,rule_digest TEXT NOT NULL,status TEXT NOT NULL,generation INT NOT NULL,PRIMARY KEY(region,rule_id))")
    conn.execute("CREATE TABLE IF NOT EXISTS ahr_checkpoint(verifier_id TEXT PRIMARY KEY,max_authenticated_generation INT NOT NULL,head_digest TEXT NOT NULL,updated_at TIMESTAMPTZ NOT NULL DEFAULT now())")
    conn.commit()

def reset_replica(conn, generation=7):
    conn.execute("DELETE FROM ahr_replica")
    rule = RULES["R1"] if generation==7 else RULES["R2"]
    conn.execute("INSERT INTO ahr_replica(region,rule_id,rule_digest,status,generation) VALUES('region-B',%s,%s,'ACTIVE',%s)",(rule["rule_id"],rule["digest"],generation)); conn.commit()

def checkpoint(conn, generation, head):
    hd=sha(head)
    conn.execute("INSERT INTO ahr_checkpoint(verifier_id,max_authenticated_generation,head_digest) VALUES('verifier-B',%s,%s) ON CONFLICT(verifier_id) DO UPDATE SET max_authenticated_generation=GREATEST(ahr_checkpoint.max_authenticated_generation,EXCLUDED.max_authenticated_generation),head_digest=CASE WHEN EXCLUDED.max_authenticated_generation>=ahr_checkpoint.max_authenticated_generation THEN EXCLUDED.head_digest ELSE ahr_checkpoint.head_digest END,updated_at=now()",(generation,hd)); conn.commit()

def checkpoint_generation(conn):
    row=conn.execute("SELECT max_authenticated_generation FROM ahr_checkpoint WHERE verifier_id='verifier-B'").fetchone(); return row["max_authenticated_generation"] if row else 0

def reset_resource(conn,rid):
    conn.execute("DELETE FROM ahr_artifacts WHERE resource_id=%s",(rid,)); conn.execute("DELETE FROM ahr_state WHERE resource_id=%s",(rid,))
    conn.execute("INSERT INTO ahr_state VALUES(%s,'worker-B',2,101,20,30,8,'model-v2',%s)",(rid,MODELS["model-v2"]["digest"])); conn.commit()

def make_artifact(conn,rid,aid):
    s=conn.execute("SELECT * FROM ahr_state WHERE resource_id=%s",(rid,)).fetchone(); out=calc("model-v1",s["price"],s["limit_value"],s["tax_rate"])
    digest=sha({"resource_id":rid,"artifact_id":aid,"model_version":"model-v1","model_digest":MODELS["model-v1"]["digest"],"dependency_fingerprint":dep_fp("model-v1",s["price"],s["limit_value"],s["tax_rate"]),"output":out})
    conn.execute("INSERT INTO ahr_artifacts(resource_id,artifact_id,model_version,model_digest,dependency_fingerprint,input_values_fingerprint,output_value,artifact_digest) VALUES(%s,%s,'model-v1',%s,%s,%s,%s,%s)",(rid,aid,MODELS["model-v1"]["digest"],dep_fp("model-v1",s["price"],s["limit_value"],s["tax_rate"]),values_fp(s["price"],s["limit_value"],s["tax_rate"]),out,digest)); conn.commit(); return conn.execute("SELECT * FROM ahr_artifacts WHERE resource_id=%s AND artifact_id=%s",(rid,aid)).fetchone()

def issue_proof(conn,rid,aid,rule_key):
    s=conn.execute("SELECT * FROM ahr_state WHERE resource_id=%s",(rid,)).fetchone(); a=conn.execute("SELECT * FROM ahr_artifacts WHERE resource_id=%s AND artifact_id=%s",(rid,aid)).fetchone(); rule=RULES[rule_key]; gen=7 if rule_key=="R1" else 9
    p={"rule_id":rule["rule_id"],"rule_digest":rule["digest"],"rule_generation":gen,"from_model_version":a["model_version"],"from_model_digest":a["model_digest"],"to_model_version":s["current_model_version"],"to_model_digest":s["current_model_digest"],"artifact_digest":a["artifact_digest"],"current_values_fingerprint":values_fp(s["price"],s["limit_value"],s["tax_rate"]),"predicate_holds":s["tax_rate"]>=0 and 2*s["price"]>=s["limit_value"]}; p["proof_digest"]=sha(p); return p

def verdict(conn,rid,aid,proof,head,enforce_monotonic):
    s=conn.execute("SELECT * FROM ahr_state WHERE resource_id=%s",(rid,)).fetchone(); a=conn.execute("SELECT * FROM ahr_artifacts WHERE resource_id=%s AND artifact_id=%s",(rid,aid)).fetchone(); hp=head["payload"]; rep=conn.execute("SELECT * FROM ahr_replica WHERE region='region-B' AND rule_id=%s",(proof["rule_id"],)).fetchone(); auth=authenticate(head); cp=checkpoint_generation(conn)
    checks={"authority_head_authentic":auth,"from_model":proof["from_model_version"]==a["model_version"] and proof["from_model_digest"]==a["model_digest"],"to_model":proof["to_model_version"]==s["current_model_version"] and proof["to_model_digest"]==s["current_model_digest"],"artifact":proof["artifact_digest"]==a["artifact_digest"],"values":proof["current_values_fingerprint"]==values_fp(s["price"],s["limit_value"],s["tax_rate"]),"predicate":bool(proof["predicate_holds"]),"replica_exists":rep is not None,"head_matches_rule":hp.get("rule_id")==proof["rule_id"] and hp.get("rule_digest")==proof["rule_digest"],"rule_active":rep is not None and rep["status"]=="ACTIVE","rule_generation":rep is not None and rep["generation"]==proof["rule_generation"],"authority_view_fresh":rep is not None and rep["generation"]>=hp.get("generation",10**9)}
    if enforce_monotonic: checks["head_not_rolled_back"]=auth and hp.get("generation",-1)>=cp
    if all(checks.values()): return {"accept":True,"reason":"proof_authorized_with_current_head","checks":checks,"checkpoint_generation":cp,"head":hp,"replica":dict(rep)}
    if not auth: reason="authority_head_authentication_failed"
    elif enforce_monotonic and not checks.get("head_not_rolled_back",False): reason="authority_head_rollback_detected"
    elif not checks["authority_view_fresh"]: reason="stale_authority_view"
    else: reason="proof_authority_conflict"
    return {"accept":False,"reason":reason,"checks":checks,"checkpoint_generation":cp,"head":hp,"replica":dict(rep) if rep else None}

def adopt(conn,rid,aid,proof,v):
    if not v["accept"]: return {"updated_rows":0,"reason":v["reason"]}
    cur=conn.execute("UPDATE ahr_artifacts a SET state='ADOPTED',adopted_by=s.owner,adopted_fence=s.fence,proof_digest=%s FROM ahr_state s WHERE a.resource_id=s.resource_id AND a.resource_id=%s AND a.artifact_id=%s AND a.state='READY' RETURNING a.artifact_id",(proof["proof_digest"],rid,aid)); rows=cur.rowcount; conn.commit(); return {"updated_rows":rows,"reason":"adopted" if rows else "compare_and_adopt_conflict"}

def http_json(method,path,headers=None):
    req=urllib.request.Request(BASE_URL+path,method=method,headers=headers or {})
    try:
        with urllib.request.urlopen(req,timeout=5) as r: return r.status,json.loads(r.read().decode())
    except urllib.error.HTTPError as e: return e.code,json.loads(e.read().decode())
def start_service():
    subprocess.run(["docker","rm","-f",CONTAINER],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); subprocess.run(["docker","volume","rm","-f",VOLUME],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); subprocess.run(["docker","volume","create",VOLUME],check=True,stdout=subprocess.DEVNULL); port=BASE_URL.rsplit(":",1)[-1]
    subprocess.run(["docker","run","-d","--name",CONTAINER,"-p",f"{port}:8080","-v",f"{VOLUME}:/state","-v",f"{SERVICE}:/app/external_service.py:ro",IMAGE,"python","/app/external_service.py"],check=True,stdout=subprocess.DEVNULL)
    for _ in range(50):
        try:
            s,p=http_json("GET","/health")
            if s==200: return p
        except Exception: pass
        time.sleep(.1)
    raise RuntimeError("service did not start")
def reset_remote(): http_json("POST","/reset")
def publish(conn,rid,aid,phase):
    a=conn.execute("SELECT * FROM ahr_artifacts WHERE resource_id=%s AND artifact_id=%s",(rid,aid)).fetchone(); s=conn.execute("SELECT * FROM ahr_state WHERE resource_id=%s",(rid,)).fetchone(); headers={"Content-Type":"application/json","X-Resource-Id":rid,"X-Worker":s["owner"],"X-Fence":str(s["fence"]),"X-Artifact-Digest":a["artifact_digest"],"X-Input-State-Version":str(s["global_version"]),"X-Output-Value":str(a["output_value"]),"X-Phase":phase}; return http_json("POST","/effect",headers)
def remote(rid): return http_json("GET",f"/state?resource_id={rid}")[1]
def check(cid,ok,evidence): return {"id":cid,"pass":bool(ok),"points":2 if ok else 0,"evidence":evidence}

def scenario(conn,rid,rule,head,enforce,phase):
    reset_remote(); reset_resource(conn,rid); a=make_artifact(conn,rid,"artifact-v1"); p=issue_proof(conn,rid,"artifact-v1",rule); v=verdict(conn,rid,"artifact-v1",p,head,enforce); ad=adopt(conn,rid,"artifact-v1",p,v); write=None
    if ad["updated_rows"]: write={"http_status":publish(conn,rid,"artifact-v1",phase)[0]}
    return {"artifact":dict(a),"proof":p,"head":head,"head_authentic":authenticate(head),"verdict":v,"adoption":ad,"write":write,"remote":remote(rid)}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--out",required=True); args=ap.parse_args(); out=Path(args.out); out.mkdir(parents=True,exist_ok=True); dsn=os.environ["DATABASE_URL"]
    svc=start_service(); conn=db(dsn); init_schema(conn); conn.execute("DELETE FROM ahr_checkpoint"); conn.commit(); reset_replica(conn,7)
    control=scenario(conn,"head7-control","R1",HEAD7,False,"authentic-head7-control")
    checkpoint(conn,9,HEAD9)
    unsafe=scenario(conn,"unsafe-authentic-replay","R1",HEAD7,False,"unsafe-authentic-head-replay")
    safe=scenario(conn,"safe-authentic-replay","R1",HEAD7,True,"safe-authentic-head-replay")
    conn.close(); conn=db(dsn); restart_cp=checkpoint_generation(conn); after_restart=scenario(conn,"restart-authentic-replay","R1",HEAD7,True,"restart-authentic-head-replay")
    reset_replica(conn,9); fresh=scenario(conn,"fresh-head9","R2",HEAD9,True,"fresh-authentic-head9")
    checks=[
      check("authentic_generation7_control_succeeds",control["head_authentic"] and control["adoption"]["updated_rows"]==1 and control["remote"].get("effect_count")==1,control),
      check("authentic_old_head_replay_fools_authentication_only_verifier",unsafe["head_authentic"] and unsafe["verdict"]["accept"] and unsafe["remote"].get("effect_count")==1,unsafe),
      check("monotonic_checkpoint_rejects_authentic_old_head_with_zero_effects",safe["verdict"]["reason"]=="authority_head_rollback_detected" and safe["adoption"]["updated_rows"]==0 and safe["remote"].get("effect_count")==0,safe),
      check("durable_checkpoint_survives_verifier_restart",restart_cp==9 and after_restart["verdict"]["reason"]=="authority_head_rollback_detected" and after_restart["remote"].get("effect_count")==0,{"checkpoint_after_restart":restart_cp,"scenario":after_restart}),
      check("fresh_authentic_generation9_head_succeeds_once",fresh["head_authentic"] and fresh["verdict"]["accept"] and fresh["remote"].get("effect_count")==1,fresh),
    ]
    result={"benchmark":"RESONANCE Authentic Head Replay / Authority Rollback","benchmark_version":"1.0","protocol":"RESONANCE Transactional Trust Protocol v1.0","executed_at":datetime.now(timezone.utc).isoformat(),"database":{"server_version":conn.execute("SHOW server_version").fetchone()["server_version"]},"http_service":svc,"http_service_image":IMAGE,"authentication_fixture":{"algorithm":"HMAC-SHA256","key_id":KEY_ID,"production_pki":False},"trusted_checkpoint":{"type":"durable verifier-local monotonic high-watermark","generation":checkpoint_generation(conn)},"heads":{"H7":HEAD7,"H9":HEAD9},"checks":checks,"score":sum(c["points"] for c in checks),"max_score":10,"classification":"Authority head anti-rollback protocol passes" if all(c["pass"] for c in checks) else "Authority head anti-rollback protocol fails","invariants":["AUTHENTIC HEAD DOES NOT IMPLY LATEST HEAD.","CURRENTNESS MUST BIND TO MONOTONIC ANTI-ROLLBACK STATE OR AN EQUIVALENT TRUSTED CHECKPOINT.","AN AUTHENTIC HEAD BELOW THE TRUSTED HIGH-WATERMARK MUST FAIL CLOSED BEFORE CONSEQUENCE.","ANTI-ROLLBACK STATE MUST SURVIVE VERIFIER RESTART OR BE RECONSTRUCTED FROM TRUSTED WITNESS/CHECKPOINT EVIDENCE."],"external_safety_certification":False,"vulnerability_claim":False}
    (out/"result.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    lines=["# RESULT — Authority Head Replay v1.0","",f"**Score: {result['score']}/{result['max_score']} — {result['classification']}**","", "| Check | Pass | Points |","|---|---:|---:|"]+[f"| `{c['id']}` | {'PASS' if c['pass'] else 'FAIL'} | {c['points']}/2 |" for c in checks]
    (out/"RESULT.md").write_text("\n".join(lines)+"\n")
    print(json.dumps(result,indent=2,sort_keys=True)); conn.close(); subprocess.run(["docker","rm","-f",CONTAINER],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    if result["score"]!=10: raise SystemExit(1)
if __name__=="__main__": main()
