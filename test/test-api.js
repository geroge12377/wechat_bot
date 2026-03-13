require('dotenv').config()
const OpenAI = require('openai')
const { HttpsProxyAgent } = require('https-proxy-agent')

const proxyAgent = new HttpsProxyAgent('http://127.0.0.1:7890')

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
  baseURL: process.env.OPENAI_BASE_URL,
  timeout: 60000, // 60秒超时
  maxRetries: 2,
  httpAgent: proxyAgent
})

async function test() {
  console.log('测试 OpenAI API...')
  console.log('API Key:', process.env.OPENAI_API_KEY?.substring(0, 20) + '...')

  try {
    const response = await openai.chat.completions.create({
      model: 'gpt-3.5-turbo',
      messages: [
        { role: 'user', content: '你好' }
      ],
      max_tokens: 50
    })

    console.log('✓ API 调用成功!')
    console.log('回复:', response.choices[0].message.content)
  } catch (error) {
    console.error('✗ API 调用失败:')
    console.error('错误类型:', error.constructor.name)
    console.error('错误信息:', error.message)
    if (error.response) {
      console.error('响应状态:', error.response.status)
      console.error('响应数据:', error.response.data)
    }
  }
}

test()
