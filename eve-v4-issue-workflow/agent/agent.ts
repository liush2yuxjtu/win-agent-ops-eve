import { defineAgent, defineDynamic } from 'eve';
import { cpaSelection } from './lib/cpa-model';

export default defineAgent({
  model: defineDynamic({
    events: {
      'session.started': () => cpaSelection(),
    },
  }),
  reasoning: 'high',
  limits: {
    maxInputTokensPerSession: 120000,
    maxOutputTokensPerSession: 24000,
  },
});
