"""Run a bounded, synthetic policy audit. No model/API/network calls.
Usage: python audit.py --out results.json
Exit 0 means the candidate matches these 12 expectations; it does not certify it.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import platform
import random
from pathlib import Path
import baseline as tb
import hardening

ROOT = Path(__file__).resolve().parent
T0 = '2026-09-05T10:00:00Z'
T1 = '2026-09-05T10:01:00Z'
T2 = '2026-09-05T10:02:00Z'
T3 = '2026-09-05T10:03:00Z'
CTX = dict(system='synthetic-adapter', environment='test', version='v1', region='region-A')


def record(rid: str, kind: str = 'assertion', **changes) -> dict:
    r = dict(id=rid, kind=kind, source_id='fixture-A', origin_id='origin-A',
        derived_from=[], event_at=T1, known_at=T1, valid_from=T0,
        valid_until=None, context=copy.deepcopy(CTX))
    if kind == 'assertion':
        r.update(claim='check_passed', value=True)
    r.update(changes)
    return r


def episode(conditional: bool = True) -> dict:
    rows = [record('report')]
    if conditional:
        rows.append(record('basis', claim='diagnostic_valid'))
    rows.append(record('withdrawal', 'retraction', target_id='report',
        source_id='fixture-auditor', known_at=T2, event_at=T2,
        derived_from=['basis'] if conditional else []))
    return dict(episode_id='audit', task='Apply the declared toy policy, not real-world truth.',
        synthetic=True, policy=dict(accepted_sources=['fixture-A','fixture-B','fixture-auditor'],
        retraction_authorities=['fixture-auditor'],
        dependency_rule='all derivation parents must remain usable at query valid time'),
        records=rows, checkpoints=[dict(id='C', known_at=T2, valid_at=T2,
        context=copy.deepcopy(CTX), query_type='claim', claim='check_passed')])


def cases() -> list[tuple[str, dict, str]]:
    out = []
    def add(name, e, expected):
        e['episode_id'] = name
        tb.validate_episode(e)
        out.append((name, e, expected))
    add('C01_unconditional_withdrawal', episode(False), 'UNKNOWN')
    add('C02_valid_conditional_withdrawal', episode(), 'UNKNOWN')
    e=episode(); e['records'][1]['valid_until']=T1
    add('C03_expired_basis', e, 'SUPPORTED')
    e=episode(); e['records'][1]['source_id']='unaccepted-fixture'
    add('C04_unaccepted_basis', e, 'SUPPORTED')
    e=episode(); e['records'].append(record('withdraw-basis','retraction',target_id='basis',
        source_id='fixture-auditor', known_at=T2))
    add('C05_revoked_basis', e, 'SUPPORTED')
    e=episode(); e['records'][-1]['known_at']=T3
    add('C06_future_withdrawal', e, 'SUPPORTED')
    e=episode(); e['records'][-1]['context']['region']='other-region'
    add('C07_wrong_context', e, 'SUPPORTED')
    e=episode(); e['records'][-1]['source_id']='fixture-B'
    add('C08_unauthorized_withdrawal', e, 'SUPPORTED')
    e=episode(); e['records'][-1]['valid_until']=T1
    add('C09_expired_withdrawal', e, 'SUPPORTED')
    e=episode(); e['records'][1]['derived_from']=['root']; e['records'].append(
        record('root',claim='calibration_current',valid_until=T1))
    add('C10_transitively_expired_basis', e, 'SUPPORTED')
    e=episode(); e['records']=[e['records'][0],record('negative',value=False,source_id='fixture-B')]
    add('C11_explicit_conflict', e, 'CONTESTED')
    e=episode(); e['records'][1]['derived_from']=['report']
    add('C12_circular_justification', e, 'REJECTED')
    return out


def outcome(fn, e):
    try:
        return fn(e, e['checkpoints'][0])['status']
    except ValueError:
        return 'REJECTED'


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',type=Path,default=ROOT/'results.json')
    args=p.parse_args()
    rows=[]; variants=0
    for name,e,expected in cases():
        original=outcome(tb.reference_evaluate,e); candidate=outcome(hardening.evaluate,e)
        rows.append(dict(case_id=name,expected=expected,baseline=original,candidate=candidate,
            baseline_match=original==expected,candidate_match=candidate==expected,
            episode_sha256=tb.canonical_hash(e)))
        # Seeded order variants are robustness checks, NOT independent tasks.
        for seed in range(50):
            altered=copy.deepcopy(e); random.Random(seed).shuffle(altered['records'])
            assert outcome(hardening.evaluate,altered)==expected, (name,seed)
            variants+=1
        # Future appends must not alter either historical input representation.
        future=copy.deepcopy(e); future['records'].append(record('future-extra',known_at=T3,claim='irrelevant'))
        for fmt in ('flat','graph'):
            assert tb.release(e,e['checkpoints'][0],fmt)==tb.release(future,future['checkpoints'][0],fmt)
    result=dict(schema='resonance.temporal-policy-audit.v1',research_date='2026-09-05',
        python_version=platform.python_version(),synthetic=True,llm_runs=0,independent_reviewers=0,
        original_module_sha256=hashlib.sha256((ROOT/'baseline.py').read_bytes()).hexdigest(),
        case_count=len(rows),baseline_matches=sum(r['baseline_match'] for r in rows),
        candidate_matches=sum(r['candidate_match'] for r in rows),
        candidate_order_variants=variants,historical_release_checks=len(rows)*2,
        boundary='author-designed open dev cases; no population accuracy estimate; no security/action authorization; circular cases rejected, not resolved',
        rows=rows)
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:v for k,v in result.items() if k!='rows'},indent=2))
    if not all(r['candidate_match'] for r in rows):
        raise SystemExit(1)

if __name__=='__main__': main()
