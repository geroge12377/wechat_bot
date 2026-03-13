require('dotenv').config()
const { WechatyBuilder } = require('wechaty')
const { PuppetXp } = require('wechaty-puppet-xp')
const { FileBox } = require('file-box')
const axios = require('axios')
const path = require('path')

// Flask 服务地址
const FLASK_API_URL = 'http://localhost:5000'

// 群消息配置
const GROUP_CONFIG = {
  keywords: ['独角兽', '妹妹'],  // 触发关键词
  cooldownMs: 5000,              // 同一群5秒冷却
  adminIds: []                   // 管理员微信ID列表（100%响应）
}

// 群聊冷却时间记录
const groupCooldowns = new Map()

// 创建机器人（使用 PuppetXp，需要 PC 微信 3.9.x 版本）
const bot = WechatyBuilder.build({
  name: 'wechat-unicorn-bot',
  puppet: new PuppetXp(),
})

// 调用 Flask API 获取回复
async function getUnicornReply(userId, message, isGroup = false, mentioned = false) {
  try {
    console.log(`[API] 调用 Flask API: ${message}`)
    const response = await axios.post(`${FLASK_API_URL}/chat`, {
      message: message,
      user_id: userId,
      is_group: isGroup,
      mentioned: mentioned
    }, {
      timeout: 120000  // 120秒超时（TTS + SILK 转码需要时间）
    })

    console.log(`[API] 收到响应:`, response.data)
    return response.data
  } catch (error) {
    console.error('[API] 调用失败:', error.message)
    throw error
  }
}

// 检查是否包含关键词或被@
function shouldRespondInGroup(text, mentionSelf) {
  // 如果被@，直接响应
  if (mentionSelf) {
    return true
  }

  // 检查是否包含关键词
  for (const keyword of GROUP_CONFIG.keywords) {
    if (text.includes(keyword)) {
      return true
    }
  }

  return false
}

// 检查群聊冷却时间
function checkGroupCooldown(roomId, userId) {
  // 管理员无冷却限制
  if (GROUP_CONFIG.adminIds.includes(userId)) {
    console.log(`[冷却] 管理员 ${userId}，无冷却限制`)
    return true
  }

  const now = Date.now()
  const lastResponse = groupCooldowns.get(roomId)

  if (!lastResponse || now - lastResponse >= GROUP_CONFIG.cooldownMs) {
    // 更新最后响应时间
    groupCooldowns.set(roomId, now)
    return true
  }

  const remainingMs = GROUP_CONFIG.cooldownMs - (now - lastResponse)
  console.log(`[冷却] 群 ${roomId} 冷却中，剩余 ${Math.ceil(remainingMs / 1000)} 秒`)
  return false
}

// 扫码登录
bot.on('scan', (qrcode, status) => {
  console.log(`[登录] 扫码登录: https://wechaty.js.org/qrcode/${encodeURIComponent(qrcode)}`)
})

// 登录成功
bot.on('login', user => {
  console.log(`[登录] 登录成功: ${user}`)
  console.log(`[系统] Flask API: ${FLASK_API_URL}`)

  // 检查 Flask 服务是否可用
  axios.get(`${FLASK_API_URL}/health`)
    .then(res => {
      console.log(`[系统] Flask 服务状态:`, res.data)
    })
    .catch(err => {
      console.error(`[错误] Flask 服务不可用，请先启动: python wechat_bot_integrated.py server`)
    })
})

// 登出
bot.on('logout', user => {
  console.log(`[登出] ${user} 已登出`)
})

// 消息处理
bot.on('message', async msg => {
  // 忽略自己发的消息
  if (msg.self()) return

  const text = msg.text()
  const contact = msg.talker()
  const room = msg.room()
  const userId = contact.id
  const userName = contact.name()

  console.log(`\n[消息] 收到 [${userName}]${room ? ` @${await room.topic()}` : ''}: ${text}`)

  // 命令处理
  if (text === '/help') {
    await msg.say(
      '🦄 独角兽 AI 助手\n\n' +
      '可用命令:\n' +
      '/help - 显示帮助\n' +
      '/ping - 测试连接\n\n' +
      '直接发送消息即可与独角兽对话~\n' +
      '群聊中需要@我或提到"独角兽"、"妹妹"'
    )
    return
  }

  if (text === '/ping') {
    try {
      const healthCheck = await axios.get(`${FLASK_API_URL}/health`)
      await msg.say(`✅ 服务正常\n${JSON.stringify(healthCheck.data, null, 2)}`)
    } catch (error) {
      await msg.say(`❌ 服务异常: ${error.message}`)
    }
    return
  }

  // 群聊处理
  if (room) {
    const roomId = room.id
    const mentionSelf = await msg.mentionSelf()

    // 检查是否应该响应（被@或包含关键词）
    if (!shouldRespondInGroup(text, mentionSelf)) {
      console.log('[群聊] 未被@且无关键词，忽略')
      return
    }

    // 检查冷却时间
    if (!checkGroupCooldown(roomId, userId)) {
      console.log('[群聊] 冷却中，忽略')
      return
    }

    console.log('[群聊] 触发响应')
    await handleChat(text, msg, userId, true, mentionSelf)
    return
  }

  // 私聊直接处理
  console.log('[私聊] 直接响应')
  await handleChat(text, msg, userId, false, false)
})

// 处理对话
async function handleChat(text, msg, userId, isGroup, mentioned) {
  try {
    console.log('[处理] 正在调用独角兽 AI...')

    const result = await getUnicornReply(userId, text, isGroup, mentioned)

    if (!result.success) {
      console.error('[错误] AI 处理失败:', result.error)
      await msg.say('抱歉，我遇到了一些问题...')
      return
    }

    // 1. 发送文字回复
    console.log('[回复] 文字:', result.text)
    await msg.say(result.text)

    // 2. 发送语音（如果有）
    if (result.audio_path) {
      try {
        console.log('[语音] 准备发送:', result.audio_path)

        // 判断文件类型并设置正确的 MIME 类型
        const isSilk = result.audio_path.endsWith('.silk')
        const audioBox = FileBox.fromFile(result.audio_path, isSilk ? 'unicorn_voice.silk' : 'unicorn_voice.wav')

        // 如果是 SILK 格式，设置正确的 MIME 类型
        if (isSilk) {
          audioBox.mimeType = 'audio/silk'
        }

        await msg.say(audioBox)

        console.log('[语音] 发送成功')
      } catch (audioError) {
        console.error('[语音] 发送失败:', audioError.message)
        // 语音发送失败不影响文字回复
      }
    }

    console.log('[完成] 消息处理完成\n')

  } catch (error) {
    console.error('[错误] 处理消息失败:', error)
    await msg.say('抱歉，处理消息时出错了')
  }
}

// 错误处理
bot.on('error', error => {
  console.error('[错误] 机器人错误:', error)
})

// 启动机器人
console.log('[启动] 正在启动独角兽微信机器人...')
console.log('[提示] 请确保已启动 Flask 服务: python wechat_bot_integrated.py server\n')

bot.start()
  .then(() => {
    console.log('[成功] 机器人启动成功')
  })
  .catch(error => {
    console.error('[失败] 启动失败:', error)
    process.exit(1)
  })

// 优雅退出
process.on('SIGINT', async () => {
  console.log('\n[退出] 正在关闭机器人...')
  await bot.stop()
  process.exit(0)
})
