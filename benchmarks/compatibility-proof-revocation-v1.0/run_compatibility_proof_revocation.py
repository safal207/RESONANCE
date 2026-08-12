from __future__ import annotations

import argparse, hashlib, json, os, subprocess, time, urllib.error, urllib.request
from datetime import datetime, timezone
from pathlib import Path
import psycopg

CONTAINER='resonance-external-proof-revocation'
VOLUME='resonance-proof-revocation-v1'
IMAGE=os.environ.get('HTTP_SERVICE_IMAGE','python:3.12-slim')
BASE_URL=os.environ.get('EXTERNAL_BASE_URL','http://127.0.0.1:18094')
SERVICE=Path('benchmarks/dependency-aware-applicability-v1.0/external_service.py').resolve()

def canonical(o): return json.dumps(o,sort_keys=True,separators=(',',':'))
def sha(o): return 'sha256:'+hashlib.sha256(canonical(o).encode()).hexdigest()

MODELS={
 'model-v1':{'version':'model-v1','dependencies':['price','limit'],'formula_id':'min_limit_2x_price'},
 'model-v2':{'version':'model-v2','dependencies':['price','limit','tax_rate'],'formula_id':'min_limit_2x_price_plus_tax'},
}
for m in MODELS.values(): m['digest']=sha({k:m[k] for k in ('version','dependencies','formula_id')})
RULES={
 'R1':{'rule_id':'cap-equivalence-r1','from_model':'model-v1','to_model':'model-v2','predicate':'tax_rate >= 0 AND 2*price >= limit','semantic_claim':'both models evaluate to limit'},
 'R2':{'rule_id':'cap-equivalence-r2','from_model':'model-v1','to_model':'model-v2','predicate':'tax_rate >= 0 AND 2*price >= limit','semantic_claim':'both models evaluate to limit','supersedes':'cap-equivalence-r1'},
}
for r in RULES.values(): r['digest']=sha(r)

def calc(v,p,l,t): return min(l,2*p) if v=='model-v1' else min(l,2*p+t)
def values_fp(p,l,t): return sha({'price':p,'limit':l,'tax_rate':t})
def dep_fp(v,p,l,t):
 vals={'price':p,'limit':l,'tax_rate':t}; return sha({k:vals[k] for k in MODELS[v]['dependencies']})
def art_digest(rid,aid,v,p,l,t,out): return sha({'resource_id':rid,'artifact_id':aid,'model_version':v,'model_digest':MODELS[v]['digest'],'dependency_fingerprint':dep_fp(v,p,l,t),'output':out})

def http_json(method,path,headers=None):
 req=urllib.request.Request(BASE_URL+path,method=method,headers=headers or {})
 try:
  with urllib.request.urlopen(req,timeout=5) as r:return r.status,json.loads(r.read().decode())
 except urllib.error.HTTPError as e:return e.code,json.loads(e.read().decode())

def start_service():
 subprocess.run(['docker','rm','-f',CONTAINER],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 subprocess.run(['docker','volume','rm','-f',VOLUME],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 subprocess.run(['docker','volume','create',VOLUME],check=True,stdout=subprocess.DEVNULL)
 port=BASE_URL.rsplit(':',1)[-1]
 subprocess.run(['docker','run','-d','--name',CONTAINER,'-p',f'{port}:8080','-v',f'{VOLUME}:/state','-v',f'{SERVICE}:/app/external_service.py:ro',IMAGE,'python','/app/external_service.py','--port','8080'],check=True,stdout=subprocess.DEVNULL)
 for _ in range(40):
  try:
   s,p=http_json('GET','/health')
   if s==200:return p
  except Exception:pass
  time.sleep(.25)
 raise RuntimeError('external service failed')
def stop_service(): subprocess.run(['docker','rm','-f',CONTAINER],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)

def init(conn):
 conn.execute('''CREATE TABLE IF NOT EXISTS proof_state(resource_id TEXT PRIMARY KEY,owner TEXT NOT NULL,fence INT NOT NULL,global_version INT NOT NULL,price INT NOT NULL,limit_value INT NOT NULL,tax_rate INT NOT NULL,current_model_version TEXT NOT NULL,current_model_digest TEXT NOT NULL)''')
 conn.execute('''CREATE TABLE IF NOT EXISTS proof_artifacts(resource_id TEXT NOT NULL,artifact_id TEXT NOT NULL,model_version TEXT NOT NULL,model_digest TEXT NOT NULL,output_value INT NOT NULL,artifact_digest TEXT NOT NULL,state TEXT NOT NULL DEFAULT 'READY',adopted_by TEXT,adopted_fence INT,proof_digest TEXT,PRIMARY KEY(resource_id,artifact_id))''')
 conn.execute('''CREATE TABLE IF NOT EXISTS compatibility_rule_registry(rule_id TEXT PRIMARY KEY,rule_digest TEXT NOT NULL,status TEXT NOT NULL,authority_epoch INT NOT NULL,successor_rule_id TEXT)''')
 conn.commit()

def reset_registry(conn):
 conn.execute('DELETE FROM compatibility_rule_registry')
 conn.execute('INSERT INTO compatibility_rule_registry VALUES (%s,%s,%s,%s,%s)',(RULES['R1']['rule_id'],RULES['R1']['digest'],'ACTIVE',1,None))
 conn.execute('INSERT INTO compatibility_rule_registry VALUES (%s,%s,%s,%s,%s)',(RULES['R2']['rule_id'],RULES['R2']['digest'],'PENDING',1,None)); conn.commit()

def revoke_activate(conn):
 conn.execute("UPDATE compatibility_rule_registry SET status='REVOKED',authority_epoch=2,successor_rule_id=%s WHERE rule_id=%s",(RULES['R2']['rule_id'],RULES['R1']['rule_id']))
 conn.execute("UPDATE compatibility_rule_registry SET status='ACTIVE',authority_epoch=2 WHERE rule_id=%s",(RULES['R2']['rule_id'],)); conn.commit()

def reset_resource(conn,rid):
 conn.execute('DELETE FROM proof_artifacts WHERE resource_id=%s',(rid,)); conn.execute('DELETE FROM proof_state WHERE resource_id=%s',(rid,))
 conn.execute('INSERT INTO proof_state VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)',(rid,'worker-B',2,101,20,30,8,'model-v2',MODELS['model-v2']['digest'])); conn.commit()

def current(conn,rid):
 c=conn.execute('SELECT * FROM proof_state WHERE resource_id=%s',(rid,)); row=c.fetchone(); return dict(zip([d.name for d in c.description],row))
def registry(conn,rule_id):
 c=conn.execute('SELECT * FROM compatibility_rule_registry WHERE rule_id=%s',(rule_id,)); row=c.fetchone(); return dict(zip([d.name for d in c.description],row)) if row else None

def make_artifact(conn,rid,aid):
 s=current(conn,rid); out=calc('model-v1',s['price'],s['limit_value'],s['tax_rate']); d=art_digest(rid,aid,'model-v1',s['price'],s['limit_value'],s['tax_rate'],out)
 conn.execute('INSERT INTO proof_artifacts(resource_id,artifact_id,model_version,model_digest,output_value,artifact_digest) VALUES (%s,%s,%s,%s,%s,%s)',(rid,aid,'model-v1',MODELS['model-v1']['digest'],out,d)); conn.commit(); return artifact(conn,rid,aid)
def artifact(conn,rid,aid):
 c=conn.execute('SELECT * FROM proof_artifacts WHERE resource_id=%s AND artifact_id=%s',(rid,aid)); row=c.fetchone(); return dict(zip([d.name for d in c.description],row))
def predicate(s): return s['tax_rate']>=0 and 2*s['price']>=s['limit_value']

def issue_proof(conn,rid,aid,rule_key):
 s=current(conn,rid); a=artifact(conn,rid,aid); rule=RULES[rule_key]; reg=registry(conn,rule['rule_id'])
 p={'rule_id':rule['rule_id'],'rule_digest':rule['digest'],'rule_authority_epoch':reg['authority_epoch'],'from_model_version':a['model_version'],'from_model_digest':a['model_digest'],'to_model_version':s['current_model_version'],'to_model_digest':s['current_model_digest'],'artifact_digest':a['artifact_digest'],'current_values_fingerprint':values_fp(s['price'],s['limit_value'],s['tax_rate']),'predicate_holds':predicate(s),'issued_status':reg['status']}
 p['proof_digest']=sha(p); return p

def static_checks(conn,rid,aid,p):
 s=current(conn,rid); a=artifact(conn,rid,aid)
 return {'from_model':p['from_model_version']==a['model_version'] and p['from_model_digest']==a['model_digest'],'to_model':p['to_model_version']==s['current_model_version'] and p['to_model_digest']==s['current_model_digest'],'artifact':p['artifact_digest']==a['artifact_digest'],'values':p['current_values_fingerprint']==values_fp(s['price'],s['limit_value'],s['tax_rate']),'predicate':bool(p['predicate_holds']) and predicate(s)}

def adopt(conn,rid,aid,p,live_registry):
 checks=static_checks(conn,rid,aid,p)
 if not all(checks.values()): return {'updated_rows':0,'reason':'proof_binding_or_scope_conflict','checks':checks}
 if live_registry:
  reg=registry(conn,p['rule_id']); checks['registry_exists']=bool(reg)
  checks['rule_digest']=bool(reg) and reg['rule_digest']==p['rule_digest']
  checks['rule_active']=bool(reg) and reg['status']=='ACTIVE'
  checks['authority_epoch']=bool(reg) and reg['authority_epoch']==p['rule_authority_epoch']
  if not all(checks.values()):
   reason='compatibility_proof_revoked' if reg and reg['status']=='REVOKED' else 'compatibility_proof_authority_conflict'
   return {'updated_rows':0,'reason':reason,'checks':checks,'registry':reg}
 cur=conn.execute("""UPDATE proof_artifacts a SET state='ADOPTED',adopted_by=s.owner,adopted_fence=s.fence,proof_digest=%s FROM proof_state s WHERE a.resource_id=s.resource_id AND a.resource_id=%s AND a.artifact_id=%s AND a.state='READY' RETURNING a.artifact_id""",(p['proof_digest'],rid,aid)); n=cur.rowcount; conn.commit(); return {'updated_rows':n,'reason':'adopted_with_live_proof' if live_registry else 'adopted_cached_proof','checks':checks}

def commit(conn,rid,aid,phase):
 a=artifact(conn,rid,aid); s=current(conn,rid)
 if a['state']!='ADOPTED': return {'http_status':None,'payload':{'delivery':'not_adopted'}}
 h={'X-Resource-Id':rid,'X-Worker':a['adopted_by'],'X-Fencing-Token':str(a['adopted_fence']),'X-Artifact-Digest':a['artifact_digest'],'X-Input-State-Version':str(s['global_version']),'X-Output-Value':str(a['output_value']),'X-Phase':phase}
 status,p=http_json('POST','/effects',headers=h); return {'http_status':status,'payload':p}
def remote(rid): return http_json('GET','/status/'+rid)[1]

def run(dsn,out_dir):
 out=Path(out_dir); out.mkdir(parents=True,exist_ok=True)
 with psycopg.connect(dsn,autocommit=False) as conn:
  init(conn); health=start_service(); checks=[]
  try:
   reset_registry(conn)
   # 1 active proof works
   r1='active-control'; reset_resource(conn,r1); a1=make_artifact(conn,r1,'a1'); p1=issue_proof(conn,r1,'a1','R1'); ad1=adopt(conn,r1,'a1',p1,True); w1=commit(conn,r1,'a1','active-proof'); rem1=remote(r1)
   checks.append({'id':'active_proof_authorizes_reuse_before_revocation','pass':ad1['updated_rows']==1 and rem1['effect_count']==1 and rem1['effects'][0]['output_value']==30,'points':2,'evidence':{'proof':p1,'adoption':ad1,'write':w1,'remote':rem1}})
   # 2 cached proof still passes static checks after revocation: unsafe
   reset_registry(conn); r2='unsafe-revoked-proof'; reset_resource(conn,r2); a2=make_artifact(conn,r2,'a2'); p2=issue_proof(conn,r2,'a2','R1'); revoke_activate(conn); ad2=adopt(conn,r2,'a2',p2,False); w2=commit(conn,r2,'a2','unsafe-revoked-proof'); rem2=remote(r2)
   checks.append({'id':'cached_verifier_accepts_revoked_but_semantically_correct_proof','pass':registry(conn,RULES['R1']['rule_id'])['status']=='REVOKED' and ad2['updated_rows']==1 and rem2['effect_count']==1 and rem2['effects'][0]['output_value']==30,'points':2,'evidence':{'proof':p2,'registry_now':registry(conn,RULES['R1']['rule_id']),'adoption':ad2,'write':w2,'remote':rem2}})
   # 3 live registry rejects same stale proof
   reset_registry(conn); r3='safe-revoked-proof'; reset_resource(conn,r3); a3=make_artifact(conn,r3,'a3'); p3=issue_proof(conn,r3,'a3','R1'); revoke_activate(conn); ad3=adopt(conn,r3,'a3',p3,True); rem3=remote(r3)
   checks.append({'id':'live_registry_rejects_revoked_proof_with_zero_effects','pass':ad3['updated_rows']==0 and ad3['reason']=='compatibility_proof_revoked' and rem3['effect_count']==0,'points':2,'evidence':{'proof':p3,'adoption':ad3,'remote':rem3}})
   # 4 successor proof re-authorizes same old-model artifact
   r4='successor-proof'; reset_resource(conn,r4); a4=make_artifact(conn,r4,'a4'); p4=issue_proof(conn,r4,'a4','R2'); ad4=adopt(conn,r4,'a4',p4,True); w4=commit(conn,r4,'a4','successor-proof'); rem4=remote(r4)
   checks.append({'id':'active_successor_proof_reauthorizes_historical_artifact','pass':ad4['updated_rows']==1 and rem4['effect_count']==1 and rem4['effects'][0]['output_value']==30,'points':2,'evidence':{'proof':p4,'registry':registry(conn,RULES['R2']['rule_id']),'adoption':ad4,'write':w4,'remote':rem4}})
   # 5 even ACTIVE rule proof becomes stale if authority epoch advances
   r5='authority-epoch-drift'; reset_resource(conn,r5); a5=make_artifact(conn,r5,'a5'); p5=issue_proof(conn,r5,'a5','R2'); conn.execute('UPDATE compatibility_rule_registry SET authority_epoch=3 WHERE rule_id=%s',(RULES['R2']['rule_id'],)); conn.commit(); ad5=adopt(conn,r5,'a5',p5,True); rem5=remote(r5)
   checks.append({'id':'active_rule_epoch_advance_invalidates_older_proof','pass':ad5['updated_rows']==0 and ad5['reason']=='compatibility_proof_authority_conflict' and rem5['effect_count']==0,'points':2,'evidence':{'proof':p5,'registry_now':registry(conn,RULES['R2']['rule_id']),'adoption':ad5,'remote':rem5}})
  finally: stop_service()
  score=sum(c['points'] for c in checks if c['pass']); result={'benchmark':'RESONANCE Compatibility Proof Revocation / Stale Compatibility Certificate','benchmark_version':'1.0','protocol':'RESONANCE Transactional Trust Protocol v1.0','executed_at':datetime.now(timezone.utc).isoformat(),'database':{'server_version':conn.execute('SHOW server_version').fetchone()[0]},'http_service':health,'models':MODELS,'rules':RULES,'checks':checks,'score':score,'max_score':10,'classification':'Compatibility proof revocation protocol passes' if score==10 else 'Compatibility proof revocation protocol failed','invariants':['PROOF VALID THEN DOES NOT IMPLY PROOF AUTHORIZED NOW.','COMPATIBILITY PROOF AUTHORITY MUST BE RESOLVED AT ADOPTION OR CONSEQUENCE TIME.','REVOCATION OR AUTHORITY-EPOCH ADVANCE INVALIDATES HISTORICAL PROOF AUTHORIZATION.','A SUCCESSOR PROOF MAY REAUTHORIZE THE SAME ARTIFACT ONLY THROUGH FRESH CURRENT AUTHORITY EVIDENCE.'],'external_safety_certification':False,'vulnerability_claim':False}
 (out/'result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
 (out/'RESULT.md').write_text(f"# Compatibility Proof Revocation v1.0\n\n**Score:** {score}/10\n\n**Classification:** {result['classification']}\n\nCore law: **PROOF VALID THEN ≠ PROOF AUTHORIZED NOW.**\n")
 print(json.dumps(result,indent=2,sort_keys=True))
 if score!=10: raise SystemExit(1)

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--dsn',default=os.environ.get('DATABASE_URL','postgresql://resonance:resonance@127.0.0.1:5432/resonance')); ap.add_argument('--out',default='benchmark-results/compatibility-proof-revocation-v1.0'); a=ap.parse_args(); run(a.dsn,a.out)
if __name__=='__main__': main()
