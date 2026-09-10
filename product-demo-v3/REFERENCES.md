# Mobbin 参考与重做决策

## 已核验来源

本次通过 Exa 在 `mobbin.com` 检索，读取了以下三张公开预览图。图片请求均返回 HTTP 200；页面与图片 URL、文件大小保存在 `references/sources.json`。没有登录、绕过权限或访问付费界面。

| Mobbin 存档 | 本地研究图 | 采用的结构 |
| --- | --- | --- |
| [Linear Web Inbox Notifications](https://mobbin.com/explore/screens/ecd4b63c-7956-4fa3-9573-bf6d78c4bca4) | `references/linear-inbox.png` | 紧凑侧栏、问题队列、轻分隔线、选中状态 |
| [Linear Web Issue Detail Page](https://mobbin.com/explore/screens/4e50fabd-fab7-487c-83cf-040de77ee7ea) | `references/linear-issue.png` | 中间内容、右侧属性、状态与责任信息分开 |
| [Stripe Web Review Changes Modal](https://mobbin.com/explore/screens/5dd20eba-4782-440c-b8cf-28251702bc1d) | `references/stripe-review.png` | 保存前集中展示收益、前提、风险及确认动作 |

来源平台为 Mobbin 官方图库，对应产品设计为 Linear 和 Stripe。不是来自这两个产品的开源代码，也不代表品牌合作或官方认可。GitHub 星数不适用。参考是历史存档，其中可见旧日期，不能冒称产品当前最新界面；具体设计版本与维护时间未核验。

研究图只用于本地设计分析。版权属于原权利人，未取得再分发授权；不嵌入原型，不作为发布素材，不复制品牌图标、插画或原文案。`index.html` 的视觉与内容均重新编写，无运行时图片、字体或 CDN 依赖。只有用户主动点击来源链接才访问外部页面。

## 从零重做的内容

删除旧版宣传页大标题、绿色风景舞台、浮窗造型和顶部五菜单。新的布局是白底业务工作台。

- 左侧只有自然工作区入口与事项定位，不按五项能力列目录。
- 中间先呈现业务影响与推荐理由，再展开事实、待核实信息和独立方案。
- 右侧承载状态、协调范围、责任判断与试选建议，随选择更新。
- 保存方案时打开确认窗口，明确确认的是本地建议，不是执行授权。
- 历史、结果反馈、潜在风险和复核保留完整交互，不用新外观掩盖缺失功能。

业务样例与方案文案沿用 V2，避免视觉重做意外改变业务定义；HTML 结构、样式和交互实现重新编写。当前是独立离线原型，没有接入 Eve、CPA、SQLite 或正式监控。

## 验证与批准边界

`verification.json` 记录实际浏览器验证结果。覆盖证据关联、五条方案试选、确认与取消、理由校验、刷新持久化、结果反馈、问题搜索、潜在风险和导出，三种视口宽度无页面横向溢出。原型打开时没有外部网络请求。

`qa/desktop.png` 与 `qa/confirmation.png` 为本版验收截图，已直接查看。未完成完整自动化无障碍审计，不冒称全面合规。

按领域建模原则保留信号、判断、方案、选择与结果边界；按真实验证原则查看 Mobbin 实图后再设计，并实际操作新原型验收。没有启动子代理，没有修改正式工作台，没有录制新视频。等待用户批准后再实施正式设计。

重建为 `python3 build.py`，验证为 `python3 verify.py`。交付入口 `index.html` 可单独离线打开，不依赖源码目录或研究图片。
