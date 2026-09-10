"""Restart only this workbench after checking ownership and active diagnosis runs."""
import json
import os
from pathlib import Path
import shlex
import signal
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'app'))
from store import Store

store=Store()
with store.connect() as c:
    if c.execute("SELECT count(*) FROM model_runs WHERE state='running' AND started>?",(time.time()-240,)).fetchone()[0]:
        raise RuntimeError('真实诊断仍在进行，未中断或重启服务')
store.backup()
runtime=ROOT/'data/runtime.json'
if runtime.exists():
    value=json.loads(runtime.read_text())
    process=subprocess.run(['ps','-p',str(value['pid']),'-o','command='],capture_output=True,text=True)
    if process.returncode==0:
        args=shlex.split(process.stdout.strip())
        if len(args)!=4 or not Path(args[0]).name.startswith('python') or args[1:]!=[str(ROOT/'app/server.py'),'--port',str(value['port'])]:
            raise RuntimeError('PID 与本工作台命令不匹配，未停止进程')
        os.kill(value['pid'],signal.SIGTERM)
        for _ in range(50):
            try:os.kill(value['pid'],0)
            except ProcessLookupError:break
            time.sleep(.1)
        else:raise RuntimeError('进程尚未退出，未启动第二份服务')
subprocess.run([sys.executable,str(ROOT/'scripts/start.py')],check=True)
