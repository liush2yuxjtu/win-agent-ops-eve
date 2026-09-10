#!/bin/bash
set -euo pipefail
mode="${1:-discover}"
mkdir -p "artifacts/$mode"
node -p 'require("playwright/package.json").version' >"artifacts/$mode/playwright-version.txt"
node --input-type=module -e 'import {chromium} from "playwright"; const b=await chromium.launch({headless:true}); await b.close();' >"artifacts/$mode/browser-check.log" 2>&1
if ! node record.mjs "$mode" >"artifacts/$mode/run.log" 2>&1; then
 tail -20 "artifacts/$mode/run.log" >&2
 exit 1
fi
if [[ "$mode" == record ]]; then python3 finalize.py; fi
printf '%s\n' "真实应用阶段完成：${mode}"
