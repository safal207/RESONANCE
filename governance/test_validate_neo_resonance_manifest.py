import sys
import unittest
from pathlib import Path


GOVERNANCE = Path(__file__).resolve().parent
sys.path.insert(0, str(GOVERNANCE))

import validate_neo_resonance_manifest as validator  # noqa: E402


class ManifestValidatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest_path = GOVERNANCE / "neo-resonance-system-manifest.v0.1.json"
        cls.manifest = validator.load_manifest(cls.manifest_path)

    def test_manifest_structure_passes(self):
        self.assertEqual(validator.structural_errors(self.manifest), [])

    def test_remote_snapshot_passes_when_all_heads_match(self):
        expected = {
            item["full_name"]: item["observed_head"]
            for item in self.manifest["repositories"]
        }

        def fetcher(name, branch):
            self.assertEqual(branch, "main")
            return expected[name]

        status, records = validator.check_remote_heads(self.manifest, fetcher)
        self.assertEqual(status, "PASS")
        self.assertEqual(len(records), 8)
        self.assertTrue(all(record["status"] == "PASS" for record in records))

    def test_changed_head_is_hold(self):
        expected = self.manifest["repositories"][0]["observed_head"]

        def fetcher(name, branch):
            return "0" * 40 if name == "safal207/RESONANCE" else next(
                item["observed_head"]
                for item in self.manifest["repositories"]
                if item["full_name"] == name
            )

        status, records = validator.check_remote_heads(self.manifest, fetcher)
        self.assertEqual(status, "HOLD")
        moved = next(record for record in records if record["expected_head"] == expected)
        self.assertEqual(moved["status"], "HOLD")
        self.assertEqual(moved["current_head"], "0" * 40)

    def test_unavailable_head_is_incomplete(self):
        def fetcher(name, branch):
            if name == "safal207/ProofPath":
                raise OSError("remote unavailable")
            return next(
                item["observed_head"]
                for item in self.manifest["repositories"]
                if item["full_name"] == name
            )

        status, records = validator.check_remote_heads(self.manifest, fetcher)
        self.assertEqual(status, "INCOMPLETE")
        unavailable = next(record for record in records if record["full_name"] == "safal207/ProofPath")
        self.assertEqual(unavailable["status"], "INCOMPLETE")
        self.assertIn("remote unavailable", unavailable["error"])


if __name__ == "__main__":
    unittest.main()
