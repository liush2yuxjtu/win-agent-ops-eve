# Product Demo V9 · Web Mock TUI

## 目的

把 V8 Triage Funnel 变成浏览器中可点击、可按键的 Mock TUI。视觉像终端，交付仍是 Web 页面。

## 三步信息流

1. `TRIAGE`：长日志由 Agent 整理成全部问题，再分到 `P0/P1/P2/P3`。
2. `PROBE`：点击 `ADD PROBE` 后只出现一次 `AskUserQuestion`；批准后自动加入探针并开始处理，显示 Agent steps 和人工反馈。
3. `ROUTE & APPLY`：Probe 完成并收到人工反馈后，Agent 给出 5 条路线与 Blast Radius，人选择并应用 Mock fix。没有第二个审批弹窗。

## 运行

- URL：`http://127.0.0.1:8772/`
- 启动：`python3 product-demo-v9/start.py`
- 页面：`product-demo-v9/index.html`
- 服务：`product-demo-v9/server.py`
- 日志：`data/product-demo-v9.log`
- PID：`data/product-demo-v9.pid`

## 安全

页面是 mock，不模拟真实登录、支付、部署或修复成功。没有外部运行时资源，没有凭据，没有业务 API。`p` 打开唯一 AskUserQuestion 审批门；批准后自动添加探针并展示 Agent steps。Probe 完成前不显示可用的应用按钮，防止跳过流程。路线应用是人主动点击的本地 Mock 状态，反馈、路线选择和决定只保存在内存。

## 验证

`product-demo-v9/verify.py` 通过远端无头 Chrome 验证标题、全部问题、P0-P3、原始长日志、键盘和点击导航、探针步骤动画、三种人工反馈、5 条路线、Blast Radius、人工决定、390px 无溢出和无脚本错误。
