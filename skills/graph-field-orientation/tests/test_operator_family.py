import importlib.util
import json
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
OPERATOR_FAMILY = SKILL_DIR / "operator_family.py"
SCORER = SKILL_DIR / "score_graph_field.py"
RECOVERY_FIXTURE = SKILL_DIR / "examples" / "cml-focus-field-v0.2-trusted.json"
ORIENTATION_FIXTURE = SKILL_DIR / "examples" / "neo-resonance-2026-08-15.json"


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


family = load_module("operator_family", OPERATOR_FAMILY)
scorer = load_module("score_graph_field_for_family", SCORER)


class GraphFieldOperatorFamilyTests(unittest.TestCase):
    def test_orientation_normalizes_without_authority(self):
        payload = json.loads(ORIENTATION_FIXTURE.read_text(encoding="utf-8"))
        source = scorer.score(payload)
        result = family.normalize_orientation(source)

        self.assertEqual("resonance.graph-field-operator.result.v0.1", result["schema"])
        self.assertEqual("orientation", result["operator_kind"])
        self.assertEqual("ADVISORY_ONLY", result["mode"])
        self.assertFalse(result["authority_granted"])
        self.assertEqual(
            "p2-1-trust-spine-cost-latency",
            result["selection"]["id"],
        )
        self.assertEqual("ORIENTATION_CANDIDATE", result["selection"]["state"])
        self.assertTrue(result["handoff"]["ready_for_separate_authority_check"])

    def test_trusted_cml_recovery_maps_to_reentry_candidate_only(self):
        payload = json.loads(RECOVERY_FIXTURE.read_text(encoding="utf-8"))
        result = family.normalize_cml_recovery(payload)

        self.assertEqual("recovery", result["operator_kind"])
        self.assertEqual("node-8", result["selection"]["id"])
        self.assertEqual("TRUSTED_REENTRY_CANDIDATE", result["selection"]["state"])
        self.assertTrue(result["handoff"]["ready_for_separate_authority_check"])
        self.assertFalse(result["authority_granted"])

    def test_exploratory_recovery_cannot_handoff_as_trusted(self):
        payload = json.loads(RECOVERY_FIXTURE.read_text(encoding="utf-8"))
        payload.update(
            {
                "state": "reanchored_exploratory",
                "trusted_continuation": False,
            }
        )
        result = family.normalize_cml_recovery(payload)

        self.assertEqual("EXPLORATORY_SELECTION", result["selection"]["state"])
        self.assertFalse(result["handoff"]["ready_for_separate_authority_check"])
        self.assertFalse(result["authority_granted"])

    def test_defocus_preserves_no_selection(self):
        payload = json.loads(RECOVERY_FIXTURE.read_text(encoding="utf-8"))
        payload.update(
            {
                "state": "defocus",
                "selected_anchor_id": None,
                "score": 0.2,
                "trusted_continuation": False,
                "rewind_steps_saved": None,
            }
        )
        result = family.normalize_cml_recovery(payload)

        self.assertIsNone(result["selection"]["id"])
        self.assertEqual("NO_SELECTION", result["selection"]["state"])
        self.assertFalse(result["handoff"]["ready_for_separate_authority_check"])

    def test_rejects_contradictory_recovery_trust_state(self):
        payload = json.loads(RECOVERY_FIXTURE.read_text(encoding="utf-8"))
        payload["trusted_continuation"] = False

        with self.assertRaises(family.OperatorFamilyError):
            family.normalize_cml_recovery(payload)

    def test_rejects_any_source_authority_grant(self):
        payload = json.loads(RECOVERY_FIXTURE.read_text(encoding="utf-8"))
        payload["authority_granted"] = True

        with self.assertRaises(family.OperatorFamilyError):
            family.normalize_cml_recovery(payload)


if __name__ == "__main__":
    unittest.main()
