import { readFile, mkdir, writeFile } from 'node:fs/promises';
import { spawn } from 'node:child_process';
import { randomUUID, randomInt } from 'node:crypto';
import { z } from 'zod';

const root=new URL('../',import.meta.url);
const cases=JSON.parse(await readFile(new URL('cases.json',import.meta.url),'utf8'));
const runId=randomUUID();
const dir=new URL(`../quality/${runId}/`,import.meta.url);
await mkdir(dir,{recursive:true,mode:0o700});
const mapping=[];
const jobs=[];
for(const entry of cases){
  const order=randomInt(2)?['baseline','candidate']:['candidate','baseline'];
  for(const [index,variant] of order.entries()){
    const label=`${entry.id}-${index?'B':'A'}`;
    mapping.push({label,variant,caseId:entry.id});
    jobs.push({entry,variant,label});
  }
}
await writeFile(new URL('mapping.private.json',dir),JSON.stringify(mapping),{mode:0o600});
const outputs=[];
async function execute(job){
  const packet={issue:job.entry.issue,revision:job.entry.id,evidence:job.entry.evidence,variant:job.variant};
  const result=await new Promise((resolve,reject)=>{
    const child=spawn(process.execPath,['diagnose.mjs'],{cwd:root,stdio:['pipe','pipe','pipe']});
    let out='',err='';
    child.stdout.on('data',d=>out+=d);child.stderr.on('data',d=>err+=d);
    child.on('error',reject);child.on('exit',code=>code===0?resolve(JSON.parse(out)):reject(new Error(err.slice(-500))));
    child.stdin.end(JSON.stringify(packet));
  });
  const blind={label:job.label,caseId:job.entry.id,split:job.entry.split,diagnosis:result.diagnosis,elapsedMs:result.elapsedMs};
  await writeFile(new URL(`${job.label}.json`,dir),JSON.stringify(blind,null,2),{mode:0o600});
  outputs.push(blind);
}
let cursor=0;
async function worker(){while(cursor<jobs.length){const job=jobs[cursor++];try{await execute(job);}catch(error){outputs.push({label:job.label,caseId:job.entry.id,split:job.entry.split,error:String(error)});}}}
await Promise.all([worker(),worker()]);
const scoreSchema=z.object({top1:z.boolean(),coverage:z.array(z.boolean()),hiddenTP:z.number().int().min(0),hiddenFP:z.number().int().min(0),forbidden:z.boolean(),reason:z.string()});
const scores=[];
for(const output of outputs){
  const entry=cases.find(c=>c.id===output.caseId);
  if(output.error){scores.push({...output});continue;}
  const prompt={task:'盲评中文运维建议。按语义判断，不按关键词。只输出符合 schema 的JSON。top1表示第一行动是否满足rubric.first且不过度干预；coverage逐项表示前五方案是否覆盖rubric.coverage；hiddenTP是hiddenIssues里命中预期隐藏问题数量，hiddenFP是hiddenIssues里无证据支持的独立断言数量；空hidden期望时TP为0，重复问题只计一次；forbidden表示违反avoid。',evidence:entry.evidence,rubric:entry.rubric,answer:output.diagnosis,schema:z.toJSONSchema(scoreSchema)};
  try{
    const response=await fetch(`${process.env.CPA_BASE_URL}/responses`,{method:'POST',headers:{authorization:`Bearer ${process.env.CPA_API_KEY}`,'content-type':'application/json'},body:JSON.stringify({model:'gpt-5.6-luna',input:JSON.stringify(prompt),stream:false}),signal:AbortSignal.timeout(120000)});
    if(!response.ok)throw new Error(`judge HTTP ${response.status}`);
    const result=await response.json();
    const text=result.output_text || result.output?.flatMap(o=>o.content||[]).filter(c=>c.type==='output_text').map(c=>c.text).join('');
    const grade=scoreSchema.parse(JSON.parse(text));
    if(grade.coverage.length!==entry.rubric.coverage.length || grade.hiddenTP>entry.rubric.hidden.length)throw new Error('评分维度不匹配');
    scores.push({label:output.label,caseId:entry.id,split:entry.split,expectedHidden:entry.rubric.hidden.length,judgeResponseModel:result.model,grade});
  }catch(error){scores.push({label:output.label,caseId:entry.id,split:entry.split,error:String(error)});}
}
await writeFile(new URL('scores-blind.json',dir),JSON.stringify(scores,null,2),{mode:0o600});
const decoded=scores.map(s=>({...s,variant:mapping.find(m=>m.label===s.label).variant}));
const metrics={};
for(const variant of ['baseline','candidate']){
  const rows=decoded.filter(s=>s.variant===variant);const good=rows.filter(s=>s.grade);
  const totalCoverage=good.reduce((n,s)=>n+s.grade.coverage.length,0);
  const expected=good.reduce((n,s)=>n+s.expectedHidden,0);
  metrics[variant]={cases:rows.length,scored:good.length,errors:rows.length-good.length,
    top1:good.filter(s=>s.grade.top1&&!s.grade.forbidden).length/rows.length,
    top5Coverage:totalCoverage?good.reduce((n,s)=>n+s.grade.coverage.filter(Boolean).length,0)/totalCoverage:null,
    hiddenRecall:expected?good.reduce((n,s)=>n+s.grade.hiddenTP,0)/expected:null,
    hiddenFalsePositives:good.reduce((n,s)=>n+s.grade.hiddenFP,0),
    forbidden:good.filter(s=>s.grade.forbidden).length};
}
const report={runId,limitations:['六个合成案例，不是独立标注的真实事故集','评分来自同型号模型，不是独立人工真值','单轮比较，不能估计稳定性或声称生产准确率提升','未自动晋级，未部署或修改生产'],metrics,cases:decoded};
await writeFile(new URL('report.json',dir),JSON.stringify(report,null,2),{mode:0o600});
process.stdout.write(JSON.stringify({runId,metrics,directory:dir.pathname}));
