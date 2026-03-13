# 记忆系统使用指南

## ✅ Phase 1 已完成：基础记忆系统

### 📦 已实现功能

1. **用户档案管理**
   - 自动创建用户档案
   - 追踪好感度和亲密度
   - 记录互动次数和时间

2. **对话历史**
   - 保存所有对话记录
   - 记录情感状态
   - 追踪好感度变化

3. **情感追踪**
   - 记录情感变化
   - 追踪触发事件
   - 情感强度评分

4. **记忆存储**
   - 分类存储（档案/事件/偏好）
   - 重要性评分
   - 智能检索

## 🚀 使用方法

### 1. 初始化记忆系统

```javascript
const memoryManager = require('./src/memory/memory-manager')

// 初始化数据库
await memoryManager.init()
```

### 2. 保存对话

```javascript
await memoryManager.saveChatHistory(
  userId,
  '我喜欢吃草莓蛋糕',
  '[普通]（眼睛发亮）哥哥喜欢草莓蛋糕呀...独角兽记住了...的说',
  '普通',
  2  // 好感度 +2
)
```

### 3. 保存记忆

```javascript
// 保存用户偏好
await memoryManager.saveMemory(
  userId,
  'preference',  // 类型
  '喜欢的食物',   // 键
  '草莓蛋糕',     // 值
  8              // 重要性 (1-10)
)
```

### 4. 检索记忆

```javascript
// 获取所有记忆
const memories = await memoryManager.getMemory(userId)

// 搜索特定记忆
const results = await memoryManager.searchMemory(userId, '草莓')
```

### 5. 获取对话历史

```javascript
// 获取最近 20 条对话
const history = await memoryManager.getChatHistory(userId, 20)

// 获取上下文（用于 AI）
const context = await memoryManager.getRecentContext(userId, 5)
```

### 6. 情感追踪

```javascript
// 记录情感
await memoryManager.logEmotion(
  userId,
  '害羞',
  '哥哥摸头',
  8  // 强度
)

// 获取当前情感
const emotion = await memoryManager.getCurrentEmotion(userId)
```

### 7. 查看统计

```javascript
const stats = await memoryManager.getStats(userId)
console.log(stats)
// {
//   nickname: '小明',
//   affectionLevel: 45,
//   intimacyScore: 30,
//   totalMessages: 128,
//   memoryCount: 15,
//   ...
// }
```

## 📊 数据库结构

### user_profile（用户档案）
- user_id: 用户ID
- nickname: 昵称
- affection_level: 好感度
- intimacy_score: 亲密度
- total_messages: 消息总数

### user_memory（用户记忆）
- user_id: 用户ID
- memory_type: 类型（profile/event/preference）
- key: 键
- value: 值
- importance: 重要性 (1-10)

### chat_history（对话历史）
- user_id: 用户ID
- user_message: 用户消息
- bot_reply: 机器人回复
- emotion: 情感状态
- affection_change: 好感度变化

### emotion_log（情感记录）
- user_id: 用户ID
- emotion: 情感
- trigger_event: 触发事件
- intensity: 强度 (1-10)

## 🎯 下一步：Phase 2 - RAG 系统

### 计划功能
- ✅ 向量数据库集成
- ✅ 台词库向量化
- ✅ 语义检索
- ✅ 智能记忆提取

### 预计时间
3-4 天

## 📝 示例代码

查看 `src/bot-with-memory.js` 了解完整集成示例。

## 🔧 配置

数据库文件位置：`data/memory.db`

可以在 `src/memory/database.js` 中修改路径。

## 🐛 故障排除

### 问题：数据库文件未创建
**解决**：确保 `data/` 目录存在
```bash
mkdir -p data
```

### 问题：sqlite3 安装失败
**解决**：使用预编译版本
```bash
npm install sqlite3 --build-from-source=false
```

---

**更新日期：2026-03-11**
**状态：Phase 1 完成 ✅**
