# 官方文档与检测资源

优先读官方文档确认当前版本语义；第三方检测站只提供当时、该浏览器、该网络路径的观察，不是永久事实源。

## 网关与 DNS

- Mihomo 文档：https://wiki.metacubex.one/ —— 配置、TUN、DNS、规则与配置测试；以实际核心版本为准。
- sing-box 文档：https://sing-box.sagernet.org/configuration/ —— 配置与 `check`。
- Cloudflare trace：https://www.cloudflare.com/cdn-cgi/trace —— 当前请求看到的部分出口元数据。
- ipify：https://api.ipify.org 与 https://api64.ipify.org —— 公共 IPv4/双栈检测端点；调用即会暴露当前出口。

## 桌面平台

- Windows `New-NetFirewallRule`：https://learn.microsoft.com/powershell/module/netsecurity/new-netfirewallrule —— 防火墙参数；MSIX 使用包族时还需回读 ApplicationFilter。
- Chromium `WebRtcIPHandling`：https://chromeenterprise.google/policies/#WebRtcIPHandling —— 策略语义；配置后仍需普通浏览器实测。

## 移动平台

- Android VPN 设置：https://support.google.com/android/answer/9089766 —— Always-on 与“阻止未使用 VPN 的连接”的用户入口；OEM 界面可能不同。
- Apple VPN 路由：https://developer.apple.com/documentation/networkextension/routing-your-vpn-network-traffic —— `includeAllNetworks`、MDM Always-on 与系统例外。
- Apple `includeAllNetworks`：https://developer.apple.com/documentation/networkextension/nepackettunnelnetworksettings/includeallnetworks —— 不得与所有流量绝对覆盖混称。

## 第三方深度检测

- BrowserLeaks DNS：https://browserleaks.com/dns
- BrowserLeaks WebRTC：https://browserleaks.com/webrtc
- ipleak：https://ipleak.net/
- DNS Leak Test：https://www.dnsleaktest.com/

使用前征得用户同意，优先普通浏览器、未登录窗口和最小测试。HTTP 200 只表示站点可达；超时、403、验证码、空列表均记 UNKNOWN/WARN。不要把“住宅/欺诈/人机评分”当作事实或 anonymity 证明。

## Skill 安装器

- `skills` CLI 官方命令文档：https://github.com/vercel-labs/skills/blob/main/docs/commands.md —— 直接 ZIP 下载、安装范围、lock 和更新行为。
