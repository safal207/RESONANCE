"""Regression guards for reviewed artifact validation, not model efficacy."""
import ast
import copy
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import build_demo
import integration_check
import verify


class ReviewedValidationContracts(unittest.TestCase):
    def test_invalid_output_suffix_rejected_without_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            target=Path(directory)/'not-created'/'trace.json'
            with self.assertRaises(ValueError):
                build_demo.build(target)
            self.assertFalse(target.parent.exists())

    def test_html_and_json_artifacts_have_distinct_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            target=Path(directory)/'trace.HTML'
            build_demo.build(target)
            self.assertTrue(target.read_text().startswith('<!doctype html>'))
            self.assertTrue(target.with_suffix('.json').read_text().startswith('{'))

    def test_skip_and_expected_failure_not_counted_as_pass(self):
        class Fixture(unittest.TestCase):
            def test_pass(self):
                self.assertTrue(True)
            @unittest.skip('synthetic reporting check')
            def test_skip(self):
                pass
            @unittest.expectedFailure
            def test_expected_failure(self):
                self.fail('synthetic expected failure')
        result=unittest.TextTestRunner(stream=io.StringIO()).run(unittest.defaultTestLoader.loadTestsFromTestCase(Fixture))
        self.assertEqual(verify.test_counts(result), {'unit_tests_run':3, 'unit_tests_passed':1, 'unit_tests_skipped':1, 'unit_tests_expected_failures':1})

    def test_invalid_trace_verdict_fails(self):
        p=build_demo.examples();p['data'][0]['snapshots'][-1]['card']['proof']['verdict']='UNKNOWN'
        with self.assertRaises(AssertionError):
            verify.validate_trace(p)

    def test_invalid_trace_reply_demand_fails(self):
        p=build_demo.examples();p['data'][0]['snapshots'][-1]['card']['reply_required']=True
        with self.assertRaises(AssertionError):
            verify.validate_trace(p)

    def test_invalid_trace_authority_fails(self):
        p=build_demo.examples();p['data'][0]['snapshots'][-1]['card']['external_action_authorized']=True
        with self.assertRaises(AssertionError):
            verify.validate_trace(p)

    def test_bridge_rejects_corrupted_projection(self):
        real=integration_check.card
        def corrupted(state):
            result=copy.deepcopy(real(state));result['external_action_authorized']=True
            return result
        with patch.object(integration_check, 'card', side_effect=corrupted):
            with self.assertRaises(AssertionError):
                integration_check.check()

    def test_runtime_validators_do_not_depend_on_assert(self):
        root=Path(__file__).resolve().parent
        for name in ('integration_check.py','verify.py','lineage_probe.py','prepare_abc.py'):
            with self.subTest(name=name):
                self.assertFalse(any(isinstance(n, ast.Assert) for n in ast.walk(ast.parse((root/name).read_text()))))


if __name__=='__main__':
    unittest.main()
