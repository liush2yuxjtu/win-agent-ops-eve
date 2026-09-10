import json
import tempfile
from pathlib import Path
from playwright.sync_api import sync_playwright

root=Path(__file__).resolve().parent
errors=[];requests=[];overlaps=[]
with tempfile.TemporaryDirectory() as temp, sync_playwright() as p:
    browser=p.chromium.launch(headless=True)
    page=browser.new_page(viewport={'width':1440,'height':1000},accept_downloads=True)
    page.on('pageerror',lambda error:errors.append(str(error)))
    page.on('request',lambda request:requests.append(request.url) if request.url.startswith(('http://','https://')) else None)
    page.goto((root/'preview.html').as_uri())
    assert page.locator('.scene-button').count()==5
    for index in range(5):
        page.locator('.scene-button').nth(index).click()
        panel=page.locator('.scene:not([hidden])')
        assert panel.count()==1
        panel.get_by_role('button',name='保留此屏',exact=True).click()
        panel.get_by_role('textbox',name='本屏修改意见').fill('设计反馈 '+str(index))
        findings=panel.locator('svg').evaluate('''svg=>{
          const boxes=[...svg.querySelectorAll('text')].map(t=>({text:t.textContent,...Object.fromEntries(['x','y','width','height'].map(k=>[k,t.getBBox()[k]]))}));
          const issues=[];
          for(let i=0;i<boxes.length;i++){
            const a=boxes[i];if(a.x<0||a.x+a.width>1280||a.y<0||a.y+a.height>720)issues.push({outside:a});
            for(let j=i+1;j<boxes.length;j++){const b=boxes[j];if(Math.min(a.x+a.width,b.x+b.width)-Math.max(a.x,b.x)>2&&Math.min(a.y+a.height,b.y+b.height)-Math.max(a.y,b.y)>2)issues.push({overlap:[a.text,b.text]});}
          }return issues;
        }''')
        overlaps.extend([{'scene':index+1,**item} for item in findings])
    page.reload()
    assert page.locator('.scene:not([hidden]) textarea').input_value()=='设计反馈 4'
    with page.expect_download() as event:
        page.get_by_role('button',name='导出设计意见',exact=True).click()
    download=event.value;target=Path(temp)/'feedback.json';download.save_as(target)
    feedback=json.loads(target.read_text());assert len(feedback['feedback'])==5
    page.locator('.scene-button').first.click();page.keyboard.press('ArrowRight')
    assert page.locator('.scene:not([hidden])').get_attribute('data-panel')=='triage'
    page.set_viewport_size({'width':390,'height':844})
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
    assert not errors,errors
    assert not requests,requests
    result={'passed':not overlaps,'scenes':5,'switching':True,'feedbackSavedAcrossReload':True,'feedbackExported':True,'keyboardNavigation':True,'mobilePageOverflow':False,'remoteRequests':requests,'scriptErrors':errors,'textGeometryIssues':overlaps,'screenshotsTaken':False,'recordingStarted':False}
    (root/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps(result,ensure_ascii=False))
    browser.close()
    assert not overlaps,overlaps
