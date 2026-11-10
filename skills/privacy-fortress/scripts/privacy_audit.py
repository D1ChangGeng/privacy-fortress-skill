#!/usr/bin/env python3
"""Read-only, standard-library privacy baseline audit.

Offline by default. --online explicitly enables requests to public IP/metadata
endpoints. Reports intentionally omit machine GUIDs, usernames, local paths,
proxy credentials, Wi-Fi names, and environment variable values.
"""
from __future__ import annotations

import argparse
import ipaddress
import json
import locale
import os
import platform
import re
import socket
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

TIMEOUT = 8
USER_AGENT = "privacy-fortress-audit/1.0"
BASELINE_FIELDS = {"expected_ipv4", "expected_country", "expected_timezone", "expected_locale"}


class CheckList:
    def __init__(self) -> None:
        self.items: List[Dict[str, str]] = []

    def add(self, name: str, status: str, detail: str) -> None:
        if status not in {"PASS", "WARN", "FAIL", "INFO", "SKIP"}:
            raise ValueError(status)
        self.items.append({"name": name, "status": status, "detail": detail})

    def summary(self) -> Dict[str, Any]:
        counts = {s: sum(1 for x in self.items if x["status"] == s)
                  for s in ("PASS", "WARN", "FAIL", "INFO", "SKIP")}
        verdict = "FAIL" if counts["FAIL"] else ("WARN" if counts["WARN"] else "PASS")
        return {"verdict": verdict, **counts}


def load_baseline(path: Optional[str]) -> Dict[str, str]:
    if not path:
        return {}
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise ValueError("baseline must be a JSON object")
    unknown = sorted(set(data) - BASELINE_FIELDS)
    if unknown:
        raise ValueError("unknown baseline fields: " + ", ".join(unknown))
    result: Dict[str, str] = {}
    for key, value in data.items():
        if value is None or value == "":
            continue
        if not isinstance(value, str):
            raise ValueError(f"{key} must be a string")
        result[key] = value.strip()
    if "expected_ipv4" in result:
        address = ipaddress.ip_address(result["expected_ipv4"])
        if address.version != 4:
            raise ValueError("expected_ipv4 must be an IPv4 address")
    if "expected_country" in result:
        country = result["expected_country"].upper()
        if not re.fullmatch(r"[A-Z]{2}", country):
            raise ValueError("expected_country must be an ISO-style two-letter code")
        result["expected_country"] = country
    return result


def run_command(command: List[str], timeout: int = 8) -> str:
    completed = subprocess.run(
        command, capture_output=True, text=True, timeout=timeout,
        errors="replace", check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"command exited {completed.returncode}")
    return completed.stdout


def current_timezone() -> str:
    if os.name == "nt":
        try:
            return run_command(["tzutil", "/g"]).strip() or "unknown"
        except Exception:
            pass
    tz_env = os.environ.get("TZ")
    if tz_env:
        return tz_env
    try:
        localtime = Path("/etc/localtime")
        if localtime.is_symlink():
            match = re.search(r"/zoneinfo/(.+)$", str(localtime.readlink()))
            if match:
                return match.group(1)
        timezone_file = Path("/etc/timezone")
        if timezone_file.is_file():
            return timezone_file.read_text(encoding="utf-8").strip()
    except OSError:
        pass
    return "/".join(x for x in time.tzname if x) or "unknown"


def current_locale() -> str:
    try:
        value = locale.getlocale()[0]
    except (ValueError, TypeError):
        value = None
    return value or "unknown"


def compare_baseline(checks: CheckList, baseline: Dict[str, str]) -> None:
    observed_tz = current_timezone()
    observed_locale = current_locale()
    for field, observed, label in (
        ("expected_timezone", observed_tz, "系统时区"),
        ("expected_locale", observed_locale, "系统区域格式"),
    ):
        expected = baseline.get(field)
        if not expected:
            checks.add(label, "INFO", f"当前={observed}；未配置基线，仅记录")
        else:
            checks.add(label, "PASS" if observed == expected else "FAIL",
                       f"当前={observed}；基线={expected}")


def inspect_proxy_environment(checks: CheckList) -> None:
    names = ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "NO_PROXY")
    present = [name for name in names if os.environ.get(name) or os.environ.get(name.lower())]
    checks.add("代理环境变量", "INFO",
               "已设置=" + (", ".join(present) if present else "无") + "；不记录变量值")


def inspect_dns_configuration(checks: CheckList) -> None:
    servers: List[str] = []
    try:
        if os.name == "nt":
            out = run_command([
                "powershell", "-NoProfile", "-Command",
                "Get-DnsClientServerAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue | "
                "Select-Object -ExpandProperty ServerAddresses",
            ])
            servers = re.findall(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", out)
        elif sys.platform == "darwin":
            out = run_command(["scutil", "--dns"])
            servers = re.findall(r"nameserver\[\d+\]\s*:\s*(\S+)", out)
        else:
            text = Path("/etc/resolv.conf").read_text(encoding="utf-8", errors="replace")
            servers = re.findall(r"^\s*nameserver\s+(\S+)", text, re.MULTILINE)
        unique = list(dict.fromkeys(servers))
        loopback = sum(1 for server in unique if server.startswith("127.") or server == "::1")
        checks.add("DNS 配置", "INFO",
                   f"发现 {len(unique)} 个系统 DNS 地址，其中 {loopback} 个为回环；实际递归解析器需在线深度测试")
    except Exception as exc:
        checks.add("DNS 配置", "WARN", f"只读采集失败={type(exc).__name__}")


def inspect_tunnel_hint(checks: CheckList) -> None:
    keywords = re.compile(r"tun|tap|utun|wg\d*|wireguard|openvpn|ppp|mihomo|clash|sing.?box|meta", re.I)
    try:
        if os.name == "nt":
            out = run_command([
                "powershell", "-NoProfile", "-Command",
                "Get-NetAdapter -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Name",
            ])
        elif sys.platform == "darwin":
            out = run_command(["ifconfig", "-l"])
        else:
            out = run_command(["ip", "-brief", "link"])
        found = sorted({match.group(0) for match in keywords.finditer(out)}, key=str.lower)
        checks.add("隧道接口线索", "INFO",
                   "发现常见隧道关键词=" + (", ".join(found) if found else "无") +
                   "；接口名不能证明默认路由或应用已受控")
    except Exception as exc:
        checks.add("隧道接口线索", "WARN", f"只读采集失败={type(exc).__name__}")


def http_get(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
        return response.read(65536).decode("utf-8", "replace").strip()


def online_checks(checks: CheckList, baseline: Dict[str, str]) -> None:
    observed_ip: Optional[str] = None
    try:
        candidate = http_get("https://api.ipify.org")
        address = ipaddress.ip_address(candidate)
        if address.version != 4:
            raise ValueError("IPv4 endpoint returned non-IPv4")
        observed_ip = candidate
        expected = baseline.get("expected_ipv4")
        if expected:
            checks.add("公网 IPv4", "PASS" if candidate == expected else "FAIL",
                       f"实测={candidate}；基线={expected}")
        else:
            checks.add("公网 IPv4", "INFO", f"实测={candidate}；未配置基线，仅记录")
    except Exception as exc:
        checks.add("公网 IPv4", "WARN", f"在线采集失败={type(exc).__name__}")

    try:
        trace = http_get("https://www.cloudflare.com/cdn-cgi/trace")
        values = dict(line.split("=", 1) for line in trace.splitlines() if "=" in line)
        country = values.get("loc", "unknown")
        trace_ip = values.get("ip", "unknown")
        expected_country = baseline.get("expected_country")
        status = "INFO"
        if expected_country:
            status = "PASS" if country == expected_country else "FAIL"
        checks.add("Cloudflare 国家信号", status,
                   f"loc={country}；ip={trace_ip}；基线={expected_country or '未配置'}")
    except Exception as exc:
        checks.add("Cloudflare 国家信号", "WARN", f"在线采集失败={type(exc).__name__}")

    try:
        candidate = http_get("https://api64.ipify.org")
        address = ipaddress.ip_address(candidate)
        if address.version == 6:
            checks.add("IPv6 出口", "WARN", "检测到 IPv6 出口；需确认它经过同一受控路径")
        else:
            checks.add("IPv6 出口", "INFO", "双栈端点返回 IPv4；不能据此证明所有应用无 IPv6")
    except Exception as exc:
        checks.add("IPv6 出口", "INFO", f"双栈采集不可用={type(exc).__name__}；需人工复核")

    if observed_ip:
        checks.add("出口一致性", "INFO", "公共端点只代表本脚本网络路径；目标应用须单独验收")


def markdown_escape(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def render_markdown(report: Dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# Privacy Fortress 只读审计", "",
        f"- 时间：{report['generated_at']}",
        f"- 模式：{'在线（已显式授权）' if report['online'] else '离线'}",
        f"- 总判定：**{summary['verdict']}**",
        f"- PASS={summary['PASS']}，WARN={summary['WARN']}，FAIL={summary['FAIL']}，INFO={summary['INFO']}，SKIP={summary['SKIP']}", "",
        "| 检查项 | 状态 | 详情 |", "|---|---|---|",
    ]
    for item in report["checks"]:
        lines.append("| {name} | {status} | {detail} |".format(
            **{key: markdown_escape(value) for key, value in item.items()}))
    lines += ["", "## 人工复核", ""]
    lines += [f"- {item}" for item in report["manual_review"]]
    lines += ["", "本报告不证明匿名，也不覆盖未运行的应用、原生设备指纹或账号侧数据。", ""]
    return "\n".join(lines)


def build_report(online: bool, baseline: Dict[str, str]) -> Dict[str, Any]:
    checks = CheckList()
    checks.add("运行平台", "INFO", f"{platform.system()} {platform.release()}；Python {platform.python_version()}")
    compare_baseline(checks, baseline)
    inspect_proxy_environment(checks)
    inspect_dns_configuration(checks)
    inspect_tunnel_hint(checks)
    checks.add("WebRTC", "SKIP", "脚本不代替普通浏览器 WebRTC 候选测试")
    checks.add("DNS 深度泄漏", "SKIP", "需用支持深度测试的网页观察实际递归解析器")
    if online:
        online_checks(checks, baseline)
    else:
        checks.add("公网出口", "SKIP", "默认不联网；显式添加 --online 后检测")
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "online": online,
        "checks": checks.items,
        "summary": checks.summary(),
        "manual_review": [
            "普通浏览器 DNS 深度测试与 WebRTC 候选",
            "目标应用出口与代理停止后的 fail-closed 双状态测试",
            "局域网、认证页、系统更新和关键工作应用可用性",
            "重启、换网、VPN/浏览器升级后的漂移复检",
        ],
    }


def write_report(report: Dict[str, Any], output_dir: str) -> Dict[str, str]:
    directory = Path(output_dir).expanduser().resolve()
    directory.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    json_path = directory / f"privacy-audit-{stamp}.json"
    md_path = directory / f"privacy-audit-{stamp}.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    return {"json": str(json_path), "markdown": str(md_path)}


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Read-only privacy baseline audit; offline by default")
    parser.add_argument("--online", action="store_true", help="explicitly contact public IP/metadata endpoints")
    parser.add_argument("--baseline", help="JSON file with optional expected_* fields")
    parser.add_argument("--output", default="./privacy-reports", help="local report directory")
    parser.add_argument("--fail-on-warn", action="store_true", help="return exit code 2 for WARN as well as FAIL")
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    try:
        baseline = load_baseline(args.baseline)
        report = build_report(args.online, baseline)
        paths = write_report(report, args.output)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"audit error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"summary": report["summary"], "reports": paths}, ensure_ascii=False, indent=2))
    verdict = report["summary"]["verdict"]
    return 2 if verdict == "FAIL" or (args.fail_on_warn and verdict == "WARN") else 0


if __name__ == "__main__":
    raise SystemExit(main())
