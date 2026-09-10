import { chromium } from 'playwright';
import { spawn } from 'node:child_process';
import { mkdtemp, mkdir, readFile, writeFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import net from 'node:net';
import { performance } from 'node:perf_hooks';

const mode=process.argv[2]||'discover';
const out=path.resolve('artifacts',mode);await mkdir(out,{recursive:true});
const temp=await mkdtemp(path.join(tmpdir(),'ops-ui-demo-'));
const port=await new Promise(resolve=>{const s=net.createServer();s.listen(0,'127.0.0.1',()=>{const p=s.address().port;s.close(()=>resolve(p));});});
const url=`http://127.0.0.1:${port}`;
await writeFile(path.join(temp,'status.json'),JSON.stringify({heartbeat:Date.now()/1000,deliveryError:null,checks:{
  'demo.backend.owner':{status:'fail',detail:'演示样例：监听进程工作目录与预期 backend 目录不一致。'},
  'demo.auth':{status:'unverified',detail:'backend-owner-invalid'},
  'demo.portal.http':{status:'pass',detail:'HTTP 200'},
  'demo.loaded-version':{status:'unverified',detail:'startup-receipt-missing'}
},events:[{id:'demo-event-001',at:new Date().toISOString(),body:'隔离演示库：后端端口归属检查不匹配，登录检查未执行。'}]}));
const server=spawn('python3',['serve.py','--port',String(port),'--db',path.join(temp,'ops.sqlite'),'--source',path.join(temp,'status.json')],{stdio:['ignore','pipe','pipe']});
let serverLog='';server.stdout.on('data',d=>serverLog+=d);server.stderr.on('data',d=>serverLog+=d);
let browser,context,page;const markers=[];const errors=[];let started;
const hold=seconds=>page.waitForTimeout(seconds*1000);
async function mark(label,extra={}){
  const state=await page.evaluate(()=>({scrollY,viewport:{width:innerWidth,height:innerHeight},documentHeight:document.documentElement.scrollHeight}));
  const row={label,elapsedMs:Math.round(performance.now()-started),...state,...extra};markers.push(row);return row;
}
async function caption(text){await page.locator('#demo-caption').evaluate((el,text)=>el.textContent=text,text);}
async function overlay(){
  await page.evaluate(()=>{
    document.querySelector('#demo-overlays')?.remove();
    const layer=document.createElement('div');layer.id='demo-overlays';layer.style.cssText='pointer-events:none;position:fixed;inset:0;z-index:2147483647';
    const label=document.createElement('div');label.textContent='隔离演示库 · 真实 Eve / CPA';label.style.cssText='position:absolute;right:24px;top:14px;padding:7px 12px;border-radius:5px;background:#183e33;color:#fff;font:14px system-ui';
    const subtitle=document.createElement('div');subtitle.id='demo-caption';subtitle.style.cssText='position:absolute;left:50%;bottom:14px;transform:translateX(-50%);max-width:calc(100vw - 48px);white-space:nowrap;padding:11px 24px;border-radius:8px;background:rgba(17,31,27,.94);color:white;font:20px system-ui;box-shadow:0 2px 15px #0002';
    const cursor=document.createElement('div');cursor.id='demo-cursor';cursor.style.cssText='position:fixed;left:-40px;top:-40px;width:22px;height:22px;border-radius:50%;border:3px solid #f1a845;background:#f1a84544;transform:translate(-50%,-50%);box-shadow:0 0 0 2px white';
    layer.append(label,subtitle,cursor);document.body.append(layer);
    document.onmousemove=e=>{cursor.style.left=e.clientX+'px';cursor.style.top=e.clientY+'px';};
  });
}
async function frame(locator,label,top=90){
  await locator.evaluate((el,top)=>window.scrollTo({top:Math.max(0,el.getBoundingClientRect().top+scrollY-top),behavior:'smooth'}),top);
  await hold(.75);
  const box=await locator.boundingBox();
  if(!box||box.y<55||box.y+box.height>page.viewportSize().height-72)throw new Error(`FRAMING FAIL ${label}: ${JSON.stringify(box)}`);
  await mark('frame-'+label,{rect:box});return box;
}
async function click(locator,label,{framed=false}={}){
  if(!framed)await frame(locator,label,160);
  const box=await locator.boundingBox();
  if(!box)throw new Error('CLICK FAIL '+label);
  await page.mouse.move(box.x+box.width/2,box.y+box.height/2,{steps:12});await hold(.35);
  await mark('click-'+label,{rect:box});await locator.click();await hold(.9);
}
async function waitReady(){
  for(let i=0;i<100;i++){
    if(server.exitCode!==null)throw new Error('演示服务退出 '+serverLog);
    try{if((await fetch(url+'/health')).ok)return;}catch{}
    await new Promise(r=>setTimeout(r,100));
  }
  throw new Error('演示服务未就绪');
}
try{
  await waitReady();browser=await chromium.launch({headless:true});
  context=await browser.newContext({viewport:{width:1440,height:900},deviceScaleFactor:1,locale:'zh-CN',...(mode==='record'?{recordVideo:{dir:path.join(temp,'video'),size:{width:1440,height:900}}}:{})});
  started=performance.now();page=await context.newPage();page.on('pageerror',e=>errors.push(String(e)));
  page.on('popup',()=>errors.push('意外弹出新页面'));
  await page.goto(url);await page.getByRole('button',{name:'请求 Eve 诊断',exact:true}).waitFor();await overlay();
  const owner=page.locator('button.issue').filter({hasText:'demo.backend.owner'});
  const auth=page.locator('button.issue').filter({hasText:'demo.auth'});
  const question=page.getByRole('textbox',{name:'向 Eve 追问',exact:true});
  if(mode==='discover'||mode==='check'){
    await caption('检查真实界面、交互状态与画面范围');
    const controls=await page.locator('button,input,textarea,select,summary').evaluateAll(nodes=>nodes.map(n=>({tag:n.tagName,text:n.textContent?.slice(0,120),label:n.getAttribute('aria-label'),placeholder:n.getAttribute('placeholder'),rect:n.getBoundingClientRect().toJSON()})));
    await click(owner,'owner');await frame(question,'question');await question.fill('只针对当前 owner 问题的追问');
    await click(auth,'auth');await frame(question,'question-after-switch');
    const questionLeaked=(await question.inputValue())!=='';
    await frame(page.locator('.diagnosis form'),'diagnosis-form');
    const feedbackRect=await page.getByRole('status').boundingBox();
    const localFeedback=page.locator('.diagnosis .local-feedback');
    const localFeedbackVisible=await localFeedback.count()>0&&await localFeedback.evaluate(el=>{const r=el.getBoundingClientRect();return r.y>=0&&r.bottom<=innerHeight-72;});
    const result={mode,url,viewport:page.viewportSize(),controls,questionLeaked,feedbackRect,localFeedbackVisible,errors,markers};
    await page.screenshot({path:path.join(out,'discovery.png')});
    await writeFile(path.join(out,'discovery.json'),JSON.stringify(result,null,2));
    process.stdout.write(JSON.stringify({questionLeaked,localFeedbackVisible,feedbackRect,errors}));
    if(mode==='check'&&(questionLeaked||!localFeedbackVisible||errors.length))throw new Error('界面回归失败：追问隔离或就近反馈不满足');
  }else{
    const proof={semantics:'OK',dependencies:'OK',selectors:'OK',stateTransitions:[],framing:'OK',recordingOnlyScale:1};
    await caption('问题队列：先看红灯与待核验证据');await hold(.4);await mark('orient');await hold(4);
    await caption('选择异常检测项，查看中文分诊');await click(owner,'choose-issue');
    await frame(page.locator('.diagnosis form'),'diagnosis-form');await mark('question');await hold(2);
    await click(question,'question-input',{framed:true});await question.pressSequentially('这两盏红灯是否有共同原因？先查哪一步？',{delay:75});await hold(1);
    await caption('请求 Eve 诊断 · 真实模型等待片段加速展示');
    const submit=page.getByRole('button',{name:'请求 Eve 诊断',exact:true});
    await click(submit,'request-eve',{framed:true});await mark('wait-start');
    const progress=page.locator('.diagnosis .local-feedback');
    await progress.filter({hasText:'Eve 正在 Mac mini'}).waitFor({timeout:5000});
    const progressRect=await progress.boundingBox();
    if(!progressRect||progressRect.y<0||progressRect.y+progressRect.height>828)throw new Error('诊断进度不在画面内');
    await page.getByRole('status').filter({hasText:'Eve 诊断已保存'}).waitFor({timeout:250000});await mark('wait-end');
    const state=await page.request.get(url+'/api/state').then(r=>r.json());
    const issue=state.issues.find(i=>i.id==='demo.backend.owner');
    if(issue.analysis.engine!=='eve-cpa-1')throw new Error('未返回真实模型诊断');
    proof.stateTransitions.push('Eve 真实请求完成，模型诊断替代当前规则显示');proof.modelSessionId=issue.analysis.sessionId;proof.solutionCount=issue.analysis.solutions.length;
    await caption('中文分诊：影响什么、可能原因，都有证据');
    await frame(page.locator('.diagnosis > dl'),'diagnosis-result');await mark('result');await hold(4);
    await page.screenshot({path:path.join(out,'diagnosis.png')});
    await caption('互补路径：先看当前首选，再看验证与回退');
    const first=page.locator('article.solution').first();
    await frame(first,'first-solution');await mark('solutions');await hold(4);
    await click(first.locator('details').first().locator('summary'),'expand-solution',{framed:true});
    await frame(first.locator('dl dd').nth(3),'verification',160);await mark('verification');await hold(3);
    await page.screenshot({path:path.join(out,'verification.png')});
    await click(first.locator('details').first().locator('summary'),'collapse-solution');
    if(issue.analysis.solutions.length>1){await frame(page.locator('article.solution').nth(1),'alternative');await hold(3);}
    await caption('填写决定理由，再采纳第一方案');
    const note=page.getByRole('textbox',{name:'决定理由 / 处理结果证据',exact:true});
    await frame(note,'decision-reason',140);await click(note,'reason-input',{framed:true});await note.pressSequentially('先核对监听进程与工作目录；不直接重启。',{delay:75});await hold(1);
    await frame(first,'adopt-solution');await click(page.getByRole('button',{name:'采纳方案1',exact:true}),'adopt',{framed:true});
    await page.getByText('已采纳 · 未执行',{exact:true}).waitFor();await mark('adopted');await caption('已采纳 · 未执行。系统只保存决定');await hold(3);
    await page.screenshot({path:path.join(out,'adopted.png')});
    await caption('重新加载页面，验证决定是否仍在');await mark('reload');await hold(1);
    await page.reload();await page.getByRole('button',{name:'请求 Eve 诊断',exact:true}).waitFor();await overlay();await caption('页面已重新加载，检查同一个问题');
    await click(page.locator('button.issue').filter({hasText:'demo.backend.owner'}),'reselect-after-reload');
    await page.getByText('已采纳 · 未执行',{exact:true}).waitFor();await frame(page.locator('article.solution').first(),'persisted');await mark('persisted');await caption('刷新后，已采纳的决定仍然保留');await hold(3);
    const final=await page.request.get(url+'/api/state').then(r=>r.json());
    if(final.metrics.decisions!==1||final.issues.find(i=>i.id==='demo.backend.owner').status!=='fail')throw new Error('持久化或采纳不执行校验失败');
    await frame(page.locator('.timeline'),'history');await mark('history');await caption('这个问题的历史：诊断版本、决定与证据可追溯');await hold(5);
    await page.screenshot({path:path.join(out,'history.png')});
    proof.stateTransitions.push('采纳保存，刷新后保留','采纳未关闭红灯或执行修复');
    if(errors.length)throw new Error(errors.join('\n'));
    await mark('end');await writeFile(path.join(out,'proof.json'),JSON.stringify({...proof,errors,markers},null,2));
    if(mode==='record'){
      const video=page.video();await context.close();context=null;await video.saveAs(path.join(out,'raw.webm'));
    }
    process.stdout.write(JSON.stringify({mode,semantics:proof.semantics,framing:proof.framing,stateTransitions:proof.stateTransitions,modelSessionId:proof.modelSessionId,solutionCount:proof.solutionCount,errors}));
  }
}finally{
  await writeFile(path.join(out,'markers.json'),JSON.stringify(markers,null,2));
  await writeFile(path.join(out,'server.log'),serverLog);
  if(context)await context.close();if(browser)await browser.close();
  if(server.exitCode===null){const stopped=new Promise(r=>server.once('exit',r));server.kill('SIGTERM');await stopped;}
  await rm(temp,{recursive:true,force:true});
}
