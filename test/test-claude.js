require('dotenv').config()
const Anthropic = require('@anthropic-ai/sdk')

const anthropic = new Anthropic({
  apiKey: process.env.ANTHROPIC_API_KEY,
  baseURL: process.env.ANTHROPIC_BASE_URL,
  defaultHeaders: {
    'anthropic-client': 'claude_code'
  }
})

async function test() {
  console.log('测试 Claude API...')
  console.log('API Key:', process.env.ANTHROPIC_API_KEY?.substring(0, 20) + '...')
  console.log('Base URL:', process.env.ANTHROPIC_BASE_URL)

  try {
    const message = await anthropic.messages.create({
      model: 'claude-3-5-sonnet-20241022',
      max_tokens: 100,
      messages: [
        { role: 'user', content: '你好，请用一句话介绍你自己' }
      ]
    })

    console.log('✓ API 调用成功!')
    console.log('回复:', message.content[0].text)
  } catch (error) {
    console.error('✗ API 调用失败:')
    console.error('错误类型:', error.constructor.name)
    console.error('错误信息:', error.message)
    if (error.status) {
      console.error('响应状态:', error.status)
    }
    if (error.error) {
      console.error('详细错误:', JSON.stringify(error.error, null, 2))
    }
  }
}

test()
