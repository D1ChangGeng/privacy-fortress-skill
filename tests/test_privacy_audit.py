import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "skills/privacy-fortress/scripts/privacy_audit.py"
SPEC = importlib.util.spec_from_file_location("privacy_audit", MODULE_PATH)
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


class BaselineTests(unittest.TestCase):
    def test_empty_baseline(self):
        self.assertEqual(audit.load_baseline(None), {})

    def test_valid_baseline(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "baseline.json"
            path.write_text(json.dumps({
                "expected_ipv4": "203.0.113.10",
                "expected_country": "jp",
                "expected_timezone": "Asia/Tokyo",
                "expected_locale": "ja_JP"
            }), encoding="utf-8")
            baseline = audit.load_baseline(str(path))
            self.assertEqual(baseline["expected_country"], "JP")

    def test_unknown_field_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "baseline.json"
            path.write_text('{"machine_guid": "secret"}', encoding="utf-8")
            with self.assertRaises(ValueError):
                audit.load_baseline(str(path))

    def test_ipv6_in_ipv4_field_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "baseline.json"
            path.write_text('{"expected_ipv4": "2001:db8::1"}', encoding="utf-8")
            with self.assertRaises(ValueError):
                audit.load_baseline(str(path))


class ReportTests(unittest.TestCase):
    def test_offline_does_not_use_network(self):
        with mock.patch.object(audit, "http_get", side_effect=AssertionError("network used")):
            report = audit.build_report(False, {})
        self.assertFalse(report["online"])
        self.assertIn("公网出口", [x["name"] for x in report["checks"]])
        self.assertNotEqual(report["summary"]["verdict"], "FAIL")

    def test_online_mismatch_fails(self):
        responses = {
            "https://api.ipify.org": "198.51.100.8",
            "https://www.cloudflare.com/cdn-cgi/trace": "ip=198.51.100.8\nloc=US\n",
            "https://api64.ipify.org": "198.51.100.8",
        }
        baseline = {"expected_ipv4": "203.0.113.10", "expected_country": "JP"}
        with mock.patch.object(audit, "http_get", side_effect=lambda url: responses[url]):
            report = audit.build_report(True, baseline)
        self.assertEqual(report["summary"]["verdict"], "FAIL")

    def test_write_report_creates_json_and_markdown(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = audit.build_report(False, {})
            paths = audit.write_report(report, tmp)
            data = json.loads(Path(paths["json"]).read_text(encoding="utf-8"))
            markdown = Path(paths["markdown"]).read_text(encoding="utf-8")
            self.assertEqual(data["schema_version"], 1)
            self.assertIn("人工复核", markdown)
            self.assertNotIn(str(Path.home()), markdown)

    def test_markdown_escapes_table_cells(self):
        self.assertEqual(audit.markdown_escape("a|b\nc"), "a\\|b c")


if __name__ == "__main__":
    unittest.main()
