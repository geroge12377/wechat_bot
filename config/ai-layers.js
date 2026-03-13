// 分层 AI 配置
module.exports = {
  // 主对话使用 Claude（更好的角色扮演）
  chat: {
    service: 'claude',
    model: 'claude-3-5-sonnet-20241022',
    apiKey: process.env.ANTHROPIC_API_KEY,
    baseURL: process.env.ANTHROPIC_BASE_URL,
    maxTokens: 500
  },

  // RAG 检索使用 GPT（更快更便宜）
  rag: {
    service: 'chatgpt',
    model: 'gpt-3.5-turbo',
    apiKey: process.env.OPENAI_API_KEY,
    baseURL: process.env.OPENAI_BASE_URL || 'https://api.openai.com/v1',
    maxTokens: 300
  },

  // 记忆提取使用 GPT（结构化任务）
  memoryExtraction: {
    service: 'chatgpt',
    model: 'gpt-3.5-turbo',
    apiKey: process.env.OPENAI_API_KEY,
    baseURL: process.env.OPENAI_BASE_URL || 'https://api.openai.com/v1',
    maxTokens: 200
  },

  // 情感分析使用 Gemini（快速便宜）
  emotionAnalysis: {
    service: 'gemini',
    model: 'gemini-3.1-flash-lite-preview',
    apiKey: process.env.AI_API_KEY,
    baseURL: process.env.AI_BASE_URL,
    maxTokens: 100
  },

  // 图片识别使用 Gemini Vision
  vision: {
    service: 'gemini',
    model: 'gemini-3.1-flash-lite-preview',
    apiKey: process.env.AI_API_KEY,
    baseURL: process.env.AI_BASE_URL,
    maxTokens: 300
  }
}
