// 测试接话判断功能
require('dotenv').config()
const axios = require('axios')

// 本地规则判断
function canRespondLocal(text) {
  // 不能接话的情况
  const cantRespondPatterns = [
    /^(好的?|嗯|哦|ok|知道了|收到|明白了?)$/i,
    /^(拜拜|再见|走了|下线了|睡了|88)$/i,
    /我(去|要)(吃饭|睡觉|上课|工作|忙)/,
    /^[。，、！？,.!?]+$/
  ]

  for (const pattern of cantRespondPatterns) {
    if (pattern.test(text)) {
      return { result: false, reason: '本地规则：不能接话' }
    }
  }

  // 可以接话的情况
  const canRespondPatterns = [
    /[？?]$/,
    /怎么|为什么|什么|哪里|谁|如何/,
    /好(累|开心|难过|高兴|伤心)/,
    /(天气|今天|明天|最近)/,
    /看(了|到|见)|听(了|到|说)/
  ]

  for (const pattern of canRespondPatterns) {
    if (pattern.test(text)) {
      return { result: true, reason: '本地规则：可以接话' }
    }
  }

  return { result: null, reason: '需要 AI 判断' }
}

// AI 判断
async function canRespondAI(text) {
  try {
    console.log('→ 调用 AI 判断...')
    const startTime = Date.now()

    const response = await axios.post(
      `${process.env.AI_BASE_URL}/chat/completions`,
      {
        model: 'gemini-3.1-flash-lite-preview',
        messages: [{
          role: 'user',
          content: `判断"独角兽"（一个可爱的女孩角色）能否自然地接这句话继续对话。只回答"能"或"不能"。\n消息：${text}`
        }],
        max_tokens: 10
      },
      {
        headers: {
          'Authorization': `Bearer ${process.env.AI_API_KEY}`,
          'Content-Type': 'application/json'
        },
        timeout: 10000
      }
    )

    const elapsed = Date.now() - startTime
    const result = response.data.choices[0].message.content.trim()
    const canRespond = result.includes('能')

    return {
      result: canRespond,
      reason: `AI 判断 (${elapsed}ms): ${result}`,
      elapsed
    }
  } catch (error) {
    const elapsed = Date.now() - startTime
    if (error.code === 'ECONNABORTED') {
      return { result: false, reason: `AI 超时 (${elapsed}ms)`, elapsed }
    } else if (error.response) {
      return { result: false, reason: `AI 错误 (HTTP ${error.response.status})`, elapsed }
    } else {
      return { result: false, reason: `AI 失败: ${error.message}`, elapsed }
    }
  }
}

// 测试用例
const testCases = [
  '？不只吧',
  '好的',
  '我去吃饭了',
  '今天天气真好',
  '你在干嘛？',
  '好累啊',
  '嗯',
  '看了部电影',
  '为什么这样',
  '拜拜'
]

async function runTests() {
  console.log('开始测试接话判断...\n')

  for (const text of testCases) {
    console.log(`\n测试: "${text}"`)
    console.log('─'.repeat(50))

    // 本地规则
    const localResult = canRespondLocal(text)
    console.log(`本地规则: ${localResult.reason}`)

    // 如果本地规则无法判断，使用 AI
    if (localResult.result === null) {
      const aiResult = await canRespondAI(text)
      console.log(`${aiResult.reason}`)
      console.log(`最终结果: ${aiResult.result ? '✓ 可以接话' : '✗ 不能接话'}`)
    } else {
      console.log(`最终结果: ${localResult.result ? '✓ 可以接话' : '✗ 不能接话'}`)
    }
  }

  console.log('\n\n测试完成')
}

runTests().catch(console.error)
