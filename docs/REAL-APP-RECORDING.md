# V3 真实应用接入与录制

用户已批准 V3 设计并要求录制真实应用。入口仍为 `http://127.0.0.1:8766/`。正式工作台已使用 V3 的白底布局、问题队列、右侧属性和确认窗口。不是把 prototype 放进 iframe，也不是录制假数据页面。

## 真实链路

- 浏览器调用实际 Python `/api/state`、`/api/issue`、`/api/diagnose`、`/api/model-run` 和 `/api/quality`。
- 源数据来自原有监控。Eve/CPA 在 Mac mini 执行，结果写入真实 `data/ops.sqlite`。
- 录制时 Mac mini 浏览器经专用 SSH 反向转发访问 MacBook 的真实应用。没有 fixture 服务、模型替换或 localStorage 业务记录。
- 视频记录了 `scaro.auth` 的实际模型回合。运行 ID、Eve 会话、SQLite 诊断版本、前后记录数量和前端 SHA-256 见 `artifacts/real-app-demo/proof.json`。
- 录制只新增真实诊断。在确认窗口返回比较，不为了展示而写入人为决定或处理结果，也没有执行业务修复。

## 改动

`web/app.jsx` 是实际 React 客户端，保留 json-render 组件注册和既有 Python 服务。采用 Sidebar、Document、Inspector、Dialog 的职责划分。`web/style.css` 消费已批准 V3 的样式，不沿用旧绿色舞台。

`/api/quality` 读取真实 SQLite 诊断数量、反馈类型、首选方案反馈关联及当前诊断中的风险候选。不用数量冒充准确率，没有新增假扫描器。

Eve 输出改为领导版、最多五条独立路线。单纯查证放入缺失证据或适用条件，不作为步骤式方案。旧技术诊断仍保留，只有生成新领导简报后才开放新的方案决定入口。

两项具体修复。

1. 确认窗口重开时，原来依赖 effect 清空理由，会短暂沿用上一次状态。改为把理由和决定类型绑定本次待确认快照，新窗口同步得到空理由。
2. 证据包明确区分监控保存结果与实时探测。源心跳不是登录执行时间，缓存异常不能说成当前已实测故障。模型提示和事实字段共同表达这个边界，旧判断不覆盖历史。

## 工程参考

核对过 Vercel Templates 的 Admin Dashboard 与 Next.js & shadcn/ui Admin Dashboard。

- `vercel/nextjs-postgres-auth-starter` 为 Vercel 官方仓库，核对时 1,053 stars，未归档，最后推送为 2024-06-23，API 未返回许可证。未复制其代码，也未引入它的 Postgres/Auth 依赖。
- 选择工程模式参考 `arhamkhnz/next-shadcn-admin-dashboard`，Vercel 目录收录的社区模板，非 Vercel 官方开发。核对时 3,009 stars，MIT，未归档，最近推送 2026-09-09，commit `27334e9bd8e7dc194c72ac08e17810ba7b52430e`。
- 源码为 `https://github.com/arhamkhnz/next-shadcn-admin-dashboard`，模板为 `https://vercel.com/templates/next.js/next-js-and-shadcn-ui-admin-dashboard`。依赖与安装脚本清单保存于 `verification/template-package.json`。
- 实际融合的是应用壳、分区客户端组件和显式加载/错误状态模式，没有复制原模板组件或声称基于它的源码 fork。已有项目不迁移到 Next.js 16，不引入模板的三十余项依赖，不执行 Husky 安装脚本，不新增云数据库、认证或分析服务费用。

## 验证

- 后端测试 23 项，包括真实反馈汇总与缓存证据语义。
- `tests/browser_leader.py` 用隔离测试数据库调用真实 Eve，验证暂缓、拒绝、采纳、结果反馈、进程重启、跨站/会话/CSRF/Host 拒绝和窄屏布局。隔离测试不是录像目标。
- `tests/browser_check.py` 和 `tests/browser_model.py` 已迁移为该真实领导界面套件的兼容入口。
- 当前 Eve 一项完整 strict eval 通过。原来检查第一方案是否写 PID 的断言，已改为检查展开归因保持正确进程语义，避免与领导版独立方案要求冲突。
- 实际应用完成 discovery、rehearse 和 record，框架错误为零。已查看全片 contact sheet、十张交互帧条，以及完整业务影响和确认窗口画面。

这不代表全项目质量目标完成。没有独立事故集证明准确率提升，没有自动优化或自动修复。

## 视频

成片为 `artifacts/real-app-demo/real-app.mp4`，65.27 秒，1440×1000，H.264、yuv420p、30 FPS，无音轨。真实模型等待约 52.27 秒，压缩到 5 秒，并有明确字幕，其余操作原速。

所有录制、编码和抽帧经 `video-render-macmini` 在 Mac mini 完成。磁盘空间多次波动，低于门槛的调用未启动；在通过预检的调用中完成了完整录制和编码。没有清理远端缓存、源码或历史。额外抽帧尝试后来被门槛拦截，未覆盖已经成功生成的视频；本次验收使用首次成功生成的十张帧条和全片缩略图。

录制代码在 `tools/real-ui-demo/`。该目录不包含应用副本或样例服务器，地址必须对应 health 返回 `ui=leader-live-v1` 的真实应用。下一次录制前先恢复专用反向转发，再经统一入口执行，不打开临时 mockup 作为替代。

启动应用用 `python3 scripts/start.py`。升级 Python 后用 `python3 scripts/restart.py`，它先检查真实诊断是否仍在运行、备份数据库、核对精确进程命令，再重启本工作台，不终止其它服务。
