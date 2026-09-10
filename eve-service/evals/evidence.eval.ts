import { defineEval } from 'eve/evals';
import { equals } from 'eve/evals/expect';
import { z } from 'zod';
import { diagnosisSchema } from '../schema.mjs';

export default defineEval({
  description: '真实 CPA 输出可解析、方案有序且引用仅来自输入证据。此检查不代表准确率。',
  async test(t) {
    await t.send(JSON.stringify({
      task: '解释证据并提供中文诊断。',
      evidence: [{ evidenceId: 'probe-1', kind: 'monitor', content: 'health=200；登录检查未执行，因为 backend-owner-invalid。不要把未执行说成 401。' }],
      outputContract: z.toJSONSchema(diagnosisSchema),
    }));
    t.succeeded();
    const result = diagnosisSchema.parse(JSON.parse(t.reply));
    t.check(result.solutions.every((s, i) => s.rank === i + 1), equals(true));
    t.check([...result.hypotheses, ...result.hiddenIssues].every(h => h.evidenceIds.every(id => id === 'probe-1')), equals(true));
    t.check(result.title.length > 0, equals(true));
    t.check(/进程|工作目录|服务归属|运行目录/.test(JSON.stringify(result.hypotheses)), equals(true));
  },
});
