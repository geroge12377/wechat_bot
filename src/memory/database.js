const sqlite3 = require('sqlite3').verbose()
const path = require('path')

class Database {
  constructor(dbPath = path.join(__dirname, '../../data/memory.db')) {
    this.dbPath = dbPath
    this.db = null
  }

  async init() {
    return new Promise((resolve, reject) => {
      this.db = new sqlite3.Database(this.dbPath, (err) => {
        if (err) {
          reject(err)
        } else {
          console.log('✓ 数据库连接成功')
          this.createTables().then(resolve).catch(reject)
        }
      })
    })
  }

  async createTables() {
    const tables = [
      // 用户记忆表
      `CREATE TABLE IF NOT EXISTS user_memory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        memory_type TEXT NOT NULL,
        key TEXT,
        value TEXT,
        importance INTEGER DEFAULT 5,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      )`,

      // 对话历史表
      `CREATE TABLE IF NOT EXISTS chat_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        user_message TEXT,
        bot_reply TEXT,
        emotion TEXT DEFAULT '普通',
        affection_change INTEGER DEFAULT 0,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      )`,

      // 情感记录表
      `CREATE TABLE IF NOT EXISTS emotion_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        emotion TEXT NOT NULL,
        trigger_event TEXT,
        intensity INTEGER DEFAULT 5,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      )`,

      // 用户档案表
      `CREATE TABLE IF NOT EXISTS user_profile (
        user_id TEXT PRIMARY KEY,
        nickname TEXT,
        affection_level INTEGER DEFAULT 0,
        intimacy_score INTEGER DEFAULT 0,
        first_met TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_interaction TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        total_messages INTEGER DEFAULT 0
      )`
    ]

    for (const sql of tables) {
      await this.run(sql)
    }

    console.log('✓ 数据库表创建完成')
  }

  run(sql, params = []) {
    return new Promise((resolve, reject) => {
      this.db.run(sql, params, function(err) {
        if (err) reject(err)
        else resolve({ id: this.lastID, changes: this.changes })
      })
    })
  }

  get(sql, params = []) {
    return new Promise((resolve, reject) => {
      this.db.get(sql, params, (err, row) => {
        if (err) reject(err)
        else resolve(row)
      })
    })
  }

  all(sql, params = []) {
    return new Promise((resolve, reject) => {
      this.db.all(sql, params, (err, rows) => {
        if (err) reject(err)
        else resolve(rows)
      })
    })
  }

  close() {
    return new Promise((resolve, reject) => {
      this.db.close((err) => {
        if (err) reject(err)
        else resolve()
      })
    })
  }
}

module.exports = new Database()
