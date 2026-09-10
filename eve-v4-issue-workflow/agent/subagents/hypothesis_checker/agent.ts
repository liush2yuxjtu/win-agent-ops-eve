import { defineAgent, defineDynamic } from 'eve';
import { cpaSelection } from '../../lib/cpa-model';

export default defineAgent({
  description: 'Challenge one proposed root-cause hypothesis. Return supported, uncertain, or weakened with one confirming check and one disconfirming check.',
  model: defineDynamic({ events: { 'session.started': () => cpaSelection() } }),
  reasoning: 'high',
});
