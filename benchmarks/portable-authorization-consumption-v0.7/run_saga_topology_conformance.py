#!/usr/bin/env python3
import argparse, json
from datetime import datetime, timezone
from pathlib import Path

def ancestor_ids(steps_by_id, failed_step):
    seen=set()
    stack=list(steps_by_id[failed_step].get("depends_on", [])) if failed_step in steps_by_id else []
    while stack:
        cur=stack.pop()
        if cur in seen:
            continue
        seen.add(cur)
        stack.extend(steps_by_id[cur].get("depends_on", []))
    if failed_step in steps_by_id and steps_by_id[failed_step].get("effect_committed"):
        seen.add(failed_step)
    return seen

def reverse_layers(steps_by_id, candidates):
    candidates=set(candidates)
    if not candidates:
        return []
    children={i:set() for i in candidates}
    for i in candidates:
        for dep in steps_by_id[i].get("depends_on", []):
            if dep in candidates:
                children[dep].add(i)
    remaining=set(candidates)
    layers=[]
    while remaining:
        layer=sorted(i for i in remaining if not (children[i] & remaining))
        if not layer:
            raise ValueError("cycle in saga topology")
        layers.append(layer)
        remaining-=set(layer)
    return layers

def evaluate_case(case, mode="baseline"):
    steps={s["id"]:dict(s) for s in case["steps"]}
    if case.get("trigger") == "NONE":
        if mode == "compensate_without_trigger":
            committed=[i for i,s in steps.items() if s.get("effect_committed")]
            layers=reverse_layers(steps, committed)
            return {"status":"COMPENSATED","compensation_layers":layers,"new_compensations":len(committed),"blocked_steps":[]}
        return {"status":"NO_COMPENSATION_REQUIRED","compensation_layers":[],"new_compensations":0,"blocked_steps":[]}

    for i,s in steps.items():
        if s.get("effect_committed"):
            for dep in s.get("depends_on", []):
                if not steps.get(dep, {}).get("effect_committed"):
                    return {"status":"BLOCK_CAUSAL_GAP","compensation_layers":[],"new_compensations":0,"blocked_steps":[i]}

    failed=case.get("failed_step")
    candidates=ancestor_ids(steps, failed)
    candidates={i for i in candidates if steps[i].get("effect_committed")}
    if mode == "compensate_unexecuted_failed" and failed in steps:
        candidates.add(failed)

    layers=reverse_layers(steps, candidates)
    if mode == "forward_compensation_order":
        layers=list(reversed(layers))
    if mode == "early_upstream_parallel_compensation" and len(layers) >= 2 and any(len(x) > 1 for x in layers):
        layers=[sorted(layers[0] + layers[1])] + layers[2:]

    emitted=[]
    blocked=[]
    barrier_status=None
    all_replay=True if candidates else False
    observed_layers=[]

    for idx,layer in enumerate(layers):
        layer_observed=[]
        layer_barrier=False
        for sid in layer:
            s=steps[sid]
            layer_observed.append(sid)

            if not s.get("reversible", True) and mode != "compensate_irreversible":
                blocked.append(sid)
                barrier_status=barrier_status or "PARTIALLY_COMPENSATED_MANUAL_INTERVENTION"
                layer_barrier=True
                all_replay=False
                continue

            if not s.get("compensation_authorized", False) and mode != "skip_compensation_authority":
                blocked.append(sid)
                barrier_status=barrier_status or "BLOCK_COMPENSATION_NOT_AUTHORIZED"
                layer_barrier=True
                all_replay=False
                continue

            if not s.get("compensation_key"):
                blocked.append(sid)
                barrier_status=barrier_status or "BLOCK_MISSING_COMPENSATION_IDEMPOTENCY_KEY"
                layer_barrier=True
                all_replay=False
                continue

            state=s.get("compensation_state", "NOT_SENT")
            if state == "COMMITTED":
                binds=s.get("receipt_binds_effect_ref") == s.get("effect_ref")
                if not binds and mode != "ignore_compensation_binding":
                    blocked.append(sid)
                    barrier_status=barrier_status or "BLOCK_COMPENSATION_BINDING"
                    layer_barrier=True
                    all_replay=False
                    continue
                if mode == "duplicate_on_saga_replay":
                    emitted.append(sid)
                    all_replay=False
            elif state == "UNKNOWN":
                if mode == "continue_after_unknown":
                    emitted.append(sid)
                    all_replay=False
                else:
                    barrier_status=barrier_status or "RECONCILE_COMPENSATION_REQUIRED"
                    layer_barrier=True
                    all_replay=False
            else:
                emitted.append(sid)
                all_replay=False

        observed_layers.append(sorted(layer_observed))
        if layer_barrier and mode != "continue_after_unknown":
            upstream=set()
            for later in layers[idx+1:]:
                upstream.update(later)
            blocked.extend(sorted(upstream))
            break

    blocked=sorted(set(blocked))
    new_count=len(emitted)

    if barrier_status:
        status=barrier_status
    elif all_replay and candidates:
        status="IDEMPOTENT_SAGA_REPLAY"
    else:
        status="COMPENSATED"

    return {
        "status":status,
        "compensation_layers":observed_layers,
        "new_compensations":new_count,
        "blocked_steps":blocked,
    }

def run(fixtures_path, mode="baseline"):
    payload=json.loads(Path(fixtures_path).read_text(encoding="utf-8"))
    results=[]
    for case in payload["cases"]:
        actual=evaluate_case(case, mode=mode)
        expected=case["expected"]
        results.append({"id":case["id"],"name":case["name"],"actual":actual,"expected":expected,"passed":actual==expected})
    passed=sum(r["passed"] for r in results)
    return {
        "benchmark":"PACC Multi-Step Saga Topology",
        "version":"0.7",
        "generated_at":datetime.now(timezone.utc).isoformat(),
        "mode":mode,
        "results":results,
        "scope":"deterministic saga-topology reference semantics; not an external-product certification",
        "summary":{"status":"PASS" if passed==len(results) else "FAIL","passed":passed,"total":len(results)}
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--fixtures", default=str(Path(__file__).with_name("saga_topology_fixtures.json")))
    p.add_argument("--output")
    p.add_argument("--mode", default="baseline")
    args=p.parse_args()
    report=run(args.fixtures,args.mode)
    text=json.dumps(report,indent=2,sort_keys=True)
    print(text)
    if args.output:
        Path(args.output).parent.mkdir(parents=True,exist_ok=True)
        Path(args.output).write_text(text+"\n",encoding="utf-8")
    raise SystemExit(0 if report["summary"]["status"]=="PASS" else 1)

if __name__=="__main__":
    main()
