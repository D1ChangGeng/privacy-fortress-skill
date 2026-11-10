# 验收、巡检与恢复

## 1. 最小验收矩阵

| 项目 | 正常状态 | 故障状态 | 证据 |
|---|---|---|---|
| 公网 IPv4 | 符合受控出口基线 | 代理停止时受保护应用无直连 | 两个独立端点+应用实测 |
| DNS | 实际递归解析器符合设计 | 上游失败不悄悄走本地明文 | 深度 DNS 测试+故障测试 |
| IPv6 | 通过同一受控路径或明确不可用 | 不出现额外直连出口 | v6 端点与浏览器测试 |
| WebRTC | 不出现真实公网/本地候选 | 代理停止时受保护浏览器断网 | 普通浏览器实测 |
| 分流 | 每个 DIRECT 例外均有用途 | 默认 MATCH 不意外 DIRECT | 配置 diff+逐应用测试 |
| 可用性 | 工作、认证、更新、局域网按设计可用 | 可一键回退 | 用户关键流程+Rollback |
| 生命周期 | 重启/换网/唤醒后恢复 | 客户端升级不静默漂移 | 重复验收 |

## 2. 审计脚本

默认离线：

```bash
python scripts/privacy_audit.py --output ./privacy-reports
```

显式在线：

```bash
python scripts/privacy_audit.py --online --baseline /path/to/baseline.json --output ./privacy-reports
```

脚本输出 JSON 与 Markdown。公共 IP 服务只能证明脚本所在网络路径；要证明某个应用，必须让该应用走同样测试或使用其连接日志。

## 3. 检测站使用原则

可选择信誉良好的 IP/DNS/WebRTC 检测站，但站点会变化，不能把某一站点当永久事实源。优先保存日期、原始观察值和测试条件，不保存无关账号页面。

- HTTP 200 只表示可达，不表示检测通过。
- 超时、403、验证码、空解析器列表均为 UNKNOWN/WARN。
- 无头浏览器和普通浏览器结果可能不同。
- 不用检测站评分替代具体信号验证。

## 4. 故障恢复

1. 停止敏感操作，保留当前配置副本和日志。
2. 使用事先演练的 Rollback，恢复普通路由/DNS/防火墙。
3. 先验证整体联网和关键工作服务。
4. 定位到具体规则、DNS、TUN 或路径漂移后，小范围重试。
5. 记录根因和新的回归测试，不把长期关闭防护当修复。

## 5. 30 项覆盖验收

```bash
python scripts/coverage_audit.py --init ./privacy-reports/coverage.json
python scripts/coverage_audit.py --ledger ./privacy-reports/coverage.json --output ./privacy-reports/coverage.md --require-tested
```

每项填写 TESTED、CONFIG、UNKNOWN、RESIDUAL 或 NOT_APPLICABLE。TESTED 需要日期和证据；RESIDUAL 与 NOT_APPLICABLE 需要原因。`--require-tested` 在仍有 CONFIG/UNKNOWN 时返回非零，帮助 Agent 把待办清晰交付。脚本校验完整性，实际状态仍来自对应设备与网络测试。

## 6. 复检触发器与节奏

每日可做轻量基线检查；每周或重要变更后做普通浏览器 DNS/WebRTC 深度测试；每月复核账号、公开元数据和残余清单。以下事件必须完整复检：更换出口/订阅、修改规则、切换 Wi-Fi、系统或 VPN 升级、浏览器大版本升级、应用路径/MSIX 包族变化、配置事实源重建、端口切换、设备重启后异常、安装新浏览器/VPN/远控。
