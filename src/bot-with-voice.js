require('dotenv').config()
const { WechatyBuilder } = require('wechaty')
const { PuppetWechat4u } = require('wechaty-puppet-wechat4u')
const aiService = require('./ai-service')
const config = require('../config/ai-config')
const axios = require('axios')
const fs = require('fs')
const path = require('path')

// 对话历史管理
const conversations = new Map()

// 语音转文字（调用 Flask 服务）
async function speechToText(audioBuffer) {
  try {
    const response = await axios.post('http://localhost:5000/api/speech_to_text', {
      audio: audioBuffer.toString('base64')
    })
    return response.data.text
  } catch (error) {
    console.error('语音识别失败:', error.message)
    return null
  }
}

// 文字转语音（调用 Flask 服务）
async function textToSpeech(text) {
  try {
    const response = await axios.post('http://localhost:5000/api/text_to_speech', {
      text: text
    }, {
      responseType: 'arraybuffer'
    })
    return Buffer.from(response.data)
  } catch (error) {
    console.error('语音合成失败:', error.message)
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

  const contact = msg.talker()
  const userId = contact.id

  // 处理语音消息
  if (msg.type() === bot.Message.Type.Audio) {
    console.log(`收到语音消息 [${contact.name()}]`)

    try {
      // 下载语音文件
      const fileBox = await msg.toFileBox()
      const audioPath = path.join(__dirname, '../temp', `${Date.now()}.silk`)
      await fileBox.toFile(audioPath)

      // 读取音频
      const audioBuffer = fs.readFileSync(audioPath)

      // 语音转文字
      const text = await speechToText(audioBuffer)

      // 删除临时文件
      fs.unlinkSync(audioPath)

      if (!text) {
        await msg.say('抱歉，无法识别语音内容')
        return
      }

      console.log(`语音识别结果: ${text}`)

      // AI 处理
      const reply = await chat(userId, text)
      console.log('AI 回复:', reply)

      // 发送文字回复
      await msg.say(reply)

      // 可选：发送语音回复
      // const audioReply = await textToSpeech(reply)
      // if (audioReply) {
      //   const audioFile = FileBox.fromBuffer(audioReply, 'reply.wav')
      //   await msg.say(audioFile)
      // }

    } catch (error) {
      console.error('处理语音消息错误:', error)
      await msg.say('抱歉，处理语音时出错了')
    }
    return
  }

  // 处理文字消息
  const text = msg.text()
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
      '\n支持语音消息（需要 Flask 服务运行）'
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
    await msg.say(reply)
    console.log('回复已发送')
  } catch (error) {
    console.error('处理消息错误:', error)
    await msg.say('抱歉，处理消息时出错了')
  }
})

// 启动机器人
bot.start()
  .then(() => {
    console.log('机器人启动成功')
    console.log('提示: 语音功能需要 Flask 服务，请运行: python app.py')
  })
  .catch(e => console.error('启动失败:', e))
