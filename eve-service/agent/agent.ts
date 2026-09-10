import { defineAgent, defineDynamic } from 'eve';
import { createOpenAI } from '@ai-sdk/openai';

export default defineAgent({
  model: defineDynamic({ events: { 'step.started': () => {
    const apiKey = process.env.CPA_API_KEY;
    const baseURL = process.env.CPA_BASE_URL;
    if (!apiKey || !baseURL) throw new Error('CPA 配置缺失');
    const provider = createOpenAI({ apiKey, baseURL });
    return { model: provider.responses('gpt-5.6-luna'), modelContextWindowTokens: 128000 };
  } } }),
  limits: { maxInputTokensPerSession: 60000, maxOutputTokensPerSession: 12000 },
});
