---
name: privacy-fortress
description: 系统审计并加固 Windows、macOS、Linux、Android 和 iOS 的网络隐私与最小信息暴露面。覆盖只读信号盘点、Mihomo/Clash 或 sing-box 网关、TUN 与分流、DoH-over-proxy、DNS/IPv6/WebRTC 泄漏检测、fail-closed  killswitch、浏览器与账号元数据卫生、回退预案和持续巡检。Use when the user asks for privacy hardening, a secure proxy/VPN setup, DNS leak prevention, per-app routing, a network kill switch, WebRTC/IPv6 leak checks, or a repeatable cross-machine privacy baseline. 默认先只读审计；不承诺匿名，不用于绕过执法、付费或服务地区限制。
---

# Privacy Fortress

把分散的网络与设备信号整理成“可观察、可验证、可回退”的隐私基线。优先减少不必要暴露，而不是伪造身份或追求不可验证的“绝对匿名”。

## 不可省略的安全门

1. **先定义威胁模型**：确认要减少的是真实公网 IP、DNS 历史、WebRTC、账号关联、应用权限，还是元数据暴露；不同目标不能互相替代。
2. **先只读**：首次运行只采集现状，不改 DNS、路由、防火墙、注册表、系统服务或浏览器策略。
3. **修改需明确授权**：列出变更、影响、所需权限、验收和回退，得到用户同意后才执行。不得把“安装 skill”视为修改系统的授权。
4. **回退先于变更**：保存配置副本，准备能独立运行的回退步骤；可能断网时提供超时回退或本地恢复入口。
5. **fail-closed 要实测**：关键应用应在“代理正常”和“代理停止”两种状态各测一次。只写规则不算验收。
6. **不破坏可用性**：不默认启用全机 DENY OUT，不叠加多个 TUN/防火墙/DNS 控制器，不为了隐私分数破坏工作、急救、系统更新或网络认证。
7. **证据分级**：区分实测、配置推断和未知。检测站不可达是 WARN，不是防护成功。
8. **最小化报告**：报告不收集 MachineGuid、序列号、Cookie、账号、完整本地路径、代理凭据或邻近 Wi-Fi 名称。

## 选择实施范围

- 只需了解现状：运行离线审计，输出信号台账，不进入施工。
- 需要统一出口与 DNS：读 `references/gateway.md` 和 `references/dns.md`。
- 需要防止代理退出后裸连：读对应平台指南与 `references/verification.md`；Windows 可使用参数化 killswitch 脚本。
- 需要浏览器防泄漏：读 `references/browsers.md`，不要把语言/时区伪装当作匿名化。
- 需要移动端配置：读 `references/mobile.md`，遵守 Android/iOS 的 VPN 生命周期边界。
- 需要 macOS/Linux：读 `references/macos-linux.md`，先生成适配方案，不照搬 Windows 命令。
- 需要账号、Git、文件或 Agent 上下文卫生：读 `references/metadata.md`。

## 标准工作流

### Phase 0：建立边界与只读基线

1. 确认操作系统、网络所有权、可用恢复方式、关键应用和不能中断的服务。
2. 复制 `assets/baseline.example.json` 为用户自己的基线；只填确实需要比较的字段。
3. 从本 skill 目录运行离线审计：

```bash
python scripts/privacy_audit.py --baseline /path/to/baseline.json --output ./privacy-reports
```

4. 用户明确允许向公共检测端点发送请求后，再加 `--online`。在线检测会暴露当前出口 IP，这是检测目的的一部分，不是无副作用操作。
5. 按 `references/methodology.md` 建“信号 → 当前证据 → 目标 → 控制 → 验证 → 残余”的台账。

### Phase 1：设计单所有者网络架构

1. 选择现有可信 VPN，或 Mihomo/Clash、sing-box 一类用户可控网关；不要同时让多个组件争夺 TUN、DNS 或防火墙。
2. 先保证节点和本地恢复可用，再启用 TUN、系统代理或平台 VPN。
3. 默认路由必须明确；任何 DIRECT 例外都记录用途和暴露面。
4. DNS 采用经过代理的加密上游，处理引导解析与回环依赖；不要把“写了 DoH”当作“没有泄漏”。
5. 对示例配置先运行静态检查，再用对应核心的官方 `check`/`-t` 功能验证：

```bash
python scripts/lint_gateway.py /path/to/config.yaml
```

### Phase 2：小范围实施与回退演练

1. 先覆盖一个测试浏览器或非关键应用，再扩展到全机。
2. Windows 防火墙 killswitch 使用外部 JSON 配置，不编辑脚本源码：

```powershell
powershell -File scripts/killswitch.ps1 -Action Plan -ConfigPath assets/killswitch-targets.example.json
powershell -File scripts/killswitch.ps1 -Action Apply -ConfigPath /path/to/targets.json
powershell -File scripts/killswitch.ps1 -Action Rollback -ConfigPath /path/to/targets.json
```

3. `Plan` 不需要管理员；`Apply` 与 `Rollback` 需要管理员。示例中的程序路径是占位符，必须替换。
4. 其他平台只按对应指南生成可审查命令，不声称该 PowerShell 脚本跨平台。
5. 先实际执行一次 Rollback，确认恢复路径有效，再继续扩大范围。

### Phase 3：端到端验收

按 `references/verification.md` 至少验证：

- 目标应用出口与预期一致，非目标例外符合台账；
- DNS 解析器没有本地运营者或非预期上游；
- IPv6 与 WebRTC 要么受控，要么明确记录残余；
- 网关/TUN 停止后，受保护应用失败关闭而非直连；
- 局域网、认证页、系统更新和关键应用仍按设计工作；
- 重启、网络切换、客户端升级后重新验证，不以一次 PASS 永久外推。

### Phase 4：持续治理

- 把审计脚本交给系统任务或 Agent 定时任务；在线检查频率保持适度。
- 每次节点、规则、VPN 客户端、操作系统或浏览器升级后重跑基线。
- FAIL 优先恢复网络，再定位隐私问题；WARN 不得包装成 PASS。
- 新发现的能力边界记入 `references/capability-gaps.md` 对应类别的用户台账副本，不修改公共模板冒充本地事实。

## 资源导航

| 资源 | 何时读取/使用 |
|---|---|
| `references/methodology.md` | 威胁模型、信号分类、证据等级与台账格式 |
| `references/gateway.md` | 单所有者网关、规则顺序、TUN、分流与链式代理 |
| `references/dns.md` | DoH-over-proxy、fake-ip、引导解析、DNS 故障排查 |
| `references/windows.md` | Windows TUN、防火墙、系统与浏览器落地 |
| `references/macos-linux.md` | macOS/Linux 适配路径与平台限制 |
| `references/mobile.md` | Android/iOS 常开 VPN、锁死和权限边界 |
| `references/browsers.md` | WebRTC、DNS、语言、profile 与指纹卫生 |
| `references/metadata.md` | Git、文件、图片、账号与 Agent 上下文元数据 |
| `references/verification.md` | 验收矩阵、在线检测、故障恢复与复检节奏 |
| `references/capability-gaps.md` | 不能承诺的隐私边界 |
| `scripts/privacy_audit.py` | Python 3.9+、纯标准库、跨平台只读审计 |
| `scripts/lint_gateway.py` | Mihomo/Clash 配置的高风险模式静态检查 |
| `scripts/killswitch.ps1` | Windows 参数化防火墙安装、计划与回退 |
| `assets/` | 无凭据、无真实地址的配置示例 |

## 结果表述

最终报告必须包含：已实测项、未测项、变更清单、回退位置、残余暴露和下次复检条件。禁止写“任何应用都无法知道真实位置”“管理员也无法绕过”“已经绝对匿名”。隐私配置只能减少特定信号，不能消除服务商、账号、支付、内容和本地恶意软件带来的关联。
