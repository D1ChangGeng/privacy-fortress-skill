#!/usr/bin/env python3
"""Validate and reproducibly package the privacy-fortress skill."""
from __future__ import annotations

import argparse
import hashlib
import json
import py_compile
import re
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL_NAME = "privacy-fortress"
SKILL_ROOT = ROOT / "skills" / SKILL_NAME
ALLOWED_SUFFIXES = {".md", ".py", ".ps1", ".json", ".yaml", ".yml"}


def validate() -> list[Path]:
    entry = SKILL_ROOT / "SKILL.md"
    if not entry.is_file():
        raise ValueError("missing SKILL.md")
    text = entry.read_text(encoding="utf-8")
    if not text.startswith("---\n") or text.count("---") < 2:
        raise ValueError("invalid YAML frontmatter boundaries")
    frontmatter = text.split("---", 2)[1]
    keys = [line.split(":", 1)[0] for line in frontmatter.splitlines() if line and not line.startswith(" ")]
    if keys != ["name", "description"]:
        raise ValueError("frontmatter must contain only name and description")
    if f"name: {SKILL_NAME}" not in frontmatter:
        raise ValueError("skill name does not match directory")
    if len(frontmatter.split("description:", 1)[1].strip()) < 100:
        raise ValueError("description is not specific enough")
    if len(text.splitlines()) >= 500:
        raise ValueError("SKILL.md exceeds 500-line progressive-disclosure budget")

    files = sorted(path for path in SKILL_ROOT.rglob("*") if path.is_file())
    if not files:
        raise ValueError("empty skill")
    for path in files:
        relative = path.relative_to(SKILL_ROOT)
        if path.is_symlink():
            raise ValueError(f"symlink not allowed: {relative}")
        if path.suffix.lower() not in ALLOWED_SUFFIXES:
            raise ValueError(f"unexpected file type: {relative}")
        if any(part in {"__pycache__", "workspace", ".git", "dist"} for part in relative.parts):
            raise ValueError(f"generated/private path not allowed: {relative}")
        if path.stat().st_size > 2 * 1024 * 1024:
            raise ValueError(f"file exceeds 2 MiB: {relative}")
        if path.suffix == ".py":
            with tempfile.TemporaryDirectory() as tmp:
                py_compile.compile(str(path), cfile=str(Path(tmp) / "module.pyc"), doraise=True)
        if path.suffix == ".json":
            json.loads(path.read_text(encoding="utf-8"))
    return files


def package(output: Path) -> dict[str, str | int]:
    files = validate()
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            arcname = f"{SKILL_NAME}/{path.relative_to(SKILL_ROOT).as_posix()}"
            info = zipfile.ZipInfo(arcname, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes())
    with zipfile.ZipFile(output) as archive:
        bad = archive.testzip()
        if bad:
            raise ValueError(f"archive CRC failure: {bad}")
        if f"{SKILL_NAME}/SKILL.md" not in archive.namelist():
            raise ValueError("archive entrypoint missing")
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    return {"archive": str(output), "files": len(files), "sha256": digest}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="validate without writing an archive")
    parser.add_argument("--output", type=Path, default=ROOT / "dist" / f"{SKILL_NAME}.skill")
    args = parser.parse_args()
    try:
        if args.check:
            files = validate()
            print(json.dumps({"valid": True, "files": len(files)}, indent=2))
        else:
            print(json.dumps(package(args.output), ensure_ascii=False, indent=2))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"package error: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
