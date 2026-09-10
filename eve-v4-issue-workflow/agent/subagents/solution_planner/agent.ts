import { defineAgent, defineDynamic } from 'eve';
import { cpaSelection } from '../../lib/cpa-model';

export default defineAgent({
  description: 'Draft exactly one independent response route for a captured ops issue. Include benefit, conditions, resources, risks, business acceptance, rollback, and a safe illustrative code snippet. Never claim execution.',
  model: defineDynamic({ events: { 'session.started': () => cpaSelection() } }),
  reasoning: 'high',
});
