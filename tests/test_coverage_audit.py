import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "skills/privacy-fortress/scripts/coverage_audit.py"
SPEC = importlib.util.spec_from_file_location("coverage_audit", MODULE_PATH)
coverage = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(coverage)


class CoverageTests(unittest.TestCase):
    def setUp(self):
        self.controls = coverage.load_controls()
        self.ledger = coverage.new_ledger(self.controls)

    def test_contract_has_thirty_unique_controls_and_existing_references(self):
        self.assertEqual(len(self.controls), 30)
        self.assertEqual(len({item["id"] for item in self.controls}), 30)
        for platform in ("android", "ios", "network", "dns"):
            self.assertTrue(any(item["id"].startswith(platform + ".") for item in self.controls))

    def test_new_ledger_is_unknown_and_incomplete(self):
        counts = coverage.validate_ledger(self.ledger, self.controls)
        self.assertEqual(counts["UNKNOWN"], 30)
        report = coverage.render_report(self.ledger, self.controls, counts)
        self.assertIn("闭环项：0/30", report)
        self.assertIn("CONFIG 与 UNKNOWN 不是完成", report)

    def test_missing_control_is_rejected(self):
        del self.ledger["controls"]["network.capture"]
        with self.assertRaisesRegex(ValueError, "network.capture"):
            coverage.validate_ledger(self.ledger, self.controls)

    def test_tested_requires_date_and_evidence(self):
        entry = self.ledger["controls"]["network.capture"]
        entry["status"] = "TESTED"
        with self.assertRaisesRegex(ValueError, "tested_at and evidence"):
            coverage.validate_ledger(self.ledger, self.controls)
        entry["tested_at"] = "2026-01-01"
        entry["evidence"] = "Example read-only test evidence"
        counts = coverage.validate_ledger(self.ledger, self.controls)
        self.assertEqual(counts["TESTED"], 1)

    def test_residual_and_not_applicable_require_reason(self):
        self.ledger["controls"]["ios.vpn"] = {
            "status": "NOT_APPLICABLE", "tested_at": "", "evidence": "",
            "notes": "No iOS device in scope", "rollback": ""
        }
        self.ledger["controls"]["upstream.visibility"]["status"] = "RESIDUAL"
        with self.assertRaisesRegex(ValueError, "RESIDUAL requires notes"):
            coverage.validate_ledger(self.ledger, self.controls)

    def test_cli_init_validate_and_require_tested(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger_path = Path(tmp) / "coverage.json"
            report_path = Path(tmp) / "coverage.md"
            with mock.patch.object(sys, "argv", ["coverage_audit.py", "--init", str(ledger_path)]):
                self.assertEqual(coverage.main(), 0)
            self.assertTrue(ledger_path.is_file())
            argv = ["coverage_audit.py", "--ledger", str(ledger_path),
                    "--output", str(report_path), "--require-tested"]
            with mock.patch.object(sys, "argv", argv):
                self.assertEqual(coverage.main(), 2)
            self.assertIn("闭环项：0/30", report_path.read_text(encoding="utf-8"))
            with mock.patch.object(sys, "argv", ["coverage_audit.py", "--init", str(ledger_path)]):
                self.assertEqual(coverage.main(), 2)


if __name__ == "__main__":
    unittest.main()
