import importlib.util
import json
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPT = SKILL_DIR / "score_graph_field.py"
FIXTURE = SKILL_DIR / "examples" / "neo-resonance-2026-08-15.json"

spec = importlib.util.spec_from_file_location("score_graph_field", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


class GraphFieldDynamicsTests(unittest.TestCase):
    def load_fixture(self):
        return json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_neo_resonance_ranking_is_deterministic_and_advisory(self):
        result = module.score(self.load_fixture())

        self.assertEqual("ADVISORY_ONLY", result["mode"])
        self.assertFalse(result["authority_granted"])
        self.assertEqual(
            [
                "p2-1-trust-spine-cost-latency",
                "cml-memory-proposal-pressure",
                "graph-field-extraction",
                "credential-boundary-rollout",
                "capu-adjacent-execution-boundary",
                "liminaldb-codeql-dependency",
                "proofpath-external-independence",
            ],
            [item["id"] for item in result["ranking"]],
        )

        top = result["ranking"][0]
        self.assertEqual(0.785, top["tension"])
        self.assertEqual(0.800588, top["field_score"])

    def test_blocked_hotspot_keeps_tension_but_loses_actionability(self):
        result = module.score(self.load_fixture())
        proofpath = next(
            item
            for item in result["ranking"]
            if item["id"] == "proofpath-external-independence"
        )

        self.assertEqual(0.71, proofpath["tension"])
        self.assertEqual(0.9, proofpath["blockedness"])
        self.assertLess(proofpath["actionability"], proofpath["tension"])
        self.assertEqual(0.31045, proofpath["field_score"])

    def test_rejects_unknown_edge_node(self):
        payload = self.load_fixture()
        payload["edges"].append(
            {"source": "missing-node", "target": "graph-field-extraction", "weight": 1.0}
        )

        with self.assertRaises(module.GFDInputError):
            module.score(payload)

    def test_rejects_out_of_range_component(self):
        payload = self.load_fixture()
        payload["nodes"][0]["uncertainty"] = 1.1

        with self.assertRaises(module.GFDInputError):
            module.score(payload)

    def test_focus_is_not_an_input_component(self):
        self.assertNotIn("focus", module.WEIGHTS)


if __name__ == "__main__":
    unittest.main()
