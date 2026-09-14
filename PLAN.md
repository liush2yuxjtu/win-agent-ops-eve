# win-agent-ops-eve：独立诊断助手

## 当前采用的三步 Triage Funnel（2026-09-11）

设计已从 V6/V7 多窗口方案收敛为单条真实工作流：`TRIAGE`、`PROBE · ONE APPROVAL GATE`、`ROUTE & APPLY FIX`。原始长日志默认收起；Agent 先整理全部问题并分到 `P0/P1/P2/P3`，人选择一个问题；添加探针只打开一次 `AskUserQuestion`，批准后显示 Agent steps 和人工反馈；最后 Agent 给出 5 条带 Blast Radius 的独立路线，人记录采纳或暂缓。真实工作台不得录制离线 product-demo 代替，当前 UI 真源为 `web/`，Mock 参考为 `product-demo-v9/`。完整契约见 `docs/PRODUCT-DEMO-DESIGN.md`。真实应用已按该契约完成隔离数据库录制，最新证据在 `artifacts/real-app-demo-v2/`，流程说明在 `docs/REAL-APP-RECORDING.md`。

## V3 已批准并接入真实工作台

用户已批准 Mobbin 参考的 V3，并明确要求录制真实应用而非 product-demo。真实入口为 `http://127.0.0.1:8766/`，React 界面已接入监控、Eve/CPA 和 SQLite。新版诊断面向领导，方案为独立处理路线。修复了确认窗口理由残留及缓存监控结果与实时检查语义混淆。23 项后端测试、真实模型浏览器隔离写入回归和 Eve strict eval 已通过。

已在 Mac mini 经统一入口录制真实应用，成片 `artifacts/real-app-demo/real-app.mp4` 约 65 秒。录制新增真实诊断，并在刷新后验证 SQLite 保留；没有写入人为决定或虚假处理结果，没有执行业务修复。原型仍保留在 `product-demo-v3/index.html`，不是此次录像目标。运行和证据说明见 `docs/REAL-APP-RECORDING.md`。准确率、自动优化及生产常驻部署等余项没有因此被宣称完成。

## 当前续接结果（2026-09-09）

真实 Eve/CPA 诊断已接入现有工作台。Eve 0.38.3 和真实模型运行于 Mac mini，工作台通过固定 SSH 客户端提交证据包。模型输出中文归因、反证、缺失证据、隐藏问题候选和最多五条方案，SQLite 追加保存输入、结果、运行状态及会话 ID。追问带入历史模型判断和人工结果，每次创建新 Eve 会话。

后端 21 项测试、真实浏览器模型回合及重启持久化验证、Eve build 和当前一项 Eve strict eval 通过。六个合成案例完成同条件盲测。候选的前五方案覆盖为 21/22，baseline 为 20/22；差异只出现在训练集，Top 1 和保留集未显示增益，默认仍用 baseline。不能据此声称生产准确率提升。进一步直接复核发现自动评分偏宽，且模型误解 owner 为人员归属。已按真实源码补项目术语，同一输入复测正确指向 PID、listener_cwd 和预期目录，新增语义回归的 Eve strict eval 通过；旧六案例数值不能代表此新版本质量。

当前不是完整目标全部实现。尚无真实独立标注事故集、持续隐藏问题扫描器、模型自主历史检索工具、自动调优或评测晋级、项目 eval MCP、Pi eval_review、生产常驻部署和 Git ship。详细运行边界与恢复步骤见 `docs/OPERATIONS.md`。旧磁盘/清理门槛不再生效。

## 上一轮规则首版交付（历史记录）

用户要求持续实施到可体验，并撤销了 Mac mini 空间/清理作为前置条件。现已提供独立轻量工作台：`http://127.0.0.1:8766/`，启动入口 `python3 scripts/start.py`。实际端口见 `data/runtime.json`。

- Python 标准库 HTTP + SQLite，前端使用已安装的官方 json-render/React 打包；没有启动 ARO/Next/Eve，没有安装新依赖，没有清理远端目录。
- 只读导入既有监控 `status.json`，每 30 秒更新；规则提供中文分诊和最多五条互补方案。
- 决定、结果反馈、状态变化和诊断版本持久化；“采纳”不执行，“有效”是人工反馈，不自动关闭事故。
- 增加心跳过期、时间倒退、缺项和投递状态检查。真实检出率与 Top 1/Top 5 质量提升未证明。
- **这是可体验的规则首版，不是下面的完整 Eve/CPA 架构已实现。** 未接模型、未 ship、未自动修复。当前运维说明见 `docs/OPERATIONS.md`，测试证据见 `verification/`。

以下保留历史设计作为未实现规格；其磁盘门槛与等待清理状态已撤销，不得据此阻塞工作。

## 交付目标

在 win-agent-os 仓库之外维护一个 Eve 应用，专门解释该项目与旧 SCARO/JDARO 的红灯。读取已有监控、Git、工作树和聊天证据，生成中文分诊、带证据的归因与最多五项互补方案。人选择采纳、拒绝或暂缓。采纳不触发执行。

运行只用 Mac mini CPA `http://127.0.0.1:8317/v1`，模型严格为 `gpt-5.6-luna`。不使用 AI Gateway，不索取新模型密钥，不回退其他模型。独立仓库名称拟为 `win-agent-ops-eve`，默认私有。原项目与旧 ARO 仓库只读，不清理、不重启、不迁移业务数据。

## 已核验的关键事实

- 本地 win-agent-os 取证基线为 `cc3e9a49eebc066d776cd9987b677bd1f05d5b79`。审计期间 GitHub main 已到 `730765e9492ffb1d67879ebc67ac75da33befdb7`，不把本地快照冒充最新主线。
- Mac mini canonical checkout 为 `main @ d5aacf401d515ed60f7f3c5b4e359b3db86ed624`。磁盘 HEAD 不能证明运行进程加载的版本。
- 现有 `scripts/legacy-aro-monitor.py` 已有常驻观察、SQLite `meta/events`、差异去重、GitHub incident #218、邮件 outbox。PR #220 已于 2026-09-08 合并；旧 deploy-record 中“未 push/merge”是过时快照。
- 现有 observer 在 MacBook 上运行。Mac mini 上部署的新 Eve 不能取代外部 observer，否则无法可靠报告自己所在主机的失联。
- `33514a6be5a1d0eb140b63cc7057330cdc36ada8` 包含独立 Maintain detector、probe、incident closure 和 eval 实现，不在本地 main 祖先中。它的 full 结果未绿，不能整包自动采用。
- Mac mini `maintain-eval-051c6a3` 还有未提交安全修正及新增 eval。已保存八份脱敏代码快照和原文件 SHA-256；不把这些快照当成可无损恢复的完整备份。
- `docs/eve-agent-tool-improvement-loop.md` 仍将项目级只读 eval MCP、Pi `eval_review`、盲测晋级与 optimizer 标为未实现。静态规格 eval 不证明这些运行时存在。
- 现有 `agent/lib/platform/web/skill-evals/history.ts` 仅保留最近十次，损坏 JSON 被当作空历史；不能作为永久故障记忆库。
- 本次核实的 Eve 官方包文档版本为 `0.38.3`，框架仍为 preview。实现时固定依赖版本并重新阅读目标安装文档，不修改官方包。

## 系统变化与真源

选择“既有 observer + 独立诊断服务”，不复制一套新的告警发送器。

1. 旧监控仍拥有采样与投递状态；GitHub #218 仍拥有该已发布 incident 的外部状态。
2. 新服务通过受限导入接收脱敏快照，SQLite 保存不可变证据、诊断版本、候选方案、人的选择及验证结果。
3. GitHub 状态在新库里是带 `source_updated_at` 的只读投影，不能由本地选择覆盖。
4. 历史记录、模型输出、人工决定、执行回执、验证结果分别存储。点击“采纳”不能变成“已执行”或“已修复”。
5. 旧工作树、旧会话、源码、数据库均没有新写入口。外部业务 API 不直接暴露给模型。
6. 新诊断若与之前归因不同，追加新版本并保留证据变化，不覆盖旧判断。

## 最小可用产品

### 证据接入

第一版支持以下输入，其他连接明确显示未接入：

- 现有 legacy-monitor 的 `status.json` 与 SQLite 事件快照，使用只读连接，不执行其 `run/start/deliver`。
- 本次生成的历史证据包。来源包括 MacBook、Mac mini、win-agent-os、旧 aro 的 refs/reflogs、worktree 状态，以及明确 cwd 的 Pi/Claude/Codex/Cursor prompt。
- 现有 `.eve/aro-health/`、`.eve/maintain-evidence/`、JUnit 和日志的受限导入。限定后缀、尺寸与目录，拒绝 symlink 越界。
- GitHub 指定仓库的只读 PR/Actions/Issue 元数据与选定日志摘要。没有建 issue、发评论、合并或部署权限。

采集器固定命令与输入白名单；项目路径来自配置，不从模型文本拼 shell。日志里的命令和旧聊天的授权均只是历史数据。没有时间戳的 Cursor prompt 保留未知时间，不用会话结束时间补造逐条时间。

持续采集不默认另起竞争 observer。先交付手动“刷新证据”，再经明确配置启用有界定时导入。健康页必须显示采集器存活、最后成功时间、源版本、采样空窗和数据是否过期。

### 诊断与 Top 5

每次诊断输出 schema：

- `issueId`、`analysisRevision`、`model`、`observedAt`、`evidenceIds`。
- `summaryZh`、`impactZh`、`priority`、`state`。
- `hypotheses[]`：组件/依赖/配置/变更归因，状态 `confirmed/suspected/rejected/unknown`，支持与反证，缺证据说明。
- `solutions[]`：排名、类别 `diagnostic/mitigation/root-cause/prevention`、适用条件、依据、风险、成本、验证方式、回退办法。

Top 1 按当前证据优先，Top 5 按不同可行动路径去重。不足五项就明确不足。诊断检查不能冒充修复方案。禁止生成校准过的成功百分比，除非对应实测数据存在。

### 持久化

SQLite 文件位于独立持久数据目录，开启 WAL、foreign keys、busy timeout 与迁移版本。业务写入在事务中完成，定期使用 SQLite backup API，而非直接复制运行中的主文件。

建议表：

- `source_snapshots`、`evidence`：源身份、主机、revision、时间、内容 hash、脱敏正文、有效期。
- `red_events`：稳定源事件 ID、检测项、严重程度、出现/恢复时间。
- `issues`、`issue_events`：跨重复告警的聚合及状态历史。
- `diagnoses`、`hypotheses`：归因版本，不归罪未被证实的个人。
- `solution_sets`、`solutions`：保留每次当时的排名。
- `adoption_decisions`：人工 `adopt/reject/defer`、真实操作人、版本、理由、时间。
- `verification_results`：验证来源、结果、证据、复发窗口；不从采纳自动推导。
- `runs`、`audit_events`：Eve session/run、工具动作、耗时、token、错误、审批记录。

幂等键覆盖源事件、导入批次、诊断请求与人工决定；重启和重复提交不生成重复状态。数据损坏应报错，不降级成“无历史”。

### 可玩的界面

运行后的独立 Web 客户端提供三块：问题列表、证据/历史检索、Eve 中文对话。点击某问题可查看归因版本、方案比较和历史证据，选择“采纳 / 拒绝 / 暂缓”，刷新与重启后仍保留选择。

这是运维产品界面，不是另建一套 Eve eval 的 HTML 评审页面。项目级 eval 的 Pi 文本评审契约保持独立，不能用此界面冒充已注册 `eval_review`。

UI 采用受控 json-render catalog 与 spec，保持与原项目使用习惯一致，但新仓库不依赖旧源码路径。模型只能产生已知组件与动作，不能注入 HTML、任意 URL 或可执行事件。

浏览器仅连接本机 SSH 转发地址。Eve 会话、历史数据和人工决定均需认证，写接口校验同源、CSRF 和版本。Eve route auth 不自动提供逐 session 所有权，项目需自行落实。第一版单操作人，不虚称多租户安全。

## Eve 与模型配置

- 固定使用 `defineDynamic` 的 `step.started` 返回 CPA 的 AI SDK `LanguageModel`，显式给 context window，防止编译时密钥缺失把 Gateway 字符串写入 manifest。
- 默认禁用 `bash/read_file/write_file/glob/grep/web_fetch/web_search/agent` 等不需要的框架工具；使用官方 `disableTool()` 文件机制，测试最终运行时工具清单。
- 仅提供 `search_history`、`read_evidence`、`list_red_events`、`get_issue`、`find_verified_solutions` 和受限 `save_diagnosis`。
- 人工决定接口不注册为 Agent tool。模型不能给自己批准、执行或关闭事故。
- 限定一次诊断的步数、时间、上下文、输出量与并发；CPA 不可用则记录错误，不返回假模型结果。
- 通过真实响应 model 字段和运行事件核验 `gpt-5.6-luna`；自定义 provider 无法确认实际上游时明确记录不可验证，不只相信环境变量。
- 持久保存 Eve `.eve/.workflow-data`；`eve build` 后用 `eve start` 运行，代理同时保留 `/eve/` 与 `/.well-known/workflow/`。
- CPA 环境与密钥仅由 Mac mini 现有安全配置注入。浏览器、导出数据、源码和 Git 均不包含密钥。

## 候选代码由人决定

1. 推荐复用已合并的 monitor 数据协议，保持现有 reporter 运行。不要复制其自动 GitHub 写入口到新 Eve。
2. 推荐有条件移植 Maintain 的纯函数 detector/probe/closure，先审阅远端未提交差异并完成自己的回归。不要直接 cherry-pick 整套 full runner。
3. 建议先建立长期证据和方案结果库，再启用检索增强诊断。没有结果标签时不能宣称 Top 1 命中率提高。
4. 暂缓自动改 prompt/工具、自动修复和生产写权限。现有改进契约尚未实现，不能借此项目绕过。
5. Vercel Alerts/CLI/Drains 仅作可选适配器。当前主要故障在 Mac mini 与 LAN 后端，不为第一版开通付费 Vercel 服务。

## 实施文件范围

- `agent/agent.ts`、`agent/instructions.md`：CPA 路由与证据/中文输出约束。
- `agent/tools/*`：只读证据工具、受限诊断保存、禁用默认工具。
- `agent/channels/eve.ts`：入站认证与会话所有权。
- `lib/store.ts`、`lib/schema.ts`、`lib/ingest.ts`：独立 SQLite、迁移与幂等导入。
- `lib/diagnosis.ts`：输出 schema、引用校验、排名与互补性约束。
- `server/*`、`web/*`：问题/历史/对话客户端与人工决定 API。
- `evals/*`：正常、坏证据、过期、指令注入、越权、重启与CPA真实回合。
- `scripts/*`：只读采集、远端安装/构建/启动/停止、SSH 转发、备份与健康。
- `docs/OPERATIONS.md`：准确命令、数据位置、PID/LaunchAgent、恢复步骤，由 Pi 保存而非用户记忆。

## 验证与 ship 门槛

1. 历史导入重复两次无重复；多工作树同源 commit 去重；被删除 cwd 与没有 cwd 的记录不伪造归属。
2. 模型输出引用存在且匹配源版本；错误/缺失/过期证据不产生“健康”。
3. 只读工具无法读 `.env`、越出 evidence root、任意 HTTP 或写原项目。
4. 三种人工选择持久化；重复请求幂等；未授权/跨会话/CSRF 被拒绝；采纳不产生执行副作用。
5. 重启后事件、历史、诊断、选择和 Eve session 可恢复；SQLite backup/integrity 验证。
6. 固定案例回放分别测误报、漏报、Top 1 与 Top 5 覆盖，标明历史分布偏差。按事故/时间拆分 train、validation、held-out，避免同一事故的不同 worktree 泄漏答案。
7. baseline 与 candidate 同模型、预算、工具、样本；评分前盲化。第一版不自动优化，不承诺未经测量的提升。
8. 全部生效 Eve eval 严格通过、真实 CPA smoke 成功、浏览器完成问题选择与刷新持久化流程后，才提交、push、PR、babysit、merge、同步默认分支并报告可玩 URL。
9. 原项目 full 的已知失败不通过删除断言、改标签、增加 skip 刷绿；本服务自己的绿色不等于原产品已经恢复。

## 历史部署阻塞与恢复（已撤销，不再生效）

Mac mini 于本次预检仅剩约 4.9 GiB，低于用户级 Eve 的 10 GiB 门槛。因此没有在任一机器安装新 Eve 依赖、启动新服务或调用真实模型，不伪造可玩链接。

只读盘点的可再生清理候选在 `research/cleanup-proposal.json`。等待明确批准精确路径；保留全部源码、未提交修改、数据库、`.eve` 与历史 artifacts。执行前重新核验路径、磁盘、进程与文件占用；状态变化即停止该项。释放空间并保留依赖安装余量后，从远端独立目录安装 Eve 开始继续。禁止回退到 MacBook 构建。
