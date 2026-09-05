"""Build an offline trace explorer. The browser displays Python-computed snapshots.

Not a live chatbot; synthetic replies only. Run the reducer to recompute traces.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from paired import card, fingerprint, replay
from test_paired import PROOF, SCOPE, T0, T1, T2, T3, event, receipt, start


def examples():
    definitions = [
        ('No reply', 'No feedback does not establish success or failure.', [], {}),
        ('Thank you', 'Acknowledgment is not evidence that the task was completed.', [event('ACK')], {}),
        ('Make it shorter', 'Change the presentation; keep the proof and its limits.',
         [event('PREFERENCE_FEEDBACK', {'detail': 'compact'})], {}),
        ('I disagree', 'Record the disagreement without reversing a supported claim.',
         [event('DISAGREEMENT')], {}),
        ('Different version', 'The old PASS does not transfer from v1 to v2.',
         [event('CONTEXT_CORRECTION', {'context': dict(SCOPE, version='v2')})], {}),
        ('Checked correction', 'A bound, evaluated receipt changes the verdict and preserves history.',
         [event('EVIDENCE_CHALLENGE', {'receipt_id': 'r1'})], {'r1': receipt()}),
        ('Stop', 'A reply to an older answer can still stop this episode.',
         [event('PREFERENCE_FEEDBACK', {'detail': 'compact'}),
          event('STOPPED', id='e2', sequence=2, event_at=T2, known_at=T2)], {}),
        ('Conflict, compact', 'Shorter must not mean hiding counterevidence.',
         [event('PREFERENCE_FEEDBACK', {'detail': 'compact'})], {}),
    ]
    result = []
    for name, description, events, receipts in definitions:
        p = dict(PROOF, verdict='CONFLICTS', counterevidence=['fixture:failed-check']) if name == 'Conflict, compact' else PROOF
        initial = start(evaluated_proof=p)
        times = [T0] + [e['known_at'] for e in events]
        # Silence has an observable later view but still NO synthetic user event.
        if not events:
            times.append(T3)
        states = []
        for at in times:
            s = replay(initial, events, as_of=at, receipts=receipts)
            states.append({'as_of': at, 'state': s, 'card': card(s)})
        result.append({'name': name, 'description': description, 'initial': initial,
                       'events': events, 'receipts': receipts, 'snapshots': states})
    return {'schema': 'resonance.r5p.trace-explorer.v1', 'synthetic': True,
            'llm_runs': 0, 'human_participants': 0, 'data': result,
            'input_fingerprint': fingerprint(result)}


HTML = '''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>R5 + P — A reply is not a proof</title>
<style>
:root{color-scheme:light;--ink:#172337;--muted:#526379;--border:#cbd5e1;--paper:#fff;--accent:#4932a6}
*{box-sizing:border-box}body{margin:0;background:#f3f5f9;color:var(--ink);font:16px/1.55 system-ui,sans-serif}
main{max-width:1180px;margin:auto;padding:32px 24px}header{margin-bottom:26px}h1{font-size:clamp(30px,4.5vw,54px);line-height:1.08;letter-spacing:-.04em;margin:10px 0 16px;max-width:830px}h2{font-size:22px;margin:0 0 14px}p{margin:10px 0}.eyebrow{font-size:12px;letter-spacing:.13em;font-weight:750;color:var(--accent)}.lede{max-width:850px;color:var(--muted)}.boundary{padding:14px 18px;background:#eae5fa;border-radius:12px;font-size:14px;margin:20px 0}
.layout{display:grid;grid-template-columns:255px 1fr;gap:24px}nav{display:flex;flex-direction:column;gap:8px}button,select{font:inherit}button{cursor:pointer;text-align:left;border:1px solid var(--border);border-radius:10px;padding:12px 14px;background:var(--paper);color:var(--ink)}button[aria-pressed=true]{background:var(--ink);color:white;border-color:var(--ink)}button:focus-visible,select:focus-visible,summary:focus-visible{outline:3px solid #7d4fff;outline-offset:3px}.panel{background:var(--paper);border:1px solid var(--border);border-radius:16px;padding:24px;min-width:0}.top{display:flex;align-items:center;justify-content:space-between;gap:14px;flex-wrap:wrap}.label{font-size:12px;font-weight:750;letter-spacing:.06em;color:var(--muted)}#verdict{font-size:34px;font-weight:800;letter-spacing:-.03em}.pill{display:inline-block;padding:5px 10px;background:#edf0f6;border-radius:99px;font-size:12px}.cols{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin:18px 0}.box{border-top:1px solid var(--border);padding-top:13px;min-width:0}ul{padding-left:22px;margin:7px 0}li{overflow-wrap:anywhere}select{padding:9px;border:1px solid var(--border);border-radius:8px;max-width:100%;background:white}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:12px/1.55 ui-monospace,monospace;background:#f4f6fa;padding:16px;border-radius:9px;max-height:340px;overflow:auto}.fine{font-size:13px;color:var(--muted)}footer{margin-top:26px;color:var(--muted);font-size:13px}summary{cursor:pointer;padding:10px 0}#description{min-height:48px;color:var(--muted)}.outcome{padding:12px;background:#f4f6fa;border-radius:9px;margin:18px 0}#history{display:flex;flex-wrap:wrap;gap:8px}.step{padding:5px 10px;border:1px solid var(--border);border-radius:8px;font-size:13px}
@media(max-width:700px){main{padding:22px 16px}.layout{grid-template-columns:1fr}nav{display:grid;grid-template-columns:1fr 1fr}nav button{font-size:14px;padding:10px}.panel{padding:18px}.cols{grid-template-columns:1fr}h1{font-size:35px}#verdict{font-size:28px}}
</style></head><body><main>
<header><div class="eyebrow">RESONANCE / RESEARCH PROTOTYPE / R5 + P</div><h1>Adapt to the person.<br>Do not negotiate the facts.</h1><p class="lede">A reply can change the form, the target or the evidence. Those are different transitions. Explore what changes — and what must stay intact.</p><div class="boundary"><strong>Synthetic trace explorer, not a live AI.</strong> These snapshots are computed by the Python reducer. No real participants, model comparisons, token savings or human-comfort results are claimed.</div></header>
<div class="layout"><nav id="scenarios" aria-label="Feedback scenarios"></nav><section class="panel" aria-live="polite"><div class="top"><h2 id="title"></h2><label class="fine">Knowledge cut-off <select id="time" aria-label="Knowledge cut-off"></select></label></div><p id="description"></p><div class="label">EVIDENCE VERDICT</div><div class="top"><div id="verdict"></div><span class="pill" id="context"></span></div><div class="cols"><div class="box"><div class="label">SUPPORTING REFERENCES</div><ul id="support"></ul></div><div class="box"><div class="label">COUNTEREVIDENCE</div><ul id="counter"></ul></div></div><div class="box"><div class="label">BOUNDARIES — NEVER HIDDEN BY COMPACT MODE</div><ul id="limits"></ul></div><div class="outcome"><strong id="outcome"></strong><div class="fine">Reply optional · No automatic follow-up · No authority to act</div></div><div class="label">ANSWER HISTORY</div><div id="history"></div><p class="fine" id="effect"></p><details><summary>Inspect the exact input and selected snapshot</summary><pre id="raw"></pre></details><button id="download" type="button">Export this synthetic trace (JSON)</button></section></div>
<footer>Receipts are supplied by a trusted local test boundary. This prototype does not authenticate people or evidence sources. “Observed” is not “independently verified”. The full A/B/C model-and-human experiment remains unrun.</footer>
</main><script id="dataset" type="application/json">__DATA__</script><script>
const payload=JSON.parse(document.getElementById('dataset').textContent);let selected=0;
const $=id=>document.getElementById(id);function list(id,items){$(id).replaceChildren(...(items.length?items:['None in this snapshot.']).map(x=>{const li=document.createElement('li');li.textContent=x;return li}));}
function render(){const e=payload.data[selected],s=e.snapshots[Number($('time').value)],c=s.card;$('title').textContent=e.name;$('description').textContent=e.description;$('verdict').textContent=c.proof.verdict;$('context').textContent=c.context.version+' / '+c.context.environment+' / '+c.detail;list('support',c.proof.support);list('counter',c.proof.counterevidence);list('limits',c.proof.limits);$('outcome').textContent='Outcome: '+c.outcome_basis+' · Episode: '+c.lifecycle+' · Review: '+(c.pending_review?'PENDING':'no pending challenge');$('history').replaceChildren(...s.state.history.map(a=>{const n=document.createElement('span');n.className='step';n.textContent=a.answer_id+' · '+a.proof.verdict;return n}));const last=s.state.audit.at(-1);$('effect').textContent='Last effect: '+(last?last.effect:'No feedback event observed.');$('raw').textContent=JSON.stringify({initial:e.initial,events:e.events.filter(x=>Date.parse(x.known_at)<=Date.parse(s.as_of)),selected_snapshot:s},null,2);}
function choose(i){selected=i;document.querySelectorAll('nav button').forEach((b,j)=>b.setAttribute('aria-pressed',i===j?'true':'false'));$('time').replaceChildren(...payload.data[i].snapshots.map((s,j)=>{const o=document.createElement('option');o.value=j;o.textContent=(j===0?'Before':'After')+' · '+s.as_of.slice(11,19)+' UTC';return o}));$('time').value=payload.data[i].snapshots.length-1;render();}
payload.data.forEach((e,i)=>{const b=document.createElement('button');b.textContent=e.name;b.type='button';b.onclick=()=>choose(i);$('scenarios').append(b)});$('time').onchange=render;$('download').onclick=()=>{const blob=new Blob([JSON.stringify(payload.data[selected],null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='r5p-synthetic-trace.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)};choose(0);
</script></body></html>'''


def build(out: Path):
    payload = examples()
    encoded = json.dumps(payload, ensure_ascii=False).replace('<', '\\u003c')
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(HTML.replace('__DATA__', encoded), encoding='utf-8')
    out.with_suffix('.json').write_text(json.dumps(payload, indent=2) + '\n', encoding='utf-8')
    return payload


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=Path('paired-feedback.html'))
    args = parser.parse_args()
    payload = build(args.out)
    print(json.dumps({'scenarios': len(payload['data']), 'html': str(args.out),
                      'input_fingerprint': payload['input_fingerprint'],
                      'synthetic': True, 'llm_runs': 0, 'human_participants': 0}))
