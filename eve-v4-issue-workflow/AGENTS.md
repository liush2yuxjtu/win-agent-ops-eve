# WIN AGENT OS V4 Eve project

This is a local-only Eve issue diagnosis agent. Read the installed Eve docs before changing code.

## Runtime contract

- Use Eve's native experimental `Workflow` tool and declared subagents.
- Model access uses the Mac mini CPA through `CPA_BASE_URL`, `CPA_API_KEY`, and `CPA_MODEL`.
- Do not add Vercel AI Gateway credentials or `providerOptions.gateway`.
- Do not expose or execute developer-only Pi adapters. App users get the Eve agent surface only.
- Do not add shell, filesystem, browser, web-search, or production-mutation tools to this app.
- Human decisions remain `pending_human` until the user chooses `adopt`, `defer`, or `reject`.

## Verification location

Run `eve info`, `pnpm typecheck`, and `pnpm build` on Mac mini. Do not run the production app from this source mirror on the MacBook.
