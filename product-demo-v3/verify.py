import json
import tempfile
from pathlib import Path
from playwright.sync_api import sync_playwright

root=Path(__file__).resolve().parent
(root/'qa').mkdir(exist_ok=True)
with tempfile.TemporaryDirectory() as temp, sync_playwright() as p:
    browser=p.chromium.launch(headless=True)
    page=browser.new_page(viewport={'width':1440,'height':1000},accept_downloads=True)
    errors=[];requests=[];checks=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.on('request',lambda r:requests.append(r.url) if r.url.startswith(('http://','https://')) else None)
    page.goto((root/'index.html').as_uri())
    assert page.locator('.stage-wallpaper,.demo-stage,.intro,.nav').count()==0
    assert page.locator('.side-nav button').count()==3
    page.get_by_role('heading',name='客户登录异常',exact=True).wait_for()
    page.screenshot(path=str(root/'qa/desktop.png'))
    checks.append('全新白底应用布局，无旧版大标题、背景舞台和顶部五菜单')
    page.get_by_role('button',name='查看证据',exact=True).click()
    page.get_by_role('button',name='确认样例关联',exact=True).click()
    page.get_by_role('button',name='查看证据',exact=True).click()
    assert page.get_by_role('button',name='样例关联已确认',exact=True).is_disabled()
    assert '3 条信号已关联' in page.locator('.issues').inner_text()
    checks.append('关联信号更新列表和证据，不重复归并')
    page.get_by_role('button',name='比较处理方案',exact=True).click()
    assert page.locator('.plan-row').count()==5
    for id in 'ABCDE':
        row=page.locator(f'.plan-row[data-id="{id}"]');row.click();name=row.locator('b').inner_text()
        assert page.locator('#plan-preview h3').inner_text()==name
        assert page.locator('.chosen-name').inner_text()==name
    page.locator('.plan-row[data-id="B"]').click()
    page.get_by_role('button',name='记录这个方案',exact=True).click()
    assert page.get_by_role('dialog',name='确认这条处理建议').is_visible()
    page.screenshot(path=str(root/'qa/confirmation.png'))
    page.keyboard.press('Escape')
    assert not page.locator('#decision').is_visible()
    assert '尚未保存' in page.locator('#inspector').inner_text()
    page.get_by_role('button',name='记录这个方案',exact=True).click()
    page.get_by_role('button',name='确认保存建议',exact=True).click()
    assert '请写明选择理由' in page.locator('#decision-error').inner_text()
    note='优先恢复业务；<img src=x onerror=alert(1)> 只是文字'
    page.get_by_role('textbox',name='为什么选择这个方案？',exact=True).fill(note)
    page.get_by_role('button',name='确认保存建议',exact=True).click()
    assert not page.locator('#decision').is_visible()
    assert '未执行' in page.locator('#inspector').inner_text()
    checks.append('五条独立路线联动；保存前集中确认；取消不保存；理由必填')
    page.locator('.side-nav [data-page="history"]').click()
    for result in ['failed','recurred','falsealarm']:
        page.get_by_label('结果类型',exact=True).select_option(result)
        page.get_by_role('textbox',name='业务验证或复发说明',exact=True).fill('演示反馈 '+result)
        page.get_by_role('button',name='保存处理反馈',exact=True).click()
    page.reload()
    assert note in page.locator('#content').inner_text()
    assert page.locator('#content img').count()==0
    assert '演示反馈 recurred' in page.locator('#content').inner_text()
    page.locator('.side-nav [data-page="quality"]').click()
    page.get_by_role('button',name='检查潜在风险（模拟）',exact=True).click()
    assert page.locator('#issue-count').inner_text()=='2'
    page.get_by_role('button',name='整理本次复核依据',exact=True).click()
    for text in ['无效建议','复发问题','疑似误报','未运行真实评测']:
        assert text in page.locator('#review-needs').inner_text()
    checks.append('刷新恢复完整历史，反馈进入复核；风险候选新增队列，无虚构准确率')
    page.locator('.issue-item[data-id="queue"]').click()
    assert page.locator('.plan-row').count()==4
    assert '尚未保存' in page.locator('#inspector').inner_text()
    page.get_by_role('searchbox',name='查找问题',exact=True).fill('不可能匹配的词')
    assert '没有匹配问题' in page.locator('#issues').inner_text()
    page.get_by_role('searchbox',name='查找问题',exact=True).fill('')
    assert page.locator('.issue-item').count()==2
    checks.append('问题切换和搜索有效；第二问题仅四条合理路线，决定不串联')
    with page.expect_download() as event:page.get_by_role('button',name='导出演示记录',exact=True).click()
    target=Path(temp)/'export.json';event.value.save_as(target);saved=json.loads(target.read_text())
    decision=next(r for r in saved['records'] if r['kind']=='decision')
    assert saved['prototype'] and len(decision['alternatives'])==5 and len(decision['evidence'])==3
    assert decision['recommendedPlanId']=='B'
    assert len([r for r in saved['records'] if r['kind']=='outcome'])==3
    page.get_by_role('button',name='设计参考 · Mobbin',exact=True).click()
    links=page.locator('#references a');assert links.count()==3
    assert all('mobbin.com/explore/screens/' in a for a in links.evaluate_all('(nodes)=>nodes.map(n=>n.href)'))
    page.get_by_role('button',name='关闭设计参考',exact=True).click()
    checks.append('导出保留快照关联；三个核验过的 Mobbin 来源可按需查看')
    for width in [390,820,1440]:
        page.set_viewport_size({'width':width,'height':900})
        for view in ['issue','history','quality']:
            page.locator(f'.side-nav [data-page="{view}"]').click()
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),(width,view)
    page.set_viewport_size({'width':390,'height':844})
    page.locator('.side-nav [data-page="issue"]').click()
    page.get_by_role('button',name='记录这个方案',exact=True).click()
    assert page.locator('#decision-title').bounding_box()['y']>=0
    page.keyboard.press('Escape')
    page.locator('.side-nav [data-page="quality"]').focus();page.keyboard.press('Enter')
    assert page.locator('.side-nav [data-page="quality"]').get_attribute('aria-pressed')=='true'
    assert not errors,errors
    assert not requests,requests
    checks.append('三种宽度无页面溢出；确认窗口标题可见；键盘操作与Esc关闭有效；离线无外部请求')
    report={'passed':True,'checks':checks,'browserErrors':errors,'externalRequests':requests,'recordingStarted':False,'productionChanged':False,'a11y':'语义、键盘、标签与布局检查通过；未完成完整自动化无障碍审计'}
    (root/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False,indent=2))
    browser.close()
