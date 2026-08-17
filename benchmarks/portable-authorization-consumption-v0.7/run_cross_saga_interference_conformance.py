#!/usr/bin/env python3
import argparse,json
from datetime import datetime,timezone
from pathlib import Path

def out(status,witness,new=0,blocked=True):
    return {"status":status,"new_compensations":new,"used_resource_version":witness,"blocked_overwrite":blocked}

def evaluate_case(c,mode="baseline"):
    w=c.get("state_witness_version"); cur=c.get("current_resource_version")
    if c.get("trigger")!="REVERSAL_REQUIRED": return out("NO_COMPENSATION_REQUIRED",w,0,False)
    if w is None:
        if mode=="invent_missing_witness": w=cur
        else: return out("BLOCK_MISSING_CURRENT_STATE_WITNESS",None)
    if w!=cur and mode!="trust_stale_witness": return out("REVALIDATE_CURRENT_STATE",w)
    if c.get("expected_resource_version")!=cur and mode!="blind_overwrite_current_state": return out("BLOCK_STALE_COMPENSATION",w)
    if c.get("current_effect_ref")!=c.get("original_effect_ref") and mode not in {"blind_overwrite_current_state","ignore_current_effect_binding"}: return out("BLOCK_CURRENT_EFFECT_BINDING",w)
    if not c.get("compensation_authorized",False) and mode!="skip_compensation_authority": return out("BLOCK_COMPENSATION_NOT_AUTHORIZED",w)
    if not c.get("compensation_key") and mode!="invent_missing_compensation_key": return out("BLOCK_MISSING_COMPENSATION_IDEMPOTENCY_KEY",w)
    state=c.get("compensation_state","NOT_SENT")
    if state=="COMMITTED":
        return out("COMPENSATED",w,1,False) if mode=="duplicate_committed_compensation" else out("IDEMPOTENT_COMPENSATION_REPLAY",w,0,False)
    if state=="UNKNOWN":
        return out("COMPENSATED",w,1,False) if mode=="blind_retry_unknown_compensation" else out("RECONCILE_COMPENSATION_REQUIRED",w)
    return out("COMPENSATED",w,1,False)

def run(path,mode="baseline"):
    p=json.loads(Path(path).read_text(encoding="utf-8")); rs=[]
    for c in p["cases"]:
        a=evaluate_case(c,mode); e=c["expected"]
        rs.append({"id":c["id"],"name":c["name"],"actual":a,"expected":e,"passed":a==e})
    n=sum(r["passed"] for r in rs)
    return {"benchmark":"PACC Cross-Saga Interference and Stale Rollback","version":"0.7","generated_at":datetime.now(timezone.utc).isoformat(),"mode":mode,"results":rs,"scope":"deterministic current-state/version binding for compensation; not an external-product certification","summary":{"status":"PASS" if n==len(rs) else "FAIL","passed":n,"total":len(rs)}}

def main():
    p=argparse.ArgumentParser(); p.add_argument("--fixtures",default=str(Path(__file__).with_name("cross_saga_interference_fixtures.json"))); p.add_argument("--output"); p.add_argument("--mode",default="baseline"); a=p.parse_args()
    r=run(a.fixtures,a.mode); t=json.dumps(r,indent=2,sort_keys=True); print(t)
    if a.output: Path(a.output).parent.mkdir(parents=True,exist_ok=True); Path(a.output).write_text(t+"\n",encoding="utf-8")
    raise SystemExit(0 if r["summary"]["status"]=="PASS" else 1)
if __name__=="__main__": main()
