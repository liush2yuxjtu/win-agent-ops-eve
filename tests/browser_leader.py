"""Verify real APIs and Eve with an isolated DB; never seed the production history."""
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
                browser=p.chromium.launch(headless=True);page=browser.new_page(viewport={'width':1440,'height':1000})
                page.on('pageerror',lambda e:errors.append(str(e)))
                page.goto(url);page.locator('.issue-item').first.wait_for()
                page.get_by_role('button',name='生成领导简报',exact=True).click()
                page.get_by_role('status').filter(has_text='领导简报已保存到 SQLite').wait_for(timeout=250000)
                state=page.request.get(url+'/api/state').json();issue=next(i for i in state['issues'] if i['id']=='test.auth')
                assert issue['analysis']['audience']=='leadership-v1'
                for choice in ('defer','reject','adopt'):
                    page.get_by_role('button',name='记录这个方案',exact=True).click()
                    dialog=page.get_by_role('dialog',name='确认这条处理建议');dialog.wait_for()
                    assert dialog.get_by_role('button',name='确认保存决定',exact=True).is_disabled()
                    dialog.get_by_label('你的决定',exact=True).select_option(choice)
                    dialog.get_by_role('textbox',name='为什么这样决定？',exact=True).fill('隔离测试 '+choice+'，未操作真实业务')
                    dialog.get_by_role('button',name='确认保存决定',exact=True).click()
                    dialog.wait_for(state='hidden')
                page.locator('.side-nav [data-page="history"]').click()
                page.get_by_label('结果类型',exact=True).select_option('unverified')
                page.get_by_role('textbox',name='业务验证或复发说明',exact=True).fill('只验证了页面和保存流程，没有执行方案。')
                page.get_by_role('button',name='保存处理反馈',exact=True).click()
                page.get_by_role('status').filter(has_text='人工结果反馈已保存').wait_for()
                state=page.request.get(url+'/api/state').json()
                assert state['metrics']['decisions']==3 and state['metrics']['outcomes']==1
                assert next(i for i in state['issues'] if i['id']=='test.auth')['status']=='fail'
                page.locator('.side-nav [data-page="quality"]').click()
                page.get_by_role('heading',name='真实推荐质量尚未测量',exact=True).wait_for()
                q=page.request.get(url+'/api/quality').json();assert q['outcomes']['unverified']==1 and not q['qualityMeasured']
                anon=browser.new_context();assert anon.request.get(url+'/api/state').status==401;anon.close()
                assert page.request.post(url+'/api/refresh',data={},headers={'Origin':'http://evil.invalid','X-CSRF-Token':state['csrf']}).status==403
                assert page.request.post(url+'/api/refresh',data={},headers={'Origin':url}).status==403
                assert page.request.get(url+'/health',headers={'Host':'evil.invalid'}).status==403
                process.terminate();process.wait(timeout=5);process=start()
                page.reload();page.locator('.issue-item').first.wait_for();page.locator('.side-nav [data-page="history"]').click()
                page.locator('[data-diagnosis-id="'+issue['revision']+'"]').wait_for()
                state=page.request.get(url+'/api/state').json();assert state['metrics']['decisions']==3 and state['metrics']['outcomes']==1
                page.set_viewport_size({'width':390,'height':844})
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
                assert not errors,errors
                report={'passed':True,'engine':'eve-cpa-1','audience':'leadership-v1','sessionId':issue['analysis']['sessionId'],'isolatedDB':True,'checks':['真实 Eve/CPA 生成领导简报','暂缓/拒绝/采纳进入 SQLite，不执行','真实结果反馈与质量汇总','跨站/会话/CSRF/Host 拒绝','进程重启后诊断和记录保留','390px 无页面溢出','无浏览器错误']}
                (ROOT/'verification/leader-browser.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False))
                browser.close()
        finally:
            process.terminate();process.wait(timeout=5)

if __name__=='__main__':main()
