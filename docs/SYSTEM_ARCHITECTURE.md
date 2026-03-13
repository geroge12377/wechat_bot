# 系统架构说明

## 📋 已实现功能

### 1. 心情/情感系统 ✅
**文件**: `src/memory/emotion-manager.js`

**功能**：
- 7种情感状态：普通、开心、兴奋、害羞、低落、吃醋、温和
- 自动分析用户消息触发情感
- 计算好感度和亲密度变化
- 情感强度评分（1-10）

**使用**：
```javascript
const emotionManager = require('./memory/emotion-manager')

// 分析情感
const { emotion, intensity } = emotionManager.analyzeEmotion('我喜欢你', 70)

// 计算关系变化
const { affectionChange, intimacyChange } =
  emotionManager.calculateRelationshipChange('抱抱')
```

---

### 2. 时间感知系统 ✅
**文件**: `src/memory/time-manager.js`

**功能**：
- 获取当前时间、日期、星期
- 判断时间段（清晨/上午/中午/下午/傍晚/晚上/深夜）
- 生成时间问候语
- 追踪距离上次聊天的时间
- 自动判断是否需要问候

**使用**：
```javascript
const timeManager = require('./memory/time-manager')

// 获取时间信息
const timeInfo = timeManager.getCurrentTimeInfo()
// { time: '14:30', period: '下午', greeting: '下午好' }

// 记录互动
timeManager.recordInteraction(userId)

// 获取距离上次聊天时间
const timeSince = timeManager.getTimeSinceLastInteraction(userId)
// { hours: 3, minutes: 25, text: '3小时25分钟' }

// 生成时间上下文
const context = timeManager.generateTimeContext(userId)
```

---

### 3. 技能库系统 ✅
**文件**: `src/skills/permission-manager.js`

**功能**：
- 5级权限：访客(0)、用户(1)、VIP(2)、管理员(3)、所有者(4)
- 分层命令系统
- 权限检查
- 动态命令列表

**权限层级**：
```
访客 (0)    - /help, /clear, /service
用户 (1)    - /stats, /mood, /memory
VIP (2)     - /switch, /voice
管理员 (3)  - /adduser, /removeuser, /whitelist, /broadcast
所有者 (4)  - /reset, /export, /setperm
```

**使用**：
```javascript
const { PermissionManager, PERMISSION_LEVELS } =
  require('./skills/permission-manager')

const pm = new PermissionManager()

// 设置权限
pm.setUserPermission('user123', PERMISSION_LEVELS.VIP)

// 检查权限
if (pm.hasPermission('user123', '/switch')) {
  // 执行命令
}

// 获取可用命令
const commands = pm.getAvailableCommands('user123')
```

---

### 4. 多层 AI 系统 ✅
**文件**: `src/ai-multi-layer.js`
**配置**: `config/ai-layers.js`

**分层策略**：
- **主对话** → Claude（角色扮演能力强）
- **RAG检索** → GPT（快速便宜）
- **记忆提取** → GPT（结构化任务）
- **情感分析** → Gemini（快速便宜）
- **图片识别** → Gemini Vision

**使用**：
```javascript
const multiAI = require('./ai-multi-layer')

// 主对话（Claude）
const reply = await multiAI.chat(messages, systemPrompt)

// RAG 检索（GPT）
const answer = await multiAI.ragQuery('问题', '上下文')

// 记忆提取（GPT）
const memory = await multiAI.extractMemory('对话内容')

// 情感分析（Gemini）
const emotion = await multiAI.analyzeEmotion('消息')

// 图片识别（Gemini）
const description = await multiAI.recognizeImage(base64Image)
```

---

## 🏗️ 系统架构

```
┌─────────────────────────────────────┐
│         用户消息                      │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│      白名单 & 关键词检查              │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│         权限检查                      │
│    (PermissionManager)               │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│       时间感知                        │
│    (TimeManager)                     │
│  - 记录互动时间                       │
│  - 生成时间上下文                     │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│       情感分析                        │
│    (EmotionManager)                  │
│  - 分析情感状态                       │
│  - 计算关系变化                       │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│       记忆检索                        │
│    (MemoryManager)                   │
│  - 获取用户档案                       │
│  - 检索相关记忆                       │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│       AI 生成回复                     │
│    (MultiLayerAI)                    │
│  - 主对话: Claude                     │
│  - RAG: GPT                          │
│  - 情感: Gemini                       │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│       保存记录                        │
│  - 对话历史                           │
│  - 情感记录                           │
│  - 更新好感度                         │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│       发送回复                        │
│  - 文字 + 表情                        │
│  - 语音（可选）                       │
└─────────────────────────────────────┘
```

---

## 📊 数据库结构

### user_profile（用户档案）
- user_id: 用户ID
- nickname: 昵称
- affection_level: 好感度 (0-100)
- intimacy_score: 亲密度 (0-100)
- permission_level: 权限等级 (0-4)
- total_messages: 消息总数
- first_met: 首次见面时间
- last_interaction: 最后互动时间

### user_memory（记忆）
- user_id: 用户ID
- memory_type: 类型（profile/event/preference）
- key: 键
- value: 值
- importance: 重要性 (1-10)
- created_at: 创建时间
- last_accessed: 最后访问时间

### chat_history（对话历史）
- user_id: 用户ID
- user_message: 用户消息
- bot_reply: 机器人回复
- emotion: 情感状态
- affection_change: 好感度变化
- timestamp: 时间戳

### emotion_log（情感记录）
- user_id: 用户ID
- emotion: 情感
- trigger_event: 触发事件
- intensity: 强度 (1-10)
- timestamp: 时间戳

---

## 🔧 配置文件

### config/ai-layers.js
```javascript
{
  chat: { service: 'claude', ... },      // 主对话
  rag: { service: 'chatgpt', ... },      // RAG检索
  memoryExtraction: { service: 'chatgpt', ... },
  emotionAnalysis: { service: 'gemini', ... },
  vision: { service: 'gemini', ... }
}
```

### config/whitelist.js
```javascript
{
  enabled: false,
  keywordMode: {
    enabled: true,
    keywords: ['独角兽', '妹妹', '@独角兽']
  }
}
```

### config/ai-config.js
```javascript
{
  bot: {
    systemPrompt: '...',  // 独角兽人设
    maxHistoryLength: 20
  }
}
```

---

## 🚀 使用流程

### 1. 初始化
```javascript
const memoryManager = require('./memory/memory-manager')
const emotionManager = require('./memory/emotion-manager')
const timeManager = require('./memory/time-manager')
const { PermissionManager } = require('./skills/permission-manager')
const multiAI = require('./ai-multi-layer')

await memoryManager.init()
await emotionManager.init()
```

### 2. 处理消息
```javascript
// 1. 权限检查
if (!pm.hasPermission(userId, command)) {
  return '权限不足'
}

// 2. 时间感知
timeManager.recordInteraction(userId)
const timeContext = timeManager.generateTimeContext(userId)

// 3. 情感分析
const profile = await memoryManager.getUserProfile(userId)
const { emotion, intensity } = emotionManager.analyzeEmotion(
  message,
  profile.affection_level
)

// 4. 记忆检索
const memories = await memoryManager.getMemory(userId, null, 5)

// 5. AI 生成
const reply = await multiAI.chat(messages, systemPrompt)

// 6. 保存记录
await memoryManager.saveChatHistory(
  userId, message, reply, emotion, affectionChange
)
```

---

## 📝 下一步

- [ ] 整合所有系统到 bot-full.js
- [ ] 测试多层 AI
- [ ] 实现 RAG 检索
- [ ] 添加更多技能
- [ ] 优化提示词

---

**更新日期：2026-03-11**
**状态：架构完成，待整合**
