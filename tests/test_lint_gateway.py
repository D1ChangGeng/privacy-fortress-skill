import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "skills/privacy-fortress/scripts/lint_gateway.py"
SPEC = importlib.util.spec_from_file_location("lint_gateway", MODULE_PATH)
lint = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(lint)


SAFE = """
dns:
  nameserver:
    - https://1.1.1.1/dns-query
tun:
  dns-hijack:
    - any:53
rules:
  - DOMAIN-SUFFIX,example.com,Proxy
  - MATCH,Proxy
"""


class GatewayLintTests(unittest.TestCase):
    def test_safe_skeleton(self):
        result = lint.lint_text(SAFE)
        self.assertFalse(result.failed)

    def test_final_direct_fails(self):
        result = lint.lint_text(SAFE.replace("MATCH,Proxy", "MATCH,DIRECT"))
        self.assertTrue(result.failed)
        self.assertIn("默认直连", [x["name"] for x in result.items])

    def test_rule_after_match_warns(self):
        text = SAFE.replace("  - MATCH,Proxy", "  - MATCH,Proxy\n  - DOMAIN-SUFFIX,late.example,Proxy")
        result = lint.lint_text(text)
        self.assertIn("兜底后规则", [x["name"] for x in result.items])

    def test_secret_value_is_redacted(self):
        text = SAFE + "\nproxies:\n  - name: test\n    password: do-not-print-this\n"
        result = lint.lint_text(text)
        rendered = str(result.items)
        self.assertIn("敏感字段", [x["name"] for x in result.items])
        self.assertNotIn("do-not-print-this", rendered)

    def test_placeholder_secret_is_allowed(self):
        text = SAFE + "\nproxies:\n  - password: <PROXY_PASSWORD>\n"
        result = lint.lint_text(text)
        self.assertNotIn("敏感字段", [x["name"] for x in result.items])

    def test_bundled_example_has_no_fail(self):
        text = (ROOT / "skills/privacy-fortress/assets/mihomo.example.yaml").read_text(encoding="utf-8")
        self.assertFalse(lint.lint_text(text).failed)


if __name__ == "__main__":
    unittest.main()
