import { z } from 'zod';
const text = z.string().min(1).max(4000);
const refs = z.array(z.string().min(1)).min(1).max(20);
export const diagnosisSchema = z.object({
  title: text, impact: text, priority: z.enum(['P0','P1','P2','P3']),
  hypothesis: text, confidence: text,
  hypotheses: z.array(z.object({ cause: text, status: z.enum(['confirmed','suspected','unknown','rejected']), evidenceIds: refs, counterEvidence: z.string().max(4000), missingEvidence: z.string().max(4000) })).min(1).max(8),
  hiddenIssues: z.array(z.object({ title: text, reason: text, evidenceIds: refs })).max(8),
  solutions: z.array(z.object({ id: z.string().regex(/^[a-zA-Z0-9_-]{1,80}$/), rank: z.number().int().min(1).max(5), title: text,
    kind: z.enum(['diagnostic','mitigation','root-cause','prevention']), steps: text, verification: text,
    applicableWhen: text, risk: text, rollback: text, cost: text, rationale: text })).min(1).max(5)
});
