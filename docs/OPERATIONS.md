# 运维工作台与 Eve 诊断

## 当前入口

工作台运行在 `http://127.0.0.1:8766/`，已接入批准的 V3 领导版界面。选问题后点击“生成领导简报”，可展开“补充关注点”填写追问。Eve 根据真实监控、历史检索、此前判断及人工反馈生成独立处理路线。旧技术诊断保留，不能冒充新版领导简报。每次生成新版本，不把采纳当作已执行。真实应用录制与改动说明见 `docs/REAL-APP-RECORDING.md`。

Python 工作台保留在 MacBook。Eve、CPA 请求、模型评测和构建在 Mac mini 执行。没有部署到 Vercel，没有修改或重启原业务服务。当前远端运行方式是 `eve dev --no-ui`，不是生产常驻部署；`eve build` 已验证。

## Pi 负责的启动与恢复

1. 远端启动或复用 Eve。
   `ssh macmini 'cd ~/projects/win-agent-ops-eve/eve-service && bash start-dev.sh'`
2. 本机启动或复用工作台。
   `python3 /Users/liushiyuwin/projects/win-agent-ops-eve/scripts/start.py`
3. 本机进程和端口在 `data/runtime.json`，日志在 `data/server.log`。桌面现有 `Win Agent 运维工作台.command` 启动本机入口；若远端重启，Pi 先执行第一步。
4. 更新 Python 后使用 `python3 scripts/restart.py`。它检查进行中的真实诊断，核对 runtime PID 完整命令、备份 SQLite，再停止本工作台 PID 并重启。启动器复用已有进程，不自动热更 Python。

Mac mini 目录为 `~/projects/win-agent-ops-eve/eve-service`。监听 `127.0.0.1:21876`，PID 在 `dev.pid`，日志在 `dev.log`。开发进程不随本次 SSH 断开退出，但未配置开机自启动。

CPA 从远端 `~/.config/cpa-luna.env` 注入。请求模型为 `gpt-5.6-luna`，使用 Responses API。工作台通过固定 SSH 命令传递有界证据包，不接触 CPA 密钥。独立 Eve 访问令牌位于远端 `.ops-token`，权限 0600，不复制回本机。

## 一次诊断经过哪里

`app/model.py` 生成证据包。内容包括当前问题、完整监控检查集合、最多十二条状态事件、最多八条人工结果及对应方案、最多两条旧模型诊断和有界历史检索结果。

`POST /api/diagnose` 先向 SQLite 写入运行记录，再启动远端调用。浏览器轮询 `GET /api/model-run?id=...`。原采集和页面读取不等待模型完成。

远端 `diagnose.mjs` 使用官方 `eve/client` 创建会话。Eve 通过动态 provider 连接 CPA。输出包括中文影响、竞争归因、反证、缺失证据、隐藏问题候选和最多五项互补方案。`schema.mjs` 只校验数据结构、引用和排序，不决定故障原因。

模型没有 shell、任意文件、网页、子代理或生产修改工具。当前检索由工作台准备证据包，不是模型主动调用历史检索工具。追问创建新的 Eve 会话，带入此前判断和反馈，不冒称同一聊天会话持续续接。

模型失败会留下失败记录，不返回规则结果冒充成功。现有规则诊断保留并明确标注 `rules-1`。模型成功后显示 `eve-cpa-1`。其他关联检查变化也会使旧模型诊断退出当前展示，旧版本仍保留在历史。

## 存储与安全

- `data/ops.sqlite` 保存 snapshots、issues、diagnoses、events、source_events、decisions、outcomes、meta 和 model_runs。模型运行表保存输入包、结果、会话 ID、耗时和错误。
- `history.sqlite` 是只读历史档案。原监控仍读取 `~/.local/state/win-agent-os/legacy-monitor/status.json`，每三十秒导入，不创建竞争 observer。
- SQLite 使用 WAL、外键、事务和 busy timeout。启动及约每小时通过 SQLite backup API 生成 `data/ops.backup.sqlite`。
- 采纳、拒绝、暂缓和处理结果绑定具体诊断版本。重复 ID 不重复记录，证据变化后的旧方案不能当作当前方案采纳。
- 当前是单本地操作人工作台。使用 Host、Origin、HttpOnly SameSite cookie、CSRF 和 CSP；不是多用户认证服务，不直接暴露公网。
- 常见凭据模式会遮盖，但不保证任意文本都完成全面秘密识别。证据会传到 Mac mini CPA 及其模型上游处理，不应放入不必要的个人或敏感信息。
- 远端 `runs/` 保存模型回合，`.eve/` 保存 Eve 持久状态。不能只备份源码而遗漏这两处和 SQLite。
- 请求模型及 Eve step model ID 可核验。产品诊断中的 CPA 实际响应模型尚未逐回合采集，`upstreamModelVerified=false`。评审请求返回了 `gpt-5.6-luna`，不据此反推每个产品回合的上游身份。

## 验证

本轮结果保存在 `verification/`。

- 远端 `python3 -m unittest discover -s tests -p 'test_*.py'`。当前二十三项，覆盖重复导入、错误、版本、关联证据变化、并发运行冲突、模型历史及反馈。
- 本机 `python3 tests/browser_leader.py`。真实按钮调用远端 Eve/CPA；使用隔离 SQLite 验证三种决定、反馈、进程重启和手机布局，测试决定不写真实库。旧 `browser_model.py`、`browser_check.py` 为此套件的兼容入口。
- 远端 `eve build` 成功。
- 远端设置 `EVE_EVAL_AUTH_TOKEN` 为 `.ops-token` 内容，再执行 `eve eval --url http://127.0.0.1:21876 --strict --json`。不得把令牌打印出来。当前一项真实模型框架评测通过；这项检查不代表诊断准确率。
- UI 构建在 Mac mini 执行 `node scripts/build-ui.cjs`，复用已有官方 json-render、React、esbuild，产物取回 `web/app.js`。

## 质量实验和明确余项

`eve-service/evals/compare.mjs` 对六个合成案例执行 baseline/candidate 同条件比较。训练、验证和保留集各两个案例。每侧使用相同输入、模型和预算；评分前随机标记，保存评分后解盲。受测模型看不到评分标准和答案。

补项目术语前的模型评分显示前五方案覆盖为 20/22 与 21/22，Top 1 都为 6/6。直接复核发现 owner 案例第一方案没有明确检查进程工作目录，评分仍判命中，评分偏宽。工作台默认 baseline，不把候选晋级，也不展示这些数值为准确率。

随后依据真实监控源码补入 owner、认证缓存和版本收据的术语说明。同一框架输入复测已正确建议检查 PID、listener_cwd 和预期目录，新增语义回归断言后 Eve strict eval 通过。旧六案例结果不冒充新版本全量质量评测。细节见 `verification/quality/REVIEW.md`。

没有新增按关键词判根因的规则。下一步质量工作需要积累真实处理结果和独立标注案例，检验假阳性、漏报和方案实际成效。当前未实现自动优化器、项目只读 eval MCP、Pi `eval_review` 工具、自动修复或 Git ship。隐藏问题目前是诊断时提出的候选，不是另一个持续自动扫描器。
