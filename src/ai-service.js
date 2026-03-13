const OpenAI = require('openai')
const config = require('../config/ai-config')

class AIService {
  constructor() {
    this.currentService = config.currentService
    this.initClient()
  }

  initClient() {
    const serviceConfig = config[this.currentService]

    this.client = new OpenAI({
      apiKey: serviceConfig.apiKey,
      baseURL: serviceConfig.baseURL
    })

    this.model = serviceConfig.model
    this.maxTokens = serviceConfig.maxTokens
  }

  async chat(messages) {
    try {
      const response = await this.client.chat.completions.create({
        model: this.model,
        messages: [
          { role: 'system', content: config.bot.systemPrompt },
          ...messages
        ],
        max_tokens: this.maxTokens
      })

      return response.choices[0].message.content
    } catch (error) {
      console.error(`${this.currentService} API 错误:`, error.message)
      throw error
    }
  }

  switchService(serviceName) {
    if (!['gemini', 'chatgpt', 'claude'].includes(serviceName)) {
      throw new Error('不支持的服务类型')
    }
    this.currentService = serviceName
    this.initClient()
    console.log(`已切换到 ${serviceName} 服务`)
  }

  getCurrentService() {
    return this.currentService
  }
}

module.exports = new AIService()
