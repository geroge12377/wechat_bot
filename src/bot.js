require('dotenv').config()
const { WechatyBuilder } = require('wechaty')
const { PuppetWechat4u } = require('wechaty-puppet-wechat4u')
const aiService = require('./ai-service')
const config = require('../config/ai-config')

// 对话历史管理
const conversations = new Map()

// 聊天处理函数
async function chat(userId, message) {
  if (!conversations.has(userId)) {
    conversations.set(userId, [])
  }
  const history = conversations.get(userId)

  history.push({ role: 'user', content: message })

  // 限制历史长度
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

// 扫码登录
bot.on('scan', (qrcode, status) => {
  console.log(`扫码登录: https://wechaty.js.org/qrcode/${encodeURIComponent(qrcode)}`)
})

// 登录成功
bot.on('login', user => {
  console.log(`登录成功: ${user}`)
  console.log(`当前 AI 服务: ${aiService.getCurrentService()}`)
})

// 消息处理
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
      '/switch <gemini|chatgpt|claude> - 切换 AI 服务'
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
  .then(() => console.log('机器人启动成功'))
  .catch(e => console.error('启动失败:', e))
