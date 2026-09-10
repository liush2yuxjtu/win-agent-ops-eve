import { defineAgent, defineDynamic } from 'eve';
import { cpaSelection } from '../../lib/cpa-model';

export default defineAgent({
  description: 'Explain one captured ops issue for a non-technical reader. Separate observed facts, possible causal paths, hypotheses, evidence ids, and missing evidence. Do not propose fixes.',
  model: defineDynamic({ events: { 'session.started': () => cpaSelection() } }),
  reasoning: 'high',
});
