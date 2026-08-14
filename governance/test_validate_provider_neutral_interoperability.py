from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from validate_provider_neutral_interoperability import (
    CONTRACT_SCHEMA,
    InteroperabilityError,
    canonical_bytes,
    independent_verify,
    load_json,
    run_lifecycle,
    run_negative_cases,
    validate_contract,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "governance" / "provider-neutral-interoperability-fixture.v0.1.json"


class ProviderNeutralInteroperabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture = load_json(FIXTURE)

    def test_contract_validates_and_preserves_route(self) -> None:
        summary = validate_contract(self.fixture)
        self.assertEqual(summary["schema"], CONTRACT_SCHEMA)
        self.assertEqual(summary["route"], ["intent", "proofpath", "cml", "liminaldb", "rinse", "contractgraph_qa"])
        self.assertTrue(summary["causal_parent_chain_preserved"])
        self.assertTrue(summary["semantic_mappings_preserved"])

    def test_lifecycle_round_trip_store_reopen_reflect_verify(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = run_lifecycle(self.fixture, Path(directory))
        self.assertTrue(result["stored_byte_match"])
        self.assertTrue(result["reopened_byte_match"])
        self.assertEqual(result["reflection"]["authority"]["classification"], "REFLECTION_ONLY")
        self.assertFalse(result["reflection"]["authority"]["execution_authorized"])
        self.assertEqual(result["independent_verification"]["status"], "PASS")

    def test_canonical_serialization_is_deterministic(self) -> None:
        self.assertEqual(canonical_bytes(self.fixture), canonical_bytes(json.loads(json.dumps(self.fixture))))

    def test_negative_cases_are_rejected(self) -> None:
        negatives = run_negative_cases(self.fixture)
        self.assertEqual(set(negatives), {
            "logical_operation_renaming",
            "causal_parent_break",
            "unknown_phase",
            "missing_evidence_ref",
            "authority_escalation",
            "semantic_rename",
        })
        self.assertTrue(all(value == "REJECTED" for value in negatives.values()))

    def test_tampered_serialized_bytes_fail_independent_replay(self) -> None:
        serialized = canonical_bytes(self.fixture)
        tampered = copy.deepcopy(self.fixture)
        tampered["events"][5]["observed_outcome"]["decision"] = "ALLOW"
        reflection = {
            "source_digest": "sha256:" + "0" * 64,
            "authority": {"execution_authorized": False},
            "source_mutated": False,
            "write_back_performed": False,
        }
        with self.assertRaises(InteroperabilityError):
            independent_verify(tampered, serialized, reflection)


if __name__ == "__main__":
    unittest.main()
