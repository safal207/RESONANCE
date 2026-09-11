"""Open development tests, not held-out tasks or observations of people."""
import copy
import unittest

from paired import card, initial_state, replay

T0 = '2026-09-05T09:00:00Z'
T1 = '2026-09-05T09:01:00Z'
T2 = '2026-09-05T09:02:00Z'
T3 = '2026-09-05T09:03:00Z'
SCOPE = {'system': 'synthetic-ci', 'environment': 'staging', 'version': 'v1', 'region': 'test'}
PROOF = {'claim_id': 'selected-check-passed', 'verdict': 'SUPPORTED',
         'support': ['fixture:check-v1'], 'counterevidence': [],
         'limits': ['One synthetic check, not a production release decision.',
                    'Evidence support never authorizes external action.']}


def start(**kwargs):
    args = dict(episode_id='demo', goal_id='check-target', recipient_id='demo-user',
                target=SCOPE, evaluated_proof=PROOF, known_at=T0, query_time=T0)
    args.update(kwargs)
    return initial_state(**args)


def event(kind, payload=None, **changes):
    e = dict(id='e1', sequence=1, episode_id='demo', goal_id='check-target',
             recipient_id='demo-user', actor_id='demo-user', answer_id='a1',
             event_at=T1, known_at=T1, kind=kind, payload=payload or {})
    e.update(changes)
    return e


def receipt(**changes):
    r = dict(accepted=True, purpose='evidence', context=copy.deepcopy(SCOPE),
             episode_id='demo', goal_id='check-target', recipient_id='demo-user',
             answer_id='a1', claim_id=PROOF['claim_id'], known_at=T1, query_time=T0,
             proof={'claim_id': PROOF['claim_id'], 'verdict': 'REFUTED', 'support': [],
                    'counterevidence': ['fixture:accepted-correction'], 'limits': PROOF['limits'][:]})
    r.update(changes)
    return r


def run(events=(), receipts=None, initial=None, as_of=T3):
    return replay(initial or start(), list(events), as_of=as_of, receipts=receipts)


class PairedContracts(unittest.TestCase):
    def test_01_silence_does_not_create_event_failure_or_followup(self):
        s = run()
        self.assertEqual(s['audit'], [])
        c = card(s)
        self.assertEqual(c['outcome_basis'], 'NOT_OBSERVED')
        self.assertFalse(c['reply_required'] or c['automatic_follow_up'])

    def test_02_thanks_is_not_success(self):
        self.assertEqual(card(run([event('ACK')]))['outcome_basis'], 'NOT_OBSERVED')

    def test_03_compact_preserves_every_critical_field(self):
        s = run([event('PREFERENCE_FEEDBACK', {'detail': 'compact'})])
        self.assertEqual(card(s)['proof'], PROOF)
        self.assertEqual(card(s)['detail'], 'compact')
        self.assertEqual(s['history'][0]['detail'], 'full')

    def test_04_disagreement_is_not_evidence(self):
        s = run([event('DISAGREEMENT')])
        self.assertEqual(card(s)['proof'], PROOF)
        self.assertIn('NOT_AUTOMATIC_REVERSAL', s['audit'][-1]['effect'])

    def test_05_accepted_counterevidence_changes_facts_preserves_history(self):
        s = run([event('EVIDENCE_CHALLENGE', {'receipt_id': 'r1'})], {'r1': receipt()})
        self.assertEqual(card(s)['proof']['verdict'], 'REFUTED')
        self.assertEqual(s['history'][0]['proof'], PROOF)
        self.assertEqual(len(s['history']), 2)

    def test_06_context_change_never_inherits_old_pass(self):
        s = run([event('CONTEXT_CORRECTION', {'context': dict(SCOPE, version='v2')})])
        self.assertEqual(card(s)['proof']['verdict'], 'UNKNOWN')
        self.assertEqual(card(s)['proof']['support'], [])
        self.assertEqual(s['history'][0]['proof']['verdict'], 'SUPPORTED')

    def test_07_known_constraint_not_asked_again(self):
        s = run([event('CLARIFICATION', {'fields': {'artifact': 'report.json'}})])
        self.assertIsNone(card(s, ('artifact', 'version'))['question'])

    def test_08_complete_request_has_no_forced_question(self):
        self.assertIsNone(card(run())['question'])

    def test_09_stop_disables_initiative(self):
        s = run([event('STOPPED')])
        self.assertIsNone(card(s, ('artifact',))['question'])
        self.assertEqual(s['lifecycle'], 'STOPPED')

    def test_10_compact_keeps_visible_conflict(self):
        p = dict(PROOF, verdict='CONFLICTS', counterevidence=['fixture:failed-check'])
        s = run([event('PREFERENCE_FEEDBACK', {'detail': 'compact'})], initial=start(evaluated_proof=p))
        self.assertEqual(card(s)['proof'], p)

    def test_11_stale_feedback_not_applied_to_new_answer(self):
        s = run([event('CONTEXT_CORRECTION', {'context': dict(SCOPE, version='v2')}),
                 event('PREFERENCE_FEEDBACK', {'detail': 'compact'}, id='e2', sequence=2,
                       event_at=T2, known_at=T2)])
        self.assertEqual(card(s)['detail'], 'full')
        self.assertEqual(s['audit'][-1]['effect'], 'STALE_ANSWER_IGNORED')

    def test_12_other_user_report_not_current_user_outcome(self):
        s = run([event('RESULT_REPORTED', {'result': 'done'}, recipient_id='other-user')])
        self.assertEqual(card(s)['outcome_basis'], 'NOT_OBSERVED')

    def test_future_feedback_does_not_change_history(self):
        e = event('CONTEXT_CORRECTION', {'context': dict(SCOPE, version='v2')})
        self.assertEqual(run([e], as_of=T0), run([], as_of=T0))

    def test_exact_duplicate_is_idempotent(self):
        e = event('PREFERENCE_FEEDBACK', {'detail': 'compact'})
        self.assertEqual(run([e, copy.deepcopy(e)]), run([e]))

    def test_changed_duplicate_is_rejected(self):
        with self.assertRaises(ValueError):
            run([event('ACK'), event('DISAGREEMENT')])

    def test_foreign_goal_is_not_applied(self):
        s = run([event('STOPPED', goal_id='different-goal')])
        self.assertEqual(s['lifecycle'], 'OPEN')

    def test_foreign_episode_is_not_applied(self):
        self.assertEqual(run([event('STOPPED', episode_id='other')])['lifecycle'], 'OPEN')

    def test_customer_cannot_replace_recipient(self):
        self.assertEqual(run([event('STOPPED', actor_id='customer')])['lifecycle'], 'OPEN')

    def test_unknown_answer_does_not_change_state(self):
        s = run([event('DISAGREEMENT', answer_id='not-issued')])
        self.assertEqual(s['audit'][-1]['effect'], 'UNKNOWN_ANSWER_IGNORED')

    def test_receipt_other_context_does_not_transfer(self):
        r = receipt(context=dict(SCOPE, region='other-region'))
        s = run([event('EVIDENCE_CHALLENGE', {'receipt_id': 'r1'})], {'r1': r})
        self.assertEqual(card(s)['proof'], PROOF)

    def test_receipt_other_answer_does_not_transfer(self):
        s = run([event('EVIDENCE_CHALLENGE', {'receipt_id': 'r1'})], {'r1': receipt(answer_id='a9')})
        self.assertEqual(card(s)['proof'], PROOF)

    def test_future_receipt_cannot_support_current_revision(self):
        s = run([event('EVIDENCE_CHALLENGE', {'receipt_id': 'r1'})], {'r1': receipt(known_at=T2)})
        self.assertEqual(card(s)['proof'], PROOF)

    def test_string_true_is_not_an_accepted_receipt(self):
        s = run([event('EVIDENCE_CHALLENGE', {'receipt_id': 'r1'})], {'r1': receipt(accepted='true')})
        self.assertEqual(card(s)['proof'], PROOF)

    def test_unaccepted_receipt_does_not_change_fact(self):
        s = run([event('EVIDENCE_CHALLENGE', {'receipt_id': 'r1'})], {'r1': receipt(accepted=False)})
        self.assertEqual(card(s)['proof'], PROOF)

    def test_different_query_time_cannot_be_reused(self):
        s = run([event('EVIDENCE_CHALLENGE', {'receipt_id': 'r1'})], {'r1': receipt(query_time=T2)})
        self.assertEqual(card(s)['proof'], PROOF)

    def test_inline_fact_override_rejected(self):
        with self.assertRaises(ValueError):
            run([event('ACK', {'verdict': 'SUPPORTED'})])

    def test_user_report_is_not_observed_result(self):
        records = card(run([event('RESULT_REPORTED', {'result': 'done'})]))['outcome_observations']
        self.assertEqual(records[0]['basis'], 'USER_REPORTED')

    def test_observation_requires_receipt(self):
        s = run([event('RESULT_OBSERVED', {'receipt_id': 'missing'}, actor_id='host-observer')])
        self.assertEqual(card(s)['outcome_basis'], 'NOT_OBSERVED')

    def test_observed_is_not_independently_verified(self):
        r = receipt(purpose='outcome', observer_id='host-observer', result='fixture execution completed')
        s = run([event('RESULT_OBSERVED', {'receipt_id': 'r1'}, actor_id='host-observer')], {'r1': r})
        record = card(s)['outcome_observations'][0]
        self.assertEqual(record['basis'], 'OBSERVED')
        self.assertEqual(record['independence'], 'NOT_ESTABLISHED')

    def test_observer_identity_must_match_receipt(self):
        r = receipt(purpose='outcome', observer_id='host-observer', result='done')
        s = run([event('RESULT_OBSERVED', {'receipt_id': 'r1'})], {'r1': r})
        self.assertEqual(card(s)['outcome_basis'], 'NOT_OBSERVED')

    def test_no_event_confers_action_authority(self):
        for e, rs in [(event('ACK'), {}), (event('RESULT_REPORTED', {'result': 'deploy now'}), {}),
                      (event('EVIDENCE_CHALLENGE', {'receipt_id': 'r1'}), {'r1': receipt()})]:
            with self.subTest(kind=e['kind']):
                self.assertFalse(card(run([e], rs))['external_action_authorized'])

    def test_decline_is_permitted(self):
        self.assertEqual(run([event('DECLINED')])['lifecycle'], 'DECLINED')

    def test_stale_stop_still_stops_episode(self):
        s = run([event('PREFERENCE_FEEDBACK', {'detail': 'compact'}),
                 event('STOPPED', id='e2', sequence=2, event_at=T2, known_at=T2)])
        self.assertEqual(s['lifecycle'], 'STOPPED')

    def test_feedback_does_not_silently_reopen_episode(self):
        s = run([event('STOPPED'), event('PREFERENCE_FEEDBACK', {'detail': 'compact'},
                                      id='e2', sequence=2, event_at=T2, known_at=T2)])
        self.assertEqual(card(s)['detail'], 'full')
        self.assertEqual(s['audit'][-1]['effect'], 'EPISODE_CLOSED_IGNORED')

    def test_only_one_missing_field_question(self):
        self.assertEqual(card(run(), ('artifact', 'budget'))['question'], 'Please specify artifact.')

    def test_preference_is_not_persistent_profile(self):
        run([event('PREFERENCE_FEEDBACK', {'detail': 'compact'})])
        self.assertEqual(card(run())['detail'], 'full')

    def test_input_and_previous_history_not_mutated(self):
        s = start()
        original = copy.deepcopy(s)
        run([event('PREFERENCE_FEEDBACK', {'detail': 'compact'})], initial=s)
        self.assertEqual(s, original)

    def test_retroactive_event_available_only_when_received(self):
        e = event('ACK', event_at=T0, known_at=T2)
        self.assertEqual(run([e], as_of=T1)['audit'], [])
        self.assertEqual(len(run([e], as_of=T2)['audit']), 1)

    def test_timezone_offsets_compare_as_instants(self):
        e = event('ACK', event_at='2026-09-05T12:01:00+03:00', known_at=T1)
        self.assertEqual(len(run([e])['audit']), 1)

    def test_naive_timestamp_rejected(self):
        with self.assertRaises(ValueError):
            run([event('ACK', known_at='2026-09-05T09:01:00')])

    def test_nonmonotonic_sequence_rejected(self):
        with self.assertRaises(ValueError):
            run([event('ACK'), event('ACK', id='e2', sequence=1, event_at=T2, known_at=T2)])

    def test_nonmonotonic_availability_rejected(self):
        with self.assertRaises(ValueError):
            run([event('ACK', event_at=T2, known_at=T2), event('ACK', id='e2', sequence=2)])

    def test_clock_skew_requires_explicit_normalization(self):
        with self.assertRaises(ValueError):
            run([event('ACK', event_at=T2, known_at=T1)])

    def test_boolean_sequence_rejected(self):
        with self.assertRaises(ValueError):
            run([event('ACK', sequence=True)])

    def test_context_dimensions_cannot_be_silently_dropped(self):
        with self.assertRaises(ValueError):
            run([event('CONTEXT_CORRECTION', {'context': {'version': 'v2'}})])

    def test_context_change_must_not_use_generic_clarification(self):
        with self.assertRaises(ValueError):
            run([event('CLARIFICATION', {'fields': {'version': 'v2'}})])

    def test_missing_receipt_preserves_fact_but_requests_recheck(self):
        s = run([event('EVIDENCE_CHALLENGE', {'receipt_id': 'unknown'})])
        self.assertEqual(card(s)['proof'], PROOF)
        self.assertIn('RECHECK_REQUIRED', s['audit'][-1]['effect'])

    def test_old_outcome_not_assigned_to_new_answer(self):
        s = run([event('RESULT_REPORTED', {'result': 'done'}),
                 event('PREFERENCE_FEEDBACK', {'detail': 'compact'}, id='e2', sequence=2,
                       event_at=T2, known_at=T2)])
        self.assertEqual(card(s)['outcome_basis'], 'NOT_OBSERVED')
        self.assertEqual(s['outcomes']['a1'][0]['basis'], 'USER_REPORTED')

    def test_pending_challenge_is_visible_without_factual_reversal(self):
        s = run([event('EVIDENCE_CHALLENGE', {'receipt_id': 'unknown'})])
        self.assertTrue(card(s)['pending_review'])
        self.assertFalse(s['history'][0]['pending_review'])
        self.assertEqual(card(s)['proof'], PROOF)

    def test_accepted_receipt_clears_pending_review(self):
        s = run([event('EVIDENCE_CHALLENGE', {'receipt_id': 'r1'})], {'r1': receipt()})
        self.assertFalse(card(s)['pending_review'])

    def test_proof_requires_boundary(self):
        with self.assertRaises(ValueError):
            start(evaluated_proof=dict(PROOF, limits=[]))

    def test_claim_binding_inside_receipt_is_checked(self):
        r = receipt()
        r['proof']['claim_id'] = 'unrelated-claim'
        with self.assertRaises(ValueError):
            run([event('EVIDENCE_CHALLENGE', {'receipt_id': 'r1'})], {'r1': r})


if __name__ == '__main__':
    unittest.main(verbosity=2)
