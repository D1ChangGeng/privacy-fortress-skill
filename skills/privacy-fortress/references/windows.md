# Windows 实施指南

## 1. 推荐层次

1. 一个支持 TUN 的 VPN/网关拥有全机捕获和 DNS。
2. 关键应用使用防火墙 killswitch，代理停止时进入断网状态。
3. 浏览器策略收紧 WebRTC，Secure DNS 与网关保持单一架构。
4. 时区、区域、语言、遥测、自启、输入法和远控按用户目标最小化。

## 2. 防火墙 killswitch

`scripts/killswitch.ps1` 使用外部 JSON。每个目标二选一：

- `program`：精确 exe 路径，适合路径稳定的桌面程序；
- `packageFamilyName`：MSIX/商店应用的稳定包族，减少版本目录漂移。

exe 示例见 `assets/killswitch-program-target.example.json`。MSIX 示例：

```json
{
  "targets": [
    {
      "name": "ExamplePrivateStoreApp",
      "packageFamilyName": "Example.PrivateApp_a1b2c3d4e5f6g",
      "allowLan": true
    }
  ]
}
```

用户可在本机查找实际包族，Agent 只引用需要的应用：

```powershell
Get-AppxPackage -Name <PackageName> | Select-Object Name, PackageFamilyName, InstallLocation
```

默认允许回环与 `198.18.0.0/15` fake-ip，阻止其余 IPv4 和 IPv6 出站。`allowLan: true` 额外允许 RFC1918 局域网，用于认证页或本地服务。其他 fake-ip 段或不同 VPN 架构需要调整脚本前先做独立评审。

```powershell
# 普通终端：参数、路径/包族格式与计划预览
powershell -File scripts/killswitch.ps1 -Action Plan -ConfigPath .\targets.json

# 管理员终端：创建/更新 PF-Killswitch-* 自有规则并回读
powershell -File scripts/killswitch.ps1 -Action Apply -ConfigPath .\targets.json

# 管理员终端：只删除本配置对应规则
powershell -File scripts/killswitch.ps1 -Action Rollback -ConfigPath .\targets.json
```

实施边界：

- 该模板适用于回环代理或对应 fake-ip 段的网关；
- 规则覆盖主程序或包族后，还要盘点独立 helper/updater；
- `node/python/java` 等共享运行时需要受控启动器、独立用户/容器或明确使用纪律，避免影响同机无关程序；
- 新装应用默认进入 UNKNOWN，确认角色后再加入；
- 防火墙规则约束配置层网络路径，高权限恶意组件属于另一类威胁。

## 3. 双状态验收

- 代理在线：目标应用可联网，出口和 DNS 符合基线；
- 代理完全停止：目标应用连接失败，测试过程使用受控时间窗；
- Rollback：规则删除后应用恢复原网络行为；
- 更新后：exe 路径仍存在，MSIX 包族与 `Get-NetFirewallApplicationFilter` 回读一致。

## 4. 系统与软件信号

优先采用低风险、可解释的设置：位置、广告 ID、后台活动、云同步、遥测、自启和不用的 VPN/远控。每项写入后回读并验证关键应用。

时区、区域格式和语言属于一致性信号，用户可以选择与长期使用场景保持一致。MachineGuid、安装语言、主机名和系统区域修改具有授权、激活、更新或软件兼容影响，只在明确收益和恢复方案下单独授权；网页通常读不到全部系统值。

VPN/远控/mesh 客户端采用两种清晰策略：用完即停并恢复手动启动，或让流量进入受控链路。协调服务器账号层可见真实端点的可能性记入 RESIDUAL。

## 5. 进程规则

`PROCESS-NAME` 适合独占且名称稳定的应用；共享运行时过宽。`PROCESS-PATH` 更精确但会随更新漂移。MSIX 防火墙使用包族，网关进程规则仍需按核心支持能力单独验证。每条规则记录 helper、更新器、内嵌浏览器和第三方 SDK 的继承关系。
