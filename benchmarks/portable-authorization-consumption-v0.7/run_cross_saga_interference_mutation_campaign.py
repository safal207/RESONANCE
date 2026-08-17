#!/usr/bin/env python3
import argparse,json
from datetime import datetime,timezone
from pathlib import Path
from run_cross_saga_interference_conformance import run

MUTANTS=[
("XSG-MUT-1-BLIND-OVERWRITE-CURRENT-STATE","blind_overwrite_current_state","Ignore intervening resource version/effect and overwrite the current world."),
("XSG-MUT-2-TRUST-STALE-WITNESS","trust_stale_witness","Use a stale verify-at-use witness instead of revalidating current state."),
("XSG-MUT-3-IGNORE-CURRENT-EFFECT-BINDING","ignore_current_effect_binding","Accept matching version while ignoring which effect currently owns that state."),
("XSG-MUT-4-SKIP-COMPENSATION-AUTHORITY","skip_compensation_authority","Treat need-to-compensate as authority to compensate."),
("XSG-MUT-5-DUPLICATE-COMMITTED-COMPENSATION","duplicate_committed_compensation","Emit another compensation even though a durable committed compensation exists."),
("XSG-MUT-6-BLIND-RETRY-UNKNOWN","blind_retry_unknown_compensation","Retry compensation while prior compensation outcome is unknown."),
("XSG-MUT-7-INVENT-MISSING-WITNESS","invent_missing_witness","Invent current-state evidence when the durable verify-at-use witness is absent."),
("XSG-MUT-8-INVENT-MISSING-KEY","invent_missing_compensation_key","Invent a fresh compensation identity when durable idempotency evidence is missing."),
]

def main():
    p=argparse.ArgumentParser(); p.add_argument("--fixtures",default=str(Path(__file__).with_name("cross_saga_interference_fixtures.json"))); p.add_argument("--output"); p.add_argument("--required-score",type=float,default=1.0); a=p.parse_args()
    base=run(a.fixtures,"baseline"); rows=[]
    for mid,mode,desc in MUTANTS:
        r=run(a.fixtures,mode); fails=[x["id"] for x in r["results"] if not x["passed"]]
        rows.append({"id":mid,"mode":mode,"description":desc,"failing_controls":fails,"status":"KILLED" if fails else "SURVIVED"})
    killed=sum(x["status"]=="KILLED" for x in rows); survived=len(rows)-killed; score=killed/len(rows) if rows else 0.0
    status="PASS" if base["summary"]["status"]=="PASS" and survived==0 and score>=a.required_score else "FAIL"
    report={"benchmark":"PACC Cross-Saga Interference Mutation Campaign","version":"0.7","generated_at":datetime.now(timezone.utc).isoformat(),"baseline":base["summary"],"mutants":rows,"scope":"falsification of stale rollback, cross-saga overwrite, stale witness, binding, authority, replay, reconciliation, and identity continuity","summary":{"status":status,"killed":killed,"survived":survived,"total":len(rows),"mutation_score":score,"required_score":a.required_score}}
    text=json.dumps(report,indent=2,sort_keys=True); print(text)
    if a.output: Path(a.output).parent.mkdir(parents=True,exist_ok=True); Path(a.output).write_text(text+"\n",encoding="utf-8")
    raise SystemExit(0 if status=="PASS" else 1)
if __name__=="__main__": main()
