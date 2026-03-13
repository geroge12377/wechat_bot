require('dotenv').config()
const { WechatyBuilder } = require('wechaty')
const { PuppetWechat4u } = require('wechaty-puppet-wechat4u')
const { FileBox } = require('file-box')
const aiService = require('./ai-service')
const config = require('../config/ai-config')
const whitelist = require('../config/whitelist')
const axios = require('axios')
const fs = require('fs')
const path = require('path')

// 导入新系统
const memoryManager = require('./memory/memory-manager')
const emotionManager = require('./memory/emotion-manager')
const timeManager = require('./memory/time-manager')
const multiAI = require('./ai-multi-layer')
const { PermissionManager, PERMISSION_LEVELS } = require('./skills/permission-manager')

// 创建目录
const tempDir = path.join(__dirname, '../temp')
const emojiDir = path.join(__dirname, '../emojis')
if (!fs.existsSync(tempDir)) fs.mkdirSync(tempDir, { recursive: true })
if (!fs.existsSync(emojiDir)) fs.mkdirSync(emojiDir, { recursive: true })

// 对话历史管理
const conversations = new Map()

// 权限管理器
const permissionManager = new PermissionManager()

// 用户对话状态跟踪
const userStates = new Map()

// 初始化系统
async function initSystems() {
  try {
    await memoryManager.init()
    await emotionManager.init()
    console.log('✓ 记忆系统已初始化')
    console.log('✓ 情感系统已初始化')

    // 检测 Claude 可用性
    try {
      const testResponse = await multiAI.chat(
        [{ role: 'user', content: '测试' }],
        '简短回复"ok"'
      )
      console.log('✓ Claude AI 可用')
      return true
    } catch (error) {
      console.error('✗ Claude AI 不可用:', error.message)
      console.log('→ 将使用备用 AI 服务')
      return false
    }
  } catch (error) {
    console.error('✗ 系统初始化失败:', error.message)
    console.log('→ 将使用基础功能')
    return false
  }
}

// 根据用户信息自动分配权限
async function assignUserPermission(userId, contact) {
  const name = contact.name()

  // 如果已有权限设置，不覆盖
  if (permissionManager.getUserPermission(userId) !== permissionManager.defaultPermission) {
    return
  }

  // 如果记忆系统未初始化，使用默认权限
  if (!memoryManager.initialized) {
    permissionManager.setUserPermission(userId, PERMISSION_LEVELS.GUEST)
    return
  }

  try {
    const profile = await memoryManager.getUserProfile(userId)

    // 修改：只分配访客权限，不自动升级
    // 权限升级必须手动通过 /setperm 命令
    if (profile.total_messages === 0) {
      permissionManager.setUserPermission(userId, PERMISSION_LEVELS.GUEST)
      console.log(`→ 新用户 [${name}] 分配权限: 访客`)
    } else {
      // 老用户也保持访客权限，除非手动设置
      const currentLevel = permissionManager.getUserPermission(userId)
      if (currentLevel === permissionManager.defaultPermission) {
        permissionManager.setUserPermission(userId, PERMISSION_LEVELS.GUEST)
      }
    }
  } catch (error) {
    console.error('权限分配失败:', error.message)
    permissionManager.setUserPermission(userId, PERMISSION_LEVELS.GUEST)
  }
}

// 白名单检查函数
function isAllowed(contact, room = null) {
  const name = contact.name()
  const id = contact.id

  // 检查黑名单
  if (whitelist.blacklist.includes(name) || whitelist.blacklist.includes(id)) {
    return false
  }

  // 如果未启用白名单，允许所有人
  if (!whitelist.enabled) {
    return true
  }

  // 群聊检查
  if (room) {
    const roomName = room.topic()
    return whitelist.rooms.includes(roomName)
  }

  // 私聊检查白名单
  return whitelist.users.includes(name) || whitelist.users.includes(id)
}

// 关键词检查函数
function hasKeyword(text) {
  if (!whitelist.keywordMode.enabled) {
    return true  // 未启用关键词模式，允许所有消息
  }

  const keywords = whitelist.keywordMode.keywords
  const exactMatch = whitelist.keywordMode.exactMatch

  for (const keyword of keywords) {
    if (exactMatch) {
      if (text === keyword) return true
    } else {
      if (text.includes(keyword)) return true
    }
  }

  return false
}

// 检测是否能接话（本地规则 + AI 判断）
async function canRespondToMessage(text) {
  // 本地规则：快速判断明显不能接话的情况
  const cantRespondPatterns = [
    /^(好的?|嗯|哦|ok|知道了|收到|明白了?)$/i,  // 简单确认
    /^(拜拜|再见|走了|下线了|睡了|88)$/i,        // 告别
    /我(去|要)(吃饭|睡觉|上课|工作|忙)/,         // 单方面通知
    /^[。，、！？,.!?]+$/                        // 纯标点
  ]

  for (const pattern of cantRespondPatterns) {
    if (pattern.test(text)) {
      console.log('→ 本地规则：不能接话')
      return false
    }
  }

  // 本地规则：可以接话的情况
  const canRespondPatterns = [
    /[？?]$/,                                    // 问句
    /怎么|为什么|什么|哪里|谁|如何/,              // 疑问词
    /好(累|开心|难过|高兴|伤心)/,                 // 情绪表达
    /(天气|今天|明天|最近)/,                      // 可聊话题
    /看(了|到|见)|听(了|到|说)/                   // 分享经历
  ]

  for (const pattern of canRespondPatterns) {
    if (pattern.test(text)) {
      console.log('→ 本地规则：可以接话')
      return true
    }
  }

  // 如果本地规则无法判断，使用 AI（但有超时保护）
  console.log('→ 使用 AI 判断...')
  try {
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

    // 检查响应格式
    if (!response.data || !response.data.choices || !response.data.choices[0]) {
      console.error('→ AI 响应格式错误:', JSON.stringify(response.data))
      return false
    }

    const result = response.data.choices[0].message.content.trim()

    // 修复：正确判断"能"和"不能"
    // 优先检查否定词
    if (result.includes('不能') || result.includes('不可以') || result.includes('不行')) {
      console.log(`→ AI 判断：不能接话 (回复: ${result})`)
      return false
    }

    // 再检查肯定词
    if (result.includes('能') || result.includes('可以') || result.includes('行')) {
      console.log(`→ AI 判断：可以接话 (回复: ${result})`)
      return true
    }

    // 无法判断时默认不接话
    console.log(`→ AI 判断：无法识别 (回复: ${result})，默认不接话`)
    return false
  } catch (error) {
    if (error.code === 'ECONNABORTED') {
      console.error('→ AI 判断超时，默认不接话')
    } else if (error.response) {
      console.error('→ AI 判断失败 (HTTP', error.response.status + '):', error.response.data)
    } else {
      console.error('→ AI 判断失败:', error.message)
    }
    // 超时或失败时，采用保守策略：不接话
    return false
  }
}

// 获取或创建用户状态
function getUserState(userId) {
  if (!userStates.has(userId)) {
    userStates.set(userId, {
      noKeywordCount: 0,        // 无关键词消息计数
      isStandby: false,         // 是否处于待机状态
      lastMessageTime: null,
      timeoutTimer: null
    })
  }
  return userStates.get(userId)
}

// 清除超时定时器
function clearUserTimeout(userId) {
  const state = getUserState(userId)
  if (state.timeoutTimer) {
    clearTimeout(state.timeoutTimer)
    state.timeoutTimer = null
  }
}

// 设置30秒超时（仅在待机状态）
function setUserTimeout(userId, msg) {
  clearUserTimeout(userId)
  const state = getUserState(userId)

  state.timeoutTimer = setTimeout(async () => {
    console.log(`⏰ 用户 ${userId} 30秒超时，发送关键词提醒`)
    try {
      await msg.say('哥哥...如果想和独角兽说话，记得叫我的名字哦...（独角兽、妹妹、@独角兽）...的说')
    } catch (error) {
      console.error('发送超时提醒失败:', error)
    }
    // 超时后保持待机状态
  }, 30000)
}

// 表情包库（可以添加更多）
const emojiPacks = {
  '笑': ['😄', '😊', '😁', '🤣'],
  '哭': ['😭', '😢', '😿'],
  '爱': ['❤️', '💕', '💖', '😍'],
  '赞': ['👍', '👏', '💪'],
  '疑问': ['❓', '🤔', '😕'],
  '惊讶': ['😲', '😮', '😯'],
  '生气': ['😠', '😡', '💢'],
  '害羞': ['😳', '😊', '🙈']
}

// 文字转语音
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

// 图片识别（使用 Gemini Vision）
async function recognizeImage(imageBuffer) {
  try {
    console.log('正在识别图片...')
    const base64Image = imageBuffer.toString('base64')

    const response = await axios.post(process.env.AI_BASE_URL.replace('/chat/completions', '/vision'), {
      model: 'gemini-3.1-flash-lite-preview',
      messages: [{
        role: 'user',
        content: [
          { type: 'text', text: '请描述这张图片的内容' },
          { type: 'image_url', image_url: { url: `data:image/jpeg;base64,${base64Image}` } }
        ]
      }],
      max_tokens: 500
    }, {
      headers: {
        'Authorization': `Bearer ${process.env.AI_API_KEY}`,
        'Content-Type': 'application/json'
      }
    })

    return response.data.choices[0].message.content
  } catch (error) {
    console.error('✗ 图片识别失败:', error.message)
    return '抱歉，无法识别这张图片'
  }
}

// 获取随机表情
function getRandomEmoji(keyword) {
  for (const [key, emojis] of Object.entries(emojiPacks)) {
    if (keyword.includes(key)) {
      return emojis[Math.floor(Math.random() * emojis.length)]
    }
  }
  return null
}

// 聊天处理（整合记忆和情感系统）
async function chat(userId, message) {
  if (!conversations.has(userId)) {
    conversations.set(userId, [])
  }
  const history = conversations.get(userId)

  let systemPrompt = config.bot.systemPrompt

  // 如果记忆系统已初始化，使用完整功能
  if (memoryManager.initialized) {
    try {
      // 获取用户档案
      const profile = await memoryManager.getUserProfile(userId)

      // 时间感知
      timeManager.recordInteraction(userId)
      const timeContext = timeManager.generateTimeContext(userId)

      // 情感分析
      const { emotion, intensity } = emotionManager.analyzeEmotion(message, profile.affection_level)
      const { affectionChange, intimacyChange } = emotionManager.calculateRelationshipChange(message)

      // 获取相关记忆
      const memories = await memoryManager.getMemory(userId, null, 5)
      const memoryContext = memories.length > 0
        ? `\n相关记忆：\n${memories.map(m => `- ${m.key}: ${m.value}`).join('\n')}`
        : ''

      // 构建系统提示词
      systemPrompt = `${config.bot.systemPrompt}

${timeContext}
当前情感状态：${emotion}（强度：${intensity}/10）
好感度：${profile.affection_level}/100
亲密度：${profile.intimacy_score}/100
${memoryContext}

权限等级：${permissionManager.getPermissionName(permissionManager.getUserPermission(userId))}`

      history.push({ role: 'user', content: message })

      if (history.length > config.bot.maxHistoryLength) {
        history.splice(0, history.length - config.bot.maxHistoryLength)
      }

      // 使用多层 AI（Claude 主对话）
      let reply
      try {
        reply = await multiAI.chat(history, systemPrompt)
      } catch (claudeError) {
        console.error('Claude 调用失败，使用备用服务:', claudeError.message)
        // 降级到原有的 AI 服务
        reply = await aiService.chat(history)
      }

      history.push({ role: 'assistant', content: reply })

      // 保存对话历史
      await memoryManager.saveChatHistory(userId, message, reply, emotion, affectionChange)

      // 记录情感
      await memoryManager.logEmotion(userId, emotion, message, intensity)

      // 更新亲密度
      if (intimacyChange !== 0) {
        await memoryManager.updateUserProfile(userId, {
          intimacy_score: Math.max(0, Math.min(100, profile.intimacy_score + intimacyChange))
        })
      }

      return reply
    } catch (error) {
      console.error('记忆系统错误，使用基础模式:', error.message)
      // 降级到基础模式
    }
  }

  // 基础模式（无记忆系统）
  history.push({ role: 'user', content: message })

  if (history.length > config.bot.maxHistoryLength) {
    history.splice(0, history.length - config.bot.maxHistoryLength)
  }

  try {
    const reply = await aiService.chat(history)
    history.push({ role: 'assistant', content: reply })
    return reply
  } catch (error) {
    console.error('AI 对话错误:', error)
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

bot.on('login', async user => {
  console.log(`登录成功: ${user}`)

  // 初始化系统（不阻塞启动）
  try {
    await initSystems()
  } catch (error) {
    console.error('✗ 系统初始化失败:', error)
    console.log('→ 将使用基础功能（无记忆和情感系统）')
  }

  console.log(`当前 AI 服务: ${aiService.getCurrentService()}`)
  console.log(`✨ 功能: 语音回复 + 表情包 + 图片识别 + 记忆系统 + 情感系统`)
  console.log(`🔒 白名单: ${whitelist.enabled ? '已启用' : '未启用'}`)
  console.log(`🔑 关键词模式: ${whitelist.keywordMode.enabled ? '已启用' : '未启用'}`)
  if (whitelist.keywordMode.enabled) {
    console.log(`   触发关键词: ${whitelist.keywordMode.keywords.join(', ')}`)
  }
  if (whitelist.enabled) {
    console.log(`   允许用户: ${whitelist.users.join(', ')}`)
  }
})

bot.on('message', async msg => {
  if (msg.self()) return

  const contact = msg.talker()
  const room = msg.room()
  const userId = contact.id

  // 白名单检查
  if (!isAllowed(contact, room)) {
    console.log(`⚠️ 忽略消息 [${contact.name()}]: 不在白名单中`)
    return
  }

  // 自动分配权限
  await assignUserPermission(userId, contact)

  // 群聊处理
  if (room) {
    // 如果不回复群消息，直接返回
    if (!whitelist.replyInRoom) {
      return
    }

    // 如果需要@才回复
    if (whitelist.requireMention) {
      const mentionSelf = await msg.mentionSelf()
      if (!mentionSelf) {
        return
      }
    }
  }

  // 处理图片消息
  if (msg.type() === bot.Message.Type.Image) {
    console.log(`收到图片 [${contact.name()}]`)

    try {
      // 下载图片
      const fileBox = await msg.toFileBox()
      const imagePath = path.join(tempDir, `${Date.now()}.jpg`)
      await fileBox.toFile(imagePath)

      // 读取图片
      const imageBuffer = fs.readFileSync(imagePath)

      // 识别图片
      const description = await recognizeImage(imageBuffer)

      // 删除临时文件
      fs.unlinkSync(imagePath)

      console.log(`图片识别结果: ${description}`)

      // 发送识别结果
      await msg.say(`我看到了：${description}`)

    } catch (error) {
      console.error('处理图片错误:', error)
      await msg.say('抱歉，无法识别这张图片')
    }
    return
  }

  // 处理文字消息
  const text = msg.text()
  console.log(`收到消息 [${contact.name()}]: ${text}`)

  // 命令处理（命令不受关键词限制）
  if (text.startsWith('/')) {
    await handleCommand(text, msg, userId, contact)
    return
  }

  // 判断是否为群聊
  const isGroupChat = !!room

  // 关键词检查
  const hasKw = hasKeyword(text)

  // 群聊中没有关键词，使用待机状态和接话判断机制（不直接返回）
  // 私聊不需要关键词

  if (hasKw) {
    // 包含关键词，清除状态和超时，退出待机
    const state = getUserState(userId)
    state.noKeywordCount = 0
    state.isStandby = false
    clearUserTimeout(userId)

    console.log(`✓ 包含关键词，正常对话`)
    // 正常处理对话
    await handleChat(text, msg, userId)
  } else if (!isGroupChat) {
    // 私聊且无关键词，直接对话（不需要关键词触发）
    console.log(`✓ 私聊消息，直接对话`)
    await handleChat(text, msg, userId)
  } else {
    // 群聊且无关键词，使用待机状态和接话判断机制
    const state = getUserState(userId)

    // 如果已经在待机状态，直接忽略
    if (state.isStandby) {
      console.log(`⚠️ 待机状态，忽略消息`)
      return
    }

    // 增加计数
    state.noKeywordCount++
    console.log(`⚠️ 群聊消息不包含关键词 (第 ${state.noKeywordCount} 次)`)

    if (state.noKeywordCount === 1) {
      // 第一次：检查能否接话
      console.log(`→ 检查能否接话...`)
      const canRespond = await canRespondToMessage(text)

      if (canRespond) {
        // 可以接话，正常对话
        console.log(`✓ 可以接话，正常对话`)
        await handleChat(text, msg, userId)
        state.noKeywordCount = 0  // 重置计数器，成功接话视为新对话开始
      } else {
        // 不能接话，进入待机准备
        console.log(`✗ 不能接话，等待第二次`)
      }
    } else if (state.noKeywordCount === 2 || state.noKeywordCount === 3) {
      // 第二三次：进入待机状态
      console.log(`→ 进入待机状态`)
      state.isStandby = true
      setUserTimeout(userId, msg)
    }
  }
})

// 处理命令
async function handleCommand(text, msg, userId, contact) {
  if (text === '/clear') {
    conversations.delete(userId)
    await msg.say('对话历史已清除 ✨')
    return
  }

  if (text === '/help') {
    const commands = permissionManager.getAvailableCommands(userId)
    const commandList = commands.map(c => `${c.command} - ${c.description}`).join('\n')
    await msg.say(
      '🤖 可用命令:\n' + commandList +
      '\n\n✨ 功能:\n' +
      '📝 文字对话\n' +
      '🎤 语音回复\n' +
      '😊 智能表情包\n' +
      '🖼️ 图片识别\n' +
      '🧠 记忆系统\n' +
      '💖 情感系统'
    )
    return
  }

  if (text === '/stats') {
    if (!permissionManager.hasPermission(userId, '/stats')) {
      await msg.say('⚠️ 权限不足')
      return
    }
    if (!memoryManager.initialized) {
      await msg.say('⚠️ 记忆系统未初始化')
      return
    }
    try {
      const stats = await memoryManager.getStats(userId)
      await msg.say(
        `📊 个人统计\n` +
        `昵称：${stats.nickname}\n` +
        `好感度：${stats.affectionLevel}/100\n` +
        `亲密度：${stats.intimacyScore}/100\n` +
        `消息总数：${stats.totalMessages}\n` +
        `记忆数量：${stats.memoryCount}\n` +
        `首次见面：${stats.firstMet}`
      )
    } catch (error) {
      await msg.say('⚠️ 获取统计失败')
    }
    return
  }

  if (text === '/mood') {
    if (!permissionManager.hasPermission(userId, '/mood')) {
      await msg.say('⚠️ 权限不足')
      return
    }
    if (!memoryManager.initialized) {
      await msg.say('⚠️ 记忆系统未初始化')
      return
    }
    try {
      const emotion = await memoryManager.getCurrentEmotion(userId)
      const profile = await memoryManager.getUserProfile(userId)
      await msg.say(
        `💭 当前状态\n` +
        `心情：${emotion}\n` +
        `好感度：${profile.affection_level}/100\n` +
        `亲密度：${profile.intimacy_score}/100`
      )
    } catch (error) {
      await msg.say('⚠️ 获取状态失败')
    }
    return
  }

  if (text === '/memory') {
    if (!permissionManager.hasPermission(userId, '/memory')) {
      await msg.say('⚠️ 权限不足')
      return
    }
    if (!memoryManager.initialized) {
      await msg.say('⚠️ 记忆系统未初始化')
      return
    }
    try {
      const memories = await memoryManager.getMemory(userId, null, 5)
      if (memories.length === 0) {
        await msg.say('还没有记忆哦')
      } else {
        const memoryText = memories.map(m => `${m.key}: ${m.value} (重要性: ${m.importance})`).join('\n')
        await msg.say(`🧠 记忆片段:\n${memoryText}`)
      }
    } catch (error) {
      await msg.say('⚠️ 获取记忆失败')
    }
    return
  }

  if (text === '/whitelist') {
    const status = whitelist.enabled ? '✅ 已启用' : '❌ 未启用'
    const users = whitelist.users.length > 0 ? whitelist.users.join(', ') : '无'
    await msg.say(
      `🔒 白名单状态: ${status}\n` +
      `👥 允许用户: ${users}\n` +
      `💬 群聊回复: ${whitelist.replyInRoom ? '是' : '否'}`
    )
    return
  }

  if (text.startsWith('/adduser ')) {
    if (!permissionManager.hasPermission(userId, '/adduser')) {
      await msg.say('⚠️ 权限不足')
      return
    }
    const username = text.replace('/adduser ', '').trim()
    if (!whitelist.users.includes(username)) {
      whitelist.users.push(username)
      await msg.say(`✅ 已添加 ${username} 到白名单`)
      console.log(`✓ 添加用户到白名单: ${username}`)
    } else {
      await msg.say(`⚠️ ${username} 已在白名单中`)
    }
    return
  }

  if (text.startsWith('/removeuser ')) {
    if (!permissionManager.hasPermission(userId, '/removeuser')) {
      await msg.say('⚠️ 权限不足')
      return
    }
    const username = text.replace('/removeuser ', '').trim()
    const index = whitelist.users.indexOf(username)
    if (index > -1) {
      whitelist.users.splice(index, 1)
      await msg.say(`✅ 已从白名单移除 ${username}`)
      console.log(`✓ 从白名单移除用户: ${username}`)
    } else {
      await msg.say(`⚠️ ${username} 不在白名单中`)
    }
    return
  }

  if (text.startsWith('/setperm ')) {
    if (!permissionManager.hasPermission(userId, '/setperm')) {
      await msg.say('⚠️ 权限不足')
      return
    }
    const parts = text.split(' ')
    if (parts.length !== 3) {
      await msg.say('用法: /setperm <用户ID> <等级0-4>')
      return
    }
    const targetUserId = parts[1]
    const level = parseInt(parts[2])
    if (level >= 0 && level <= 4) {
      permissionManager.setUserPermission(targetUserId, level)
      await msg.say(`✅ 已设置用户权限为 ${permissionManager.getPermissionName(level)}`)
    } else {
      await msg.say('⚠️ 权限等级必须在 0-4 之间')
    }
    return
  }

  if (text === '/service') {
    await msg.say(`当前使用: ${aiService.getCurrentService()} 🤖`)
    return
  }

  if (text.startsWith('/switch ')) {
    if (!permissionManager.hasPermission(userId, '/switch')) {
      await msg.say('⚠️ 权限不足')
      return
    }
    const service = text.split(' ')[1]
    try {
      aiService.switchService(service)
      await msg.say(`已切换到 ${service} ✅`)
    } catch (error) {
      await msg.say('切换失败: ' + error.message)
    }
    return
  }
}

// 处理对话
async function handleChat(text, msg, userId) {
  try {
    console.log('正在调用 AI...')
    const reply = await chat(userId, text)
    console.log('AI 回复:', reply)

    // 空回复保护
    if (!reply || !reply.trim()) {
      console.error('✗ AI 返回空回复，使用兜底消息')
      await msg.say('……独角兽刚刚有点走神了的说。')
      return
    }

    // 添加表情包
    const emoji = getRandomEmoji(reply)
    const replyWithEmoji = emoji ? `${reply} ${emoji}` : reply

    // 发送文字回复
    await msg.say(replyWithEmoji)
    console.log('✓ 文字回复已发送')

    // 生成并发送语音回复
    const audioBuffer = await textToSpeech(reply)
    if (audioBuffer) {
      const audioPath = path.join(tempDir, `voice_${Date.now()}.wav`)
      fs.writeFileSync(audioPath, audioBuffer)

      const fileBox = FileBox.fromFile(audioPath)
      await msg.say(fileBox)
      console.log('✓ 语音回复已发送')

      setTimeout(() => {
        if (fs.existsSync(audioPath)) {
          fs.unlinkSync(audioPath)
        }
      }, 5000)
    }

  } catch (error) {
    console.error('处理消息错误:', error)
    await msg.say('抱歉，处理消息时出错了 😢')
  }
}

// 启动机器人
bot.start()
  .then(async () => {
    console.log('🚀 机器人启动成功')
    console.log('💡 提示: 语音功能需要 Flask 服务，请先运行: python app.py')
    console.log('✨ 功能: 语音回复 + 表情包 + 图片识别 + 记忆系统 + 情感系统 + 智能对话启动')
    console.log('🧠 智能对话: 自动检测相关性 + 主动发起对话 + 30秒超时提醒')
  })
  .catch(e => console.error('启动失败:', e))
