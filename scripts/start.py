#!/usr/bin/env python3
"""Idempotent launcher; never stops another process or opens a GUI."""
import fcntl
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
RUNTIME=ROOT/'data'

def health(port):
    try:
        opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(f'http://127.0.0.1:{port}/health',timeout=2) as r:
            return json.load(r).get('app')=='win-agent-ops'
    except Exception:return False

def main():
    os.umask(0o077);RUNTIME.mkdir(exist_ok=True,mode=0o700)
    with (RUNTIME/'launcher.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        if (RUNTIME/'runtime.json').exists():
            old=json.loads((RUNTIME/'runtime.json').read_text())
            if health(old['port']):print(old['url']);return
        for port in range(8766,8776):
            sock=socket.socket()
            try:sock.bind(('127.0.0.1',port))
            except OSError:sock.close();continue
            sock.close();break
        else:raise RuntimeError('候选端口均被占用；未停止任何现有服务')
        with (RUNTIME/'server.log').open('ab') as log:
            child=subprocess.Popen([sys.executable,str(ROOT/'app/server.py'),'--port',str(port)],cwd=ROOT,stdout=log,stderr=log,stdin=subprocess.DEVNULL,start_new_session=True)
        for _ in range(50):
            if child.poll() is not None:raise RuntimeError('服务启动失败，详情见 data/server.log')
            if health(port):break
            time.sleep(.1)
        else:raise RuntimeError('服务未在 5 秒内就绪；保留进程日志，未宣称已运行')
        result={'pid':child.pid,'port':port,'url':f'http://127.0.0.1:{port}/','started':time.time()}
        (RUNTIME/'runtime.json').write_text(json.dumps(result));print(result['url'])
if __name__=='__main__':main()
