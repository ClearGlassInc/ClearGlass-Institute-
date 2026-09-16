export interface ArtemisProvider {
  id: string
  name: string
  baseUrl?: string
  apiKey?: string
  models(): Promise<string[]>
}

export const providerRegistry: ArtemisProvider[] = [
  { id: 'openrouter', name: 'OpenRouter', async models() { return [] } },
  { id: 'anthropic', name: 'Anthropic', async models() { return [] } },
  { id: 'openai', name: 'OpenAI', async models() { return [] } },
  { id: 'gemini', name: 'Google Gemini', async models() { return [] } },
  { id: 'grok', name: 'xAI Grok', async models() { return [] } },
  { id: 'nous', name: 'Nous Portal', async models() { return [] } },
  { id: 'qwen', name: 'Qwen', async models() { return [] } },
  { id: 'minimax', name: 'MiniMax', async models() { return [] } },
  { id: 'huggingface', name: 'Hugging Face', async models() { return [] } },
  { id: 'groq', name: 'Groq', async models() { return [] } },
  { id: 'ollama', name: 'Ollama', baseUrl: 'http://127.0.0.1:11434', async models() { return [] } },
  { id: 'lmstudio', name: 'LM Studio', baseUrl: 'http://127.0.0.1:1234', async models() { return [] } },
  { id: 'llamacpp', name: 'llama.cpp', async models() { return [] } },
  { id: 'vllm', name: 'vLLM', async models() { return [] } }
]
