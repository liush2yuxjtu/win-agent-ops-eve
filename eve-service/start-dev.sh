#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
umask 077
if curl --silent --fail --max-time 2 http://127.0.0.1:21876/eve/v1/health >/dev/null; then
  if [[ -f dev.pid ]] && lsof -a -p "$(<dev.pid)" -d cwd -Fn 2>/dev/null | grep -Fqx "n$PWD"; then
    printf '%s\n' 'Eve 开发服务已响应；复用本目录实例。'
    exit 0
  fi
  printf '%s\n' '端口已有 Eve 服务但归属未匹配；未修改该进程。' >&2
  exit 1
fi
if [[ -f dev.pid ]] && kill -0 "$(<dev.pid)" 2>/dev/null; then
  printf '%s\n' '已记录进程仍在运行但未就绪；查看 dev.log，不另起进程。' >&2
  exit 1
fi
set -a
source "$HOME/.config/cpa-luna.env"
set +a
[[ -s .ops-token ]] || openssl rand -hex 32 > .ops-token
export OPS_EVE_TOKEN="$(<.ops-token)"
nohup ./node_modules/.bin/eve dev --no-ui --host 127.0.0.1 --port 21876 >dev.log 2>&1 </dev/null &
pid=$!
printf '%s\n' "$pid" >dev.pid
for attempt in {1..60}; do
  kill -0 "$pid" 2>/dev/null || { printf '%s\n' 'Eve 启动失败，查看 dev.log。' >&2; exit 1; }
  if curl --silent --fail --max-time 1 http://127.0.0.1:21876/eve/v1/health >/dev/null; then
    printf '%s\n' 'Eve 开发服务就绪，127.0.0.1:21876。'
    exit 0
  fi
  sleep 1
done
printf '%s\n' '启动等待超时；保留日志和 PID，未声称成功。' >&2
exit 1
