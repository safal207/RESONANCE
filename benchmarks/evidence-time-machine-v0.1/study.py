"""Reproduce source-backed replay and existing policy audit. No LLM calls.

python study.py --out results.json
python study.py --input fresh-observation.json --out fresh-results.json
"""
from __future__ import annotations
import argparse
import copy
from datetime import timedelta
import hashlib
import json
import platform
import random
import statistics
import time
from pathlib import Path
import adapter as a
import audit as prior

HERE=Path(__file__).resolve().parent

def read_json(path): return json.loads(path.read_text(encoding='utf8'))

def run(observation):
    now=observation['recorded_at']
    before=(a.policy.timestamp(now)-timedelta(seconds=1)).isoformat()
    raw=observation['check_runs'][0]
    before_end=(a.policy.timestamp(raw['completed_at'])-timedelta(seconds=1)).isoformat()
    cp_cases=[
        ('R01_before_local_observation',dict(known_at=before),'UNKNOWN','The result had occurred, but this observation was not yet available.'),
        ('R02_exact_run_and_commit',{},'SUPPORTED','The captured GitHub result supports this run on this exact commit.'),
        ('R03_merge_commit_is_different',dict(sha=a.MERGE_SHA),'UNKNOWN','A PR-head result alone does not establish the result for the merge commit.'),
        ('R04_before_run_completed',dict(valid_at=before_end),'UNKNOWN','The query concerns the period before the run completed.'),
        ('R05_run_not_in_selected_snapshot',dict(check_id=101291849043),'UNKNOWN','Other check runs were intentionally not captured here; missing is not failure.')]
    real=[]
    for cid,kw,expected,why in cp_cases:
        cp=a.checkpoint(observation,**kw); result=a.replay(observation,cp)
        real.append(dict(id=cid,expected=expected,actual=result['status'],match=result['status']==expected,
                         explanation=why,query=cp,result=result))
    original=[]
    cases=prior.cases()
    for cid,e,expected in cases:
        b=prior.outcome(a.policy.reference_evaluate,e)
        c=prior.outcome(a.hardening.evaluate,e)
        original.append(dict(id=cid,expected=expected,baseline=b,candidate=c,baseline_match=b==expected,candidate_match=c==expected))
    # Robustness variants, not extra cases, sampled populations or success-rate estimates.
    order_checks=0
    for _,e,expected in cases:
        for seed in range(20):
            x=copy.deepcopy(e); random.Random(seed).shuffle(x['records'])
            assert prior.outcome(a.hardening.evaluate,x)==expected
            order_checks+=1
    # Counterfactual synthetic timeline for the demonstrated original defect.
    _,ep,_=next(x for x in cases if x[0]=='C03_expired_basis')
    timeline=[]
    for stamp in (prior.T1,prior.T2):
        e=copy.deepcopy(ep); cp=e['checkpoints'][0]
        cp.update(known_at=stamp,valid_at=stamp)
        timeline.append(dict(known_at=stamp,valid_at=stamp,
                             baseline=a.policy.reference_evaluate(e,cp)['status'],
                             candidate=a.hardening.evaluate(e,cp)['status'],
                             visible_ids=[r['id'] for r in a.policy.release(e,cp)['records']]))
    # End-to-end deterministic query includes selection, dependency work and fingerprint.
    # Build cost reported separately; this is synthetic load, NOT independent evidence.
    load=[]
    for n in (0,1000,10000):
        start=time.perf_counter()
        # Construct in linear time (the previous convenience helper is quadratic).
        e=copy.deepcopy(ep)
        for i in range(n):
            e['records'].append(prior.record(f'noise-{i:06d}',claim=f'noise-{i}',
                context=dict(system='unrelated',environment='test',version='v0',region='elsewhere')))
        a.policy.validate_episode(e)
        build_ms=(time.perf_counter()-start)*1000
        times=[]; verdicts=[]
        for _ in range(7):
            start=time.perf_counter()
            r=a.hardening.evaluate(e,e['checkpoints'][0])
            times.append((time.perf_counter()-start)*1000)
            verdicts.append((r['status'],r['support_ids']))
        assert all(x==('SUPPORTED',['report']) for x in verdicts)
        load.append(dict(synthetic_distractors=n,total_records=len(e['records']),
                         construction_validation_ms=round(build_ms,3),repetitions=7,
                         median_full_query_ms=round(statistics.median(times),3),
                         min_full_query_ms=round(min(times),3),max_full_query_ms=round(max(times),3),
                         verdict='SUPPORTED',support_ids=['report'],raw_full_query_ms=[round(t,3) for t in times]))
    return dict(schema='resonance.evidence-time-machine.results.v1',date='2026-09-05',
                runtime=dict(python=platform.python_version(),platform=platform.platform()),
                observation_recorded_at=now,source_snapshot_sha256=a.policy.canonical_hash(observation),
                real_source_observations=1,real_selected_check_runs=len(observation['check_runs']),
                real_source_queries=len(real),real_source_matches=sum(x['match'] for x in real),
                prior_open_synthetic_cases=len(original),prior_baseline_matches=sum(x['baseline_match'] for x in original),
                prior_candidate_matches=sum(x['candidate_match'] for x in original),
                order_robustness_checks=order_checks,llm_runs=0,independent_reviewers=0,
                real_queries=real,prior_audit=original,synthetic_timeline=timeline,synthetic_load=load,
                boundaries=['Real-source queries share ONE observation and are not five independent integrations.',
                  'The 12 synthetic cases repeat the published audit; no new population accuracy estimate.',
                  'Synthetic mutations are not GitHub incidents; no measured LLM uplift.',
                  'A source-observation fingerprint checks saved bytes, not authenticity or external completeness.',
                  'Historical check-run evidence is not a required-check evaluation, deployment test, or permission to act.',
                  'Load timings are seven local runs per size, include snapshot hashing, and are not model latency or a production SLA.'])

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',type=Path,default=HERE/'source_observation.json')
    p.add_argument('--out',type=Path,default=HERE/'results.json')
    args=p.parse_args(); result=run(read_json(args.input))
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:v for k,v in result.items() if k not in {'real_queries','prior_audit','synthetic_timeline','synthetic_load','boundaries'}},indent=2))
    print('Load (synthetic distractors, median full query ms):',[(x['synthetic_distractors'],x['median_full_query_ms']) for x in result['synthetic_load']])
    if result['real_source_matches']!=result['real_source_queries'] or result['prior_candidate_matches']!=12:
        raise SystemExit(1)
if __name__=='__main__': main()
