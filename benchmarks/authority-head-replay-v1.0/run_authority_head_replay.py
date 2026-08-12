from __future__ import annotations

import argparse, hashlib, hmac, json, os, subprocess, time, urllib.error, urllib.request
from datetime import datetime, timezone
from pathlib import Path
import psycopg
from psycopg.rows import dict_row

CONTAINER="resonance-external-authority-head-replay"
VOLUME="resonance-authority-head-replay-v1"
IMAGE=os.environ.get("HTTP_SERVICE_IMAGE","python:3.12-slim")
BASE=os.environ.get("EXTERNAL_BASE_URL","http://127.0.0.1:18097")
SERVICE=Path("benchmarks/dependency-aware-applicability-v1.0/external_service.py").resolve()
KEY=b"resonance-authority-head-demo-key-v1"; KEY_ID="authority-head-demo-key-v1"; NS="resonance-proof-authority"

def canonical(x): return json.dumps(x,sort_keys=True,separators=(",",":"))
def sha(x): return "sha256:"+hashlib.sha256(canonical(x).encode()).hexdigest()
def mac(p): return hmac.new(KEY,canonical(p).encode(),hashlib.sha256).hexdigest()
def sign(p): return {"alg":"HMAC-SHA256","key_id":KEY_ID,"payload":p,"mac":mac(p)}
def authentic(h): return h.get("alg")=="HMAC-SHA256" and h.get("key_id")==KEY_ID and h.get("payload",{}).get("authority_namespace")==NS and hmac.compare_digest(h.get("mac",""),mac(h.get("payload",{})))

MODELS={
 "model-v1":{"version":"model-v1","dependencies":["price","limit"],"formula_id":"min_limit_2x_price"},
 "model-v2":{"version":"model-v2","dependencies":["price","limit","tax_rate"],"formula_id":"min_limit_2x_price_plus_tax"},
}
for m in MODELS.values(): m["digest"]=sha(m)
RULES={
 "R1":{"rule_id":"cap-equivalence-r1","from_model":"model-v1","to_model":"model-v2","predicate":"tax_rate >= 0 AND 2*price >= limit","semantic_claim":"both models evaluate to limit"},
 "R2":{"rule_id":"cap-equivalence-r2","from_model":"model-v1","to_model":"model-v2","predicate":"tax_rate >= 0 AND 2*price >= limit","semantic_claim":"both models evaluate to limit","supersedes":"cap-equivalence-r1"},
}
for r in RULES.values(): r["digest"]=sha(r)
H7=sign({"authority_namespace":NS,"generation":7,"rule_id":RULES["R1"]["rule_id"],"rule_digest":RULES["R1"]["digest"],"status":"ACTIVE","successor_rule_id":None})
H9=sign({"authority_namespace":NS,"generation":9,"rule_id":RULES["R2"]["rule_id"],"rule_digest":RULES["R2"]["digest"],"status":"ACTIVE","successor_rule_id":None})

def db(dsn): return psycopg.connect(dsn,autocommit=False,row_factory=dict_row)
def init(conn):
 conn.execute("CREATE TABLE IF NOT EXISTS ahr_state(resource_id TEXT PRIMARY KEY,owner TEXT,fence INT,global_version INT,price INT,limit_value INT,tax_rate INT,current_model_version TEXT,current_model_digest TEXT)")
 conn.execute("CREATE TABLE IF NOT EXISTS ahr_artifacts(resource_id TEXT,artifact_id TEXT,model_version TEXT,model_digest TEXT,input_values_fingerprint TEXT,output_value INT,artifact_digest TEXT,state TEXT DEFAULT 'READY',adopted_by TEXT,adopted_fence INT,proof_digest TEXT,PRIMARY KEY(resource_id,artifact_id))")
 conn.execute("CREATE TABLE IF NOT EXISTS ahr_replica(region TEXT,rule_id TEXT,rule_digest TEXT,status TEXT,generation INT,PRIMARY KEY(region,rule_id))")
 conn.execute("CREATE TABLE IF NOT EXISTS ahr_checkpoint(verifier_id TEXT PRIMARY KEY,max_authenticated_generation INT,head_digest TEXT,updated_at TIMESTAMPTZ DEFAULT now())")
 conn.commit()
def reset_replica(conn,g):
 conn.execute("DELETE FROM ahr_replica"); r=RULES["R1" if g==7 else "R2"]
 conn.execute("INSERT INTO ahr_replica VALUES('region-B',%s,%s,'ACTIVE',%s)",(r["rule_id"],r["digest"],g)); conn.commit()
def checkpoint(conn,g,h):
 conn.execute("INSERT INTO ahr_checkpoint(verifier_id,max_authenticated_generation,head_digest) VALUES('verifier-B',%s,%s) ON CONFLICT(verifier_id) DO UPDATE SET max_authenticated_generation=GREATEST(ahr_checkpoint.max_authenticated_generation,EXCLUDED.max_authenticated_generation),head_digest=CASE WHEN EXCLUDED.max_authenticated_generation>=ahr_checkpoint.max_authenticated_generation THEN EXCLUDED.head_digest ELSE ahr_checkpoint.head_digest END,updated_at=now()",(g,sha(h))); conn.commit()
def cp(conn):
 r=conn.execute("SELECT max_authenticated_generation FROM ahr_checkpoint WHERE verifier_id='verifier-B'").fetchone(); return r["max_authenticated_generation"] if r else 0
def reset_resource(conn,rid):
 conn.execute("DELETE FROM ahr_artifacts WHERE resource_id=%s",(rid,)); conn.execute("DELETE FROM ahr_state WHERE resource_id=%s",(rid,))
 conn.execute("INSERT INTO ahr_state VALUES(%s,'worker-B',2,101,20,30,8,'model-v2',%s)",(rid,MODELS["model-v2"]["digest"])); conn.commit()
def values_fp(s): return sha({"price":s["price"],"limit":s["limit_value"],"tax_rate":s["tax_rate"]})
def make_artifact(conn,rid):
 s=conn.execute("SELECT * FROM ahr_state WHERE resource_id=%s",(rid,)).fetchone(); out=min(s["limit_value"],2*s["price"])
 d=sha({"resource_id":rid,"artifact_id":"artifact-v1","model_version":"model-v1","model_digest":MODELS["model-v1"]["digest"],"output":out})
 conn.execute("INSERT INTO ahr_artifacts(resource_id,artifact_id,model_version,model_digest,input_values_fingerprint,output_value,artifact_digest) VALUES(%s,'artifact-v1','model-v1',%s,%s,%s,%s)",(rid,MODELS["model-v1"]["digest"],values_fp(s),out,d)); conn.commit(); return conn.execute("SELECT * FROM ahr_artifacts WHERE resource_id=%s",(rid,)).fetchone()
def proof(conn,rid,rk):
 s=conn.execute("SELECT * FROM ahr_state WHERE resource_id=%s",(rid,)).fetchone(); a=conn.execute("SELECT * FROM ahr_artifacts WHERE resource_id=%s",(rid,)).fetchone(); r=RULES[rk]; g=7 if rk=="R1" else 9
 p={"rule_id":r["rule_id"],"rule_digest":r["digest"],"rule_generation":g,"from_model_version":a["model_version"],"from_model_digest":a["model_digest"],"to_model_version":s["current_model_version"],"to_model_digest":s["current_model_digest"],"artifact_digest":a["artifact_digest"],"current_values_fingerprint":values_fp(s),"predicate_holds":s["tax_rate"]>=0 and 2*s["price"]>=s["limit_value"]}; p["proof_digest"]=sha(p); return p
def verdict(conn,rid,p,h,enforce):
 s=conn.execute("SELECT * FROM ahr_state WHERE resource_id=%s",(rid,)).fetchone(); a=conn.execute("SELECT * FROM ahr_artifacts WHERE resource_id=%s",(rid,)).fetchone(); hp=h["payload"]; rep=conn.execute("SELECT * FROM ahr_replica WHERE region='region-B' AND rule_id=%s",(p["rule_id"],)).fetchone(); au=authentic(h); high=cp(conn)
 checks={"authority_head_authentic":au,"from_model":p["from_model_version"]==a["model_version"] and p["from_model_digest"]==a["model_digest"],"to_model":p["to_model_version"]==s["current_model_version"] and p["to_model_digest"]==s["current_model_digest"],"artifact":p["artifact_digest"]==a["artifact_digest"],"values":p["current_values_fingerprint"]==values_fp(s),"predicate":bool(p["predicate_holds"]),"replica_exists":rep is not None,"head_matches_rule":hp.get("rule_id")==p["rule_id"] and hp.get("rule_digest")==p["rule_digest"],"rule_active":rep is not None and rep["status"]=="ACTIVE","rule_generation":rep is not None and rep["generation"]==p["rule_generation"],"authority_view_fresh":rep is not None and rep["generation"]>=hp.get("generation",10**9)}
 if enforce: checks["head_not_rolled_back"]=au and hp.get("generation",-1)>=high
 if all(checks.values()): return {"accept":True,"reason":"proof_authorized_with_current_head","checks":checks,"checkpoint_generation":high,"head":hp,"replica":dict(rep)}
 reason="authority_head_authentication_failed" if not au else "authority_head_rollback_detected" if enforce and not checks.get("head_not_rolled_back",False) else "stale_authority_view" if not checks["authority_view_fresh"] else "proof_authority_conflict"
 return {"accept":False,"reason":reason,"checks":checks,"checkpoint_generation":high,"head":hp,"replica":dict(rep) if rep else None}
def adopt(conn,rid,p,v):
 if not v["accept"]: return {"updated_rows":0,"reason":v["reason"]}
 c=conn.execute("UPDATE ahr_artifacts a SET state='ADOPTED',adopted_by=s.owner,adopted_fence=s.fence,proof_digest=%s FROM ahr_state s WHERE a.resource_id=s.resource_id AND a.resource_id=%s AND a.state='READY' RETURNING a.artifact_id",(p["proof_digest"],rid)); n=c.rowcount; conn.commit(); return {"updated_rows":n,"reason":"adopted" if n else "compare_and_adopt_conflict"}

def http(method,path,headers=None):
 req=urllib.request.Request(BASE+path,method=method,headers=headers or {})
 try:
  with urllib.request.urlopen(req,timeout=5) as r: return r.status,json.loads(r.read().decode())
 except urllib.error.HTTPError as e: return e.code,json.loads(e.read().decode())
def start_service():
 subprocess.run(["docker","rm","-f",CONTAINER],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); subprocess.run(["docker","volume","rm","-f",VOLUME],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); subprocess.run(["docker","volume","create",VOLUME],check=True,stdout=subprocess.DEVNULL); port=BASE.rsplit(":",1)[-1]
 subprocess.run(["docker","run","-d","--name",CONTAINER,"-p",f"{port}:8080","-v",f"{VOLUME}:/state","-v",f"{SERVICE}:/app/external_service.py:ro",IMAGE,"python","/app/external_service.py"],check=True,stdout=subprocess.DEVNULL)
 for _ in range(50):
  try:
   code,p=http("GET","/health")
   if code==200: return p
  except Exception: pass
  time.sleep(.1)
 raise RuntimeError("external service did not start")
def publish(conn,rid,phase):
 a=conn.execute("SELECT * FROM ahr_artifacts WHERE resource_id=%s",(rid,)).fetchone(); s=conn.execute("SELECT * FROM ahr_state WHERE resource_id=%s",(rid,)).fetchone()
 headers={"X-Resource-Id":rid,"X-Worker":s["owner"],"X-Fencing-Token":str(s["fence"]),"X-Artifact-Digest":a["artifact_digest"],"X-Input-State-Version":str(s["global_version"]),"X-Output-Value":str(a["output_value"]),"X-Phase":phase}
 return http("POST","/effects",headers)
def remote(rid): return http("GET",f"/status/{rid}")[1]
def scenario(conn,rid,rk,h,enforce,phase):
 reset_resource(conn,rid); a=make_artifact(conn,rid); p=proof(conn,rid,rk); v=verdict(conn,rid,p,h,enforce); ad=adopt(conn,rid,p,v); w=None
 if ad["updated_rows"]: code,payload=publish(conn,rid,phase); w={"http_status":code,"payload":payload}
 return {"artifact":dict(a),"proof":p,"head":h,"head_authentic":authentic(h),"verdict":v,"adoption":ad,"write":w,"remote":remote(rid)}
def chk(i,ok,e): return {"id":i,"pass":bool(ok),"points":2 if ok else 0,"evidence":e}

def main():
 ap=argparse.ArgumentParser(); ap.add_argument("--out",required=True); a=ap.parse_args(); out=Path(a.out); out.mkdir(parents=True,exist_ok=True); dsn=os.environ["DATABASE_URL"]
 svc=start_service(); conn=db(dsn); init(conn); conn.execute("DELETE FROM ahr_checkpoint"); conn.commit(); reset_replica(conn,7)
 control=scenario(conn,"head7-control","R1",H7,False,"authentic-head7-control")
 checkpoint(conn,9,H9)
 unsafe=scenario(conn,"unsafe-authentic-replay","R1",H7,False,"unsafe-authentic-head-replay")
 safe=scenario(conn,"safe-authentic-replay","R1",H7,True,"safe-authentic-head-replay")
 conn.close(); conn=db(dsn); restart_cp=cp(conn); restarted=scenario(conn,"restart-authentic-replay","R1",H7,True,"restart-authentic-head-replay")
 reset_replica(conn,9); fresh=scenario(conn,"fresh-head9","R2",H9,True,"fresh-authentic-head9")
 checks=[
  chk("authentic_generation7_control_succeeds",control["head_authentic"] and control["adoption"]["updated_rows"]==1 and control["write"]["http_status"]==200 and control["remote"].get("effect_count")==1,control),
  chk("authentic_old_head_replay_fools_authentication_only_verifier",unsafe["head_authentic"] and unsafe["verdict"]["accept"] and unsafe["write"]["http_status"]==200 and unsafe["remote"].get("effect_count")==1,unsafe),
  chk("monotonic_checkpoint_rejects_authentic_old_head_with_zero_effects",safe["head_authentic"] and safe["verdict"]["reason"]=="authority_head_rollback_detected" and safe["adoption"]["updated_rows"]==0 and safe["remote"].get("effect_count")==0,safe),
  chk("durable_checkpoint_survives_verifier_restart",restart_cp==9 and restarted["verdict"]["reason"]=="authority_head_rollback_detected" and restarted["remote"].get("effect_count")==0,{"checkpoint_after_restart":restart_cp,"scenario":restarted}),
  chk("fresh_authentic_generation9_head_succeeds_once",fresh["head_authentic"] and fresh["verdict"]["accept"] and fresh["write"]["http_status"]==200 and fresh["remote"].get("effect_count")==1,fresh),
 ]
 result={"benchmark":"RESONANCE Authentic Head Replay / Authority Rollback","benchmark_version":"1.0","protocol":"RESONANCE Transactional Trust Protocol v1.0","executed_at":datetime.now(timezone.utc).isoformat(),"database":{"server_version":conn.execute("SHOW server_version").fetchone()["server_version"]},"http_service":svc,"http_service_image":IMAGE,"authentication_fixture":{"algorithm":"HMAC-SHA256","key_id":KEY_ID,"production_pki":False},"trusted_checkpoint":{"type":"durable verifier-local monotonic high-watermark","generation":cp(conn)},"heads":{"H7":H7,"H9":H9},"checks":checks,"score":sum(x["points"] for x in checks),"max_score":10,"classification":"Authority head anti-rollback protocol passes" if all(x["pass"] for x in checks) else "Authority head anti-rollback protocol fails","invariants":["AUTHENTIC HEAD DOES NOT IMPLY LATEST HEAD.","CURRENTNESS MUST BIND TO MONOTONIC ANTI-ROLLBACK STATE OR AN EQUIVALENT TRUSTED CHECKPOINT.","AN AUTHENTIC HEAD BELOW THE TRUSTED HIGH-WATERMARK MUST FAIL CLOSED BEFORE CONSEQUENCE.","ANTI-ROLLBACK STATE MUST SURVIVE VERIFIER RESTART OR BE RECONSTRUCTED FROM TRUSTED WITNESS/CHECKPOINT EVIDENCE."],"external_safety_certification":False,"vulnerability_claim":False}
 (out/"result.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n"); (out/"RESULT.md").write_text("# RESULT — Authority Head Replay v1.0\n\n**Score: %s/%s — %s**\n\n| Check | Pass | Points |\n|---|---:|---:|\n%s\n"%(result["score"],result["max_score"],result["classification"],"\n".join(f"| `{x['id']}` | {'PASS' if x['pass'] else 'FAIL'} | {x['points']}/2 |" for x in checks)))
 print(json.dumps(result,indent=2,sort_keys=True)); conn.close(); subprocess.run(["docker","rm","-f",CONTAINER],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 if result["score"]!=10: raise SystemExit(1)
if __name__=="__main__": main()
