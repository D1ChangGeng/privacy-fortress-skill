# Android 与 iOS / iPadOS 实施指南

移动端使用操作系统提供的 VPN 生命周期、分应用和权限能力。桌面 PowerShell 防火墙脚本只用于 Windows。网络出口、账号、SIM、设备、权限和内容分别验收。

## 1. Android：先回读，再逐批配置

### 只读基线

在用户明确连接并授权 ADB 后，先确认设备序列号、当前 VPN 包名、锁死和实际隧道状态：

```bash
adb shell settings get secure always_on_vpn_app
adb shell settings get secure always_on_vpn_lockdown
adb shell settings get secure always_on_vpn_lockdown_whitelist
adb shell dumpsys vpn
```

同时记录 VPN 客户端版本、分应用清单、当前代理/直连浏览器和关键 domestic 应用。`dumpsys` 输出可能包含设备或网络信息，只提取必要字段。

### Always-on 与锁死

系统设置中的目标是：

1. 一个 VPN 所有者；
2. “始终开启 VPN”；
3. 需要故障关闭时开启“阻止未使用 VPN 的连接”；
4. 重启、换网、订阅失效后仍按设计恢复或断开。

写入前展示旧值、目标包名、完整命令、锁死白名单、回退和是否需要重启，并取得独立确认。命令模板：

```bash
adb shell settings put secure always_on_vpn_app <VPN_PACKAGE>
adb shell settings put secure always_on_vpn_lockdown 1
```

部分设备或客户端在更换 Always-on 所有者后需要重启，快捷磁贴和另一个客户端的“已连接”文字不能替代系统真实状态。写入后再次回读，并实测重启后的 VPN、出口、DNS 和关键应用。

### 分应用清单与 UID

维护两个互斥数组，保存到用户自己的文件：

```json
{
  "proxy_packages": ["com.example.foreign"],
  "direct_packages": ["com.example.domestic"]
}
```

- `proxy_packages`：进入受控 VPN 的应用；
- `direct_packages`：明确绕过 VPN 的应用，目标服务可看到真实出口；
- 同一包名只出现在一侧；新增应用先确定角色，再同步客户端访问控制与系统锁死白名单；
- 客户端界面“已勾选”后还要确认真实保存、VPN 重连和应用 UID；系统组件不在客户端列表时单独记录；
- 清单同步可能耗时，给用户可恢复的断点，完成后逐项核验而非只看总数。

### 浏览器与新增网址

代理浏览器处理境外/隔离账号，直连浏览器处理明确的 domestic 服务。应用绕过 VPN 后，同一 VPN 无法再把其中部分域名拉回，因此代理网址直接放在 VPN 内浏览器。

只有代理应用内部的域名确需特殊出口、拦截或修正时才改网关规则：修改事实源→同步生成器→官方核心检查→导入→回读→目标应用验收。订阅和自定义规则分离，升级后 diff 实际配置。

### 权限与 ADB 卫生

按最小权限审查定位、精确位置、通知监听、媒体、通讯录、附近设备、后台、剪贴板和输入法。成功撤销与系统仍保留的权限分开记录；`pm revoke` 或 App Ops 命令未改变实际状态时保持 UNKNOWN/FAIL。

日常关闭 USB 调试；运维结束后撤销不再需要的电脑授权。Root、bootloader 解锁、刷写和反检测模块属于独立高风险项目，需要精确官方镜像、恢复链和单独授权。

## 2. iOS / iPadOS：区分三种能力

| 能力 | 适用范围 | 验收重点 |
|---|---|---|
| 普通 VPN + On Demand | 普通用户客户端支持的自动连接 | 重启恢复、Stop 后行为、默认 DIRECT、UDP、DNS |
| `includeAllNetworks` | 客户端/系统支持时扩大系统流量覆盖 | 平台仍有 DHCP、认证页、部分蜂窝和配套设备例外 |
| MDM Always-on VPN | 受监督设备与描述文件 | 启动和断开时丢包语义、应用/服务例外、MDM 所有权 |

普通客户端的 On Demand 不等于 MDM Always-on。手动 Stop 可能同时关闭 On Demand；需要确保不联网时先关闭 Wi-Fi/蜂窝数据，再排查。

配置审查：

1. 默认路由指向受控出口，节点失败不会 DIRECT 回退；
2. UDP 按链路能力受控或拒绝，IPv6 与 DNS 走同一威胁模型；
3. 未启用/验证 `includeAllNetworks` 时，将 Apple 系统服务覆盖标 UNKNOWN 或 RESIDUAL；
4. Safari 与原生应用分别记录设备型号、地区、语言、运营商和权限信号；
5. 开启 App 隐私报告，新增应用后复查定位、跟踪、照片、通讯录、蓝牙、本地网络与异常域名。

远程导入配置使用本机限时、限次数、随机路径通道；完成后立即停止服务并回读端口。含节点凭据的配置留在本机，由用户手动导入。

## 3. 移动端验收清单

- 普通浏览器公网 IPv4、DNS 深度测试、WebRTC、IPv6；
- 关键原生应用实际出口/区域表现与权限；
- 重启、换 Wi-Fi、蜂窝切换、订阅失效和客户端升级；
- Android Always-on/锁死/UID/包清单，iOS On Demand/Stop/系统服务例外；
- 新增应用后的分应用规则与 App 权限；
- 照片 EXIF、剪贴板、通知、账号、SIM/eSIM 和支付各自作为独立信号记录。
