# 真实应用 UI Demo

最新真实录像位于 `artifacts/real-app-demo-v2/real-app.mp4`。

- 时长：59.166 秒
- 画面：1440×1000
- 编码：H.264、`yuv420p`、30 FPS、无音轨
- 录制对象：`web/` 构建出的真实工作台
- 模型：真实 Eve/CPA 回合
- 录制库：临时隔离 SQLite
- 最新运行：`wrun_01M2ESAQPJ45BY00VEC6YEWY6S`
- 人工决定：1 条，仅写入隔离库
- 生产执行：0

## 观看顺序

1. **Triage**：真实问题队列、P0/P1/P2/P3、长日志默认收起。
2. **Probe**：打开唯一 `AskUserQuestion`，批准添加探针；页面展示读取问题、添加探针、寻找复现、等待人工反馈。
3. **Feedback**：人工点击“问题已复现”。
4. **Route & Apply Fix**：查看 5 条独立路线与 Blast Radius，选择路线并点击“应用这条路线（只记录）”。
5. **SQLite history**：打开决策记录，重载页面确认真实诊断与人工决定仍在。

视频只压缩明确标记的真实 Eve 等待段，其余鼠标移动、点击、输入、页面滚动和状态变化保持原速。字幕明确区分真实模型等待与后处理加速。

## 证据

- `artifacts/real-app-demo-v2/proof.json`：真实 URL、前端 hash、Eve session、诊断版本、SQLite 指标和边界。
- `artifacts/real-app-demo-v2/ffprobe.json`：远端 FFmpeg 输出元数据。
- `artifacts/real-app-demo-v2/chapters.json`：由运行时标记生成的章节。
- `artifacts/real-app-demo-v2/contact.png`：全片 contact sheet。
- `artifacts/real-app-demo-v2/strip-*.png`：主要交互区间帧条。
- `artifacts/real-app-demo-v2/QA.json`：画面检查结论。
- `tools/real-ui-demo/BRIEF.md`、`record.mjs`、`finalize.py`：真实录制流程。

## 边界

`product-demo-v9/` 是已批准设计的本地 Mock 参考，不能替代真实录像。真实录像使用同一 `web/` UI、真实监控源、真实 Eve/CPA 和真实 SQLite 代码路径；录制期间不使用 fixture server、模型替换或 localStorage 业务记录。

“应用这条路线”在当前工作台语义中只记录人工采纳，不直接修复业务。探针流程仍是 UI 中的受控展示，不自动写入生产系统。历史旧录像 `artifacts/demo/demo.mp4` 与 `artifacts/real-app-demo/real-app.mp4` 保留，但不作为最新交付。
