# 使用者防护地图：30 项是否都已回答

这份地图覆盖当前方案的全部防护类别，但“文档包含”不等于“你的机器已配置”。机器事实以 `scripts/coverage_audit.py` 校验的用户台账和实际测试为准。

## 1. 出口、捕获与规则

| 你能得到什么 | 对应控制项 | 怎样才算有证据 |
|---|---|---|
| 敏感应用不遵守系统代理时也进入唯一受控网关 | `network.capture`、`network.exit` | 默认路由/TUN 回读、单实例与端口检查、目标应用出口实测 |
| 未命中流量不会意外直连 | `network.default_route` | 最终 MATCH/default 为代理或拒绝，官方核心校验+联网测试 |
| 规则按预期首命中，探测域不会借 DIRECT 旁路 | `network.rule_order` | REJECT→进程→域名→私网/分类→UDP→MATCH 的逐条 diff 和命中日志 |
| 每条真实出口直连都是有意选择 | `network.direct_exceptions` | 所有者、用途、暴露面、最近验证、零命中清理记录 |

共享 `node/python/java` 等运行时不能按名字获得高信任 DIRECT。进程 DIRECT 同时覆盖 helper、更新器和内嵌 SDK；GeoSite/GeoIP 只是名单推断，不是安全边界。

## 2. DNS、IPv6、UDP 与 WebRTC

| 你能得到什么 | 对应控制项 | 怎样才算有证据 |
|---|---|---|
| 敏感 DNS 查询不经本地明文 UDP/53 | `dns.encrypted_path`、`dns.hijack_fakeip` | DoH-over-proxy 路由回读、TUN 劫持/fake-ip、深度解析器测试 |
| DoH 自身和节点恢复不会形成引导回环或旁路 | `dns.bootstrap_policy` | IP 字面量/受控 bootstrap、节点 nameserver、respect-rules 等等价配置审查 |
| 国内/内网例外的暴露是知情选择 | `dns.local_exceptions`、`upstream.visibility` | split-DNS 范围、上游可见性与代答残余记录 |
| 浏览器没有第二条未审计 DNS 通道 | `dns.browser` | Secure DNS 设置回读+普通浏览器深度测试 |
| IPv6/UDP/WebRTC 不绕回真实出口 | `network.ipv6`、`network.udp_quic`、`browser.webrtc` | v4/v6、UDP/QUIC、普通浏览器候选、代理停止双状态测试 |

只写 `ipv6: false` 或关闭 AAAA 不等于全机 IPv6 已闭合。WebRTC 策略也不能替代网络层 UDP 控制。

## 3. 防火墙、浏览器与系统软件

| 你能得到什么 | 对应控制项 | 主要边界 |
|---|---|---|
| 代理退出时关键应用宁断不漏 | `firewall.desktop` | exe 与 MSIX 包族分别处理；共享运行时、helper 和未列入应用需单独说明 |
| 境外与 domestic 使用场景不互相串号 | `browser.separation` | 直连浏览器是有意的真实出口面，不登录隔离账号 |
| 手机可只作远程显示/输入，网页在受控桌面执行 | `browser.remote_control` | 远控供应商、剪贴板、账号与桌面指纹仍是独立残余 |
| 系统声明、遥测、自启和远控被纳入审计 | `system.region`、`system.telemetry`、`remote_access` | 不默认改 MachineGuid/安装语言；不承诺本地采集面等于未上传 |

## 4. Android：双场景与分应用规则

- `android.vpn`：一个活动 VPN；回读 Always-on、锁死和真实隧道状态。切换常开客户端后，部分设备需要重启并重新验收。
- `android.apps`：`proxy_packages` 与 `direct_packages` 互斥，逐个核对包名、UID、系统锁死白名单和客户端保存结果。
- 代理浏览器处理境外服务，直连浏览器处理明确的 domestic 服务。某应用一旦绕过 VPN，不能再让同一 VPN 按域名把其部分流量拉回。
- `android.permissions`：定位、通知、媒体、通讯录、附近设备、后台和 USB 调试逐项复核；撤销失败必须保留为未闭合项。
- 新增代理网址优先在代理浏览器打开，不为每个网站增加 DIRECT；只有代理应用内部域名确需特殊出口时才改网关规则。
- Root、解锁和刷写不是默认步骤。

## 5. iOS / iPadOS：全代理专用机与普通设备要区分

- `ios.vpn`：检查 On Demand、默认无 DIRECT、UDP 策略和重启恢复；手动 Stop 可能关闭 On Demand，异常时先关闭 Wi-Fi/蜂窝数据。
- `ios.system_services`：普通客户端的 On Demand 不等于 MDM 监督设备的 Always-on VPN。未启用并验证 `includeAllNetworks` 时，不承诺所有 Apple 服务经过隧道；即使启用也仍有平台例外。
- `ios.permissions`：App 隐私报告、定位/跟踪/照片/蓝牙/本地网络与原生应用设备信号需要单独检查。
- 专用全代理设备不为 domestic 应用临时增加 DIRECT；需要直连时使用另一台明确角色的设备。

## 6. 上游、身份与持续运维

- `upstream.visibility`：分别记录接入归因、五元组、流量时序、明文 DNS、DPI/TLS、DIRECT 与主动探测；加密不等于上游什么也不知道。
- `identity.metadata`：账号、支付/KYC、Git、文件/图片、日志、Agent 上下文和公开附件不是网络层能自动消除的。
- `operations.rollback`：备份、独立回退、必要的超时自愈和实际回退演练。
- `operations.lifecycle`：重启、换网、升级、配置重建、端口和应用路径/包族漂移后的复检。
- `operations.monitoring`：日常轻量巡检+定期普通浏览器深度测试+变更台账；WARN/UNKNOWN 不能包装成 PASS。

完整、机器可校验的问题清单在 `assets/coverage-controls.json`。Agent 必须在开始和交付时使用它，不得自行删减“看起来不重要”的行。
