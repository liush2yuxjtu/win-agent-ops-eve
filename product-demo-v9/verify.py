#!/usr/bin/env python3
"""Browser smoke test for the three-step Web Mock TUI."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path(__file__).resolve().parent / 'verification'
OUT.mkdir(exist_ok=True)
URL = 'http://127.0.0.1:8772'

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, channel='chrome')
    page = browser.new_page(viewport={'width': 1440, 'height': 1000}, device_scale_factor=1)
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.goto(URL, wait_until='networkidle')
    assert page.request.get(URL + '/health').json()['app'] == 'win-agent-ops-mock-tui-v9'
    assert page.locator('#mock-tui').count() == 1
    assert page.locator('.flow-strip-step').count() == 3
    assert page.locator('.tab').count() == 0
    assert page.locator('.stage-block').count() == 3
    assert page.locator('.issue-item').count() == 6
    assert page.locator('.triage-card').count() == 6
    page.screenshot(path=str(OUT / 'desktop-before.png'), full_page=True)

    page.locator('.raw-log summary').click()
    assert page.locator('.raw-log[open]').count() == 1
    page.get_by_role('button', name='p  ADD PROBE').click()
    dialog = page.get_by_role('dialog')
    assert dialog.is_visible()
    assert dialog.get_by_text('ONE APPROVAL GATE', exact=True).count() == 1
    assert dialog.get_by_role('button', name='批准并开始', exact=True).count() == 1
    dialog.get_by_role('button', name='批准并开始', exact=True).click()
    page.locator('#terminal-status').get_by_text('探针已自动加入修复流程。没有执行业务修复。', exact=True).wait_for(timeout=10000)
    page.locator('#terminal-status').get_by_text('探针流程完成。现在等待人工反馈。', exact=True).wait_for(timeout=10000)
    assert page.locator('.agent-step').count() >= 8
    page.get_by_role('button', name='r  ISSUE REPRODUCED').click()
    assert page.locator('.feedback-box').get_by_text('反馈已记录：问题已复现。', exact=True).count() == 1
    page.get_by_role('button', name='s  ISSUE SOLVED').click()
    assert page.locator('.feedback-box').get_by_text('反馈已记录：问题已解决。', exact=True).count() == 1
    page.get_by_role('button', name='t  TYPE PROMPT').click()
    page.locator('#typed-feedback').fill('请下一轮检查真实执行时间')
    page.get_by_role('button', name='保存文字反馈').click()
    assert page.locator('.feedback-box').get_by_text('反馈已记录：自定义文字。', exact=True).count() == 1

    assert page.locator('.route').count() == 5
    assert page.get_by_text('BLAST RADIUS', exact=True).count() == 5
    page.locator('.route-head').last.click()
    assert page.locator('.route.selected').count() == 1
    page.get_by_role('button', name='a  APPLY SELECTED FIX').click()
    assert page.get_by_role('button', name='✓ FIX APPLIED · MOCK', exact=True).count() == 1

    page.screenshot(path=str(OUT / 'desktop-after.png'), full_page=True)
    page.set_viewport_size({'width': 390, 'height': 844})
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    page.screenshot(path=str(OUT / 'mobile.png'), full_page=True)
    assert not errors, errors
    result = {
        'passed': True,
        'mode': 'web-mock-tui',
        'checks': [
            '三步流程，无大 tab', '全部已有问题标题与描述', 'P0/P1/P2/P3 分诊',
            '原始长日志展开', '唯一 AskUserQuestion 审批门', 'Agent steps 动态展示',
            '问题已复现/问题已解决/输入反馈', '5 条路线与 Blast Radius',
            '人选路线并应用 Mock fix', '390px 无页面横向溢出', '浏览器无脚本错误',
        ],
        'productionActions': False,
    }
    (OUT / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2))
    print(json.dumps(result, ensure_ascii=False))
    browser.close()
