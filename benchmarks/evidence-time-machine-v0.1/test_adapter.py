"""Open development tests, not independent episodes or LLM evaluations."""
import copy
from datetime import timedelta
import json
from pathlib import Path
import unittest
from unittest.mock import patch
import adapter as a

FIXTURE=json.loads((Path(__file__).with_name('source_observation.json')).read_text())

class AdapterTests(unittest.TestCase):
    def setUp(self): self.s=copy.deepcopy(FIXTURE)
    def row(self): return self.s['check_runs'][0]
    def verdict(self,**kw): return a.replay(self.s,a.checkpoint(self.s,**kw))
    def rejected(self):
        with self.assertRaises((ValueError,KeyError)): a.normalize(self.s)
    def test_01_real_exact_commit(self): self.assertEqual(self.verdict()['status'],'SUPPORTED')
    def test_02_real_other_commit(self): self.assertEqual(self.verdict(sha=a.MERGE_SHA)['status'],'UNKNOWN')
    def test_03_real_before_observation(self):
        t=(a.policy.timestamp(self.s['recorded_at'])-timedelta(seconds=1)).isoformat()
        self.assertEqual(self.verdict(known_at=t)['status'],'UNKNOWN')
    def test_04_real_before_completion(self):
        self.assertEqual(self.verdict(valid_at='2026-09-05T10:26:17Z')['status'],'UNKNOWN')
    def test_05_omitted_run_is_unknown_not_false(self):
        self.assertEqual(self.verdict(check_id=101291849043)['status'],'UNKNOWN')
    def test_06_never_action_permission(self): self.assertIs(self.verdict()['action_authorized'],False)
    def test_07_exact_one_declared_origin(self): self.assertEqual(self.verdict()['declared_origin_count'],1)
    def test_08_event_time_not_knowledge_time(self):
        row=a.normalize(self.s)['records'][0]
        self.assertNotEqual(row['known_at'],row['event_at'])
    def test_09_unaccepted_app(self):
        self.row()['app']['id']=999
        self.assertEqual(self.verdict()['status'],'UNKNOWN')
    def test_10_failure(self):
        self.row()['conclusion']='failure'
        self.assertEqual(self.verdict()['status'],'REFUTED')
    def test_11_skipped_is_not_pass(self):
        self.row()['conclusion']='skipped'
        self.assertEqual(self.verdict()['status'],'UNKNOWN')
    def test_12_cancelled_is_not_negative_evidence(self):
        self.row()['conclusion']='cancelled'
        self.assertEqual(self.verdict()['status'],'UNKNOWN')
    def test_13_pending(self):
        self.row().update(status='in_progress',conclusion=None,completed_at=None)
        self.assertEqual(self.verdict()['status'],'UNKNOWN')
    def test_14_duplicate_id(self):
        self.s['check_runs']*=2; self.rejected()
    def test_15_future_completion(self):
        self.row()['completed_at']='2027-01-01T00:00:00Z'; self.rejected()
    def test_16_reverse_chronology(self):
        self.row()['completed_at']='2026-09-05T10:26:13Z'; self.rejected()
    def test_17_naive_timestamp(self):
        self.s['recorded_at']='2026-09-05T10:41:26'; self.rejected()
    def test_18_short_commit(self): self.row()['head_sha']='0bf8f40'; self.rejected()
    def test_19_bad_check_id(self): self.row()['id']=True; self.rejected()
    def test_20_missing_app(self): self.row()['app']={}; self.rejected()
    def test_21_cross_repo_url(self):
        self.row()['html_url']='https://github.com/other/repo/actions/runs/1'; self.rejected()
    def test_22_unknown_schema(self): self.s['schema']='wrong'; self.rejected()
    def test_23_pending_with_final_result(self): self.row()['status']='queued'; self.rejected()
    def test_24_final_without_completion(self): self.row()['completed_at']=None; self.rejected()
    def test_25_empty_observation(self):
        self.s['check_runs']=[]
        self.assertEqual(self.verdict()['status'],'UNKNOWN')
    def test_26_wrong_query_repo(self):
        self.assertEqual(self.verdict(repository='example/other')['status'],'UNKNOWN')
    def test_27_no_input_mutation(self):
        before=copy.deepcopy(self.s); self.verdict(); self.assertEqual(self.s,before)
    def test_28_capture_mock_get_only(self):
        class Response:
            def __enter__(self): return self
            def __exit__(self,*args): return False
            def read(self,n): return json.dumps({'total_count':1,'check_runs':FIXTURE['check_runs']}).encode()
        class Opener:
            def open(self,req,timeout):
                assert req.get_method()=='GET'
                assert req.full_url.startswith('https://api.github.com/repos/safal207/RESONANCE/commits/')
                return Response()
        with patch.object(a,'build_opener',return_value=Opener()):
            result=a.capture_live(a.REPO,a.SOURCE_SHA,a.CHECK_ID)
            self.assertEqual(result['check_runs'][0]['id'],a.CHECK_ID)
            self.assertNotIn('Authorization',json.dumps(result))
    def test_29_capture_refuses_invalid_repo(self):
        with self.assertRaises(ValueError): a.capture_live('bad/repo/extra',a.SOURCE_SHA)
    def test_30_empty_name(self): self.row()['name']=''; self.rejected()
    def test_31_wrong_source_url_scheme(self):
        self.row()['html_url']='http://github.com/safal207/RESONANCE/x'; self.rejected()
    def test_32_unknown_final_conclusion(self): self.row()['conclusion']='made-up'; self.rejected()

if __name__=='__main__': unittest.main(verbosity=2)
