#!/usr/bin/env python3
"""Heuristic safety lint for Mihomo/Clash YAML; not a YAML/schema validator."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class Results:
    def __init__(self) -> None:
        self.items: List[Dict[str, Any]] = []

    def add(self, status: str, name: str, detail: str, line: Optional[int] = None) -> None:
        item: Dict[str, Any] = {"status": status, "name": name, "detail": detail}
        if line is not None:
            item["line"] = line
        self.items.append(item)

    @property
    def failed(self) -> bool:
        return any(item["status"] == "FAIL" for item in self.items)


def rule_entries(lines: List[str]) -> List[Tuple[int, str]]:
    in_rules = False
    entries: List[Tuple[int, str]] = []
    for number, line in enumerate(lines, 1):
        if re.match(r"^rules:\s*(?:#.*)?$", line):
            in_rules = True
            continue
        if in_rules and line and not line[0].isspace() and not line.lstrip().startswith("#"):
            break
        if in_rules:
            match = re.match(r"^\s*-\s*(.+?)\s*(?:#.*)?$", line)
            if match:
                entries.append((number, match.group(1).strip(" \"'")))
    return entries


def lint_text(text: str) -> Results:
    result = Results()
    lines = text.splitlines()
    if not lines:
        result.add("FAIL", "空配置", "文件没有内容")
        return result

    result.add("INFO", "检查范围", "启发式文本检查；仍须使用 Mihomo/sing-box 官方配置校验和联网验收")
    if any("\t" in line for line in lines):
        result.add("WARN", "YAML 制表符", "发现 Tab；YAML 通常要求空格缩进")
    if re.search(r"<[A-Z][A-Z0-9_]+>", text):
        result.add("WARN", "占位符", "仍有大写占位符；部署前必须替换，公开分享时不得填入真实凭据")

    secret_pattern = re.compile(
        r"^\s*(?:password|uuid|secret|token|private-key|private_key)\s*:\s*['\"]?([^'\"#\s][^#\r\n]*)",
        re.IGNORECASE | re.MULTILINE,
    )
    for match in secret_pattern.finditer(text):
        value = match.group(1).strip().strip("'\"")
        if value and not (value.startswith("<") and value.endswith(">")):
            line = text.count("\n", 0, match.start()) + 1
            result.add("WARN", "敏感字段", "发现非占位凭据值；公开分享前移除或轮换（不输出该值）", line)

    entries = rule_entries(lines)
    if not entries:
        result.add("WARN", "规则表", "未识别到 rules 列表；可能是其他核心格式或非常规缩进")
    else:
        match_indexes = [(i, line, rule) for i, (line, rule) in enumerate(entries)
                         if rule.upper().startswith("MATCH,")]
        if not match_indexes:
            result.add("WARN", "默认路由", "未找到 MATCH 兜底；需确认默认策略不会意外 DIRECT")
        else:
            index, line, final_rule = match_indexes[-1]
            parts = [part.strip() for part in final_rule.split(",")]
            target = parts[1].upper() if len(parts) > 1 else ""
            if target == "DIRECT":
                result.add("FAIL", "默认直连", "最终 MATCH 为 DIRECT，未命中流量会暴露真实出口", line)
            elif target == "REJECT":
                result.add("WARN", "默认拒绝", "最终 MATCH 为 REJECT；确认可用性和故障语义符合预期", line)
            else:
                result.add("PASS", "默认代理", f"最终 MATCH 指向 {parts[1] if len(parts) > 1 else '未知组'}", line)
            if index != len(entries) - 1:
                result.add("WARN", "兜底后规则", "MATCH 后仍有规则；首命中内核中这些规则可能不会生效", entries[index + 1][0])

    if re.search(r"^\s*nameserver:\s*$", text, re.MULTILINE):
        if re.search(r"https://\d{1,3}(?:\.\d{1,3}){3}/dns-query", text):
            result.add("PASS", "加密 DNS", "发现 IP 字面量 DoH 上游；仍须验证其连接经过代理")
        else:
            result.add("WARN", "加密 DNS", "未同时发现 IP 字面量 DoH 上游；检查明文 DNS 或引导泄漏")
    else:
        result.add("WARN", "DNS 模块", "未识别到 nameserver 配置")

    if re.search(r"dns-hijack:\s*\[?\s*[\"']?any:53", text) or re.search(r"^\s*-\s*[\"']?any:53", text, re.MULTILINE):
        result.add("PASS", "DNS 接管", "发现 any:53 DNS 劫持声明；运行态仍需实测")
    else:
        result.add("WARN", "DNS 接管", "未发现 any:53；其他 DNS 捕获方式需人工说明")

    if re.search(r"^\s*ipv6:\s*true\s*$", text, re.MULTILINE | re.IGNORECASE):
        result.add("WARN", "IPv6", "配置启用 IPv6；必须验证双栈出口与 DNS")
    else:
        result.add("INFO", "IPv6", "未发现显式 ipv6: true；不代表操作系统 IPv6 已关闭")

    controller = re.search(r"^external-controller:\s*['\"]?(0\.0\.0\.0|::)", text, re.MULTILINE)
    if controller:
        result.add("WARN", "控制面暴露", "external-controller 绑定非回环地址；确认鉴权和网络访问控制")
    return result


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Heuristic Mihomo/Clash privacy safety lint")
    parser.add_argument("config", help="configuration file to read")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    try:
        path = Path(args.config)
        if path.stat().st_size > 2 * 1024 * 1024:
            raise ValueError("configuration exceeds 2 MiB safety limit")
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"lint error: {exc}", file=sys.stderr)
        return 2
    result = lint_text(text)
    if args.json:
        print(json.dumps({"checks": result.items, "failed": result.failed}, ensure_ascii=False, indent=2))
    else:
        for item in result.items:
            location = f" (line {item['line']})" if "line" in item else ""
            print(f"{item['status']}: {item['name']}{location}: {item['detail']}")
    return 1 if result.failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
