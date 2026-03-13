require('dotenv').config()
const { WechatyBuilder } = require('wechaty')
const { PuppetWechat4u } = require('wechaty-puppet-wechat4u')
const { FileBox } = require('file-box')
const aiService = require('./ai-service')
const config = require('../config/ai-config')
const axios = require('axios')
const fs = require('fs')
const path = require('path')

// 创建临时目录
const tempDir = path.join(__dirname, '../temp')
if (!fs.existsSync(tempDir)) {
  fs.mkdirSync(tempDir, { recursive: true })
}

// 对话历史管理
const conversations = new Map()

// 文字转语音（调用 Flask 服务）
async function textToSpeech(text) {
  try {
    console.log('正在生成语音...')
    const response = await axios.post('http://localhost:5000/api/synthesize', {
      text: text,
      voice_enabled: true
    }, {
      responseType: 'arraybuffer',
      timeout: 30000
    })

    console.log('✓ 语音生成成功')
    return Buffer.from(response.data)
  } catch (error) {
    console.error('✗ 语音合成失败:', error.message)
    return null
  }
}

// 聊天处理函数
async function chat(userId, message) {
  if (!conversations.has(userId)) {
    conversations.set(userId, [])
  }
  const history = conversations.get(userId)

  history.push({ role: 'user', content: message })

  if (history.length > config.bot.maxHistoryLength) {
    history.splice(0, history.length - config.bot.maxHistoryLength)
  }

  try {
    const reply = await aiService.chat(history)
    history.push({ role: 'assistant', content: reply })
    return reply
  } catch (error) {
    return '抱歉，我遇到了一些问题，请稍后再试。'
  }
}

// 创建机器人
const bot = WechatyBuilder.build({
  name: config.bot.name,
  puppet: new PuppetWechat4u(),
})

bot.on('scan', (qrcode, status) => {
  console.log(`扫码登录: https://wechaty.js.org/qrcode/${encodeURIComponent(qrcode)}`)
})

bot.on('login', user => {
  console.log(`登录成功: ${user}`)
  console.log(`当前 AI 服务: ${aiService.getCurrentService()}`)
  console.log(`语音功能: 需要 Flask 服务运行在 http://localhost:5000`)
})

bot.on('message', async msg => {
  if (msg.self()) return

  const text = msg.text()
  const contact = msg.talker()
  const userId = contact.id

  console.log(`收到消息 [${contact.name()}]: ${text}`)

  // 命令处理
  if (text === '/clear') {
    conversations.delete(userId)
    await msg.say('对话历史已清除')
    return
  }

  if (text === '/help') {
    await msg.say(
      '可用命令:\n' +
      '/clear - 清除对话历史\n' +
      '/help - 显示帮助\n' +
      '/service - 查看当前 AI 服务\n' +
      '/switch <gemini|chatgpt|claude> - 切换 AI 服务\n' +
      '/voice - 切换语音回复模式\n' +
      '\n当前会以语音形式回复你的消息'
    )
    return
  }

  if (text === '/service') {
    await msg.say(`当前使用: ${aiService.getCurrentService()}`)
    return
  }

  if (text.startsWith('/switch ')) {
    const service = text.split(' ')[1]
    try {
      aiService.switchService(service)
      await msg.say(`已切换到 ${service}`)
    } catch (error) {
      await msg.say('切换失败: ' + error.message)
    }
    return
  }

  // AI 对话
  try {
    console.log('正在调用 AI...')
    const reply = await chat(userId, text)
    console.log('AI 回复:', reply)

    // 发送文字回复
    await msg.say(reply)
    console.log('✓ 文字回复已发送')

    // 生成并发送语音回复
    const audioBuffer = await textToSpeech(reply)
    if (audioBuffer) {
      // 保存为临时文件
      const audioPath = path.join(tempDir, `voice_${Date.now()}.wav`)
      fs.writeFileSync(audioPath, audioBuffer)

      // 发送语音文件
      const fileBox = FileBox.fromFile(audioPath)
      await msg.say(fileBox)
      console.log('✓ 语音回复已发送')

      // 延迟删除临时文件
      setTimeout(() => {
        if (fs.existsSync(audioPath)) {
          fs.unlinkSync(audioPath)
        }
      }, 5000)
    } else {
      console.log('⚠️ 语音生成失败，仅发送文字')
    }

  } catch (error) {
    console.error('处理消息错误:', error)
    await msg.say('抱歉，处理消息时出错了')
  }
})

// 启动机器人
bot.start()
  .then(() => {
    console.log('机器人启动成功')
    console.log('提示: 语音功能需要 Flask 服务，请先运行: python app.py')
  })
  .catch(e => console.error('启动失败:', e))
