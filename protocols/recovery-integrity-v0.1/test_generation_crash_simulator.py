#!/usr/bin/env python3
"""Regression tests for Generation-N recovery classification."""
from __future__ import annotations

import unittest

from generation_crash_simulator import CANONICAL_CASES, make_record, simulate
from validate import validate


class GenerationCrashSimulatorTests(unittest.TestCase):
    def test_canonical_matrix(self) -> None:
        expected = {
            "healthy": ("HEALTHY", "NO_REBUILD", "HOLD"),
            "stale": ("STALE", "ALLOW_REBUILD", "HOLD"),
            "corrupt": ("CORRUPT", "ALLOW_REBUILD", "HOLD"),
            "split-generation": ("UNPROVABLE", "HOLD", "HOLD"),
        }
        for case in CANONICAL_CASES:
            with self.subTest(case=case.name):
                result = simulate(case)
                self.assertEqual(
                    (
                        result.projection_state,
                        result.rebuild_decision,
                        result.execution_decision,
                    ),
                    expected[case.name],
                )
                self.assertEqual(result.validator_errors, ())

    def test_split_generation_cannot_be_rebuilt_from_older_authority(self) -> None:
        case = next(c for c in CANONICAL_CASES if c.name == "split-generation")
        record = make_record(case)
        record["decision"]["rebuild_projection"] = "ALLOW_REBUILD"
        errors = validate(record)
        self.assertIn(
            "ALLOW_REBUILD forbidden when projection generation is newer than authority generation",
            errors,
        )

    def test_rebuild_does_not_grant_execution(self) -> None:
        case = next(c for c in CANONICAL_CASES if c.name == "stale")
        record = make_record(case)
        record["decision"]["execution_continuation"] = "ALLOW_FORK"
        errors = validate(record)
        self.assertIn("ALLOW_FORK requires rollout.continuation_proof=PROVEN", errors)
        self.assertIn("ALLOW_FORK forbidden with ambiguous/unknown external side effects", errors)
        self.assertIn(
            "ALLOW_FORK requires current authority proven or explicitly not required",
            errors,
        )


if __name__ == "__main__":
    unittest.main()
