import { createOpenAI } from '@ai-sdk/openai';

export function cpaSelection() {
  const apiKey = process.env.CPA_API_KEY;
  const baseURL = process.env.CPA_BASE_URL || 'http://127.0.0.1:8317/v1';
  const modelId = process.env.CPA_MODEL || 'gpt-5.6-luna';

  if (!apiKey) throw new Error('CPA_API_KEY is missing');

  const provider = createOpenAI({ apiKey, baseURL });
  return {
    model: provider.responses(modelId),
    modelContextWindowTokens: 128000,
  };
}
