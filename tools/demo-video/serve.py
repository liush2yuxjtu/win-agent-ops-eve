import json
import os
from pathlib import Path
import subprocess
import sys

sys.path.insert(0,str(Path(__file__).parent/'workbench/app'))
import model

def local_eve(packet):
    service=Path.home()/'projects/win-agent-ops-eve/eve-service'
    result=subprocess.run(['node','diagnose.mjs'],cwd=service,input=json.dumps(packet,ensure_ascii=False),text=True,capture_output=True,timeout=215)
    if result.returncode:
        raise RuntimeError('真实 Eve 调用失败：'+result.stderr[-500:])
    report=json.loads(result.stdout)
    if report['issue']!=packet['issue'] or report['revision']!=packet['revision']:
        raise ValueError('Eve 证据版本不匹配')
    return report

model.diagnose_remote=local_eve
import server
server.main()
