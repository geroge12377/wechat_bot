require('dotenv').config()
const OpenAI = require('openai')

const client = new OpenAI({
  apiKey: process.env.AI_API_KEY,
  baseURL: process.env.AI_BASE_URL
})

async function test() {
  console.log('测试 VectorEngine API...')
  console.log('Base URL:', process.env.AI_BASE_URL)
  console.log('API Key:', process.env.AI_API_KEY?.substring(0, 20) + '...')

  try {
    const response = await client.chat.completions.create({
      model: 'gemini-3.1-flash-lite-preview',
      messages: [
        { role: 'user', content: '你好，请用一句话介绍你自己' }
      ],
      max_tokens: 100
    })

    console.log('✓ API 调用成功!')
    console.log('回复:', response.choices[0].message.content)
  } catch (error) {
    console.error('✗ API 调用失败:')
    console.error('错误类型:', error.constructor.name)
    console.error('错误信息:', error.message)
    if (error.status) {
      console.error('响应状态:', error.status)
    }
  }
}

test()
