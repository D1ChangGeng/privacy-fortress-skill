# macOS 与 Linux 适配指南

## 1. 不照搬 Windows

Windows 的 `New-NetFirewallRule`、fake-ip 段和进程路径模型不能直接用于 macOS/Linux。先识别当前 VPN 的所有者和系统提供的正式能力，再选择最小实现。

## 2. macOS

优先级：

1. 使用可信 VPN 的 Network Extension，并启用官方提供的 kill switch/on-demand。
2. 需要自定义时选择支持 macOS 的 sing-box/Mihomo 图形或守护进程形态，确认系统扩展/网络权限。
3. 浏览器单独检查 Secure DNS 和 WebRTC。
4. 在“Wi-Fi → 详细信息”检查 DNS 与代理，但不要把界面值当作实际解析器证明。

`pf` 可以做地址级故障关闭，但按进程归因能力有限，规则锚点和系统服务交互复杂。除非用户明确需要且有本地恢复入口，不直接写入全局 PF 配置。优先使用 VPN 官方 kill switch、独立用户/设备或受控网络。

macOS 的 on-demand 规则可能包含系统服务例外；应用流量通过 VPN 不等于所有 Apple 服务都通过。不能把 Stop 后行为未测试的客户端称为 fail-closed。

## 3. Linux

先识别发行版、init 系统、网络管理器和权限模型：

- 桌面 VPN 优先使用 NetworkManager/官方客户端的 kill switch。
- 自建网关可使用 sing-box/Mihomo TUN，配合 systemd 单实例与配置检查。
- `nftables` 可按用户、cgroup、地址和接口设计故障关闭；按进程路径匹配并不可靠。
- 不要把 `ufw deny out all` 或整段 nftables 规则直接复制到未知机器；先确保 SSH、本地管理和 DHCP 恢复路径。
- systemd-resolved、NetworkManager、dnsmasq 和网关不能同时争夺同一 DNS 入口。

容器/独立用户通常比“按可执行文件路径封锁”更可靠，但容器共享宿主机 VPN 时仍需验证实际路由。

## 4. 验收矩阵

至少覆盖：默认路由、DNS 实际解析器、IPv4/IPv6、代理停止、VPN 自动重连、重启、睡眠唤醒、Wi-Fi 切换和关键应用。服务器额外验证 SSH 带外恢复，避免远程把自己锁在门外。
