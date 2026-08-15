from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

MODULE_PATH = ROOT / "evaluate_prospective_routing_ab.py"
SPEC = importlib.util.spec_from_file_location("evaluate_prospective_routing_ab", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

evaluate = MODULE.evaluate
RoutingOutcomeError = MODULE.RoutingOutcomeError
FREEZE = ROOT / "examples" / "prospective-routing-ab-2026-08-15.json"
OBSERVATIONS = ROOT / "examples" / "prospective-routing-ab-outcomes-2026-08-15.json"


class ProspectiveRoutingOutcomeTests(unittest.TestCase):
    def inputs(self):
        return (
            json.loads(FREEZE.read_text(encoding="utf-8")),
            json.loads(OBSERVATIONS.read_text(encoding="utf-8")),
        )

    def test_first_pair_has_small_treatment_advantage_and_no_weight_authority(self):
        freeze_payload, observations = self.inputs()
        result = evaluate(freeze_payload, observations)
        self.assertEqual(result["decision"], "PAIRED_OBSERVED")
        self.assertEqual(result["treatment"]["utility"], 0.75)
        self.assertEqual(result["baseline"]["utility"], 0.7)
        self.assertEqual(result["advantage"], 0.05)
        self.assertEqual(result["winner"], "TREATMENT")
        self.assertEqual(result["calibration_confidence"], "INSUFFICIENT")
        self.assertFalse(result["weight_update_allowed"])
        self.assertFalse(result["authority_granted"])
        self.assertFalse(result["calibration_observation"]["synthetic"])

    def test_treatment_normalization_is_mechanical(self):
        freeze_payload, observations = self.inputs()
        result = evaluate(freeze_payload, observations)
        self.assertEqual(
            result["treatment"]["normalized"],
            {
                "useful_finding": 1.0,
                "information_gain": 1.0,
                "blocked_work_avoidance": 0.0,
                "stale_evidence_catch": 0.0,
                "downstream_rework_avoidance": 1.0,
            },
        )

    def test_baseline_normalization_is_mechanical(self):
        freeze_payload, observations = self.inputs()
        result = evaluate(freeze_payload, observations)
        self.assertEqual(
            result["baseline"]["normalized"],
            {
                "useful_finding": 1.0,
                "information_gain": 0.5,
                "blocked_work_avoidance": 0.5,
                "stale_evidence_catch": 1.0,
                "downstream_rework_avoidance": 0.5,
            },
        )

    def test_frozen_selection_cannot_be_swapped_after_outcome(self):
        freeze_payload, observations = self.inputs()
        observations["baseline"]["selection_id"] = "cml-memory-proposal-pressure"
        with self.assertRaisesRegex(RoutingOutcomeError, "must match frozen selection"):
            evaluate(freeze_payload, observations)

    def test_authority_escalation_is_rejected(self):
        freeze_payload, observations = self.inputs()
        observations["authority"]["may_close_pr"] = True
        with self.assertRaisesRegex(RoutingOutcomeError, "may_close_pr must be false"):
            evaluate(freeze_payload, observations)

    def test_ambiguous_two_item_information_gain_is_rejected(self):
        freeze_payload, observations = self.inputs()
        observations["baseline"]["raw"]["affected_work_items"] = 2
        with self.assertRaisesRegex(RoutingOutcomeError, "outside the predeclared rubric"):
            evaluate(freeze_payload, observations)

    def test_actionable_and_confirmation_only_are_mutually_exclusive(self):
        freeze_payload, observations = self.inputs()
        observations["treatment"]["raw"]["state_confirmation_only"] = True
        with self.assertRaisesRegex(RoutingOutcomeError, "mutually exclusive"):
            evaluate(freeze_payload, observations)


if __name__ == "__main__":
    unittest.main()
