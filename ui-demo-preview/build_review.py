import subprocess
import sys
from pathlib import Path

root=Path(__file__).resolve().parent
skill=Path.home()/'.pi/agent/skills/ui-demo-preview/scripts'
subprocess.run([sys.executable,str(root/'build_mockups.py')],check=True)
subprocess.run([sys.executable,str(skill/'build_preview.py'),str(root/'scenes.json'),'--output-dir',str(root)],check=True)
p=root/'preview.html';s=p.read_text()
replacements={
 'lang="en"':'lang="zh-CN"',
 ' · storyboard preview':' · 领导版设计评审',
 'SVG FIRST · RECORD LATER':'先审设计，再录演示',
 'Switch scenes, mark Keep, Revise, or Cut, then export notes. No video or generated images used.':'五屏领导版 mockup。请评审业务表达与独立方案。当前只支持切屏和设计反馈，画内按钮为示意；不会执行业务操作。',
 'aria-label="Scenes"':'aria-label="五屏设计稿"',
 'aria-label="Scene decision"':'aria-label="本屏设计意见"',
 '>Keep<':'>保留此屏<','>Revise<':'>需要修改<','>Cut<':'>建议删去<',
 'placeholder="What should change in this scene?"':'aria-label="本屏修改意见" placeholder="例如：去掉术语；把这一项改成独立解决路线。意见自动保存在本机。"',
 '<dt>Action</dt>':'<dt>拟议交互</dt>', '<dt>Subtitle</dt>':'<dt>演示表达</dt>',
 'SCENE ':'第 ',
 'Source: ':'来源项目：', 'Pi session: ':'Pi 会话：',
 'id="export">Export feedback JSON':'id="export" data-export-label="Export feedback JSON">导出设计意见',
 '<footer><span>':'<footer data-source-label="Source:" data-session-label="Pi session:"><span>',
}
for old,new in replacements.items():s=s.replace(old,new)
s=s.replace('</style>', '''
:root{--bg:#f4f2ed;--panel:#fefdf9;--line:#d5dbd4;--text:#202a28;--muted:#626d68;--accent:#214f42}
body{background:var(--bg);font-family:'Avenir Next','PingFang SC','Microsoft YaHei',sans-serif}
main{width:min(1280px,calc(100% - 32px))}h1{letter-spacing:0;font-weight:600}
.scene-button,.choices button,.export{background:var(--panel);border-radius:6px}
.scene-button.active,.choices button.selected{background:#e8eee7;box-shadow:none}.scene-button span{color:var(--muted)}
.scene{background:var(--panel);border-radius:10px;box-shadow:none}.canvas{background:var(--bg)}
textarea{background:var(--bg);border-radius:6px}footer{color:var(--muted);line-height:1.7}footer span{overflow-wrap:anywhere;min-width:0}.export{color:var(--accent);flex-shrink:0}
button:focus-visible,textarea:focus-visible{outline:3px solid #b87827;outline-offset:3px}
.review-status{margin:18px 0;color:var(--accent);font-size:14px}.review button{white-space:nowrap}
@media(max-width:760px){.choices{flex-wrap:wrap}.scene-copy{padding:18px}.review{padding:0 18px 18px}footer button{margin-top:14px}.canvas{overflow-x:auto;aspect-ratio:auto}.canvas svg{min-width:900px;height:auto}.scene-copy h2{font-size:22px}}
</style>''')
s=s.replace('<nav class="scene-nav"','<p class="review-status" role="status">等待你批准设计。尚未修改正式工作台，也未开始新录制。</p><nav class="scene-nav"')
s=s.replace('</body>', '''<script>
document.querySelectorAll('[data-choice]').forEach(button=>button.addEventListener('click',()=>{
 document.querySelector('[role="status"]').textContent='设计意见已保存在本机。导出后可交回修改；这不是业务执行授权。';
}));
</script></body>''')
p.write_text(s)
p=root/'storyboard.svg';s=p.read_text().replace('Static SVG storyboard · 5 scenes · review before recording','五屏静态设计稿 · 先评审，再实施与录制').replace('Source:','来源项目：').replace('Pi session:','Pi 会话：')
for old,new in {'#07111f':'#f4f2ed','#f8fafc':'#202a28','#94a3b8':'#626d68','#111827':'#fefdf9','#334155':'#d5dbd4','#2563eb':'#214f42'}.items():s=s.replace(old,new)
p.write_text(s)
subprocess.run([sys.executable,str(skill/'validate_preview.py'),str(root/'scenes.json'),str(root/'preview.html'),str(root/'storyboard.svg')],check=True)
