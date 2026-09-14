# V8 三步 Triage Funnel：真实应用接入与录制

## 当前结论

`web/` 已采用 `product-demo-v9/` 的三步信息流，并完成真实应用录像。不能用 Mock 页面代替真实应用，也不能把“人工采纳”说成业务修复。

真实入口仍是 `http://127.0.0.1:8766/`。录像时为避免污染正式工作台历史，在 MacBook 启动了同一真实应用代码的隔离实例 `http://127.0.0.1:8773/`，读取真实 `legacy-monitor` 源，使用临时 SQLite；Mac mini 浏览器通过专用 SSH 反向转发访问它。

## 三步真实流程

### 1. TRIAGE

- 展示全部已有问题的标题、描述和 `P0/P1/P2/P3`。
- 原始长日志默认收起，按需展开。
- Agent 先整理问题，人只选择一个继续。

### 2. PROBE · ONE APPROVAL GATE

- 点击“添加探针”后打开唯一 `AskUserQuestion`。
- “批准并开始”后，真实页面展示四个 Agent steps：读取问题、自动添加探针、寻找复现、等待人工反馈。
- 人点击“问题已复现”。录制不执行生产探针。

### 3. ROUTE & APPLY FIX

- 真实 Eve 结果提供 5 条独立路线。
- 每条显示复现探针、解决动作、Blast Radius、验收和回退。
- 选择第二条路线，填写理由，点击“应用这条路线（只记录）”。
- 决定写入隔离 SQLite，随后进入决策记录并重载页面确认留痕。
- 真实业务修复仍由团队手工执行，页面不直接改变业务服务。

## 录制证据

最新成片：`tools/real-ui-demo/artifacts/real-app-demo-v2/real-app.mp4`；本机交付副本：`artifacts/real-app-demo-v2/real-app.mp4`

- 时长：59.166 秒
- 画面：1440×1000
- 编码：H.264、`yuv420p`、30 FPS、无音轨
- 真实问题：`scaro.auth`
- 真实 Eve session：`wrun_01M2ESAQPJ45BY00VEC6YEWY6S`
- 真实诊断 revision：`7603599b8e0ea5d532f2bb922675849e5c06c6537f4bd4c32909f1a42f5d3209`
- fixture server：否
- mocked model：否
- 隔离数据库：是
- 录制期间人工决定：1 条，未写正式数据库
- 录制期间处理结果：0 条

`proof.json` 保存实际 URL、health、前端 SHA-256、run ID、session ID、SQLite 前后指标和 marker。`chapters.json` 由实际运行时 marker 生成。`contact.png` 和 `strip-*.png` 已逐张检查。record 模式会在 `run.sh` 完成后自动把最终证据提升到 `artifacts/real-app-demo-v2/`。

## 固定执行路线

作者脚本在本机，浏览器录制、FFmpeg、抽帧和 MP4 编码全部经过：

```bash
$HOME/.pi/agent/bin/video-render-macmini --check
$HOME/.pi/agent/bin/video-render-macmini \
  --project "$PWD/tools/real-ui-demo" \
  --output artifacts/real-app-demo-v2 \
  -- bash run.sh record
```

`tools/real-ui-demo/run.sh` 使用 Mac mini 已安装 Chrome channel。`finalize.py` 只在 Mac mini 执行 FFmpeg、`ffprobe`、poster、contact sheet 和交互帧条。MacBook 仅负责编辑、传输和使用 Pi `read` 检查返回的 PNG。

## 验证

- `python3 -m unittest discover -s tests -p 'test_*.py'`：23 项通过。
- `python3 tests/browser_leader.py`：隔离 DB、真实 Eve、三步界面、唯一探针审批门、Agent steps、人工反馈、5 条路线、Blast Radius、人工应用留痕、重启、移动端和安全边界通过。
- `impeccable detect --json web/app.jsx web/style.css web/index.html`：无发现。
- `video-render-macmini --check`：通过；录像时 Mac mini 可用空间约 32 GiB。
- 远端 `ffprobe`：H.264、1440×1000、30 FPS、`yuv420p`、59.166 秒，无音轨。
- 画面检查：无空白帧、错误弹窗、裁切主要内容或未拥有的页面；AskUserQuestion、Agent steps、路线范围和历史留痕均可读。

## 历史产物

- `artifacts/demo/demo.mp4`：旧隔离演示库录像，不是最新真实交付。
- `artifacts/real-app-demo/real-app.mp4`：旧 V3 真实应用录像，保留作历史。
- `product-demo-v9/`：已批准的 Web Mock TUI 参考，不能冒充真实 UI。
