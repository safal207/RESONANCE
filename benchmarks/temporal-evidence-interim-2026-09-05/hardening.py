"""Experimental acyclic evidence policy; no authentication or action permission.

A conditional withdrawal must have live premises, just like a derived assertion.
Unconditional administrative withdrawals retain their existing semantics.
Circular justification/invalidation is rejected, not solved by list order.
"""
from __future__ import annotations
import copy
from graphlib import CycleError, TopologicalSorter
import baseline as tb


def evaluate(episode: dict, cp: dict) -> dict:
    available = tb.release(episode, cp)['records']
    ids = {r['id']: r for r in available}
    accepted = set(episode['policy']['accepted_sources'])
    authorities = set(episode['policy']['retraction_authorities'])
    at = tb.timestamp(cp['valid_at'])

    def timely(r: dict) -> bool:
        return tb.timestamp(r['valid_from']) <= at and (
            r.get('valid_until') is None or at < tb.timestamp(r['valid_until']))

    candidates = {}
    for r in available:
        if r['kind'] != 'retraction' or r['source_id'] not in accepted or not timely(r):
            continue
        target = ids.get(r['target_id'])
        if target and target['context'] == r['context'] and (
                r['source_id'] == target['source_id'] or r['source_id'] in authorities):
            candidates[r['id']] = target['id']
    incoming = {rid: set() for rid in ids}
    for rid, target in candidates.items():
        incoming[target].add(rid)
    dependencies = {rid: set(r['derived_from']) | incoming[rid] for rid, r in ids.items()}
    # Retractions are control records, not positive derivation premises in this policy.
    if any(ids.get(parent, {}).get('kind') == 'retraction'
           for r in available for parent in r['derived_from']):
        raise ValueError('derivation from a retraction is unsupported')
    try:
        order = tuple(TopologicalSorter(dependencies).static_order())
    except CycleError as exc:
        raise ValueError('cyclic justification/invalidation: no grounded verdict') from exc
    active = {}
    for rid in order:
        r = ids.get(rid)
        active[rid] = bool(r and r['source_id'] in accepted and timely(r)
            and (r['kind'] != 'retraction' or rid in candidates)
            and all(active.get(parent, False) for parent in r['derived_from'])
            and not any(active.get(x, False) for x in incoming[rid]))
    filtered = copy.deepcopy(episode)
    filtered['records'] = [copy.deepcopy(r) for r in available
                           if active[r['id']] and r['kind'] != 'retraction']
    result = tb.reference_evaluate(filtered, cp)
    # Keep the fingerprint of the complete available input, not our filtered view.
    result['snapshot_sha256'] = tb.canonical_hash(tb.release(episode, cp))
    return result
