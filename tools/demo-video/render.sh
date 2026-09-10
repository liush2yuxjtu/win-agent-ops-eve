#!/bin/bash
set -euo pipefail
mode="${1:-record}"
mkdir -p "artifacts/$mode"
node -p 'require("playwright/package.json").version' > "artifacts/$mode/playwright-version.txt"
if ! node --input-type=module -e 'import {chromium} from "playwright"; const b=await chromium.launch({headless:true}); await b.close();' >"artifacts/$mode/browser-probe.log" 2>&1; then
  ./node_modules/.bin/playwright install chromium >"artifacts/$mode/browser-install.log" 2>&1
fi
node workbench/scripts/build-ui.cjs
cp workbench/web/app.js "artifacts/$mode/app.js"
if ! node demo.mjs "$mode" >"artifacts/$mode/run.log" 2>&1; then
  tail -18 "artifacts/$mode/run.log" >&2
  exit 1
fi
if [[ "$mode" == record ]]; then
  python3 finalize.py
fi
printf '%s\n' "阶段完成：${mode}。证据在 artifacts/${mode}。"
