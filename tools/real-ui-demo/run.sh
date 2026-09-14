#!/bin/bash
set -euo pipefail
mode="${1:-discover}"
mkdir -p "artifacts/$mode"
node -p 'require("playwright/package.json").version' >"artifacts/$mode/playwright-version.txt"
node --input-type=module -e 'import {chromium} from "playwright"; const b=await chromium.launch({headless:true,channel:"chrome"}); await b.close();' >"artifacts/$mode/browser-check.log" 2>&1
if ! node record.mjs "$mode" >"artifacts/$mode/run.log" 2>&1; then
 tail -20 "artifacts/$mode/run.log" >&2
 exit 1
fi
if [[ "$mode" == record ]]; then
  python3 finalize.py
  # Promote final evidence beside the recording workflow so DELIVERY.json has a reproducible target.
  mkdir -p artifacts/real-app-demo-v2
  for file in real-app.mp4 poster.png contact.png chapters.json proof.json QA.json edit.json ffprobe.json markers.json; do
    [[ -f "artifacts/record/$file" ]] && cp "artifacts/record/$file" "artifacts/real-app-demo-v2/$file"
  done
  find artifacts/record -maxdepth 1 -name 'strip-*.png' -exec cp {} artifacts/real-app-demo-v2/ \;
fi
printf '%s\n' "真实应用阶段完成：${mode}"
