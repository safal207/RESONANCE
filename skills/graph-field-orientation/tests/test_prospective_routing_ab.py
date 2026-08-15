from __future__ import annotations

import copy
import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

MODULE_PATH = ROOT / "prospective_routing_ab.py"
SPEC = importlib.util.spec_from_file_location("prospective_routing_ab", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

RoutingFreezeError = MODULE.RoutingFreezeError
freeze = MODULE.freeze
FIXTURE = ROOT / "examples" / "prospective-routing-ab-2026-08-15.json"


class ProspectiveRoutingABTests(unittest.TestCase):
    def payload(self):
        return json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_freeze_selects_gfd_and_fifo_before_outcomes(self):
        result = freeze(self.payload())
        self.assertEqual(result["status"], "FROZEN_BEFORE_OUTCOME")
        self.assertEqual(result["treatment"]["selection_id"], "cml-memory-proposal-pressure")
        self.assertEqual(result["treatment"]["field_score"], 0.728913)
        self.assertEqual(result["baseline"]["selection_id"], "liminaldb-codeql-dependency")
        self.assertEqual(result["baseline"]["ready_since"], "2026-07-31T14:45:26Z")
        self.assertFalse(result["authority_granted"])
        self.assertFalse(result["calibration_allowed"])
        self.assertFalse(result["weight_update_allowed"])

    def test_completed_p2_1_cannot_reenter_active_candidate_set(self):
        payload = self.payload()
        payload["nodes"].append(
            {
                "id": "p2-1-trust-spine-cost-latency",
                "label": "completed",
                "divergence": 1,
                "uncertainty": 1,
                "blast_radius": 1,
                "freshness_gap": 1,
                "open_pressure": 1,
                "opportunity": 1,
                "blockedness": 0,
                "eligible": True,
                "ready_since": "2026-08-14T00:00:00Z",
                "ready_evidence": ["historical completed node"],
            }
        )
        with self.assertRaisesRegex(RoutingFreezeError, "completed P2-1"):
            freeze(payload)

    def test_blocked_proofpath_is_not_fifo_eligible(self):
        payload = self.payload()
        proofpath = next(node for node in payload["nodes"] if node["id"] == "proofpath-external-independence")
        proofpath["ready_since"] = "2026-01-01T00:00:00Z"
        result = freeze(payload)
        self.assertNotEqual(result["baseline"]["selection_id"], "proofpath-external-independence")
        self.assertEqual(result["baseline"]["selection_id"], "liminaldb-codeql-dependency")

    def test_fifo_timestamp_mutation_fails_frozen_expected_selection(self):
        payload = self.payload()
        cml = next(node for node in payload["nodes"] if node["id"] == "cml-memory-proposal-pressure")
        cml["ready_since"] = "2026-07-01T00:00:00Z"
        with self.assertRaisesRegex(RoutingFreezeError, "baseline selection drift"):
            freeze(payload)

    def test_posthoc_outcome_is_rejected_from_freeze_fixture(self):
        payload = self.payload()
        payload["outcomes"] = {"treatment": {"useful_finding": 1.0}}
        with self.assertRaisesRegex(RoutingFreezeError, "must not contain post-selection outcomes"):
            freeze(payload)

    def test_posthoc_utility_weight_change_is_rejected(self):
        payload = self.payload()
        payload["utility"]["dimensions"]["useful_finding"]["weight"] = 0.35
        with self.assertRaisesRegex(RoutingFreezeError, "weight drifted"):
            freeze(payload)

    def test_authority_escalation_is_rejected(self):
        payload = self.payload()
        payload["authority"]["may_change_weights"] = True
        with self.assertRaisesRegex(RoutingFreezeError, "may_change_weights must be false"):
            freeze(payload)

    def test_gfd_component_mutation_fails_expected_treatment(self):
        payload = self.payload()
        cml = next(node for node in payload["nodes"] if node["id"] == "cml-memory-proposal-pressure")
        cml["opportunity"] = 0.0
        with self.assertRaises(RoutingFreezeError):
            freeze(payload)


if __name__ == "__main__":
    unittest.main()
