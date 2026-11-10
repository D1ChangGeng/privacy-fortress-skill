# Privacy Fortress Skill

给 AI Agent 使用的跨平台网络隐私加固技能：把代理网关、规则、DNS、IPv6、WebRTC、防火墙、浏览器、Android／iOS、系统信号和持续巡检整理成一套**先只读、逐批确认、可回退、可验收**的工作流。

> 目标是减少不必要的信息暴露，不是承诺匿名。Skill 不是 VPN 服务，不提供节点，也不会因为安装就获得修改系统的授权。

## 1. 作为使用者，它能帮我做到什么

你不需要先懂 Mihomo、sing-box、防火墙或 ADB。你可以让 Agent 先盘点，再决定是否施工。

| 你希望达到的结果 | Skill 会帮助 Agent 完成什么 | 不能缺少的验收 |
|---|---|---|
| 境外／敏感应用只见受控出口 | 设计唯一 VPN／网关、TUN 与系统代理捕获、链式出口和默认路由 | 目标应用公网 IPv4／ASN 实测，代理停止时不能意外直连 |
| 分流规则没有旁路 | 审查 REJECT、进程 DIRECT／代理、域名、私网／GeoSite／GeoIP、UDP 和最终 MATCH 的顺序 | 官方核心校验、命中日志、每条 DIRECT 的用途与暴露面 |
| DNS 不被本地网络旁观或投毒 | 配置 DoH-over-proxy、TUN DNS 劫持、fake-ip、引导解析和最小 split-DNS | 普通浏览器深度 DNS 测试，确认 DoH 本身也经代理 |
| IPv6／UDP／WebRTC 不绕回真实网络 | 明确 v6、QUIC、STUN 的受控或拒绝策略，收紧浏览器 WebRTC | 普通浏览器候选、v4／v6、代理在线／停止双状态测试 |
| 关键应用代理退出时宁断不漏 | Windows exe 与 MSIX 包族防火墙 killswitch，支持 Plan／Apply／Rollback | 在线可用、停止断网、Rollback 恢复、升级后回读 |
| 浏览器和系统信号不互相“拆台” | 代理／直连浏览器分工、独立 profile、DNS／语言／时区／遥测／远控审查 | 不用网页结果外推原生应用；账号、硬件和行为残余单列 |
| Android 有完整的双场景规则 | Always-on VPN、锁死、代理包／直连包、UID、浏览器分工、权限与 ADB 卫生 | 回读实际 VPN 状态，重启／换网／新增应用后复验 |
| iPhone／iPad 不迷信“VPN 已连接” | On Demand、无 DIRECT、UDP、Stop 风险、App 隐私报告与系统服务边界 | 重启恢复、DNS／WebRTC／IPv6、明确 `includeAllNetworks` 残余 |
| 知道上游和账号仍然能看到什么 | 接入归因、五元组、流量时序、明文例外、账号／Git／图片／Agent 元数据审查 | 每个观察者单独记录，不写“加密后无人可见” |
| 改坏能恢复，升级后能发现漂移 | 备份、回退、必要的超时自愈、覆盖台账、日常巡检与升级复检 | 实际回退演练，WARN／UNKNOWN 不包装成 PASS |

完整清单是 **30 个必答控制项**，见 `skills/privacy-fortress/references/coverage.md` 和 `assets/coverage-controls.json`。这意味着它覆盖当前方案的全部防护**类别**，不表示任何机器安装后就自动达到全部防护。

## 2. 安装：只下载 Skill，不克隆仓库

需要 Node.js 22.20+。下面的地址是 GitHub Release 中的 `privacy-fortress.zip`，其中只有 Skill 本体，不包含本仓库的测试、CI、开发文档或 `.git` 历史。

```bash
npx skills add https://github.com/D1ChangGeng/privacy-fortress-skill/releases/latest/download/privacy-fortress.zip --skill privacy-fortress
```

全局安装：

```bash
npx skills add https://github.com/D1ChangGeng/privacy-fortress-skill/releases/latest/download/privacy-fortress.zip --skill privacy-fortress -g
```

Windows 或不支持符号链接的环境可追加 `--copy`。需要可复现版本时，把 URL 中的 `latest` 换成具体标签，例如 `v1.1.0`。

这里 `npx` 会按自身机制取得 `skills` 安装器，但 **Skill 内容通过 HTTPS ZIP 直链下载，不执行 Git clone**。项目级安装会生成 `.agents/skills/privacy-fortress` 和所选 Agent 的链接，可用 `npx skills list --json` 检查。skills CLI 1.7.6 的直链项目安装可能显示 `untracked`，更新时重新执行同一直链命令；生成 lock 的版本应记录 `sourceType: "download"`。

也保留 `.skill` 附件供支持该格式的客户端使用。普通使用与更新都沿用上面的 ZIP 直链命令，下载内容始终是 Skill 本体。

## 3. 第一次怎么用

安装后可以直接对 Agent 说：

### 只审计，不改机器

> 用 privacy-fortress 做离线只读审计，列出 30 项防护台账。不要联网检测，不要修改任何设置。

### 先给方案和回退，不施工

> 用 privacy-fortress 为这台电脑设计唯一网关、DoH-over-proxy、IPv6／WebRTC 防护和关键应用 fail-closed。只生成 Plan、配置草案与 Rollback，等我逐批确认。

### 逐批实际配置

> 按 privacy-fortress 帮我配置网络环境。先只读审计；每批变更前列出精确命令、权限、影响、备份、回退和验收，得到我的明确确认后再执行。

### Android

> 用 privacy-fortress 审计这台 Android 的 Always-on VPN、锁死、代理包／直连包和浏览器分工。先只读回读；任何 ADB 写入、清单变更或重启都单独问我。

### iPhone／iPad

> 用 privacy-fortress 检查 iOS 的 On Demand、默认 DIRECT、Stop 风险、DNS／WebRTC／IPv6 和 App 权限。区分普通 VPN 与 MDM Always-on，不承诺未测的系统服务覆盖。

### 新增应用或网址

> 按 privacy-fortress 的规则变更清单评估这个新应用：它会继承哪条进程规则、helper 是否同路、是否需要 DIRECT、会影响哪些 DNS／UDP／WebRTC 防护？先给结论，不改规则。

## 4. Agent 应该怎样与你交互

标准过程是：

1. **解释边界**：说明能减少哪些暴露，不承诺匿名；确认设备、网络所有权、关键应用和恢复入口。
2. **离线只读**：运行审计，建立 30 项 UNKNOWN 台账；不读凭据、Cookie、私人文件或无关环境变量。
3. **在线检测另问**：列出将联系的公共 IP／DNS／WebRTC 端点，说明它们会看到当前出口。
4. **给架构选择**：唯一网关、规则、DNS、fail-closed、浏览器和移动端分别说明；你可以选择只审计或只生成 Plan。
5. **逐批确认**：每批变更都展示确认卡，不能用一次“配置好”授权所有后续操作。
6. **回读和双状态测试**：写入不算成功；验证实际生效、代理在线、代理停止和 Rollback。
7. **交付覆盖报告**：明确 TESTED／CONFIG／UNKNOWN／RESIDUAL／NOT_APPLICABLE，未闭环项不能隐藏。

一批高风险变更前，你应该看到类似内容：

```text
批次：BATCH-02／关键应用防火墙
变更：精确规则、程序路径或 MSIX 包族
权限：管理员
影响：代理停止时这些应用会断网；局域网是否放行已列明
备份与回退：对应文件、命令和预计恢复时间
验收：代理在线可用；代理停止断网；Rollback 后恢复
请回复“确认执行 BATCH-02”后才会执行。
```

如果 Agent 没有给回退、把配置存在当成已生效、把检测站超时当成通过，或者要求你把订阅秘密贴进聊天，应让它停止并按 `references/agent-protocol.md` 重新执行。

## 5. 怎样确认“没有漏项”

让 Agent 创建一份你自己的台账：

```bash
python scripts/coverage_audit.py --init ./privacy-reports/coverage.json
python scripts/coverage_audit.py --list
```

完成审计和测试后：

```bash
python scripts/coverage_audit.py \
  --ledger ./privacy-reports/coverage.json \
  --output ./privacy-reports/coverage.md \
  --require-tested
```

判定口径：

- `TESTED`：当前设备、当前网络实际测过，必须有日期和证据；
- `CONFIG`：只写好配置，尚未端到端验收，不能算完成；
- `UNKNOWN`：未测、不可达或平台不可见；
- `RESIDUAL`：明确接受的残余，必须说明原因；
- `NOT_APPLICABLE`：确实不在范围，必须说明理由。

`--require-tested` 在仍有 CONFIG／UNKNOWN 时返回非零，这是故意的“禁止误报完成”。脚本检查台账完整性，不会把一段文字声明自动变成独立实测。

## 6. Skill 里有哪些资源

| 资源 | 用途 |
|---|---|
| `references/agent-protocol.md` | Agent 授权、提问、确认卡、实施与交付协议 |
| `references/coverage.md` + `assets/coverage-controls.json` | 使用者防护地图与 30 项机器可校验清单 |
| `references/gateway.md` / `dns.md` / `upstream.md` | 网关、规则、DNS 和上游可见性 |
| `references/windows.md` / `macos-linux.md` | 桌面平台实施边界 |
| `references/mobile.md` | Android／iOS 常开、锁死、分应用、权限与生命周期 |
| `references/browsers.md` / `metadata.md` | 浏览器、远控、账号、文件与 Agent 上下文 |
| `references/verification.md` / `resources.md` | 双状态验收、巡检、官方文档和检测端点 |
| `scripts/privacy_audit.py` | Python 3.9+、纯标准库，默认离线的只读信号审计 |
| `scripts/coverage_audit.py` | 创建并校验 30 项防护台账，完全离线 |
| `scripts/lint_gateway.py` | Mihomo／Clash 高风险配置模式检查，不代替官方核心校验 |
| `scripts/killswitch.ps1` | Windows exe／MSIX 防火墙 Plan、Apply、Rollback |
| `assets/` | 无凭据基线、网关和 killswitch 示例 |

## 7. 明确不能承诺什么

- 不能消除代理供应商、目标服务、账号、支付、KYC、内容和行为关联；
- 不能让本地网络完全看不到加密流量、接入归因或活动时段；
- 不能用浏览器检测证明原生应用没有设备、SIM、权限或硬件信号；
- 不能把普通 iOS VPN On Demand 等同于 MDM Always-on；
- 不能防止已控制管理员、内核、恶意驱动或供应链的攻击者；
- 不能仅凭静态 lint 证明 Mihomo／sing-box 配置有效，仍需官方核心校验与联网验收；
- 不默认 Root、刷机、轮换 MachineGuid、修改安装语言或叠加全机 DENY OUT。

## 8. 开发与验证

```bash
python -m unittest discover -s tests -v
python tools/package_skill.py --check
python tools/package_skill.py
```

CI 覆盖 Windows、macOS、Linux。仓库用于开发；普通使用者只需上面的 Release ZIP，不需要克隆本仓库。

## License

MIT，见 `LICENSE`。
