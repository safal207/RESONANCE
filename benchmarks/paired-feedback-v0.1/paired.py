"""R5+P development reducer. Structured events, not a language model or authority.

The caller supplies evaluated evidence receipts from a trusted local boundary.
This module neither authenticates that caller nor evaluates arbitrary evidence.
No operation here authorizes or performs external actions.
"""
from __future__ import annotations

import copy
import hashlib
import json
from datetime import datetime
from typing import Any

CONTEXT_KEYS = {'system', 'environment', 'version', 'region'}
VERDICTS = {'SUPPORTED', 'REFUTED', 'UNKNOWN', 'CONFLICTS'}
KINDS = {
    'ACK': set(), 'DISAGREEMENT': set(),
    'PREFERENCE_FEEDBACK': {'detail'}, 'CLARIFICATION': {'fields'},
    'CONTEXT_CORRECTION': {'context'}, 'EVIDENCE_CHALLENGE': {'receipt_id'},
    'RESULT_REPORTED': {'result'}, 'RESULT_OBSERVED': {'receipt_id'},
    'DECLINED': set(), 'STOPPED': set(),
}
EVENT_KEYS = {'id', 'sequence', 'episode_id', 'goal_id', 'recipient_id',
              'actor_id', 'answer_id', 'event_at', 'known_at', 'kind', 'payload'}


def timestamp(value: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError('timestamp must be a string')
    try:
        result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError as exc:
        raise ValueError('invalid timestamp') from exc
    if result.tzinfo is None or result.utcoffset() is None:
        raise ValueError('timezone required')
    return result


def fingerprint(value: Any) -> str:
    data = json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False)
    return hashlib.sha256(data.encode()).hexdigest()


def context(value: dict) -> dict:
    if not isinstance(value, dict) or set(value) != CONTEXT_KEYS:
        raise ValueError('context must contain exactly four dimensions')
    if any(not isinstance(v, str) or not v.strip() for v in value.values()):
        raise ValueError('context dimensions must be nonempty strings')
    return copy.deepcopy(value)


def proof(value: dict) -> dict:
    keys = {'claim_id', 'verdict', 'support', 'counterevidence', 'limits'}
    if not isinstance(value, dict) or set(value) != keys:
        raise ValueError('invalid evaluated proof shape')
    if not isinstance(value['claim_id'], str) or not value['claim_id'].strip():
        raise ValueError('claim_id required')
    if value['verdict'] not in VERDICTS:
        raise ValueError('invalid verdict')
    for field in ('support', 'counterevidence', 'limits'):
        if not isinstance(value[field], list) or any(
                not isinstance(x, str) or not x.strip() for x in value[field]):
            raise ValueError('proof fields must be string lists')
    if not value['limits']:
        raise ValueError('an explicit proof boundary is required')
    if value['verdict'] == 'SUPPORTED' and not value['support']:
        raise ValueError('SUPPORTED needs support references')
    if value['verdict'] in {'REFUTED', 'CONFLICTS'} and not value['counterevidence']:
        raise ValueError('negative or conflicting verdict needs counterevidence')
    if value['verdict'] == 'CONFLICTS' and not value['support']:
        raise ValueError('CONFLICTS also needs supporting evidence')
    return copy.deepcopy(value)


def initial_state(*, episode_id: str, goal_id: str, recipient_id: str,
                  target: dict, evaluated_proof: dict, known_at: str,
                  query_time: str, known_fields: dict | None = None) -> dict:
    """query_time is the fixed evidence-validity query; known_at is availability."""
    for value in (episode_id, goal_id, recipient_id):
        if not isinstance(value, str) or not value.strip():
            raise ValueError('nonempty identity required')
    timestamp(known_at)
    timestamp(query_time)
    fields = copy.deepcopy(known_fields or {})
    if any(k in CONTEXT_KEYS or not isinstance(k, str) or not k.strip()
           or not isinstance(v, str) or not v.strip() for k, v in fields.items()):
        raise ValueError('known_fields must be nonempty strings outside context')
    answer = {'answer_id': 'a1', 'context': context(target),
              'proof': proof(evaluated_proof), 'detail': 'full', 'pending_review': False,
              'reason': 'initial evaluated snapshot', 'known_at': known_at}
    return {'episode_id': episode_id, 'goal_id': goal_id, 'recipient_id': recipient_id,
            'query_time': query_time, 'history': [answer], 'known_fields': fields,
            'outcomes': {}, 'lifecycle': 'OPEN', 'audit': [],
            'external_action_authorized': False}


def _revise(state: dict, event: dict, reason: str, **changes: Any) -> None:
    answer = copy.deepcopy(state['history'][-1])
    answer.update(changes)
    answer.update(answer_id=f"a{len(state['history']) + 1}", reason=reason,
                  known_at=event['known_at'])
    state['history'].append(answer)


def _receipt(registry: dict, event: dict, state: dict, purpose: str) -> dict | None:
    rid = event['payload'].get('receipt_id')
    r = registry.get(rid) if isinstance(rid, str) else None
    if not isinstance(r, dict) or r.get('accepted') is not True:
        return None
    answer = state['history'][-1]
    if (r.get('purpose') != purpose or r.get('context') != answer['context']
            or r.get('claim_id') != answer['proof']['claim_id']
            or r.get('episode_id') != state['episode_id']
            or r.get('goal_id') != state['goal_id']
            or r.get('recipient_id') != state['recipient_id']
            or r.get('answer_id') != answer['answer_id']):
        return None
    if timestamp(r['known_at']) > timestamp(event['known_at']):
        return None
    if timestamp(r['query_time']) != timestamp(state['query_time']):
        return None
    return r


def replay(initial: dict, events: list[dict], *, as_of: str,
           receipts: dict | None = None) -> dict:
    """Replay a host-ordered log; future entries are not used in historical views.

    Sequence is explicit append order, not inferred physical or causal order.
    Exact duplicate event IDs are idempotent; altered duplicates are rejected.
    """
    state = copy.deepcopy(initial)
    if state['audit'] or len(state['history']) != 1 or state['outcomes']:
        raise ValueError('replay requires an initial state, not a partial replay')
    cutoff = timestamp(as_of)
    first_known = timestamp(state['history'][0]['known_at'])
    if cutoff < first_known:
        raise ValueError('the initial answer was not yet available')
    registry = receipts or {}
    seen: dict[str, str] = {}
    last_seq, last_known = 0, first_known
    for e in events:
        available = timestamp(e['known_at'])
        if available > cutoff:
            continue
        if set(e) != EVENT_KEYS or e['kind'] not in KINDS:
            raise ValueError('invalid event shape or kind')
        if any(not isinstance(e[k], str) or not e[k].strip() for k in
               ('id', 'episode_id', 'goal_id', 'recipient_id', 'actor_id', 'answer_id')):
            raise ValueError('invalid event identity')
        if type(e['sequence']) is not int or e['sequence'] < 1:
            raise ValueError('positive integer sequence required')
        payload = e['payload']
        if not isinstance(payload, dict) or set(payload) != KINDS[e['kind']]:
            raise ValueError('invalid payload fields; inline verdicts are not accepted')
        digest = fingerprint(e)
        if e['id'] in seen:
            if digest != seen[e['id']]:
                raise ValueError('event ID reused with a different payload')
            continue
        if e['sequence'] <= last_seq or available < last_known:
            raise ValueError('log sequence/availability must be monotonic')
        if timestamp(e['event_at']) > available:
            raise ValueError('event clock is ahead of observation; normalize explicitly')
        last_seq, last_known = e['sequence'], available
        seen[e['id']] = digest
        audit = {k: e[k] for k in ('id', 'sequence', 'answer_id', 'event_at', 'known_at')}
        audit['effect'] = 'NO_FACT_CHANGE'
        state['audit'].append(audit)
        if any(e[k] != state[k] for k in ('episode_id', 'goal_id', 'recipient_id')):
            audit['effect'] = 'FOREIGN_SCOPE_IGNORED'
            continue
        user_event = e['kind'] != 'RESULT_OBSERVED'
        if user_event and e['actor_id'] != state['recipient_id']:
            audit['effect'] = 'OTHER_ACTOR_IGNORED'
            continue
        if e['answer_id'] not in {a['answer_id'] for a in state['history']}:
            audit['effect'] = 'UNKNOWN_ANSWER_IGNORED'
            continue
        # A recipient can stop this episode even while replying to an older answer.
        if e['kind'] in {'STOPPED', 'DECLINED'}:
            state['lifecycle'] = e['kind']
            audit['effect'] = 'INITIATIVE_STOPPED'
            continue
        if state['lifecycle'] != 'OPEN':
            audit['effect'] = 'EPISODE_CLOSED_IGNORED'
            continue
        current = state['history'][-1]
        if e['answer_id'] != current['answer_id']:
            audit['effect'] = 'STALE_ANSWER_IGNORED'
            continue
        kind = e['kind']
        if kind == 'PREFERENCE_FEEDBACK':
            if payload['detail'] not in {'compact', 'full'}:
                raise ValueError('detail must be compact or full')
            if payload['detail'] != current['detail']:
                _revise(state, e, 'presentation only', detail=payload['detail'])
                audit['effect'] = 'PRESENTATION_REVISED'
        elif kind == 'CLARIFICATION':
            fields = payload['fields']
            if not isinstance(fields, dict) or any(
                    k in CONTEXT_KEYS or not isinstance(k, str) or not k.strip()
                    or not isinstance(v, str) or not v.strip() for k, v in fields.items()):
                raise ValueError('clarifications must be named non-context string fields')
            state['known_fields'].update(fields)
            audit['effect'] = 'CONSTRAINTS_UPDATED'
        elif kind == 'CONTEXT_CORRECTION':
            target = context(payload['context'])
            if target != current['context']:
                p = {'claim_id': current['proof']['claim_id'], 'verdict': 'UNKNOWN',
                     'support': [], 'counterevidence': [],
                     'limits': ['No evaluated evidence for this target context.',
                                'Evidence support never authorizes external action.']}
                _revise(state, e, 'target changed; previous evidence does not transfer',
                        context=target, proof=p, pending_review=True)
                audit['effect'] = 'TARGET_REQUIRES_RECHECK'
        elif kind == 'EVIDENCE_CHALLENGE':
            r = _receipt(registry, e, state, 'evidence')
            if r is None:
                _revise(state, e, 'challenge pending evaluation; previous proof preserved', pending_review=True)
                audit['effect'] = 'RECHECK_REQUIRED_NO_ACCEPTED_RECEIPT'
            else:
                p = proof(r['proof'])
                if p['claim_id'] != current['proof']['claim_id']:
                    raise ValueError('receipt proof claim does not match receipt binding')
                _revise(state, e, f"evaluated receipt: {payload['receipt_id']}", proof=p, pending_review=False)
                audit['effect'] = 'FACTS_REVISED_FROM_RECEIPT'
        elif kind == 'RESULT_REPORTED':
            if not isinstance(payload['result'], str) or not payload['result'].strip():
                raise ValueError('a reported result must be explicit text')
            state['outcomes'].setdefault(e['answer_id'], []).append({
                'basis': 'USER_REPORTED', 'result': payload['result'], 'event_id': e['id']})
            audit['effect'] = 'REPORT_RECORDED_NOT_VERIFIED'
        elif kind == 'RESULT_OBSERVED':
            r = _receipt(registry, e, state, 'outcome')
            if r is None or r.get('observer_id') != e['actor_id']:
                audit['effect'] = 'OBSERVATION_NOT_ACCEPTED'
            elif not isinstance(r.get('result'), str) or not r['result'].strip():
                raise ValueError('outcome receipt lacks result')
            else:
                state['outcomes'].setdefault(e['answer_id'], []).append({
                    'basis': 'OBSERVED', 'result': r['result'], 'event_id': e['id'],
                    'receipt_id': payload['receipt_id'], 'independence': 'NOT_ESTABLISHED'})
                audit['effect'] = 'OBSERVATION_RECORDED'
        elif kind == 'DISAGREEMENT':
            audit['effect'] = 'EXAMINE_DISAGREEMENT_NOT_AUTOMATIC_REVERSAL'
    return state


def card(state: dict, required_fields: tuple[str, ...] = ()) -> dict:
    """A structured proof card; never truncate critical evidence to a word budget."""
    a = state['history'][-1]
    known = {**state['known_fields'], **a['context']}
    missing = [key for key in required_fields if key not in known]
    outcome = copy.deepcopy(state['outcomes'].get(a['answer_id'], []))
    return {'answer_id': a['answer_id'], 'detail': a['detail'],
            'context': copy.deepcopy(a['context']), 'proof': copy.deepcopy(a['proof']),
            'pending_review': a['pending_review'],
            'outcome_observations': outcome, 'outcome_basis': 'RECORDED' if outcome else 'NOT_OBSERVED',
            'question': (f"Please specify {missing[0]}." if missing and state['lifecycle'] == 'OPEN' else None),
            'reply_required': False, 'automatic_follow_up': False,
            'external_action_authorized': False, 'lifecycle': state['lifecycle']}
