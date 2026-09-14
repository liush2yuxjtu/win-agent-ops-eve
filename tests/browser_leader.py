"""Verify real triage-funnel UI and APIs with an isolated DB."""
import json
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]


def main():
    with tempfile.TemporaryDirectory(prefix='ops-leader-test-') as temp:
        temp=Path(temp);source=temp/'status.json';db=temp/'ops.sqlite'
        source.write_text(json.dumps({'heartbeat':time.time(),'checks':{'test.auth':{'status':'fail','detail':'login-401'}},'deliveryError':None}))
        with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
        url=f'http://127.0.0.1:{port}'
        def start():
            process=subprocess.Popen([sys.executable,str(ROOT/'app/server.py'),'--port',str(port),'--db',str(db),'--source',str(source)],stdout=subprocess.DEVNULL)
            for _ in range(100):
                try:
                    with urllib.request.urlopen(url+'/health',timeout=1):return process
                except OSError:time.sleep(.1)
            raise RuntimeError('测试服务未启动')
        process=start();errors=[]
        try:
            with sync_playwright() as p:
                browser=p.chromium.launch(headless=True,channel='chrome');page=browser.new_page(viewport={'width':1440,'height':1000})
                page.on('pageerror',lambda e:errors.append(str(e)))
                page.goto(url);page.locator('.issue-item').first.wait_for()
                assert page.locator('#triage-real').count()==1
                assert page.locator('#probe-real').count()==1
                assert page.locator('#route-real').count()==1
                assert page.locator('.funnel-stage').count()==3
                assert page.locator('.triage-lane').count()==4
                assert page.locator('.triage-lane button').count()==1
                page.locator('.raw-log summary').click()
                assert page.locator('.raw-log[open]').count()==1
                page.get_by_role('button',name='让 Eve 整理当前问题',exact=True).click()
                page.get_by_role('status').filter(has_text='领导简报已保存到 SQLite').wait_for(timeout=250000)
                state=page.request.get(url+'/api/state').json();issue=next(i for i in state['issues'] if i['id']=='test.auth')
                assert issue['analysis']['audience']=='leadership-v1'
                assert page.locator('.real-route').count()==5
                assert page.locator('.real-route-head').count()==5
                page.get_by_role('button',name='添加探针',exact=True).click()
                dialog=page.get_by_role('dialog');dialog.wait_for()
                assert dialog.get_by_text('ONE APPROVAL GATE',exact=True).count()==1
                assert dialog.get_by_role('button',name='批准并开始',exact=True).count()==1
                dialog.get_by_role('button',name='批准并开始',exact=True).click()
                page.locator('#probe-real').get_by_text('探针已加入处理流程。',exact=True).first.wait_for(timeout=10000)
                page.locator('#probe-real').get_by_text('等待人工反馈：问题已复现、问题已解决或输入反馈。',exact=True).wait_for(timeout=10000)
                assert page.locator('.agent-step').count()>=4
                page.get_by_role('button',name='问题已复现',exact=True).click()
                assert page.locator('#probe-real').get_by_text('反馈已记录：问题已复现。',exact=True).count()>=1
                page.get_by_role('button',name='问题已解决',exact=True).click()
                assert page.locator('#probe-real').get_by_text('反馈已记录：问题已解决。',exact=True).count()>=1
                page.get_by_role('button',name='输入反馈',exact=True).click()
                page.get_by_label('自定义反馈',exact=True).fill('下一轮检查实际执行时间。')
                page.get_by_role('button',name='保存文字反馈',exact=True).click()
                assert page.locator('#probe-real').get_by_text('反馈已记录：自定义文字。',exact=True).count()>=1
                page.locator('.real-route-head').nth(1).click()
                page.get_by_label('决定理由',exact=True).fill('先选择最小范围路线，交给团队手工执行。')
                page.get_by_role('button',name='应用这条路线（只记录）',exact=True).click()
                page.get_by_role('status').filter(has_text='决定已写入真实 SQLite').wait_for(timeout=10000)
                state=page.request.get(url+'/api/state').json()
                assert state['metrics']['decisions']==1
                assert next(i for i in state['issues'] if i['id']=='test.auth')['status']=='fail'
                page.locator('.side-nav [data-page="history"]').click()
                page.get_by_role('heading',name='决策记录',exact=True).wait_for()
                page.locator('[data-diagnosis-id="'+issue['revision']+'"]').wait_for()
                anonymous=browser.new_context();assert anonymous.request.get(url+'/api/state').status==401;anonymous.close()
                assert page.request.post(url+'/api/refresh',data={},headers={'Origin':'http://evil.invalid','X-CSRF-Token':state['csrf']}).status==403
                assert page.request.post(url+'/api/refresh',data={},headers={'Origin':url}).status==403
                assert page.request.get(url+'/health',headers={'Host':'evil.invalid'}).status==403
                process.terminate();process.wait(timeout=5);process=start()
                page.reload();page.locator('.issue-item').first.wait_for();page.set_viewport_size({'width':390,'height':844})
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
                assert not errors,errors
                report={'passed':True,'engine':'eve-cpa-1','audience':'leadership-v1','sessionId':issue['analysis']['sessionId'],'isolatedDB':True,'checks':['三步 Triage Funnel 真实界面','全部问题分诊到 P0-P3','唯一 AskUserQuestion 探针审批门','Agent steps 和人工反馈','5 条路线与 Blast Radius','人工应用只记录不执行','跨站/会话/CSRF/Host 拒绝','进程重启与 390px 布局','无浏览器错误']}
                (ROOT/'verification').mkdir(exist_ok=True)
                (ROOT/'verification/leader-browser.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False))
                browser.close()
        finally:
            process.terminate();process.wait(timeout=5)

if __name__=='__main__':main()
