"""Bridge the existing temporal toy evaluator to R5+P. Reuses 12 open cases.

This is an in-process integration, not a new live connector or authentication.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

from paired import card, initial_state, replay

UPSTREAM = Path(__file__).resolve().parents[1] / 'temporal-evidence-interim-2026-09-05'


def check() -> dict:
    if not (UPSTREAM / 'hardening.py').is_file():
        raise FileNotFoundError(f'existing temporal benchmark required: {UPSTREAM}')
    sys.path.insert(0, str(UPSTREAM))
    import audit
    import hardening
    rows = []
    for name, episode, expected in audit.cases():
        cp = episode['checkpoints'][0]
        try:
            audit.tb.validate_episode(episode)
            evaluated = hardening.evaluate(episode, cp)
        except ValueError:
            if expected != 'REJECTED':
                raise
            rows.append({'case_id': name, 'expected': expected, 'actual': 'REJECTED',
                         'receipt_created': False, 'match': True})
            continue
        target_status = {'CONTESTED': 'CONFLICTS'}.get(evaluated['status'], evaluated['status'])
        claim = cp['claim']
        p = {'claim_id': claim, 'verdict': target_status,
             'support': evaluated['support_ids'], 'counterevidence': evaluated['refute_ids'],
             'limits': [evaluated['boundary'], 'Synthetic open development case; no independent verification.']}
        initial = initial_state(episode_id=name, goal_id='check-claim', recipient_id='demo-user',
                                target=cp['context'], known_at=cp['known_at'], query_time=cp['valid_at'],
                                evaluated_proof=dict(p, verdict='UNKNOWN', support=[], counterevidence=[]))
        receipt = dict(accepted=True, purpose='evidence', context=cp['context'],
                       episode_id=name, goal_id='check-claim', recipient_id='demo-user', answer_id='a1',
                       claim_id=claim, known_at=cp['known_at'], query_time=cp['valid_at'], proof=p,
                       evaluator_snapshot_sha256=evaluated['snapshot_sha256'])
        e = dict(id='e1', sequence=1, episode_id=name, goal_id='check-claim', recipient_id='demo-user',
                 actor_id='demo-user', answer_id='a1', event_at=cp['known_at'], known_at=cp['known_at'],
                 kind='EVIDENCE_CHALLENGE', payload={'receipt_id': 'evaluated'})
        s = replay(initial, [e], as_of=cp['known_at'], receipts={'evaluated': receipt})
        actual = card(s)['proof']['verdict']
        mapped_expected = {'CONTESTED': 'CONFLICTS'}.get(expected, expected)
        assert actual == mapped_expected, (name, actual, mapped_expected)
        assert card(s)['proof']['support'] == evaluated['support_ids']
        assert card(s)['proof']['counterevidence'] == evaluated['refute_ids']
        assert s['history'][0]['proof']['verdict'] == 'UNKNOWN'
        assert not card(s)['external_action_authorized']
        rows.append({'case_id': name, 'expected': mapped_expected, 'actual': actual,
                     'receipt_created': True, 'match': True})
    return {'schema': 'resonance.r5p.temporal-bridge.v1', 'cases_reused': len(rows),
            'new_independent_tasks': 0, 'live_connector_calls': 0, 'rows': rows}


if __name__ == '__main__':
    result = check()
    if len(sys.argv) > 1:
        Path(sys.argv[1]).write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2))
