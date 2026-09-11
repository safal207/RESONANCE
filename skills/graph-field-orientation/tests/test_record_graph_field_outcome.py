import copy
import importlib.util
import json
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPT = SKILL_DIR / "record_graph_field_outcome.py"
FIXTURE = SKILL_DIR / "examples" / "p2-1-real-outcome-unpaired-v0.2.json"

spec = importlib.util.spec_from_file_location("record_graph_field_outcome", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


class GraphFieldRealOutcomeTests(unittest.TestCase):
    def load_fixture(self):
        return json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_real_p2_1_outcome_is_recorded_but_not_calibration_ready(self):
        result = module.validate(self.load_fixture())
        self.assertEqual("RECORDED_UNPAIRED", result["decision"])
        self.assertEqual("ADVISORY_ONLY", result["mode"])
        self.assertFalse(result["authority_granted"])
        self.assertFalse(result["weight_update_allowed"])
        self.assertEqual("BASELINE_REQUIRED", result["calibration_eligibility"])
        self.assertEqual("liminaldb", result["dominant_measurement_group"])
        self.assertEqual(23, result["dominant_group_observed_seconds"])
        self.assertEqual(45, result["job_elapsed_seconds"])
        self.assertEqual(35, result["substantive_window_seconds"])
        self.assertEqual(28222, result["source_evidence_artifact_bytes"])
        self.assertEqual("NOT_MEASURED", result["monetary_cost_status"])

    def test_rejects_retroactive_field_score_change(self):
        payload = self.load_fixture()
        payload["pre_action"]["field_score"] = 0.9
        with self.assertRaises(module.OutcomeIntakeError):
            module.validate(payload)

    def test_rejects_outcome_metric_drift(self):
        payload = self.load_fixture()
        payload["observed_outcome"]["metrics"]["dominant_group_observed_seconds"] = 22
        with self.assertRaises(module.OutcomeIntakeError):
            module.validate(payload)

    def test_rejects_post_hoc_utility_score(self):
        payload = self.load_fixture()
        payload["calibration"]["utility_annotation_status"] = "SCORED"
        with self.assertRaises(module.OutcomeIntakeError):
            module.validate(payload)

    def test_rejects_fabricated_baseline_readiness(self):
        payload = self.load_fixture()
        payload["calibration"]["baseline_status"] = "OBSERVED"
        payload["calibration"]["eligibility"] = "CALIBRATION_READY"
        payload["calibration"]["weight_update_allowed"] = True
        with self.assertRaises(module.OutcomeIntakeError):
            module.validate(payload)

    def test_rejects_authority_escalation(self):
        payload = self.load_fixture()
        payload["authority"]["may_execute"] = True
        with self.assertRaises(module.OutcomeIntakeError):
            module.validate(payload)

    def test_receipt_is_deterministic(self):
        first = module.validate(self.load_fixture())
        second = module.validate(copy.deepcopy(self.load_fixture()))
        self.assertEqual(first, second)
        self.assertTrue(first["receipt_digest"].startswith("sha256:"))


if __name__ == "__main__":
    unittest.main()
