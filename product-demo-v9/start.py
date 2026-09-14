#!/usr/bin/env python3
"""Start or reuse the Web Mock TUI demo."""
import json
from pathlib import Path
import subprocess
import sys
import time
import urllib.error
import urllib.request

HERE = Path(__file__).resolve().parent
URL = 'http://127.0.0.1:8772'


def healthy():
    try:
        with urllib.request.urlopen(URL + '/health', timeout=2) as response:
            data = json.load(response)
        if data.get('app') != 'win-agent-ops-mock-tui-v9':
            raise RuntimeError('8772 已被其他服务占用；不会关闭该服务。')
        return True
    except urllib.error.HTTPError as error:
        raise RuntimeError('8772 已被其他服务占用且未返回 V9 健康 JSON。') from error
    except urllib.error.URLError:
        return False
    except json.JSONDecodeError as error:
        raise RuntimeError('8772 已被其他服务占用且未返回 V9 健康 JSON。') from error


if __name__ == '__main__':
    if not healthy():
        data = HERE.parent / 'data'
        data.mkdir(exist_ok=True)
        with (data / 'product-demo-v9.log').open('ab') as log:
            child = subprocess.Popen([sys.executable, str(HERE / 'server.py')], stdout=log, stderr=log, start_new_session=True)
        for _ in range(50):
            if child.poll() is not None:
                raise RuntimeError('演示启动失败；检查 data/product-demo-v9.log。')
            if healthy():
                (data / 'product-demo-v9.pid').write_text(str(child.pid))
                break
            time.sleep(.2)
        else:
            child.terminate()
            raise RuntimeError('演示未在限定时间内就绪。')
    print(URL)
