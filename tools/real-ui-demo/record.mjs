import { chromium } from 'playwright';
import { mkdir, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { performance } from 'node:perf_hooks';
import { createHash } from 'node:crypto';

const mode=process.argv[2]||'discover',out=path.resolve('artifacts',mode),url='http://127.0.0.1:8766';
await mkdir(out,{recursive:true});
const browser=await chromium.launch({headless:true});
const context=await browser.newContext({viewport:{width:1440,height:1000},locale:'zh-CN',...(mode==='record'?{recordVideo:{dir:path.join(out,'raw'),size:{width:1440,height:1000}}}:{})});
const started=performance.now(),page=await context.newPage(),errors=[],markers=[];
let closed=false,runId=null;
page.on('pageerror',e=>errors.push(String(e)));
page.on('popup',()=>errors.push('意外弹出新页面'));
page.on('response',async response=>{if(response.url()===url+'/api/diagnose'&&response.request().method()==='POST'&&response.ok()){try{runId=(await response.json()).runId;}catch{}}});
const hold=s=>page.waitForTimeout(s*1000);
async function mark(label,extra={}){const data=await page.evaluate(()=>({scrollY,viewport:{width:innerWidth,height:innerHeight}}));const row={label,elapsedMs:Math.round(performance.now()-started),...data,...extra};markers.push(row);return row;}
async function overlay(){await page.evaluate(()=>{
 document.querySelector('#record-overlay')?.remove();const layer=document.createElement('div');layer.id='record-overlay';layer.style.cssText='position:fixed;inset:0;pointer-events:none;z-index:2147483647';
 const tag=document.createElement('div');tag.textContent='真实应用录制 · 监控 / Eve / SQLite';tag.style.cssText='position:fixed;top:10px;right:22px;background:#234a86;color:white;padding:6px 10px;border-radius:5px;font:13px system-ui';
 const sub=document.createElement('div');sub.id='record-caption';sub.style.cssText='position:fixed;bottom:12px;left:50%;transform:translateX(-50%);max-width:95vw;white-space:nowrap;color:white;background:rgba(26,38,57,.96);padding:11px 24px;border-radius:7px;font:19px system-ui';
 const cursor=document.createElement('div');cursor.id='record-cursor';cursor.style.cssText='position:fixed;left:-50px;top:-50px;width:20px;height:20px;border-radius:50%;border:3px solid #df9c35;background:#efb75044;transform:translate(-50%,-50%);box-shadow:0 0 0 2px white';
 layer.append(tag,sub,cursor);document.body.append(layer);document.onmousemove=e=>{cursor.style.left=e.clientX+'px';cursor.style.top=e.clientY+'px';};
});}
async function caption(text){await page.locator('#record-caption').evaluate((el,s)=>el.textContent=s,text);}
async function frame(locator,label,top=90){await locator.evaluate((el,y)=>scrollTo({top:Math.max(0,el.getBoundingClientRect().top+scrollY-y),behavior:'smooth'}),top);await hold(.8);const rect=await locator.boundingBox();if(!rect||rect.y<55||rect.y+rect.height>930)throw Error('FRAMING FAIL '+label+' '+JSON.stringify(rect));await mark('frame-'+label,{rect});}
async function click(locator,label,framed=false){if(!framed)await frame(locator,label,160);const b=await locator.boundingBox();if(!b)throw Error('CLICK FAIL '+label);await page.mouse.move(b.x+b.width/2,b.y+b.height/2,{steps:12});await hold(.35);await mark('click-'+label,{rect:b});await locator.click();await hold(.9);}
async function appState(){return await page.request.get(url+'/api/state').then(r=>r.json());}
try{
 await page.goto(url);await page.locator('.issue-item').first().waitFor();
 const health=await page.request.get(url+'/health').then(r=>r.json());if(health.ui!=='leader-live-v1')throw Error('不是批准后实施的真实工作台');
 const before=await appState(),selected=before.issues.find(i=>i.id==='scaro.auth')||before.issues.find(i=>i.status!=='pass')||before.issues[0];if(!selected)throw Error('没有真实监控问题，不用样例替代');
 const asset=await page.request.get(url+'/app.js').then(r=>r.body());
 const provenance={url,health,selectedIssue:selected.id,frontendSha256:createHash('sha256').update(asset).digest('hex'),before:before.metrics,collector:before.collector,fixtureServer:false,mockedModel:false};
 delete provenance.collector.source;
 await overlay();
 if(mode==='discover'){
  const controls=await page.locator('button,input,textarea,select,summary').evaluateAll(nodes=>nodes.map(n=>({tag:n.tagName,text:n.textContent?.slice(0,100),label:n.getAttribute('aria-label'),rect:n.getBoundingClientRect().toJSON()})));
  await writeFile(path.join(out,'discovery.json'),JSON.stringify({provenance,controls,errors},null,2));await page.screenshot({path:path.join(out,'screen.png')});
 }else{
  await caption('真实监控中的问题，直接进入领导简报');await hold(.4);await mark('orient');await hold(4);
  const entry=page.locator('.issue-item[data-issue-id="'+selected.id+'"]');
  await click(entry,'select-issue');
  const box=page.locator('.document .summary-box').first();await frame(box,'request');
  await caption('生成领导简报 · 真实模型等待片段加速展示');
  await click(page.getByRole('button',{name:'生成领导简报',exact:true}),'generate',true);await mark('wait-start');
  await page.getByRole('status').filter({hasText:'领导简报已保存到 SQLite'}).waitFor({timeout:250000});await mark('wait-end');
  if(!runId)throw Error('未捕获真实诊断请求');
  const run=await page.request.get(url+'/api/model-run?id='+encodeURIComponent(runId)).then(r=>r.json());
  if(run.state!=='completed'||run.report.audience!=='leadership-v1')throw Error('领导诊断未真实完成');
  const revision=run.report.diagnosisRevision;
  await caption('领导先看业务影响，不必先读技术日志');await frame(page.locator('.document .lead'),'impact',180);await mark('impact');await hold(4);await page.screenshot({path:path.join(out,'impact.png')});
  await caption('区分原因假设与已经确认的证据');await frame(page.locator('.brief-grid'),'triage');await mark('triage');await hold(4);await page.screenshot({path:path.join(out,'triage.png')});
  await caption('每条方案是独立路线，不是步骤一至五');await frame(page.locator('.plan-list'),'plans');await mark('plans');await hold(4);
  const rows=page.locator('.plan-row');const count=await rows.count();if(count>1){await click(rows.nth(1),'try-alternative',true);await hold(2);await click(rows.first(),'return-first',true);}
  await frame(page.locator('#plan-preview'),'chosen-plan');await mark('chosen-plan');await hold(3);
  await caption('确认前看清取舍；本次录制不保存人为决定');
  await click(page.getByRole('button',{name:'记录这个方案',exact:true}),'open-confirm',true);
  const dialog=page.getByRole('dialog',{name:'确认这条处理建议'});await dialog.waitFor();
  await page.evaluate(()=>{const dialog=document.querySelector('dialog[open]'),layer=document.querySelector('#record-overlay'),sub=document.querySelector('#record-caption');dialog.append(layer);Object.assign(sub.style,{left:'18px',width:'360px',maxWidth:'360px',whiteSpace:'normal',transform:'none',fontSize:'16px'});dialog.addEventListener('close',()=>{document.body.append(layer);Object.assign(sub.style,{left:'50%',width:'auto',maxWidth:'95vw',whiteSpace:'nowrap',transform:'translateX(-50%)',fontSize:'19px'});},{once:true});});
  const dialogRect=await dialog.boundingBox();if(!dialogRect||dialogRect.y<0||dialogRect.y+dialogRect.height>1000)throw Error('确认窗口超出视口');
  await mark('review');await hold(4);await page.screenshot({path:path.join(out,'confirmation.png')});
  const back=dialog.getByRole('button',{name:'返回比较',exact:true});await back.scrollIntoViewIfNeeded();await click(back,'cancel-confirm',true);
  await page.evaluate(()=>document.body.append(document.querySelector('#record-overlay')));
  await caption('查看 SQLite 中刚保存的真实诊断');
  await click(page.locator('.side-nav button[data-page="history"]'),'history');
  const saved=page.locator('[data-diagnosis-id="'+revision+'"]');await saved.waitFor();await frame(saved,'saved-diagnosis');await hold(3);await mark('reload');await caption('重新加载应用，核实诊断历史没有丢失');await hold(1);
  await page.reload();await page.locator('.issue-item').first().waitFor();await overlay();await caption('重新打开同一真实问题的历史');
  await click(page.locator('.issue-item[data-issue-id="'+selected.id+'"]'),'reselect');
  await click(page.locator('.side-nav button[data-page="history"]'),'reopen-history');
  const persisted=page.locator('[data-diagnosis-id="'+revision+'"]');await persisted.waitFor();await frame(persisted,'persisted');await mark('persisted');await caption('真实诊断仍在。没有虚构采纳，也没有宣称修复完成');await hold(5);await page.screenshot({path:path.join(out,'persisted.png')});await mark('end');
  const after=await appState();if(after.metrics.decisions!==before.metrics.decisions||after.metrics.outcomes!==before.metrics.outcomes)throw Error('录制期间出现决定或结果写入，需核验来源');if(errors.length)throw Error(errors.join('\n'));
  await writeFile(path.join(out,'proof.json'),JSON.stringify({semantics:'OK',framing:'OK',interaction:'OK',provenance,runId,sessionId:run.report.sessionId,diagnosisRevision:revision,solutions:count,after:after.metrics,decisionsWritten:0,outcomesWritten:0,realSQLitePersistence:true,errors,markers},null,2));
  if(mode==='record'){const video=page.video();await context.close();closed=true;await video.saveAs(path.join(out,'raw.webm'));}
 }
 await writeFile(path.join(out,'markers.json'),JSON.stringify(markers,null,2));
 console.log(JSON.stringify({mode,errors,runId}));
}finally{if(!closed)await context.close();await browser.close();}
