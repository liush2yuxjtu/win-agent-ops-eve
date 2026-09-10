import json
import tempfile
from pathlib import Path
from playwright.sync_api import sync_playwright

root=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory() as temp, sync_playwright() as p:
    browser=p.chromium.launch(headless=True)
    page=browser.new_page(viewport={'width':1440,'height':1000},accept_downloads=True)
    errors=[];remote=[];checks=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.on('request',lambda r:remote.append(r.url) if r.url.startswith(('http://','https://')) else None)
    page.goto((root/'index.html').as_uri())
    assert page.locator('nav').count()==0
    assert page.get_by_role('region',name='内嵌 HTML 产品原型').count()==1
    def route(view):
        if view=='signals': page.locator('.context-actions [data-view="signals"]').click()
        elif view=='history': page.locator('.context-actions [data-view="history"]').click()
        elif view=='quality': page.locator('.quality-entry [data-view="quality"]').click()
        else:
            page.locator('.case[aria-pressed="true"]').click()
            if view=='solutions': page.get_by_role('button',name='比较独立解决方案',exact=True).click()
    route('signals')
    page.get_by_role('button',name='合并相关信号（模拟）',exact=True).click()
    assert page.get_by_role('button',name='相关信号已归并',exact=True).is_disabled()
    assert page.locator('#cases').inner_text().find('3 条信号已归并为同一问题')>=0
    checks.append('合并信号更新证据区与问题队列，重复操作不可再次计入')
    page.get_by_role('button',name='体验异常处理',exact=True).click()
    route('triage')
    for label in ['已经确认','可能原因','还需核实','责任范围']:
        assert label in page.locator('#content').inner_text()
    assert '尚无证据归责到个人' in page.locator('#content').inner_text()
    checks.append('领导版分诊区分事实、推测、未知与责任范围')
    route('solutions')
    assert page.locator('.plan-choice').count()==5
    for letter in 'ABCDE':
        page.locator(f'.plan-choice[data-id="{letter}"]').click()
        name=page.locator(f'.plan-choice[data-id="{letter}"] b').inner_text()
        assert name in page.locator('#plan-detail h3').inner_text()
        assert page.locator('#summary-plan').inner_text()==name
    assert page.locator('#plan-detail dt').count()==6
    page.locator('.plan-choice[data-id="B"]').click()
    page.get_by_role('button',name='保存方案选择（演示）',exact=True).click()
    assert '请填写选择理由' in page.get_by_role('status').inner_text()
    note='优先恢复客户业务；<img src=x onerror=alert(1)> 仅作为文字保存'
    page.get_by_role('textbox',name='选择理由',exact=True).fill(note)
    page.get_by_role('button',name='保存方案选择（演示）',exact=True).click()
    assert '恢复上一稳定版本' in page.locator('#summary').inner_text()
    checks.append('五条独立路线可试选，六类取舍完整，选择同时更新主面板与摘要')
    route('history')
    for result in ['success','failed','recurred','falsealarm']:
        page.get_by_label('结果类型',exact=True).select_option(result)
        page.get_by_role('textbox',name='处理结果说明',exact=True).fill('演示验证依据 '+result)
        page.get_by_role('button',name='记录处理结果（演示）',exact=True).click()
    assert note in page.locator('#content').inner_text()
    assert page.locator('#content img').count()==0
    page.reload()
    assert '演示验证依据 recurred' in page.locator('#content').inner_text()
    assert '浏览器本地存储' in page.locator('#content').inner_text()
    checks.append('选择、归因、全部备选方案和结果持久保存；刷新后仍可见，不执行用户输入HTML')
    route('quality')
    assert '真实质量尚未测量' in page.locator('#content').inner_text()
    page.get_by_role('button',name='检查潜在风险（模拟）',exact=True).click()
    assert '2 个关注事项' in page.locator('#case-count').inner_text()
    assert page.get_by_role('button',name='潜在风险候选已加入',exact=True).is_disabled()
    page.get_by_role('button',name='整理改进依据（模拟）',exact=True).click()
    text=page.locator('#review-needs').inner_text()
    for label in ['无效反馈','复发反馈','疑似误报','真实评测未运行']:assert label in text
    checks.append('潜在风险更新队列，结果反馈生成复核关注点，不编造命中率或已运行评测')
    page.locator('.case[data-id="queue"]').click()
    route('solutions')
    assert page.locator('.plan-choice').count()==4
    route('history')
    assert '还没有方案选择' in page.locator('#content').inner_text()
    checks.append('第二个问题只有四条合理路线，不硬凑五条，历史和草稿按问题隔离')
    with page.expect_download() as event:
        page.get_by_role('button',name='导出演示记录',exact=True).click()
    target=Path(temp)/'export.json';event.value.save_as(target)
    saved=json.loads(target.read_text());assert saved['simulated'] is True
    decision=next(r for r in saved['records'] if r['kind']=='decision')
    assert len(decision['alternatives'])==5 and len(decision['evidence'])==3
    assert decision['recommendedPlanId']=='B' and decision['diagnosis']['responsibility']
    assert len([r for r in saved['records'] if r['kind']=='outcome'])==4
    assert len([r for r in saved['records'] if r['kind']=='association'])==1
    checks.append('导出保留证据、判断、方案快照、选择理由、推荐版本和反馈关联')
    for width in [390,820,1440]:
        page.set_viewport_size({'width':width,'height':1000})
        for view in ['signals','triage','solutions','history','quality']:
            route(view)
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),(width,view)
    page.locator('.context-actions [data-view="signals"]').focus();page.keyboard.press('Enter')
    assert page.locator('#window-label').inner_text()=='从红灯发现问题'
    checks.append('顶部五菜单已删除，五项能力由上下文按钮进入，三种宽度无页面横向溢出，键盘可操作')
    assert not errors,errors
    assert not remote,remote
    report={'passed':True,'checks':checks,'browserErrors':errors,'externalRequests':remote,'videoRecorded':False,'screenshotsTaken':False,'productionChanged':False}
    (root/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    print(json.dumps(report,ensure_ascii=False,indent=2))
    browser.close()
