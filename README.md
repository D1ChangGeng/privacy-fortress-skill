# Privacy Fortress Skill

一个面向 AI Agent 的跨平台网络隐私加固技能：从只读审计开始，把代理网关、DNS、IPv6、WebRTC、fail-closed、浏览器与元数据卫生整理成一套可验证、可回退的工作流。

> 目标是减少不必要的信息暴露，不是承诺匿名，也不用于规避执法、付费或服务地区限制。

## 安装

需要 Node.js 22.20+。在希望使用 skill 的项目目录运行：

```bash
npx skills add D1ChangGeng/privacy-fortress-skill --skill privacy-fortress
```

全局安装：

```bash
npx skills add D1ChangGeng/privacy-fortress-skill --skill privacy-fortress -g
```

Windows 或不支持符号链接的环境可加 `--copy`。也可以从 Releases 下载 `privacy-fortress.skill`，解压后把其中的 `privacy-fortress/` 放入 Agent 的 skills 目录。

安装后可以对 Agent 说：

> 用 privacy-fortress 只读审计这台机器的网络隐私，不要修改任何设置。

或：

> 按 privacy-fortress 设计 DNS 防泄漏与代理断线 fail-closed 方案，先给变更和回退计划，等我确认再执行。

## 包含什么

- Windows、macOS、Linux、Android、iOS 的分平台实施边界；
- Mihomo/Clash 与 sing-box 的架构指导，不绑定代理服务商；
- DoH-over-proxy、fake-ip、DNS 引导和泄漏验收；
- Windows 参数化防火墙 killswitch，支持 `Plan`、`Apply`、`Rollback`；
- 跨平台只读审计：默认离线，在线检测需显式 `--online`；
- 配置静态检查、跨平台 CI 测试、无凭据模板；
- 浏览器、移动端、Git/图片/Agent 上下文元数据与能力边界。

## 快速自测

```bash
python skills/privacy-fortress/scripts/privacy_audit.py --output ./privacy-reports
python -m unittest discover -s tests -v
```

在线审计会联系公共端点并暴露当前出口 IP，只有明确需要时才使用：

```bash
python skills/privacy-fortress/scripts/privacy_audit.py --online --output ./privacy-reports
```

## 安全设计

- 默认只读，不自动修改 DNS、路由、防火墙或注册表；
- 不收集机器 GUID、Cookie、账号、代理凭据或 Wi-Fi 名称；
- 示例只使用文档保留地址与明显占位符；
- 每个系统级变更都要求备份、回退与双状态验收；
- 检测站不可达只记 WARN，不能当作“无泄漏”。

## 仓库结构

```text
skills/privacy-fortress/   可分发的 Agent Skill
├── SKILL.md
├── references/            按需加载的平台与协议指南
├── scripts/               只读审计、配置检查、Windows killswitch
└── assets/                无秘密配置示例
tests/                     标准库单元测试与发布检查
tools/package_skill.py     .skill 打包与内容校验
.github/workflows/         Windows/macOS/Linux CI
```

## English summary

Privacy Fortress is an agent skill for evidence-driven, rollback-first network privacy hardening. It supports cross-platform read-only audits, DNS/WebRTC/IPv6 leak-review workflows, gateway configuration linting, and a parameterized Windows firewall kill switch. It makes no anonymity guarantee and never treats installing the skill as permission to change the host.

## License

MIT. See `LICENSE`.
