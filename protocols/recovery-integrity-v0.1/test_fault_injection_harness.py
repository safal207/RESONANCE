#!/usr/bin/env python3
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fault_injection_harness import CRASH_POINTS, EXPECTED, assert_expected, run_one


class ProcessCrashFaultInjectionTests(unittest.TestCase):
    def test_all_crash_boundaries_match_expected_recovery_state(self) -> None:
        with tempfile.TemporaryDirectory(prefix="recovery-integrity-fi-test-") as temp_root:
            base = Path(temp_root)
            for crash_point in CRASH_POINTS:
                with self.subTest(crash_point=crash_point):
                    observed = run_one(crash_point, base / crash_point)
                    assert_expected(crash_point, observed)

    def test_pre_commit_crash_does_not_advance_authority(self) -> None:
        with tempfile.TemporaryDirectory(prefix="recovery-integrity-fi-test-") as temp_root:
            observed = run_one("before_authority_commit", Path(temp_root) / "case")
            record = observed["record"]
            self.assertEqual(record["authority"]["generation"], 1)
            self.assertEqual(record["projection"]["generation"], 1)
            self.assertEqual(record["projection"]["state"], "HEALTHY")
            self.assertEqual(record["decision"]["rebuild_projection"], "NO_REBUILD")

    def test_post_commit_pre_projection_crash_is_stale_not_missing(self) -> None:
        with tempfile.TemporaryDirectory(prefix="recovery-integrity-fi-test-") as temp_root:
            observed = run_one("after_authority_commit", Path(temp_root) / "case")
            record = observed["record"]
            self.assertEqual(record["authority"]["generation"], 2)
            self.assertEqual(record["projection"]["generation"], 1)
            self.assertEqual(record["projection"]["state"], "STALE")
            self.assertEqual(record["decision"]["rebuild_projection"], "ALLOW_REBUILD")
            self.assertEqual(record["decision"]["execution_continuation"], "HOLD")

    def test_temp_fsync_crash_preserves_old_projection_and_orphan_candidate(self) -> None:
        with tempfile.TemporaryDirectory(prefix="recovery-integrity-fi-test-") as temp_root:
            observed = run_one("after_projection_temp_fsync", Path(temp_root) / "case")
            record = observed["record"]
            self.assertEqual(record["projection"]["state"], "STALE")
            self.assertTrue(observed["temp_projection_present"])
            self.assertEqual(record["decision"]["execution_continuation"], "HOLD")

    def test_full_projection_commit_restores_generation_alignment(self) -> None:
        with tempfile.TemporaryDirectory(prefix="recovery-integrity-fi-test-") as temp_root:
            observed = run_one("after_projection_commit", Path(temp_root) / "case")
            record = observed["record"]
            self.assertEqual(record["authority"]["generation"], 2)
            self.assertEqual(record["projection"]["generation"], 2)
            self.assertEqual(record["projection"]["state"], "HEALTHY")
            self.assertEqual(record["decision"]["rebuild_projection"], "NO_REBUILD")

    def test_matrix_definition_covers_all_crash_points(self) -> None:
        self.assertEqual(set(CRASH_POINTS), set(EXPECTED))


if __name__ == "__main__":
    unittest.main()
