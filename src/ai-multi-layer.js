const OpenAI = require('openai')
const Anthropic = require('@anthropic-ai/sdk')
const aiLayers = require('../config/ai-layers')

class MultiLayerAI {
  constructor() {
    this.clients = {}
    this.initClients()
  }

  initClients() {
    // 初始化 Claude 客户端
    if (aiLayers.chat.apiKey) {
      this.clients.claude = new Anthropic({
        apiKey: aiLayers.chat.apiKey,
        baseURL: aiLayers.chat.baseURL
      })
    }

    // 初始化 GPT 客户端
    if (aiLayers.rag.apiKey) {
      this.clients.chatgpt = new OpenAI({
        apiKey: aiLayers.rag.apiKey,
        baseURL: aiLayers.rag.baseURL
      })
    }

    // 初始化 Gemini 客户端
    if (aiLayers.emotionAnalysis.apiKey) {
      this.clients.gemini = new OpenAI({
        apiKey: aiLayers.emotionAnalysis.apiKey,
        baseURL: aiLayers.emotionAnalysis.baseURL
      })
    }
  }

  // 主对话（使用 Claude）
  async chat(messages, systemPrompt) {
    const config = aiLayers.chat

    if (config.service === 'claude') {
      if (!this.clients.claude) {
        throw new Error('Claude 客户端未初始化，请检查 ANTHROPIC_API_KEY 环境变量')
      }
      const response = await this.clients.claude.messages.create({
        model: config.model,
        max_tokens: config.maxTokens,
        system: systemPrompt,
        messages: messages
      })
      return response.content[0].text
    }

    throw new Error(`不支持的服务: ${config.service}`)
  }

  // RAG 检索（使用 GPT）
  async ragQuery(query, context) {
    const config = aiLayers.rag

    const response = await this.clients.chatgpt.chat.completions.create({
      model: config.model,
      messages: [
        {
          role: 'system',
          content: '你是一个信息检索助手，根据提供的上下文回答问题。'
        },
        {
          role: 'user',
          content: `上下文：\n${context}\n\n问题：${query}`
        }
      ],
      max_tokens: config.maxTokens
    })

    return response.choices[0].message.content
  }

  // 记忆提取（使用 GPT）
  async extractMemory(conversation) {
    const config = aiLayers.memoryExtraction

    const response = await this.clients.chatgpt.chat.completions.create({
      model: config.model,
      messages: [
        {
          role: 'system',
          content: `从对话中提取重要信息，格式：
{
  "type": "profile/event/preference",
  "key": "信息类别",
  "value": "具体内容",
  "importance": 1-10
}`
        },
        {
          role: 'user',
          content: conversation
        }
      ],
      max_tokens: config.maxTokens
    })

    try {
      return JSON.parse(response.choices[0].message.content)
    } catch {
      return null
    }
  }

  // 情感分析（使用 Gemini）
  async analyzeEmotion(message) {
    const config = aiLayers.emotionAnalysis

    const response = await this.clients.gemini.chat.completions.create({
      model: config.model,
      messages: [
        {
          role: 'system',
          content: '分析消息的情感，返回：普通/开心/兴奋/害羞/低落/吃醋 之一'
        },
        {
          role: 'user',
          content: message
        }
      ],
      max_tokens: config.maxTokens
    })

    return response.choices[0].message.content.trim()
  }

  // 图片识别（使用 Gemini Vision）
  async recognizeImage(imageBase64) {
    const config = aiLayers.vision

    const response = await this.clients.gemini.chat.completions.create({
      model: config.model,
      messages: [{
        role: 'user',
        content: [
          { type: 'text', text: '请描述这张图片的内容' },
          {
            type: 'image_url',
            image_url: { url: `data:image/jpeg;base64,${imageBase64}` }
          }
        ]
      }],
      max_tokens: config.maxTokens
    })

    return response.choices[0].message.content
  }
}

module.exports = new MultiLayerAI()
