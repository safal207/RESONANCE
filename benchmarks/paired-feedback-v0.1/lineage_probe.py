"""Paired presentation-path audit. Deterministic fixtures, NOT an LLM A/B/C trial.

Reproduce with the pinned pre-fix module supplied via --baseline. No API/network.
"""
from __future__ import annotations
import argparse
import hashlib
import html
import importlib.util
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
import paired
from test_paired import SCOPE, PROOF, T0, event, receipt

BASELINE_SHA256 = '0517e3c573772a999b149d8f1b6c3ee96b40b7cd3d628cb067a0d49a331027c6'
BASELINE_COMMIT = '0d83d3e767756e40b5fceab4fe207a524c152ede'


def stamp(i):
    return (datetime(2026, 9, 5, 9, tzinfo=timezone.utc) + timedelta(minutes=i)).isoformat().replace('+00:00', 'Z')


def initial(module, compact=False):
    s = module.initial_state(episode_id='demo', goal_id='check-target', recipient_id='demo-user', target=SCOPE,
                             evaluated_proof=PROOF, known_at=T0, query_time=T0)
    if compact:
        s['history'][0]['detail'] = 'compact'
    return s


def path(module, changes, bound_index=1, initially_compact=False):
    s = initial(module, initially_compact)
    es = []
    detail = s['history'][0]['detail']
    for i in range(1, changes + 1):
        detail = 'compact' if detail == 'full' else 'full'
        es.append(event('PREFERENCE_FEEDBACK', {'detail': detail}, id=f'e{i}', sequence=i,
                        answer_id=f'a{i}', event_at=stamp(i), known_at=stamp(i)))
    i = changes + 1
    es.append(event('EVIDENCE_CHALLENGE', {'receipt_id': 'r'}, id=f'e{i}', sequence=i,
                    answer_id=f'a{bound_index}', event_at=stamp(i), known_at=stamp(i)))
    r = receipt(answer_id=f'a{bound_index}', known_at=stamp(i))
    out = module.replay(s, es, as_of=stamp(i), receipts={'r': r})
    return {'card': module.card(out), 'audit': out['audit'], 'history': out['history'],
            'initial': s, 'events': es, 'receipts': {'r': r}}


def make_report(baseline):
    rows = []
    for name, n, brief in [('Full from start', 0, False), ('Compact from start', 0, True), ('Compact after issued answer', 1, False)]:
        old, new = path(baseline, n, initially_compact=brief), path(paired, n, initially_compact=brief)
        assert new['card']['proof']['verdict'] == 'REFUTED'
        assert not new['card']['external_action_authorized']
        rows.append({'path': name, 'expected': 'REFUTED', 'baseline': old['card']['proof']['verdict'],
                     'candidate': new['card']['proof']['verdict'], 'trace_before': old, 'trace_after': new})
    matrix = []
    for n in range(6):
        for bound in range(1, n + 2):
            old, new = path(baseline, n, bound), path(paired, n, bound)
            matrix.append({'presentation_changes': n, 'receipt_answer': f'a{bound}',
                           'baseline_correct': old['card']['proof']['verdict'] == 'REFUTED',
                           'candidate_correct': new['card']['proof']['verdict'] == 'REFUTED'})
    assert len(matrix) == 21 and all(x['candidate_correct'] for x in matrix)
    outcome = {}
    es = [event('RESULT_REPORTED', {'result': 'fixture completed'}),
          event('PREFERENCE_FEEDBACK', {'detail': 'compact'}, id='e2', sequence=2, event_at=stamp(2), known_at=stamp(2))]
    for label, mod in [('baseline', baseline), ('candidate', paired)]:
        state = mod.replay(initial(mod), es, as_of=stamp(2))
        c = mod.card(state)
        outcome[label] = {'current_answer_id': c['answer_id'], 'current_outcome_basis': c['outcome_basis'],
                          'earlier_answer_records_visible': c.get('related_outcome_observations', []),
                          'historically_stored': state['outcomes']}
    assert outcome['candidate']['current_outcome_basis'] == 'NOT_OBSERVED'
    assert outcome['candidate']['earlier_answer_records_visible'][0]['answer_id'] == 'a1'
    assert outcome['candidate']['historically_stored'] == outcome['baseline']['historically_stored']
    return {'schema': 'resonance.presentation-lineage.probe.v1', 'synthetic': True,
            'baseline_commit': BASELINE_COMMIT, 'baseline_sha256': BASELINE_SHA256,
            'candidate_sha256': hashlib.sha256(Path(paired.__file__).read_bytes()).hexdigest(),
            'rows': rows, 'matrix': matrix,
            'matrix_baseline_correct': sum(x['baseline_correct'] for x in matrix),
            'matrix_candidate_correct': sum(x['candidate_correct'] for x in matrix),
            'outcome_visibility': outcome, 'llm_runs': 0, 'human_participants': 0,
            'tokens_measured': False,
            'boundary': 'Three paths and 21 overlapping perturbations of one developer-authored fixture. Not a population error rate, token saving, or a comparison of models/protocol efficacy.'}


def render(report):
    rows = ''.join('<tr><td>'+html.escape(r['path'])+'</td><td>'+r['baseline']+'</td><td>'+r['candidate']+'</td><td>'+r['expected']+'</td></tr>' for r in report['rows'])
    raw = json.dumps(report, indent=2)
    return '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Shorter must not mean harder to correct — RESONANCE</title>
<style>body{margin:0;background:#f4f6fa;color:#182236;font:17px/1.6 system-ui,sans-serif}main{max-width:1050px;margin:auto;padding:36px 22px}h1{font-size:clamp(32px,5vw,58px);line-height:1.1;letter-spacing:-.035em}h2{font-size:24px}section{background:white;border:1px solid #cdd6e1;border-radius:14px;padding:24px;margin:22px 0}.label{font-size:12px;letter-spacing:.12em;font-weight:700}.limit{padding:16px;border-left:4px solid #6250b4;background:#ece9f8}.table{overflow-x:auto}table{width:100%;border-collapse:collapse;font-size:15px}td,th{text-align:left;padding:13px;border-bottom:1px solid #dbe1e8}th{background:#edf1f7}pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:12px;max-height:550px;overflow:auto}code{overflow-wrap:anywhere}summary,button{cursor:pointer}button{font:inherit;padding:10px 14px;border-radius:8px;border:1px solid #adb9cc;background:white}.flow{font-size:22px}footer{font-size:14px;color:#546276}</style>
<main><div class="label">RESONANCE / R5 + P / DEVELOPMENT EVIDENCE</div><h1>Shorter must not mean<br>harder to correct.</h1><p>A presentation change must not orphan a verified correction. A factual change must still block stale evidence.</p>
<div class="limit"><strong>Observed in deterministic code, not in a language-model trial.</strong> One synthetic fixture; no human participants; no measured token or accuracy benefit.</div>
<section><h2>The failure</h2><p class="flow">Answer a1 → “Make it shorter” → Answer a2 → Verified correction addressed to a1</p><p>The original reducer treats the correction as stale merely because the answer ID changed. The candidate separates <strong>answer_id</strong> from <strong>fact_revision</strong>. Exact receipt bindings are retained.</p></section>
<section><h2>Same evidence. Three presentation paths.</h2><div class="table"><table><thead><tr><th>Presentation path</th><th>Before</th><th>Candidate</th><th>Expected</th></tr></thead><tbody>'''+rows+'''</tbody></table></div><p>Compact from the start works in both versions. The failure is tied to the presentation transition, not to the length of the answer. These are state-machine paths, not experimental R5/R5+P model arms.</p></section>
<section><h2>Do not erase — or misattribute — the outcome</h2><p>A report associated with a1 remains associated with a1. The current a2 outcome is still <code>NOT_OBSERVED</code>; the earlier record is shown separately as <code>RECORDED_FOR_EARLIER_ANSWER</code>. Visibility is not evidence that the reformulated answer caused success.</p></section>
<section><h2>Systematic presentation perturbations</h2><p><strong>Before: '''+str(report['matrix_baseline_correct'])+'''/21. Candidate: '''+str(report['matrix_candidate_correct'])+'''/21.</strong> These 21 overlapping variations change the number of presentation revisions and the exact answer receiving the receipt. They are not 21 independent tasks.</p><p>Context changes and accepted factual revisions are barriers even when a version name or verdict later returns to its previous value.</p></section>
<section><details><summary>Inspect source fingerprints and complete before/after traces</summary><pre id="raw">'''+html.escape(raw)+'''</pre></details><button id="save">Export audit JSON</button></section>
<footer>Baseline commit: <code>'''+BASELINE_COMMIT+'''</code><br>Read-only local test boundary. No release decision, source authentication or external action authority. Candidate pending review; not scientific novelty or product efficacy evidence.</footer></main>
<script>document.getElementById('save').onclick=()=>{const b=new Blob([document.getElementById('raw').textContent],{type:'application/json'}),u=URL.createObjectURL(b),a=document.createElement('a');a.href=u;a.download='presentation-lineage-audit.json';a.click();setTimeout(()=>URL.revokeObjectURL(u),1000)};</script></html>'''


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--baseline', type=Path, required=True)
    ap.add_argument('--out', type=Path, default=Path('results'))
    args = ap.parse_args()
    if hashlib.sha256(args.baseline.read_bytes()).hexdigest() != BASELINE_SHA256:
        raise SystemExit('Baseline fingerprint mismatch; refusing an unpinned comparison.')
    spec = importlib.util.spec_from_file_location('paired_pinned_baseline', args.baseline)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    report = make_report(mod)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / 'lineage-audit.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    (args.out / 'lineage-audit.html').write_text(render(report), encoding='utf-8')
    print(json.dumps({k: v for k,v in report.items() if k not in {'rows','matrix','outcome_visibility'}}, indent=2))

if __name__ == '__main__':
    main()
