# Windows 实施指南

## 1. 推荐层次

1. 使用一个支持 TUN 的 VPN/网关拥有全机捕获。
2. 明确 DNS 由该网关或系统 split-DNS 管理，关闭不需要的第二个控制器。
3. 对“代理停止时绝不能直连”的应用添加 Windows 防火墙 killswitch。
4. 用浏览器策略收紧 WebRTC 和不必要的独立 DoH。
5. 收缩位置、广告 ID、后台活动、遥测和不必要自启；逐项验证应用兼容性。

## 2. 防火墙 killswitch

`scripts/killswitch.ps1` 使用外部 JSON：

```json
{
  "targets": [
    {
      "name": "ExamplePrivateBrowser",
      "program": "C:\\Program Files\\Example\\browser.exe",
      "allowLan": true
    }
  ]
}
```

默认允许回环与 `198.18.0.0/15` fake-ip，阻止其余 IPv4 和 IPv6 出站。`allowLan: true` 额外允许 RFC1918 局域网，适用于需要认证页或本地服务的浏览器。

```powershell
# 只检查参数、路径和将执行的操作
powershell -File scripts/killswitch.ps1 -Action Plan -ConfigPath .\targets.json

# 管理员终端：创建/更新 PF-Killswitch-* 自有规则
powershell -File scripts/killswitch.ps1 -Action Apply -ConfigPath .\targets.json

# 管理员终端：只删除本配置对应规则
powershell -File scripts/killswitch.ps1 -Action Rollback -ConfigPath .\targets.json
```

限制：

- 使用精确程序路径；商店/MSIX 应用更新后路径可能变化，必须重验。
- 默认模板只适用于使用回环代理或该 fake-ip 段的网关。其他 VPN 不能照搬。
- 防火墙规则不约束已经控制管理员/内核的恶意软件。
- 本 skill 不自动检测代理是否真的停止；验收时需要用户在受控窗口内停止网关并测试。

## 3. 双状态验收

- 代理在线：目标应用可联网，出口和 DNS 符合基线。
- 代理完全停止：目标应用连接失败；不得用另一个未受保护浏览器代替判断。
- Rollback：删除规则后应用恢复原网络行为。
- 更新后：规则程序路径仍存在且指向当前应用。

## 4. 系统与软件卫生

优先做低风险、可解释的设置：关闭不需要的位置和广告 ID、审查启动项、卸载不用的 VPN/远控、限制云同步与遥测。不要默认轮换 MachineGuid、修改安装语言、禁用系统 DNS Client 或叠加第三方“优化/清理”工具；这些操作可能破坏授权、更新或全网连通，而网页通常也读不到相应值。

## 5. 进程规则

`PROCESS-NAME` 对共享运行时过宽，`PROCESS-PATH` 又会随更新漂移。选择其一就要记录维护成本。Node/Python 等 CLI 工具不应因为 Agent 使用就被整体加入 DIRECT 或 killswitch，避免影响同机无关程序。
