# 运维工作台操作演示

成片位于 `artifacts/demo/demo.mp4`，67.6 秒，1440×900，H.264、yuv420p、30 FPS，无配音。字幕、鼠标移动、逐字输入及状态变化来自真实浏览器。

视频使用隔离演示库和合成监控案例，右上角始终明确标注。Eve/CPA 回合是真实调用。约 45.7 秒模型等待压缩为 5 秒，字幕明确说明加速；其他操作原速。正式 SQLite 未写入演示决定。

## 录制中修复的问题

1. 切换问题后，上一问题的追问文本仍留在输入框。根因是组件状态不随问题 ID 更新。现按问题 ID 清空草稿。
2. 在诊断区域操作时，页顶反馈已滚出视口。根因是进度和错误只在 Header 渲染。现于诊断按钮旁同步显示反馈，并保留 aria-live。

产品改动在 `web/app.jsx` 和 `web/style.css`，Mac mini 构建产物已同步为 `web/app.js`。没有修改诊断规则、模型、业务服务或生产数据。

复现前的浏览器结果在 `verification/ui-demo-before/reproduction.json`。修复后 `tools/demo-video/artifacts/check/run.log` 显示 `questionLeaked=false`、`localFeedbackVisible=true`、无浏览器错误。

## 验证和产物

- discover 保存真实元素、名称和几何位置。
- check 重跑切换追问及就近反馈回归，有断言，失败退出。
- rehearse 完成真实模型调用、方案展开、采纳和页面刷新，无录屏。
- record 重跑上述操作，实际模型返回四条互补方案，采纳后红灯未被关闭，刷新后决定仍在。
- inspect 已逐张查看全片缩略图、十一张关键区间帧条、全尺寸方案画面和最终历史画面。最终历史停留约五秒。未发现空白片段、核心操作遮挡或弹窗分片。

`artifacts/demo/chapters.json` 来自实际运行时标记。`qa/` 保存帧条，`proof.json` 保存语义、状态和几何验证，`edit.json` 保存等待加速参数。原始 WebM 保留于 `tools/demo-video/artifacts/record/raw.webm`。

## 由 Pi 重录

只复制指定的八个源文件，不能把整个项目和历史数据库送进同步目录。

```bash
cd /Users/liushiyuwin/projects/win-agent-ops-eve
python3 tools/demo-video/prepare.py
```

随后按顺序通过统一远端入口执行 `check`、`rehearse`、`record`。

```bash
~/.pi/agent/bin/video-render-macmini \
  --project "$PWD/tools/demo-video" \
  --output artifacts/record \
  -- bash render.sh record
```

`serve.py` 只把 SSH 传输换为 Mac mini 同机调用原来的 `diagnose.mjs`，不替换或模拟模型结果。演示数据库和浏览器 profile 位于本次临时目录，结束后清理。生产 Eve 服务保持运行。

全部浏览器录制、视频编码和帧提取均在 Mac mini 完成。未公开发布、未 ship。子代理启动开关仍关闭，未做独立子代理评审。
