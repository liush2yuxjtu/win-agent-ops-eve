import { Client } from 'eve/client';
import { z } from 'zod';
import { readFile, mkdir, writeFile } from 'node:fs/promises';
import { randomUUID, createHash } from 'node:crypto';

import { diagnosisSchema } from './schema.mjs';
const packetSchema = z.object({
  issue: z.string().max(120), revision: z.string().max(100),
  question: z.string().max(2000).default('解释这个问题，比较根因并给出最值得先做的方案。'),
  evidence: z.array(z.object({ evidenceId: z.string().min(1), kind: z.string(), content: z.unknown() })).min(1).max(60),
  variant: z.enum(['baseline','candidate']).default('candidate')
});
let input='';
for await (const chunk of process.stdin) { input+=chunk; if(input.length>80000) throw new Error('证据包超过 80 KB'); }
const packet=packetSchema.parse(JSON.parse(input));
const token=(await readFile(new URL('./.ops-token',import.meta.url),'utf8')).trim();
const client=new Client({host:'http://127.0.0.1:21876',auth:{bearer:token},redirect:'error'});
const runId=randomUUID();
await mkdir(new URL('./runs/',import.meta.url),{recursive:true,mode:0o700});
const started=Date.now();
const authoredPromptHash=createHash('sha256').update(await readFile(new URL('./agent/instructions.md',import.meta.url))).digest('hex');
const strategy=packet.variant==='candidate'
  ? '先比较至少两个合理的竞争解释，找反证；优先消除最关键的不确定性。把不同检查项的时间及依赖关系联系起来。依据历史失败结果避免重荐无效行动，并解释第一名为什么优先。'
  : '根据证据解释问题并按优先顺序推荐方案。';
let response;
let timer;
try {
  const created=await client.sessions.create({message:JSON.stringify({task:packet.question,strategy,issue:packet.issue,evidence:packet.evidence,outputContract:z.toJSONSchema(diagnosisSchema)})},{signal:AbortSignal.timeout(20000)});
  response=created.response;
  const pending=response.result();
  const timeout=new Promise((_,reject)=>{ timer=setTimeout(()=>reject(new Error('诊断超过 180 秒')),180000); });
  const result=await Promise.race([pending,timeout]);
  if(result.status==='failed') throw new Error('Eve 诊断失败');
  const diagnosis=diagnosisSchema.parse(JSON.parse(result.message));
  const allowed=new Set(packet.evidence.map(e=>e.evidenceId));
  for(const item of [...diagnosis.hypotheses,...diagnosis.hiddenIssues]) {
    if(item.evidenceIds.some(id=>!allowed.has(id))) throw new Error('模型引用了不存在的证据');
  }
  if(new Set(diagnosis.solutions.map(s=>s.id)).size!==diagnosis.solutions.length || diagnosis.solutions.some((s,i)=>s.rank!==i+1)) throw new Error('方案 ID 或排名无效');
  const report={runId,sessionId:result.sessionId,issue:packet.issue,revision:packet.revision,variant:packet.variant,
    engine:'eve-cpa-1',audience:'leadership-v1',requestedModel:'gpt-5.6-luna',upstreamModelVerified:false,
    authoredPromptHash,
    elapsedMs:Date.now()-started,diagnosis,
    events:result.events.filter(e=>['step.started','session.waiting','session.failed'].includes(e.type)).map(e=>({type:e.type,data:e.data}))};
  await writeFile(new URL(`./runs/${runId}.json`,import.meta.url),JSON.stringify(report,null,2),{mode:0o600});
  process.stdout.write(JSON.stringify(report));
} catch(error) {
  if(response) await response.cancel().catch(()=>{});
  const report={runId,issue:packet.issue,error:error instanceof Error?error.message:'诊断失败',elapsedMs:Date.now()-started};
  await writeFile(new URL(`./runs/${runId}.json`,import.meta.url),JSON.stringify(report),{mode:0o600});
  process.stderr.write(JSON.stringify(report)); process.exitCode=1;
} finally {clearTimeout(timer);}
