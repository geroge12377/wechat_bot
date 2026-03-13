const db = require('./database')

class MemoryManager {
  constructor() {
    this.initialized = false
  }

  async init() {
    if (!this.initialized) {
      await db.init()
      this.initialized = true
    }
  }

  // ==================== 用户档案管理 ====================

  async getUserProfile(userId) {
    let profile = await db.get(
      'SELECT * FROM user_profile WHERE user_id = ?',
      [userId]
    )

    if (!profile) {
      // 创建新用户档案
      await db.run(
        'INSERT INTO user_profile (user_id) VALUES (?)',
        [userId]
      )
      profile = await db.get(
        'SELECT * FROM user_profile WHERE user_id = ?',
        [userId]
      )
    }

    return profile
  }

  async updateUserProfile(userId, updates) {
    const fields = Object.keys(updates).map(k => `${k} = ?`).join(', ')
    const values = [...Object.values(updates), userId]

    await db.run(
      `UPDATE user_profile SET ${fields}, last_interaction = CURRENT_TIMESTAMP WHERE user_id = ?`,
      values
    )
  }

  async incrementMessageCount(userId) {
    await db.run(
      'UPDATE user_profile SET total_messages = total_messages + 1 WHERE user_id = ?',
      [userId]
    )
  }

  // ==================== 记忆管理 ====================

  async saveMemory(userId, type, key, value, importance = 5) {
    await db.run(
      `INSERT INTO user_memory (user_id, memory_type, key, value, importance)
       VALUES (?, ?, ?, ?, ?)`,
      [userId, type, key, value, importance]
    )
  }

  async getMemory(userId, type = null, limit = 10) {
    let sql = 'SELECT * FROM user_memory WHERE user_id = ?'
    const params = [userId]

    if (type) {
      sql += ' AND memory_type = ?'
      params.push(type)
    }

    sql += ' ORDER BY importance DESC, last_accessed DESC LIMIT ?'
    params.push(limit)

    return await db.all(sql, params)
  }

  async searchMemory(userId, keyword) {
    return await db.all(
      `SELECT * FROM user_memory
       WHERE user_id = ? AND (key LIKE ? OR value LIKE ?)
       ORDER BY importance DESC LIMIT 5`,
      [userId, `%${keyword}%`, `%${keyword}%`]
    )
  }

  async updateMemoryAccess(memoryId) {
    await db.run(
      'UPDATE user_memory SET last_accessed = CURRENT_TIMESTAMP WHERE id = ?',
      [memoryId]
    )
  }

  // ==================== 对话历史 ====================

  async saveChatHistory(userId, userMessage, botReply, emotion = '普通', affectionChange = 0) {
    await db.run(
      `INSERT INTO chat_history (user_id, user_message, bot_reply, emotion, affection_change)
       VALUES (?, ?, ?, ?, ?)`,
      [userId, userMessage, botReply, emotion, affectionChange]
    )

    // 更新用户档案
    await this.incrementMessageCount(userId)

    if (affectionChange !== 0) {
      await db.run(
        'UPDATE user_profile SET affection_level = affection_level + ? WHERE user_id = ?',
        [affectionChange, userId]
      )
    }
  }

  async getChatHistory(userId, limit = 20) {
    return await db.all(
      `SELECT * FROM chat_history
       WHERE user_id = ?
       ORDER BY timestamp DESC
       LIMIT ?`,
      [userId, limit]
    )
  }

  async getRecentContext(userId, limit = 5) {
    const history = await this.getChatHistory(userId, limit)
    return history.reverse().map(h => ({
      role: 'user',
      content: h.user_message
    })).concat(history.reverse().map(h => ({
      role: 'assistant',
      content: h.bot_reply
    })))
  }

  // ==================== 情感追踪 ====================

  async logEmotion(userId, emotion, triggerEvent = null, intensity = 5) {
    await db.run(
      `INSERT INTO emotion_log (user_id, emotion, trigger_event, intensity)
       VALUES (?, ?, ?, ?)`,
      [userId, emotion, triggerEvent, intensity]
    )
  }

  async getEmotionHistory(userId, limit = 10) {
    return await db.all(
      `SELECT * FROM emotion_log
       WHERE user_id = ?
       ORDER BY timestamp DESC
       LIMIT ?`,
      [userId, limit]
    )
  }

  async getCurrentEmotion(userId) {
    const recent = await db.get(
      `SELECT emotion FROM emotion_log
       WHERE user_id = ?
       ORDER BY timestamp DESC
       LIMIT 1`,
      [userId]
    )
    return recent ? recent.emotion : '普通'
  }

  // ==================== 统计信息 ====================

  async getStats(userId) {
    const profile = await this.getUserProfile(userId)
    const memoryCount = await db.get(
      'SELECT COUNT(*) as count FROM user_memory WHERE user_id = ?',
      [userId]
    )
    const chatCount = await db.get(
      'SELECT COUNT(*) as count FROM chat_history WHERE user_id = ?',
      [userId]
    )

    return {
      nickname: profile.nickname || '哥哥',
      affectionLevel: profile.affection_level,
      intimacyScore: profile.intimacy_score,
      totalMessages: profile.total_messages,
      memoryCount: memoryCount.count,
      chatHistoryCount: chatCount.count,
      firstMet: profile.first_met,
      lastInteraction: profile.last_interaction
    }
  }
}

module.exports = new MemoryManager()
