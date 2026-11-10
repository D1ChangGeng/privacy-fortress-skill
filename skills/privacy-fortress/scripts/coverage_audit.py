#!/usr/bin/env python3
"""Validate a user-owned 30-control privacy coverage ledger; never probes the host."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

SKILL_ROOT = Path(__file__).resolve().parents[1]
CONTROLS_PATH = SKILL_ROOT / "assets" / "coverage-controls.json"
CLOSED_STATUSES = {"TESTED", "RESIDUAL", "NOT_APPLICABLE"}


def load_controls() -> List[Dict[str, str]]:
    data = json.loads(CONTROLS_PATH.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1 or not isinstance(data.get("controls"), list):
        raise ValueError("invalid bundled coverage controls")
    controls = data["controls"]
    ids = [item.get("id") for item in controls]
    if len(controls) != 30 or len(set(ids)) != 30 or any(not item for item in ids):
        raise ValueError("coverage contract must contain 30 unique controls")
    for item in controls:
        if not all(item.get(key) for key in ("layer", "question", "reference")):
            raise ValueError("incomplete bundled control: " + str(item.get("id")))
        if not (SKILL_ROOT / item["reference"]).is_file():
            raise ValueError("missing control reference: " + item["reference"])
    return controls


def new_ledger(controls: List[Dict[str, str]]) -> Dict[str, Any]:
    return {
        "schema_version": 1,
        "device_label": "change-me-use-a-nonsensitive-alias",
        "controls": {
            item["id"]: {
                "status": "UNKNOWN",
                "tested_at": "",
                "evidence": "",
                "notes": "",
                "rollback": ""
            }
            for item in controls
        },
    }


def validate_ledger(data: Dict[str, Any], controls: List[Dict[str, str]]) -> Dict[str, int]:
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise ValueError("ledger schema_version must be 1")
    entries = data.get("controls")
    if not isinstance(entries, dict):
        raise ValueError("ledger controls must be an object")
    expected = {item["id"] for item in controls}
    missing = sorted(expected - set(entries))
    extra = sorted(set(entries) - expected)
    if missing or extra:
        raise ValueError("control mismatch; missing=" + ",".join(missing) + "; extra=" + ",".join(extra))
    allowed = {"TESTED", "CONFIG", "UNKNOWN", "RESIDUAL", "NOT_APPLICABLE"}
    counts = {status: 0 for status in sorted(allowed)}
    for control_id, entry in entries.items():
        if not isinstance(entry, dict):
            raise ValueError(control_id + " must be an object")
        status = entry.get("status")
        if status not in allowed:
            raise ValueError(control_id + " has invalid status")
        counts[status] += 1
        if status == "TESTED" and not (entry.get("tested_at") and entry.get("evidence")):
            raise ValueError(control_id + ": TESTED requires tested_at and evidence")
        if status == "CONFIG" and not entry.get("evidence"):
            raise ValueError(control_id + ": CONFIG requires evidence")
        if status in {"RESIDUAL", "NOT_APPLICABLE"} and not entry.get("notes"):
            raise ValueError(control_id + ": " + status + " requires notes")
    return counts


def escape(value: Any) -> str:
    return str(value or "").replace("|", "\\|").replace("\r", " ").replace("\n", " ")


def render_report(data: Dict[str, Any], controls: List[Dict[str, str]], counts: Dict[str, int]) -> str:
    closed = sum(counts[status] for status in CLOSED_STATUSES)
    lines = [
        "# Privacy Fortress 防护覆盖台账", "",
        "- 设备别名：" + escape(data.get("device_label", "未命名")),
        "- 闭环项：" + str(closed) + "/" + str(len(controls)) + "（TESTED、已说明的 RESIDUAL / NOT_APPLICABLE）",
        "- 状态：" + "，".join(key + "=" + str(value) for key, value in sorted(counts.items())),
        "- 注意：状态与证据由用户/Agent 填写，本脚本只检查完整性，不把文字声明升级为独立实测。", "",
        "| 控制项 | 防护面 | 状态 | 必答问题 | 日期 | 证据 / 说明 |",
        "|---|---|---|---|---|---|",
    ]
    for item in controls:
        entry = data["controls"][item["id"]]
        detail = entry.get("evidence") or entry.get("notes") or "待补充"
        lines.append("| {id} | {layer} | {status} | {question} | {date} | {detail} |".format(
            id=item["id"], layer=escape(item["layer"]), status=entry["status"],
            question=escape(item["question"]), date=escape(entry.get("tested_at")),
            detail=escape(detail)))
    lines += ["", "CONFIG 与 UNKNOWN 不是完成；RESIDUAL 必须保留残余说明，NOT_APPLICABLE 必须说明不适用原因。", ""]
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate the 30-control privacy coverage ledger; offline only")
    parser.add_argument("--list", action="store_true", help="list every required control")
    parser.add_argument("--init", help="create a new UNKNOWN ledger; never overwrites")
    parser.add_argument("--ledger", help="user-owned ledger JSON to validate")
    parser.add_argument("--output", help="write a Markdown coverage report")
    parser.add_argument("--require-tested", action="store_true", help="exit 2 while CONFIG or UNKNOWN remains")
    return parser.parse_args()


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    args = parse_args()
    try:
        controls = load_controls()
        if args.list:
            for item in controls:
                print(item["id"] + "\t" + item["layer"] + "\t" + item["question"])
        if args.init:
            path = Path(args.init).expanduser()
            if path.exists():
                raise ValueError("refusing to overwrite existing ledger: " + str(path))
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(new_ledger(controls), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print("Created UNKNOWN ledger: " + str(path))
        if not args.ledger:
            if args.output or args.require_tested:
                raise ValueError("--output and --require-tested require --ledger")
            return 0
        data = json.loads(Path(args.ledger).expanduser().read_text(encoding="utf-8"))
        counts = validate_ledger(data, controls)
        report = render_report(data, controls, counts)
        if args.output:
            output = Path(args.output).expanduser()
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(report, encoding="utf-8")
            print("Coverage report: " + str(output))
        else:
            print(report)
        if args.require_tested and (counts["CONFIG"] or counts["UNKNOWN"]):
            print("Coverage incomplete: CONFIG or UNKNOWN remains.", file=sys.stderr)
            return 2
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print("coverage error: " + str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
