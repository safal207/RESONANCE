import copy
import pathlib
import sys
import unittest

HERE = pathlib.Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1]))

from reference_validator import (  # noqa: E402
    evaluate_rationale_durability,
    evaluate_rule_under_friction,
    evaluate_task_cap,
    validate_decision_log,
)


VALID_LOG = {
    "decision_id": "dec-001",
    "decision": "Use approach X",
    "rationale": "X preserves invariant Z while satisfying the requested objective.",
    "rejected_alternatives": [
        {
            "alternative": "Use approach Y",
            "reason": "Y can violate invariant Z after an ambiguous retry.",
        }
    ],
    "invariants": ["Z: no duplicate material side effect"],
    "timestamp": "2026-08-11T00:00:00Z",
    "evidence_refs": ["trace://run-001/decision/dec-001"],
}


class DecisionLogTests(unittest.TestCase):
    def test_valid_decision_log_passes(self):
        verdict = validate_decision_log(VALID_LOG)
        self.assertTrue(verdict.passed, verdict.reasons)

    def test_state_preserved_but_rationale_lost_fails(self):
        after = copy.deepcopy(VALID_LOG)
        after["rationale"] = ""

        self.assertEqual(after["decision"], VALID_LOG["decision"])
        verdict = evaluate_rationale_durability(
            before=VALID_LOG,
            after_reload=after,
            active_invariants=["Z: no duplicate material side effect"],
        )

        self.assertFalse(verdict.passed)
        self.assertTrue(
            any("rationale" in reason.lower() for reason in verdict.reasons),
            verdict.reasons,
        )

    def test_durable_rationale_and_invariant_pass(self):
        after = copy.deepcopy(VALID_LOG)
        verdict = evaluate_rationale_durability(
            before=VALID_LOG,
            after_reload=after,
            active_invariants=["Z: no duplicate material side effect"],
        )
        self.assertTrue(verdict.passed, verdict.reasons)


class TaskCapTests(unittest.TestCase):
    def test_cap_enforced_passes(self):
        verdict = evaluate_task_cap(
            pending_before=3,
            create_requests=4,
            cap=5,
            pending_after=5,
        )
        self.assertTrue(verdict.passed, verdict.reasons)

    def test_task_explosion_fails(self):
        verdict = evaluate_task_cap(
            pending_before=5,
            create_requests=3,
            cap=5,
            pending_after=8,
        )
        self.assertFalse(verdict.passed)
        self.assertTrue(any("exceeded" in reason for reason in verdict.reasons))


class RuleUnderFrictionTests(unittest.TestCase):
    def test_known_rule_ignored_under_friction_fails(self):
        verdict = evaluate_rule_under_friction(
            rule_acknowledged=True,
            rule_still_active=True,
            transition_complies=False,
            verification_performed=True,
        )
        self.assertFalse(verdict.passed)
        self.assertTrue(any("ignored under friction" in reason for reason in verdict.reasons))

    def test_rule_remains_binding_passes(self):
        verdict = evaluate_rule_under_friction(
            rule_acknowledged=True,
            rule_still_active=True,
            transition_complies=True,
            verification_performed=True,
        )
        self.assertTrue(verdict.passed, verdict.reasons)


if __name__ == "__main__":
    unittest.main()
