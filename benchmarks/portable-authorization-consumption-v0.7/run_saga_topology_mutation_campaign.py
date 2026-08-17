#!/usr/bin/env python3
import argparse, json, importlib.util
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("saga", ROOT/"run_saga_topology_conformance.py")
saga=importlib.util.module_from_spec(spec)
spec.loader.exec_module(saga)

MUTANTS=[
 {"id":"SAGA-MUT-1-FORWARD-COMPENSATION","mode":"forward_compensation_order","description":"Compensate ancestors before downstream effects."},
 {"id":"SAGA-MUT-2-COMPENSATE-UNEXECUTED","mode":"compensate_unexecuted_failed","description":"Compensate the failed step even when its effect never committed."},
 {"id":"SAGA-MUT-3-COMPENSATE-IRREVERSIBLE","mode":"compensate_irreversible","description":"Pretend an irreversible effect can be automatically undone."},
 {"id":"SAGA-MUT-4-EARLY-UPSTREAM-PARALLEL","mode":"early_upstream_parallel_compensation","description":"Compensate shared ancestor before all parallel downstream branches are closed."},
 {"id":"SAGA-MUT-5-CONTINUE-AFTER-UNKNOWN","mode":"continue_after_unknown","description":"Continue upstream compensation while a downstream compensation outcome is unknown."},
 {"id":"SAGA-MUT-6-DUPLICATE-ON-REPLAY","mode":"duplicate_on_saga_replay","description":"Saga replay emits duplicate compensations instead of replaying receipts."},
 {"id":"SAGA-MUT-7-IGNORE-BINDING","mode":"ignore_compensation_binding","description":"Accept compensation evidence bound to the wrong original effect."},
 {"id":"SAGA-MUT-8-SKIP-AUTHORITY","mode":"skip_compensation_authority","description":"Compensate a step without current compensation authority."}
]

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--fixtures", default=str(ROOT/"saga_topology_fixtures.json"))
    p.add_argument("--required-score", type=float, default=1.0)
    p.add_argument("--output")
    args=p.parse_args()

    baseline=saga.run(args.fixtures,"baseline")
    records=[]
    for m in MUTANTS:
        r=saga.run(args.fixtures,m["mode"])
        failing=[x["id"] for x in r["results"] if not x["passed"]]
        records.append({**m,"status":"KILLED" if failing else "SURVIVED","failing_controls":failing})

    payload=json.loads(Path(args.fixtures).read_text(encoding="utf-8"))
    par=next(c for c in payload["cases"] if c["id"]=="PACC-SAGA-5")
    smap={s["id"]:s for s in par["steps"]}
    def reaches(src,dst):
        stack=list(smap[dst].get("depends_on", []))
        seen=set()
        while stack:
            cur=stack.pop()
            if cur==src:
                return True
            if cur in seen:
                continue
            seen.add(cur)
            stack.extend(smap[cur].get("depends_on", []))
        return False

    sibling_equiv=not reaches("B","C") and not reaches("C","B")
    records.append({
      "id":"SAGA-EQUIV-1-PARALLEL-SIBLING-SWAP",
      "mode":"parallel_sibling_swap",
      "description":"Swap B/C within the same reverse compensation antichain.",
      "status":"EQUIVALENT" if sibling_equiv else "INVALID",
      "failing_controls":[],
      "equivalence_basis":"B and C are in the same reverse layer and neither is reachable from the other; order within the antichain has no causal precedence."
    })

    scored=[x for x in records if x["status"] in {"KILLED","SURVIVED"}]
    killed=sum(x["status"]=="KILLED" for x in scored)
    survived=sum(x["status"]=="SURVIVED" for x in scored)
    equivalent=sum(x["status"]=="EQUIVALENT" for x in records)
    invalid=sum(x["status"]=="INVALID" for x in records)
    score=killed/len(scored) if scored else 1.0
    status="PASS" if baseline["summary"]["status"]=="PASS" and survived==0 and invalid==0 and score>=args.required_score else "FAIL"

    report={
      "benchmark":"PACC Saga Topology Mutation Campaign","version":"0.7",
      "generated_at":datetime.now(timezone.utc).isoformat(),
      "baseline":baseline["summary"],"mutants":records,
      "scope":"falsification of reverse causal compensation order, partial execution, irreversible barriers, parallel joins, reconciliation barriers, idempotency, binding, and authority",
      "summary":{"status":status,"killed":killed,"survived":survived,"equivalent":equivalent,"invalid":invalid,"scored_total":len(scored),"total_candidates":len(records),"mutation_score":score,"required_score":args.required_score}
    }
    text=json.dumps(report,indent=2,sort_keys=True)
    print(text)
    if args.output:
        Path(args.output).parent.mkdir(parents=True,exist_ok=True)
        Path(args.output).write_text(text+"\n",encoding="utf-8")
    raise SystemExit(0 if status=="PASS" else 1)

if __name__=="__main__":
    main()
