import { chromium } from 'playwright';
import { mkdir, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { performance } from 'node:perf_hooks';
import { createHash } from 'node:crypto';

const mode=process.argv[2]||'discover';
const out=path.resolve('artifacts',mode);
const url=process.env.REAL_APP_URL||'http://127.0.0.1:8773';
await mkdir(out,{recursive:true});
const browser=await chromium.launch({headless:true,channel:'chrome'});
const context=await browser.newContext({viewport:{width:1440,height:1000},locale:'zh-CN',...(mode==='record'?{recordVideo:{dir:path.join(out,'raw'),size:{width:1440,height:1000}}}:{})});
const started=performance.now(),page=await context.newPage(),errors=[],markers=[];
let closed=false,runId=null;
page.on('pageerror',error=>errors.push(String(error)));
page.on('popup',()=>errors.push('意外弹出新页面'));
page.on('response',async response=>{if(response.url()===url+'/api/diagnose'&&response.request().method()==='POST'&&response.ok()){try{runId=(await response.json()).runId;}catch{}}});
const hold=seconds=>page.waitForTimeout(seconds*1000);
async function mark(label,extra={}){const data=await page.evaluate(()=>({scrollY,viewport:{width:innerWidth,height:innerHeight}}));const row={label,elapsedMs:Math.round(performance.now()-started),...data,...extra};markers.push(row);return row;}
async function overlay(){await page.evaluate(()=>{document.querySelector('#record-overlay')?.remove();const layer=document.createElement('div');layer.id='record-overlay';layer.style.cssText='position:fixed;inset:0;pointer-events:none;z-index:2147483647';const tag=document.createElement('div');tag.textContent='真实应用 · 三步 Triage Funnel · SQLite';tag.style.cssText='position:fixed;top:12px;right:22px;background:#152a49;color:#c9f48a;padding:7px 11px;border-radius:5px;font:13px system-ui';const sub=document.createElement('div');sub.id='record-caption';sub.style.cssText='position:fixed;bottom:14px;left:50%;transform:translateX(-50%);max-width:92vw;white-space:nowrap;color:#fff;background:rgba(8,16,28,.96);padding:11px 24px;border-radius:6px;font:18px system-ui';const cursor=document.createElement('div');cursor.id='record-cursor';cursor.style.cssText='position:fixed;left:-50px;top:-50px;width:20px;height:20px;border-radius:50%;border:3px solid #b9f36d;background:#b9f36d33;transform:translate(-50%,-50%);box-shadow:0 0 0 2px #07101d';layer.append(tag,sub,cursor);document.body.append(layer);document.onmousemove=event=>{cursor.style.left=event.clientX+'px';cursor.style.top=event.clientY+'px';};});}
async function caption(value){await page.locator('#record-caption').evaluate((element,text)=>element.textContent=text,value);}
async function frame(locator,label,top=125){const element=typeof locator==='string'?page.locator(locator).first():locator.first();await element.evaluate((node,offset)=>scrollTo({top:Math.max(0,node.getBoundingClientRect().top+scrollY-offset),behavior:'smooth'}),top);await hold(.8);const rect=await element.boundingBox();if(!rect||rect.y<55||rect.y+rect.height>945)throw Error(`FRAMING FAIL ${label} ${JSON.stringify(rect)}`);await mark('frame-'+label,{rect});}
async function moveAndClick(locator,label,framed=false){const element=typeof locator==='string'?page.locator(locator).first():locator.first();if(!framed)await frame(element,label);const rect=await element.boundingBox();if(!rect)throw Error(`CLICK FAIL ${label}`);await page.mouse.move(rect.x+rect.width/2,rect.y+rect.height/2,{steps:12});await hold(.35);await mark('click-'+label,{rect});await element.click();await hold(.9);}
async function appState(){return await page.request.get(url+'/api/state').then(response=>response.json());}
async function restoreOverlay(){await page.evaluate(()=>{const layer=document.querySelector('#record-overlay');if(layer&&!document.body.contains(layer))document.body.append(layer);const sub=document.querySelector('#record-caption');if(sub)Object.assign(sub.style,{left:'50%',width:'auto',maxWidth:'92vw',whiteSpace:'nowrap',transform:'translateX(-50%)',fontSize:'18px'});});}
try{
 await page.goto(url);await page.locator('.issue-item').first().waitFor();
 const health=await page.request.get(url+'/health').then(response=>response.json());if(health.ui!=='leader-live-v1')throw Error('不是批准后实施的真实工作台');
 const before=await appState();const selected=before.issues.find(item=>item.id==='scaro.auth')||before.issues.find(item=>item.status!=='pass')||before.issues[0];if(!selected)throw Error('没有真实监控问题，不用样例替代');
 const asset=await page.request.get(url+'/app.js').then(response=>response.body());
 const provenance={url,health,selectedIssue:selected.id,frontendSha256:createHash('sha256').update(asset).digest('hex'),before:before.metrics,fixtureServer:false,mockedModel:false,isolatedRecordingDB:true};
 delete provenance.health.collector;
 await overlay();
 if(mode==='discover'){
  const controls=await page.locator('button,input,textarea,select,summary').evaluateAll(nodes=>nodes.map(node=>({tag:node.tagName,text:node.textContent?.slice(0,120),label:node.getAttribute('aria-label'),rect:node.getBoundingClientRect().toJSON()})));
  await writeFile(path.join(out,'discovery.json'),JSON.stringify({provenance,controls,errors},null,2));await page.screenshot({path:path.join(out,'screen.png')});
 }else{
  await caption('真实问题队列：Agent 先整理，人不先读长日志');await mark('orient');await hold(3);
  await moveAndClick(page.locator('.issue-item[data-issue-id="'+selected.id+'"]'),'select-issue');
  await caption('真实监控证据进入同一条分诊流程');await frame(page.locator('#triage-real .funnel-stage-title'),'triage-entry');await hold(2);
  await caption('Eve 读取真实证据，生成领导简报');await moveAndClick(page.getByRole('button',{name:'让 Eve 整理当前问题',exact:true}),'generate');await mark('wait-start');
  await page.getByRole('status').filter({hasText:'领导简报已保存到 SQLite'}).waitFor({timeout:250000});await mark('wait-end');
  if(!runId)throw Error('未捕获真实诊断请求');
  const run=await page.request.get(url+'/api/model-run?id='+encodeURIComponent(runId)).then(response=>response.json());
  if(run.state!=='completed'||run.report.audience!=='leadership-v1')throw Error('领导诊断未真实完成');
  const revision=run.report.diagnosisRevision;
  await caption('只看分诊结果：影响、优先级和问题描述');await frame(page.locator('#triage-real .selected-real'),'triage-result');await mark('triage');await hold(3);
  await caption('第二步只问一次：允许 Agent 添加探针？');await frame(page.locator('#probe-real .funnel-stage-title'),'probe-entry');await hold(2);await moveAndClick(page.getByRole('button',{name:'添加探针',exact:true}),'open-probe-ask',true);
  const dialog=page.getByRole('dialog');await dialog.waitFor();await page.evaluate(()=>{const dialog=document.querySelector('dialog[open]'),layer=document.querySelector('#record-overlay'),caption=document.querySelector('#record-caption');if(dialog&&layer){dialog.append(layer);Object.assign(caption.style,{left:'18px',width:'360px',maxWidth:'360px',whiteSpace:'normal',transform:'none',fontSize:'16px'});dialog.addEventListener('close',()=>{document.body.append(layer);Object.assign(caption.style,{left:'50%',width:'auto',maxWidth:'92vw',whiteSpace:'nowrap',transform:'translateX(-50%)',fontSize:'18px'});},{once:true});}});
  await mark('probe-ask');await hold(3);await dialog.getByRole('button',{name:'批准并开始',exact:true}).click();await restoreOverlay();await mark('probe-start');
  await page.locator('#probe-real .busy-note').filter({hasText:'探针已加入当前处理流程'}).waitFor({timeout:10000});await mark('probe-added');await page.locator('#probe-real .busy-note').filter({hasText:'等待人工反馈'}).waitFor({timeout:10000});await mark('probe-feedback');await caption('Agent steps 完成，等待人的真实反馈');await hold(2);
  await moveAndClick(page.getByRole('button',{name:'问题已复现',exact:true}),'feedback-reproduced',true);await caption('人反馈：问题已复现；不自动关闭问题');await hold(3);
  await caption('第三步：Agent 给路线，人看 Blast Radius 后选择');await frame(page.locator('#route-real .funnel-stage-title'),'route-entry');await mark('route');await hold(3);
  const routeButtons=page.locator('#route-real .real-route-head');const solutionCount=await routeButtons.count();if(solutionCount<5)throw Error('真实应用未展示五条路线');await moveAndClick(routeButtons.nth(1),'choose-route');await page.getByLabel('决定理由',{exact:true}).pressSequentially('先选择影响范围较小的路线，交给团队手工执行。',{delay:32});await caption('人选择路线并应用决定；按钮只记录，不替人修业务');await moveAndClick(page.getByRole('button',{name:'应用这条路线（只记录）',exact:true}),'apply-route',true);await page.getByRole('status').filter({hasText:'决定已写入真实 SQLite'}).waitFor({timeout:10000});await mark('apply');
  const afterApply=await appState();if(afterApply.metrics.decisions!==before.metrics.decisions+1)throw Error('真实决定未写入隔离 SQLite');
  await caption('打开真实 SQLite 历史，确认这次人工决定留痕');await page.locator('.issue-item[data-issue-id="'+selected.id+'"]').click();await hold(.6);await moveAndClick(page.locator('.side-nav button[data-page="history"]'),'history');const saved=page.locator('[data-diagnosis-id="'+revision+'"]');await saved.waitFor();await frame(saved,'saved-history');await mark('persisted');await hold(4);
  await page.reload();await page.locator('.issue-item').first().waitFor();await overlay();await page.locator('.issue-item[data-issue-id="'+selected.id+'"]').click();await hold(.6);await page.locator('.side-nav button[data-page="history"]').click();await page.locator('[data-diagnosis-id="'+revision+'"]').waitFor();await mark('reload-persisted');await caption('真实应用重载后，诊断与人工决定仍在；没有虚构修复成功');await hold(4);await page.screenshot({path:path.join(out,'persisted.png')});await mark('end');
  const after=await appState();if(after.metrics.decisions!==before.metrics.decisions+1||after.metrics.outcomes!==before.metrics.outcomes)throw Error('录制期间真实 SQLite 指标不符合预期');if(errors.length)throw Error(errors.join('\n'));
  await writeFile(path.join(out,'proof.json'),JSON.stringify({semantics:'OK',framing:'OK',interaction:'OK',provenance,runId,sessionId:run.report.sessionId,diagnosisRevision:revision,solutions:solutionCount,after:after.metrics,decisionsWritten:1,outcomesWritten:0,realSQLitePersistence:true,probeApprovalGate:'one',errors,markers},null,2));
  if(mode==='record'){const video=page.video();await context.close();closed=true;await video.saveAs(path.join(out,'raw.webm'));}
 }
 await writeFile(path.join(out,'markers.json'),JSON.stringify(markers,null,2));
 console.log(JSON.stringify({mode,errors,runId}));
}finally{if(!closed)await context.close();await browser.close();}
