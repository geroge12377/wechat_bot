require('dotenv').config()
const https = require('https')
const http = require('http')

async function testClaude() {
  const url = new URL(process.env.ANTHROPIC_BASE_URL + '/v1/messages')

  const data = JSON.stringify({
    model: 'claude-3-5-sonnet-20241022',
    max_tokens: 100,
    messages: [
      { role: 'user', content: '你好，请用一句话介绍你自己' }
    ]
  })

  const options = {
    hostname: url.hostname,
    port: url.port || (url.protocol === 'https:' ? 443 : 80),
    path: url.pathname,
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-api-key': process.env.ANTHROPIC_API_KEY,
      'anthropic-version': '2023-06-01',
      'User-Agent': 'claude_code'
    }
  }

  console.log('测试 Claude API (原始 HTTP)...')
  console.log('URL:', url.href)
  console.log('API Key:', process.env.ANTHROPIC_API_KEY?.substring(0, 20) + '...')

  return new Promise((resolve, reject) => {
    const client = url.protocol === 'https:' ? https : http

    const req = client.request(options, (res) => {
      let body = ''

      res.on('data', (chunk) => {
        body += chunk
      })

      res.on('end', () => {
        console.log('响应状态:', res.statusCode)

        if (res.statusCode === 200) {
          const response = JSON.parse(body)
          console.log('✓ API 调用成功!')
          console.log('回复:', response.content[0].text)
          resolve(response)
        } else {
          console.error('✗ API 调用失败:')
          console.error('响应内容:', body)
          reject(new Error(body))
        }
      })
    })

    req.on('error', (error) => {
      console.error('✗ 请求错误:', error.message)
      reject(error)
    })

    req.write(data)
    req.end()
  })
}

testClaude().catch(console.error)
