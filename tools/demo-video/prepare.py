"""Copy only reviewed source files, never runtime state or credentials."""
import hashlib
import json
from pathlib import Path
import shutil

here=Path(__file__).resolve().parent
root=here.parents[1]
files=['app/model.py','app/rules.py','app/server.py','app/store.py','web/app.jsx','web/index.html','web/style.css','scripts/build-ui.cjs']
manifest={}
for name in files:
    source=root/name
    if source.is_symlink():
        raise ValueError('拒绝通过软链接扩大演示传输范围')
    target=here/'workbench'/name
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(source,target)
    manifest[name]=hashlib.sha256(source.read_bytes()).hexdigest()
(here/'source-manifest.json').write_text(json.dumps(manifest,indent=2))
print('已准备八个源文件；未复制 SQLite、历史会话、凭据或浏览器状态。')
