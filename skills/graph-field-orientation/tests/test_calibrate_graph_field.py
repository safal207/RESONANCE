import importlib.util
import json
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPT = SKILL_DIR / "calibrate_graph_field.py"
FIXTURE = SKILL_DIR / "examples" / "synthetic-calibration-v0.2.json"

spec = importlib.util.spec_from_file_location("calibrate_graph_field", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


class GraphFieldCalibrationTests(unittest.TestCase):
    def load_fixture(self):
        return json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_proposal_is_advisory_and_never_auto_applies(self):
        result = module.calibrate(self.load_fixture())

        self.assertEqual("resonance.graph-field-calibration.proposal.v0.2", result["schema"])
        self.assertEqual("ADVISORY_ONLY", result["mode"])
        self.assertFalse(result["authority_granted"])
        self.assertFalse(result["apply_recommended"])
        self.assertEqual("INSUFFICIENT", result["confidence"])
        self.assertEqual(2, result["observation_count"])

    def test_proposed_weights_remain_normalized(self):
        result = module.calibrate(self.load_fixture())
        self.assertAlmostEqual(1.0, sum(result["proposed_weights"].values()), places=8)

    def test_synthetic_fixture_reduces_open_pressure_relative_weight(self):
        result = module.calibrate(self.load_fixture())
        self.assertLess(
            result["proposed_weights"]["open_pressure"],
            result["current_weights"]["open_pressure"],
        )

    def test_missing_outcome_evidence_fails_closed(self):
        payload = self.load_fixture()
        payload["observations"][0]["outcome"]["evidence"] = []
        with self.assertRaises(module.CalibrationInputError):
            module.calibrate(payload)

    def test_learning_rate_above_bound_is_rejected(self):
        payload = self.load_fixture()
        payload["learning_rate"] = 0.11
        with self.assertRaises(module.CalibrationInputError):
            module.calibrate(payload)

    def test_current_weights_must_sum_to_one(self):
        payload = self.load_fixture()
        payload["current_weights"]["opportunity"] = 0.20
        with self.assertRaises(module.CalibrationInputError):
            module.calibrate(payload)

    def test_field_score_is_not_part_of_calibration_input_contract(self):
        self.assertNotIn("field_score", module.OUTCOME_WEIGHTS)
        self.assertNotIn("field_score", module.COMPONENTS)


if __name__ == "__main__":
    unittest.main()
