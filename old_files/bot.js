require('dotenv').config()
const { WechatyBuilder } = require('wechaty')
const { PuppetWechat4u } = require('wechaty-puppet-wechat4u')
const OpenAI = require('openai')

const client = new OpenAI({
  apiKey: process.env.AI_API_KEY,
  baseURL: process.env.AI_BASE_URL
})

const conversations = new Map()

async function chat(userId, message) {
  if (!conversations.has(userId)) {
    conversations.set(userId, [])
  }
  const history = conversations.get(userId)

  history.push({ role: 'user', content: message })

  if (history.length > 20) {
    history.splice(0, history.length - 20)
  }

  try {
    const response = await client.chat.completions.create({
      model: 'gemini-3.1-flash-lite-preview',
      messages: [
        { role: 'system', content: '你是一个友好的AI助手。' },
        ...history
      ],
      max_tokens: 1000
    })

    const reply = response.choices[0].message.content
    history.push({ role: 'assistant', content: reply })

    return reply
  } catch (error) {
    console.error('AI API 错误:', error)
    return '抱歉，我遇到了一些问题，请稍后再试。'
  }
}

const bot = WechatyBuilder.build({
  name: 'wechat-bot',
  puppet: new PuppetWechat4u(),
})

bot.on('scan', (qrcode, status) => {
  console.log(`扫码登录: https://wechaty.js.org/qrcode/${encodeURIComponent(qrcode)}`)
})

bot.on('login', user => {
  console.log(`登录成功: ${user}`)
})

bot.on('message', async msg => {
  if (msg.self()) return

  const text = msg.text()
  const contact = msg.talker()
  const userId = contact.id

  console.log(`收到消息 [${contact.name()}]: ${text}`)

  if (text === '/clear') {
    conversations.delete(userId)
    await msg.say('对话历史已清除')
    return
  }

  if (text === '/help') {
    await msg.say('可用命令:\n/clear - 清除对话历史\n/help - 显示帮助')
    return
  }

  try {
    console.log('正在调用 AI...')
    const reply = await chat(userId, text)
    console.log('AI 回复:', reply)
    console.log('正在发送回复...')
    await msg.say(reply)
    console.log('回复已发送')
  } catch (error) {
    console.error('处理消息错误:', error)
    await msg.say('抱歉，处理消息时出错了')
  }
})

bot.start()
  .then(() => console.log('机器人启动成功'))
  .catch(e => console.error('启动失败:', e))
