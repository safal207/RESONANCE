"""Offline temporal/context evidence fixtures. No LLM, network or action executor.

SUPPORTED means supported under the declared toy evidence policy, not authenticated
truth. Known-time release and explicit relations prevent retrospective leakage.
"""
from __future__ import annotations

import argparse
import copy
from datetime import datetime
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
STATUSES = {'SUPPORTED', 'REFUTED', 'CONTESTED', 'UNKNOWN',
            'A_BEFORE_B', 'B_BEFORE_A', 'ORDER_CONFLICT'}
CONTEXT_FIELDS = ('system', 'environment', 'version', 'region')


def timestamp(value: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError('timestamp must be a timezone-aware ISO string')
    try:
        result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError as exc:
        raise ValueError(f'invalid timestamp: {value!r}') from exc
    if result.utcoffset() is None:
        raise ValueError('timestamp must include timezone')
    return result


def canonical_hash(value: Any) -> str:
    """Integrity fingerprint only; not a signature, source attestation or proof."""
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True,
                     separators=(',', ':'), allow_nan=False).encode('utf-8')
    return hashlib.sha256(raw).hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    for n, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
        if line.strip():
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f'{path}:{n}: invalid JSON') from exc
            if not isinstance(row, dict):
                raise ValueError(f'{path}:{n}: expected object')
            rows.append(row)
    return rows


def validate_episode(episode: dict[str, Any]) -> None:
    for key in ('episode_id', 'task'):
        if not isinstance(episode.get(key), str) or not episode[key].strip():
            raise ValueError(f'missing {key}')
    policy = episode.get('policy', {})
    for key in ('accepted_sources', 'retraction_authorities'):
        if not isinstance(policy.get(key), list) or not all(
                isinstance(x, str) and x for x in policy[key]):
            raise ValueError(f'invalid policy {key}')
    records, checkpoints = episode.get('records'), episode.get('checkpoints')
    if not isinstance(records, list) or not isinstance(checkpoints, list) or not checkpoints:
        raise ValueError('records and nonempty checkpoints required')
    if any(k in episode for k in ('oracle', 'expected_status', 'answers')):
        raise ValueError('oracle must be separate')
    ids: dict[str, dict[str, Any]] = {}
    for r in records:
        for key in ('id', 'source_id'):
            if not isinstance(r.get(key), str) or not r[key].strip():
                raise ValueError(f'missing record {key}')
        if r['id'] in ids:
            raise ValueError('duplicate record id')
        ids[r['id']] = r
        if r.get('kind') not in ('assertion', 'retraction', 'event', 'happens_before'):
            raise ValueError('invalid record kind')
        timestamp(r['known_at']); timestamp(r['event_at']); timestamp(r['valid_from'])
        if r.get('valid_until') is not None and timestamp(r['valid_until']) <= timestamp(r['valid_from']):
            raise ValueError('invalid half-open validity interval')
        if not all(isinstance(r.get('context', {}).get(k), str) and r['context'][k]
                   for k in CONTEXT_FIELDS):
            raise ValueError('explicit context required')
        if not isinstance(r.get('derived_from'), list) or not all(
                isinstance(x, str) and x for x in r['derived_from']):
            raise ValueError('invalid derivation links')
        if r.get('origin_id') is not None and not isinstance(r['origin_id'], str):
            raise ValueError('origin_id must be string or null')
        if r['kind'] == 'assertion' and (type(r.get('value')) is not bool or
                not isinstance(r.get('claim'), str) or not r['claim']):
            raise ValueError('assertion needs claim and boolean value')
    for r in records:
        refs = list(r['derived_from'])
        if r['kind'] == 'retraction': refs.append(r.get('target_id'))
        if r['kind'] == 'happens_before': refs.extend([r.get('before_id'), r.get('after_id')])
        for ref in refs:
            if ref not in ids: raise ValueError('dangling evidence reference')
            if timestamp(ids[ref]['known_at']) > timestamp(r['known_at']):
                raise ValueError('record references future unseen evidence')
        if r['kind'] == 'retraction' and ids[r['target_id']]['kind'] == 'retraction':
            raise ValueError('retraction-of-retraction unsupported: issue fresh evidence')
        if r['kind'] == 'happens_before':
            if r['before_id'] == r['after_id']:
                raise ValueError('self happens-before edge')
            if any(ids[x]['kind'] != 'event' for x in (r['before_id'], r['after_id'])):
                raise ValueError('happens-before endpoints must be events')
    done, visiting = set(), set()
    def visit(rid: str) -> None:
        if rid in visiting: raise ValueError('cyclic evidence derivation')
        if rid in done: return
        visiting.add(rid)
        for parent in ids[rid]['derived_from']: visit(parent)
        visiting.remove(rid); done.add(rid)
    for rid in ids: visit(rid)
    cp_ids = set()
    for cp in checkpoints:
        if not cp.get('id') or cp['id'] in cp_ids: raise ValueError('duplicate/missing checkpoint id')
        cp_ids.add(cp['id'])
        timestamp(cp['known_at']); timestamp(cp['valid_at'])
        if cp.get('query_type') not in ('claim', 'order'): raise ValueError('invalid query type')
        if not all(isinstance(cp.get('context', {}).get(k), str) and cp['context'][k]
                   for k in CONTEXT_FIELDS): raise ValueError('checkpoint context required')
        if cp['query_type'] == 'claim' and not cp.get('claim'): raise ValueError('claim required')
        if cp['query_type'] == 'order' and (not cp.get('a_id') or not cp.get('b_id')):
            raise ValueError('event ids required')
        if any(k in cp for k in ('expected_status', 'oracle', 'answer')):
            raise ValueError('oracle leaked into checkpoint')


def release(episode: dict[str, Any], checkpoint: dict[str, Any],
            representation: str = 'flat') -> dict[str, Any]:
    """Only evidence known by the cutoff. Never send full episode to a model.

    Both representations contain identical record bodies, validity and provenance.
    Raw irrelevant contexts remain visible to test the model's context selection.
    Graph edges are syntax-only extraction; no reference verdict is disclosed.
    """
    if representation not in ('flat', 'graph'):
        raise ValueError('representation must be flat or graph')
    cutoff = timestamp(checkpoint['known_at'])
    records = sorted((copy.deepcopy(r) for r in episode['records']
                      if timestamp(r['known_at']) <= cutoff), key=lambda r: r['id'])
    common = {'episode_id': episode['episode_id'], 'task': episode['task'],
              'policy': copy.deepcopy(episode['policy']), 'query': copy.deepcopy(checkpoint)}
    if representation == 'flat':
        return {**common, 'records': records}
    edges = []
    for r in records:
        for parent in r['derived_from']:
            edges.append({'from': r['id'], 'to': parent, 'type': 'derived_from', 'record_id': r['id']})
        if r['kind'] == 'retraction':
            edges.append({'from': r['id'], 'to': r['target_id'], 'type': 'retracts', 'record_id': r['id']})
        if r['kind'] == 'happens_before':
            edges.append({'from': r['before_id'], 'to': r['after_id'],
                          'type': 'happens_before', 'record_id': r['id']})
    return {**common, 'graph': {'nodes': records, 'edges': edges}}


def reference_evaluate(episode: dict[str, Any], cp: dict[str, Any]) -> dict[str, Any]:
    """Toy policy oracle; explicit facts only, no NLP, causal discovery or execution."""
    available = release(episode, cp)['records']
    ids = {r['id']: r for r in available}
    accepted = set(episode['policy']['accepted_sources'])
    authorities = set(episode['policy']['retraction_authorities'])
    valid_at = timestamp(cp['valid_at'])
    def timely(r: dict[str, Any]) -> bool:
        return (timestamp(r['valid_from']) <= valid_at and
                (r.get('valid_until') is None or valid_at < timestamp(r['valid_until'])))
    revoked = set()
    for r in available:
        if r['kind'] != 'retraction' or not timely(r): continue
        target = ids.get(r['target_id'])
        if target and r['source_id'] in accepted and r['context'] == target['context'] and (
                r['source_id'] == target['source_id'] or r['source_id'] in authorities):
            revoked.add(target['id'])
    # Revoked/invalid dependency invalidates descendants under this declared toy policy.
    memo: dict[str, bool] = {}
    def usable(rid: str, visiting: frozenset[str] = frozenset()) -> bool:
        if rid in memo: return memo[rid]
        if rid not in ids or rid in revoked or rid in visiting: return False
        r = ids[rid]
        value = (r['kind'] != 'retraction' and r['source_id'] in accepted and timely(r)
                 and all(usable(parent, visiting | {rid}) for parent in r['derived_from']))
        memo[rid] = value
        return value
    eligible = [r for r in available if usable(r['id']) and r['context'] == cp['context']]
    support, refute = [], []
    if cp['query_type'] == 'claim':
        evidence = [r for r in eligible if r['kind'] == 'assertion' and r['claim'] == cp['claim']]
        support = sorted(r['id'] for r in evidence if r['value'])
        refute = sorted(r['id'] for r in evidence if not r['value'])
        status = ('CONTESTED' if support and refute else 'SUPPORTED' if support
                  else 'REFUTED' if refute else 'UNKNOWN')
        roots = {r['origin_id'] for r in evidence if r.get('origin_id')}
        unknown_origins = sum(not r.get('origin_id') for r in evidence)
    else:
        # Wall-clock time never synthesizes an ordering edge.
        event_ids = {r['id'] for r in eligible if r['kind'] == 'event'}
        adjacency: dict[str, list[tuple[str, str]]] = {}
        for r in eligible:
            if r['kind'] == 'happens_before' and r['before_id'] in event_ids and r['after_id'] in event_ids:
                adjacency.setdefault(r['before_id'], []).append((r['after_id'], r['id']))
        def path(a: str, b: str) -> list[str]:
            queue = [(a, [])]; seen = set()
            while queue:
                node, links = queue.pop(0)
                if node in seen: continue
                seen.add(node)
                if node == b and links: return links
                queue.extend((n, links + [e]) for n, e in adjacency.get(node, []))
            return []
        support = path(cp['a_id'], cp['b_id'])
        refute = path(cp['b_id'], cp['a_id'])
        status = ('ORDER_CONFLICT' if support and refute else 'A_BEFORE_B' if support
                  else 'B_BEFORE_A' if refute else 'UNKNOWN')
        roots, unknown_origins = set(), 0
    return {'episode_id': episode['episode_id'], 'checkpoint_id': cp['id'],
            'status': status, 'support_ids': support, 'refute_ids': refute,
            'declared_origin_count': len(roots), 'unknown_origin_records': unknown_origins,
            'known_at': cp['known_at'], 'valid_at': cp['valid_at'],
            'scope': copy.deepcopy(cp['context']),
            'snapshot_sha256': canonical_hash(release(episode, cp)),
            'boundary': 'toy_policy_not_authentication_not_causality_not_action_authorization'}


def validate_answer(answer: dict[str, Any], payload: dict[str, Any]) -> None:
    """Structural/citation-existence checks only, not semantic entailment."""
    if answer.get('status') not in STATUSES: raise ValueError('invalid answer status')
    ids = {r['id'] for r in (payload['records'] if 'records' in payload else payload['graph']['nodes'])}
    refs = answer.get('evidence_ids')
    if not isinstance(refs, list) or not all(isinstance(r, str) and r in ids for r in refs):
        raise ValueError('missing, unavailable or invented citation')
    if answer.get('known_at') != payload['query']['known_at'] or answer.get('valid_at') != payload['query']['valid_at']:
        raise ValueError('answer cutoff mismatch')
    if answer.get('context') != payload['query']['context']: raise ValueError('answer context mismatch')


def with_distractors(episode: dict[str, Any], count: int) -> dict[str, Any]:
    """Synthetic load only, NOT additional independent experimental evidence."""
    if type(count) is not int or count < 0: raise ValueError('nonnegative integer count required')
    result = copy.deepcopy(episode)
    earliest = min((cp['known_at'] for cp in episode['checkpoints']), key=timestamp)
    for i in range(count):
        rid = f'distractor-{i:06d}'
        if any(r['id'] == rid for r in episode['records']): raise ValueError('distractor id collision')
        result['records'].append({'id': rid, 'kind': 'assertion', 'source_id': 'fixture-A',
            'origin_id': f'synthetic-load-{i}', 'derived_from': [], 'event_at': earliest,
            'known_at': earliest, 'valid_from': earliest, 'valid_until': None,
            'context': {'system': 'unrelated-service', 'environment': 'dev', 'version': 'v0', 'region': 'test'},
            'claim': f'unrelated_metric_{i}', 'value': bool(i % 2)})
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['reference', 'prepare'])
    parser.add_argument('--out', type=Path, default=ROOT / 'temporal/reports')
    args = parser.parse_args()
    try:
        episodes = read_jsonl(ROOT / 'temporal/data/episodes.jsonl')
        for e in episodes: validate_episode(e)
        args.out.mkdir(parents=True, exist_ok=True)
        if args.command == 'reference':
            rows = [reference_evaluate(e, cp) for e in episodes for cp in e['checkpoints']]
            path = args.out/'reference_checkpoints.jsonl'
            path.write_text(''.join(json.dumps(r, ensure_ascii=False)+'\n' for r in rows), encoding='utf-8')
            print(json.dumps({'kind':'DETERMINISTIC_SYNTHETIC_REFERENCE', 'episodes':len(episodes),
                'checkpoints':len(rows), 'llm_runs':0, 'path':str(path)}, ensure_ascii=False))
        else:
            index = []
            for e in episodes:
                for cp in e['checkpoints']:
                    for fmt in ('flat', 'graph'):
                        name = f"{e['episode_id']}-{cp['id']}-{fmt}.json"
                        payload = release(e, cp, fmt)
                        (args.out/name).write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n', encoding='utf-8')
                        index.append({'episode_id':e['episode_id'], 'checkpoint_id':cp['id'],
                                      'format':fmt,'path':name,'sha256':canonical_hash(payload)})
            (args.out/'payload_index.json').write_text(json.dumps(index,indent=2)+'\n', encoding='utf-8')
            print(json.dumps({'kind':'PAYLOADS_ONLY', 'payloads':len(index), 'llm_runs':0}))
    except (ValueError, KeyError, OSError) as exc:
        parser.error(str(exc))

if __name__ == '__main__':
    main()
