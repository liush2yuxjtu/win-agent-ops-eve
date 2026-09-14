# 真实工作台三步录制

用户已批准 `product-demo-v9` 的三步 Triage Funnel 设计，并要求真实应用采用同一信息流后录制。禁止把 Mock、fixture 或旧 UI 录像当作交付。

## 真实目标

- 应用代码：项目 `web/`，使用真实 Python 工作台和真实 React/json-render bundle。
- 录制访问：Mac mini 浏览器经专用 SSH 反向转发访问 MacBook 上的真实应用代码。
- 录制数据库：一次性隔离 SQLite；源监控仍来自真实 `legacy-monitor`，不是 fixture 服务。
- 模型：真实 Eve/CPA 请求，模型结果不能替换或伪造。
- 录制允许写入一条隔离数据库中的人工“采纳”决定，用来证明真实 UI 的 Route & Apply；不执行任何业务修复。

## 三个节拍

1. **TRIAGE**：显示真实问题队列和 P0-P3，原始长日志默认收起。选择 `scaro.auth`，停留三秒。
2. **PROBE · ONE APPROVAL GATE**：生成真实 Eve 领导简报；打开唯一 `AskUserQuestion`，批准添加探针；真实页面显示读取问题、添加探针、寻找复现、等待人工反馈；点击“问题已复现”。
3. **ROUTE & APPLY FIX**：查看真实简报中的 5 条路线和 Blast Radius，选择第二条，填写人工理由并点击“应用这条路线（只记录）”；打开真实 SQLite 历史，重载页面确认记录保留。

模型等待只在成片后处理时压缩为五秒，并用字幕说明；所有点击、输入、状态变化原速可见。

## 规格

- viewport：`1440×1000`
- 输出：H.264 MP4、`yuv420p`、30 FPS、无音轨
- browser：Mac mini 已安装的可见 Chrome channel，headless 录制
- overlay：真实应用、三步流程、唯一审批门、无生产动作
- chapters：由 `markers.json` 的单调运行时标记生成

## 验收

`discover` 保存真实控件名称、角色、几何和 health；`rehearse` 不录视频地完成同一真实链路；`record` 重新执行真实链路；`finalize.py` 只在 Mac mini 做 FFmpeg 编码、poster、contact sheet 和交互帧条。

必须检查：三步入口、问题分诊、唯一 AskUserQuestion、批准后 Agent steps、人工反馈、五条路线、Blast Radius、隔离 SQLite 决定、刷新后历史、移动端无溢出、无浏览器错误。不能用 API 成功代替画面验收。
