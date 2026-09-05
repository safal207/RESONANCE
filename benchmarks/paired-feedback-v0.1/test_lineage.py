"""New open boundary cases: presentation is not a factual revision.

These tests overlap the earlier fixtures. They are not LLM efficacy trials.
"""
import copy
import unittest

from paired import card
from test_paired import SCOPE, T0, T1, T2, T3, event, receipt, run


def later(kind, payload=None, n=2, **kw):
    return event(kind, payload, id=f'e{n}', sequence=n,
                 event_at=T2 if n == 2 else T3,
                 known_at=T2 if n == 2 else T3, **kw)


def compact():
    return event('PREFERENCE_FEEDBACK', {'detail': 'compact'})


class FactualLineageContracts(unittest.TestCase):
    def test_counterevidence_survives_presentation_revision(self):
        s = run([compact(), later('EVIDENCE_CHALLENGE', {'receipt_id': 'r'})], {'r': receipt(known_at=T2)})
        self.assertEqual(card(s)['proof']['verdict'], 'REFUTED')
        self.assertEqual([a['fact_revision'] for a in s['history']], ['a1', 'a1', 'a3'])
        self.assertEqual(s['history'][0]['proof']['verdict'], 'SUPPORTED')

    def test_recorded_result_survives_compaction_with_original_answer(self):
        s = run([event('RESULT_REPORTED', {'result': 'done'}), later('PREFERENCE_FEEDBACK', {'detail': 'compact'})])
        obs = card(s)['related_outcome_observations']
        self.assertEqual(len(obs), 1)
        self.assertEqual(obs[0]['answer_id'], 'a1')
        self.assertEqual(obs[0]['basis'], 'USER_REPORTED')
        self.assertNotIn('a2', s['outcomes'])
        self.assertEqual(card(s)['outcome_basis'], 'NOT_OBSERVED')
        self.assertEqual(card(s)['related_outcome_basis'], 'RECORDED_FOR_EARLIER_ANSWER')

    def test_late_report_survives_compaction(self):
        s = run([compact(), later('RESULT_REPORTED', {'result': 'done'})])
        self.assertEqual(card(s)['related_outcome_observations'][0]['answer_id'], 'a1')

    def test_late_observation_survives_compaction(self):
        r = receipt(purpose='outcome', observer_id='host', result='check completed', known_at=T2)
        s = run([compact(), later('RESULT_OBSERVED', {'receipt_id': 'r'}, actor_id='host')], {'r': r})
        obs = card(s)['related_outcome_observations'][0]
        self.assertEqual((obs['answer_id'], obs['basis'], obs['independence']), ('a1', 'OBSERVED', 'NOT_ESTABLISHED'))

    def test_observed_result_survives_presentation_revision(self):
        r = receipt(purpose='outcome', observer_id='host', result='check completed')
        s = run([event('RESULT_OBSERVED', {'receipt_id': 'r'}, actor_id='host'), later('PREFERENCE_FEEDBACK', {'detail': 'compact'})], {'r': r})
        self.assertEqual(card(s)['related_outcome_observations'][0]['receipt_id'], 'r')

    def test_pending_review_does_not_orphan_later_receipt(self):
        s = run([event('EVIDENCE_CHALLENGE', {'receipt_id': 'missing'}), later('EVIDENCE_CHALLENGE', {'receipt_id': 'r'})], {'r': receipt(known_at=T2)})
        self.assertEqual(card(s)['proof']['verdict'], 'REFUTED')
        self.assertFalse(card(s)['pending_review'])

    def test_evidence_bound_to_intermediate_presentation_is_accepted(self):
        es = [compact(), later('PREFERENCE_FEEDBACK', {'detail': 'full'}, answer_id='a2'), later('EVIDENCE_CHALLENGE', {'receipt_id': 'r'}, n=3, answer_id='a2')]
        s = run(es, {'r': receipt(answer_id='a2', known_at=T3)})
        self.assertEqual(card(s)['proof']['verdict'], 'REFUTED')

    def test_future_receipt_still_cannot_change_history(self):
        s = run([compact(), later('EVIDENCE_CHALLENGE', {'receipt_id': 'r'})], {'r': receipt(known_at=T3)}, as_of=T2)
        self.assertEqual(card(s)['proof']['verdict'], 'SUPPORTED')
        self.assertTrue(card(s)['pending_review'])

    def test_wrong_original_answer_binding_rejected(self):
        s = run([compact(), later('EVIDENCE_CHALLENGE', {'receipt_id': 'r'})], {'r': receipt(answer_id='a2', known_at=T2)})
        self.assertEqual(card(s)['proof']['verdict'], 'SUPPORTED')
        self.assertTrue(card(s)['pending_review'])

    def test_changed_context_rejects_late_counterevidence(self):
        for key in SCOPE:
            with self.subTest(key=key):
                s = run([event('CONTEXT_CORRECTION', {'context': dict(SCOPE, **{key: 'other'})}), later('EVIDENCE_CHALLENGE', {'receipt_id': 'r'})], {'r': receipt(known_at=T2)})
                self.assertEqual(card(s)['proof']['verdict'], 'UNKNOWN')
                self.assertEqual(s['audit'][-1]['effect'], 'STALE_ANSWER_IGNORED')

    def test_context_roundtrip_does_not_resurrect_old_receipt(self):
        es = [event('CONTEXT_CORRECTION', {'context': dict(SCOPE, version='v2')}), later('CONTEXT_CORRECTION', {'context': SCOPE}, answer_id='a2'), later('EVIDENCE_CHALLENGE', {'receipt_id': 'r'}, n=3)]
        s = run(es, {'r': receipt(known_at=T3)})
        self.assertEqual(card(s)['proof']['verdict'], 'UNKNOWN')
        self.assertEqual(card(s)['fact_revision'], 'a3')

    def test_new_evaluated_proof_rejects_old_receipt_even_same_verdict(self):
        first = receipt(); first['proof'] = copy.deepcopy(run()['history'][0]['proof'])
        s = run([event('EVIDENCE_CHALLENGE', {'receipt_id': 'first'}), later('EVIDENCE_CHALLENGE', {'receipt_id': 'old'})], {'first': first, 'old': receipt(known_at=T2)})
        self.assertEqual(card(s)['proof']['verdict'], 'SUPPORTED')
        self.assertEqual(s['audit'][-1]['effect'], 'STALE_ANSWER_IGNORED')

    def test_outcome_not_transferred_to_new_context(self):
        s = run([event('RESULT_REPORTED', {'result': 'done'}), later('CONTEXT_CORRECTION', {'context': dict(SCOPE, version='v2')})])
        self.assertEqual(card(s)['outcome_basis'], 'NOT_OBSERVED')
        self.assertEqual(len(s['outcomes']['a1']), 1)

    def test_outcome_not_transferred_to_new_fact_revision(self):
        s = run([event('RESULT_REPORTED', {'result': 'done'}), later('EVIDENCE_CHALLENGE', {'receipt_id': 'r'})], {'r': receipt(known_at=T2)})
        self.assertEqual(card(s)['outcome_basis'], 'NOT_OBSERVED')
        self.assertEqual(len(s['outcomes']['a1']), 1)

    def test_late_report_after_context_change_ignored(self):
        s = run([event('CONTEXT_CORRECTION', {'context': dict(SCOPE, version='v2')}), later('RESULT_REPORTED', {'result': 'done'})])
        self.assertEqual(card(s)['outcome_basis'], 'NOT_OBSERVED')

    def test_presentation_does_not_relax_scope_bindings(self):
        for field, value in [('episode_id', 'other'), ('goal_id', 'other'), ('recipient_id', 'other'), ('claim_id', 'other'), ('query_time', T1), ('context', dict(SCOPE, version='v2')), ('accepted', False)]:
            with self.subTest(field=field):
                s = run([compact(), later('EVIDENCE_CHALLENGE', {'receipt_id': 'r'})], {'r': receipt(known_at=T2, **{field: value})})
                self.assertEqual(card(s)['proof']['verdict'], 'SUPPORTED')

    def test_stopped_episode_does_not_apply_late_receipt(self):
        s = run([compact(), later('STOPPED'), later('EVIDENCE_CHALLENGE', {'receipt_id': 'r'}, n=3)], {'r': receipt(known_at=T3)})
        self.assertEqual(card(s)['proof']['verdict'], 'SUPPORTED')
        self.assertEqual(card(s)['lifecycle'], 'STOPPED')

    def test_duplicate_late_receipt_event_is_idempotent(self):
        e = later('EVIDENCE_CHALLENGE', {'receipt_id': 'r'})
        rs = {'r': receipt(known_at=T2)}
        self.assertEqual(run([compact(), e, copy.deepcopy(e)], rs), run([compact(), e], rs))

    def test_no_transfer_of_stale_presentation_preferences(self):
        s = run([compact(), later('PREFERENCE_FEEDBACK', {'detail': 'full'})])
        self.assertEqual(card(s)['detail'], 'compact')
        self.assertEqual(s['audit'][-1]['effect'], 'STALE_ANSWER_IGNORED')

    def test_history_is_not_rewritten_and_authority_is_not_granted(self):
        a = run(); s = run([compact(), later('EVIDENCE_CHALLENGE', {'receipt_id': 'r'})], {'r': receipt(known_at=T2)})
        self.assertEqual(s['history'][0], a['history'][0])
        self.assertFalse(card(s)['external_action_authorized'])


if __name__ == '__main__':
    unittest.main()
