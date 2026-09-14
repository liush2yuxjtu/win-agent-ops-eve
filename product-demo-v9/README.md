# 运行简报 · Web Mock TUI V9

这是浏览器里的终端界面，不是实际 shell TUI。

## 启动

```bash
python3 product-demo-v9/start.py
```

打开：`http://127.0.0.1:8772/`

## 三步流程

1. `TRIAGE`：Agent 整理全部问题，分到 `P0/P1/P2/P3`。
2. `PROBE`：点击 `ADD PROBE`，只弹一次 `AskUserQuestion`；批准后自动开始探针流程。
3. `ROUTE & APPLY`：Agent 给 5 条路线和 Blast Radius；人选择并应用 Mock fix。

## 交互

- `j/k`：切换问题
- `[/]`：切换路线
- `l`：展开/收起原始长日志
- `p`：打开唯一 AskUserQuestion 审批门
- `r/s/t`：问题已复现、问题已解决、输入反馈
- `a`：应用当前 Mock fix

## 边界

V9 使用自包含本地 mock 数据，页面明确标注 `MOCK TUI`。交互只改变浏览器内状态，不读取凭据，不调用业务 API，不执行真实探针或修复。唯一审批门只保护添加探针；路线应用仍是人主动点击的本地 Mock 状态。
