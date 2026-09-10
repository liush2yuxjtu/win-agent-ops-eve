# WIN AGENT OS V4 Eve issue workflow

Eve project that turns one captured ops issue into the four Product Demo V4 outputs:

1. explain how the error may happen, keeping facts and hypotheses separate;
2. review folded, untrusted logs;
3. generate exactly five independent response routes;
4. ask the human to adopt, defer, or reject a route.

The project uses Eve's native experimental `Workflow` tool. The model-authored workflow calls declared specialist subagents, using the same useful shape as Claude Dynamic Workflow: phases, parallel fan-out, per-item pipeline checks, schemas, plain aggregation, and a final structured return.

`pi -p` is not part of this app. The old Pi compatibility adapter lives in the developer archive outside this Eve project and is not an app-user capability.

## Remote development

Eve work runs on Mac mini through the existing CPA route. No Vercel AI Gateway.

```bash
pnpm typecheck
eve info --json
pnpm build
eve dev --no-ui
```

Set `CPA_BASE_URL`, `CPA_API_KEY`, and `CPA_MODEL` in the remote process environment. Keep real values out of this checkout.

## App conversation

Send a captured issue with its observed facts, evidence, and logs. The agent should return a structured report with `preExplanation`, `foldedLogs`, `solutions`, and `decision`. It must ask one human decision question after the report and must not execute a fix.

## Boundaries

This is an MVP backend agent. It does not connect to the existing Python ops database, execute remediation, or expose the developer archive. Add those only as separately authorized, typed, and approval-gated capabilities.
