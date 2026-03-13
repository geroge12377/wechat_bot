require('dotenv').config()
const http = require('http')

async function testGemini() {
  const url = new URL('http://8.137.115.72:9002/api/v1beta/models/gemini-3.1-flash-lite-preview:generateContent')

  const data = JSON.stringify({
    contents: [{
      parts: [{
        text: '你好，请用一句话介绍你自己'
      }]
    }]
  })

  const options = {
    hostname: url.hostname,
    port: url.port,
    path: url.pathname,
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-api-key': process.env.GEMINI_API_KEY,
      'Content-Length': data.length
    }
  }

  console.log('测试 Gemini API...')
  console.log('URL:', url.href)
  console.log('API Key:', process.env.GEMINI_API_KEY?.substring(0, 20) + '...')

  return new Promise((resolve, reject) => {
    const req = http.request(options, (res) => {
      let body = ''

      res.on('data', (chunk) => {
        body += chunk
      })

      res.on('end', () => {
        console.log('响应状态:', res.statusCode)

        if (res.statusCode === 200) {
          const response = JSON.parse(body)
          console.log('✓ API 调用成功!')
          console.log('回复:', response.candidates[0].content.parts[0].text)
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

testGemini().catch(console.error)
