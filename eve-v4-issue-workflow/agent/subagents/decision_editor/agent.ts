import { defineAgent, defineDynamic } from 'eve';
import { cpaSelection } from '../../lib/cpa-model';

export default defineAgent({
  description: 'Assemble the V4 human decision packet from one issue explanation, reviewed logs, checked hypotheses, and five independent solutions. Never choose for the human.',
  model: defineDynamic({ events: { 'session.started': () => cpaSelection() } }),
  reasoning: 'high',
});
