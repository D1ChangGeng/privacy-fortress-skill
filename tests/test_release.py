import json
import py_compile
import re
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "skills/privacy-fortress"


class ReleaseTests(unittest.TestCase):
    def test_frontmatter_contract(self):
        text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertTrue(text.startswith("---\n"))
        frontmatter = text.split("---", 2)[1]
        keys = [line.split(":", 1)[0] for line in frontmatter.splitlines() if line and not line.startswith(" ")]
        self.assertEqual(keys, ["name", "description"])
        self.assertIn("name: privacy-fortress", frontmatter)
        self.assertGreater(len(frontmatter.split("description:", 1)[1].strip()), 100)

    def test_skill_is_concise_and_references_exist(self):
        text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertLess(len(text.splitlines()), 500)
        refs = re.findall(r"`((?:references|scripts|assets)/[^`]+)`", text)
        self.assertGreater(len(refs), 10)
        for ref in refs:
            self.assertTrue((SKILL_ROOT / ref).exists(), ref)

    def test_no_private_workspace_or_affiliate_residue(self):
        forbidden = [
            r"D:\\Kimi", r"D:/Kimi", r"D26FO", r"133\.157\.56\.173",
            r"ipdeep", r"fengwo", r"yxRGajMF", r"extendid=",
            r"Magic4", r"LGE-AN10", r"9DLDLD", r"workspace/reports",
        ]
        for path in ROOT.rglob("*"):
            if path == Path(__file__) or "privacy-reports" in path.parts:
                continue
            if not path.is_file() or ".git" in path.parts or "dist" in path.parts:
                continue
            if path.suffix.lower() not in {".md", ".py", ".ps1", ".json", ".yaml", ".yml", ".gitignore", ""}:
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            for pattern in forbidden:
                self.assertIsNone(re.search(pattern, text, re.IGNORECASE), f"{pattern} in {path}")

    def test_python_scripts_compile(self):
        for path in SKILL_ROOT.rglob("*.py"):
            with tempfile.TemporaryDirectory() as tmp:
                py_compile.compile(str(path), cfile=str(Path(tmp) / (path.name + "c")), doraise=True)

    def test_examples_are_valid_json_and_reserved_ips(self):
        for path in (SKILL_ROOT / "assets").glob("*.json"):
            json.loads(path.read_text(encoding="utf-8"))
        gateway = (SKILL_ROOT / "assets/mihomo.example.yaml").read_text(encoding="utf-8")
        self.assertIn("192.0.2.10", gateway)
        self.assertNotIn("133.157.", gateway)

    def test_no_symlinks_in_skill(self):
        for path in SKILL_ROOT.rglob("*"):
            self.assertFalse(path.is_symlink(), str(path))


if __name__ == "__main__":
    unittest.main()
