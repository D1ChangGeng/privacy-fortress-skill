---
name: privacy-fortress
description: 系统审计并加固 Windows、macOS、Linux、Android 和 iOS 的网络隐私与最小信息暴露面。覆盖 30 项防护台账、Mihomo/Clash 或 sing-box 网关、TUN 与规则顺序、DoH-over-proxy、DNS/IPv6/UDP/WebRTC 泄漏、exe/MSIX fail-closed、浏览器分边、Android Always-on/锁死/分应用、iOS On Demand/includeAllNetworks 边界、上游可见性、回退与巡检。Use when the user asks for privacy hardening, a secure proxy/VPN setup, DNS leak prevention, per-app routing, mobile VPN lockdown, a network kill switch, coverage/gap audits, or repeatable network configuration. 默认先只读；逐批确认变更；不承诺匿名，不用于绕过执法、付费或服务地区限制。
---

# Privacy Fortress

把网络、设备与身份信号整理成“可观察、可验证、可回退”的隐私基线。优先减少不必要暴露，不把安装 Skill、写好配置或网页检测包装成整机完成。

## 开始时必须读取

1. 读 `references/agent-protocol.md`：按权限级别与用户交互，逐批展示变更、备份、回退和验收。
2. 读 `references/coverage.md` 与 `assets/coverage-controls.json`：用同一份 30 项清单开始和交付，不自行删减。
3. 读 `references/methodology.md`：区分 TESTED、CONFIG、UNKNOWN、RESIDUAL，分别描述不同观察者。
4. 仅当前任务需要时再加载对应平台、协议和 `references/resources.md`，避免一次读入全部文档。

## 不可省略的安全门

1. **先定义威胁模型**：分别列出本地网络、代理入口/出口、目标网站、账号服务、同机应用和物理接触者。
2. **先只读**：首次运行不改 DNS、路由、防火墙、注册表、系统服务、浏览器策略或移动 VPN。
3. **修改逐批授权**：安装 Skill、概括性“配置好”和上一批确认都不能代替下一批具体确认。
4. **回退先于变更**：保存配置副本，准备独立回退；可能断网时提供超时自愈或本地恢复入口。
5. **fail-closed 双状态实测**：代理正常与代理停止各测一次；规则存在、进程存在或 HTTP 200 都不算通过。
6. **不破坏可用性**：不默认全机 DENY OUT，不叠加 TUN/DNS/防火墙控制器，不默认 Root、刷机或高风险标识修改。
7. **证据分级**：检测站不可达是 WARN/UNKNOWN；网页结果不能外推到原生应用。
8. **最小化数据**：不收集或回显凭据、Cookie、MachineGuid、序列号、完整路径、Wi-Fi 名称或无关环境变量。

## 标准工作流

### Phase 0：只读基线与覆盖台账

1. 按 Agent 协议询问设备、OS、网络所有权、恢复方式、关键应用、现有 VPN 和不能中断的服务。
2. 解析实际 Skill 根目录，在该目录运行，不假设调用者当前目录：

```bash
python scripts/privacy_audit.py --output ./privacy-reports
python scripts/coverage_audit.py --init ./privacy-reports/coverage.json
python scripts/coverage_audit.py --list
```

3. 用户明确允许公共端点检测后，才给 `privacy_audit.py` 加 `--online`；先说明端点会看到当前出口。
4. 把 30 项初始标为 UNKNOWN。只读结果可以补证据，但不能凭空标 TESTED。

### Phase 1：设计单所有者架构与规则

1. 读 `references/gateway.md`：确定唯一 TUN/VPN 所有者、系统代理关系、单实例、端口和配置事实源。
2. 审查 REJECT、进程 DIRECT/代理、域名、私网/分类、UDP 和最终 MATCH 的首命中顺序。每条 DIRECT 记录用途、所有者与暴露面。
3. 读 `references/dns.md`：设计 DoH-over-proxy、fake-ip、DNS 劫持、引导/节点解析、本地 split-DNS 与浏览器通道。
4. 读 `references/upstream.md`：评估新规则在五元组、时序、明文 DNS、TLS/DPI、DIRECT 和主动探测面上的影响。
5. 对示例配置运行静态检查，再用对应核心的官方 `check`/配置测试；lint 不是 YAML/schema 或运行时验证：

```bash
python scripts/lint_gateway.py /path/to/config.yaml
```

### Phase 2：逐批实施与回退演练

1. 每批使用 `references/agent-protocol.md` 的确认卡；未获对应批次确认则停止。
2. 先覆盖一个测试浏览器或非关键应用，再扩大范围；写入后回读实际生效状态。
3. Windows 读 `references/windows.md`。killswitch 支持 exe 与 MSIX 包族，使用外部 JSON，不改脚本源码：

```powershell
powershell -File scripts/killswitch.ps1 -Action Plan -ConfigPath assets/killswitch-targets.example.json
powershell -File scripts/killswitch.ps1 -Action Apply -ConfigPath /path/to/targets.json
powershell -File scripts/killswitch.ps1 -Action Rollback -ConfigPath /path/to/targets.json
```

4. `Plan` 不需要管理员；`Apply` 与 `Rollback` 需要管理员。先实际演练 Rollback，再扩大范围。
5. macOS/Linux 读 `references/macos-linux.md`；不照搬 Windows 命令，不让远程用户失去带外恢复。
6. Android/iOS 读 `references/mobile.md`；ADB 写入、锁死、清单、重启、On Demand 和系统设置分别确认。

### Phase 3：端到端验收

读 `references/verification.md`，至少验证：

- 目标应用出口、ASN、DNS 和规则命中符合设计，DIRECT 例外没有扩大；
- 实际递归解析器、IPv4/IPv6、UDP/QUIC、普通浏览器 WebRTC 候选；
- 网关/TUN 停止后受保护应用失败关闭，Rollback 恢复；
- 局域网、认证页、系统更新和关键工作应用可用；
- Android 重启/锁死/UID/浏览器分工，iOS On Demand/Stop/系统服务边界；
- 重启、换网、客户端升级、配置重建、端口和应用路径/包族变化后的漂移。

### Phase 4：交付与持续治理

1. 更新用户自己的 coverage JSON，再运行：

```bash
python scripts/coverage_audit.py --ledger ./privacy-reports/coverage.json --output ./privacy-reports/coverage.md --require-tested
```

2. 仍有 CONFIG/UNKNOWN 时明确报告“尚未闭环”；用户可接受有原因的 RESIDUAL/NOT_APPLICABLE，但不能隐瞒。
3. 最终包含已实测、仅配置、未测、残余、变更、备份/回退、在线端点、移动边界和复检条件。
4. 日常轻量巡检与定期普通浏览器深度测试分开；FAIL 先恢复网络，WARN 不包装成 PASS。

## 资源导航

| 资源 | 何时读取/使用 |
|---|---|
| `references/agent-protocol.md` | 每次任务开始、变更确认、回退与最终交付 |
| `references/coverage.md` | 向用户解释 30 项防护范围与移动端/规则要求 |
| `references/methodology.md` | 威胁模型、证据等级与最小数据 |
| `references/gateway.md` | 单所有者、TUN、规则顺序、DIRECT、链式代理 |
| `references/dns.md` | DoH-over-proxy、fake-ip、引导、split-DNS |
| `references/upstream.md` | 上游检测面与规则变更对照 |
| `references/windows.md` | exe/MSIX 防火墙、系统与软件落地 |
| `references/macos-linux.md` | macOS/Linux 平台适配与恢复 |
| `references/mobile.md` | Android/iOS 常开、锁死、分应用、权限与 Stop |
| `references/browsers.md` | WebRTC、浏览器分工、profile 与远程受控浏览器 |
| `references/metadata.md` | 账号、Git、文件、图片与 Agent 上下文 |
| `references/verification.md` | 双状态验收、巡检、故障恢复与复检 |
| `references/resources.md` | 官方文档与第三方检测端点 |
| `references/capability-gaps.md` | 信任、账号、硬件和高权限残余 |
| `scripts/privacy_audit.py` | 默认离线的跨平台只读信号审计 |
| `scripts/coverage_audit.py` | 创建和校验 30 项台账；不主动探测机器 |
| `scripts/lint_gateway.py` | Mihomo/Clash 高风险文本模式检查 |
| `scripts/killswitch.ps1` | Windows exe/MSIX Plan、Apply、Rollback |
| `assets/` | 无凭据基线、30 项控制定义和配置示例 |

禁止写“任何应用都无法知道真实位置”“管理员也无法绕过”“已经绝对匿名”。网络配置不能消除供应商、账号、支付、内容、行为和本地恶意软件带来的关联。
