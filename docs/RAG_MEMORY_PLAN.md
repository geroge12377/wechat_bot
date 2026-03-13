# RAG 和记忆系统实现计划

## 📋 功能规划

### 1. 记忆系统（Memory System）

#### 短期记忆（Short-term Memory）
- **对话历史**：保存最近 20 条对话
- **情感状态**：记录当前情感（害羞、兴奋、吃醋等）
- **上下文理解**：理解对话连贯性

#### 长期记忆（Long-term Memory）
- **用户档案**：
  - 用户昵称/称呼偏好
  - 重要日期（生日、纪念日）
  - 兴趣爱好
  - 对话习惯
- **关系进度**：
  - 好感度等级
  - 亲密度分数
  - 重要事件记录
- **个性化记忆**：
  - 用户提到的重要事情
  - 共同经历
  - 特殊约定

#### 情感记忆（Emotional Memory）
- **情感历史**：记录每次对话的情感变化
- **触发事件**：记录让独角兽开心/难过的事
- **情感倾向**：学习用户的情感偏好

### 2. RAG 系统（Retrieval-Augmented Generation）

#### 知识库
- **游戏设定**：
  - 独角兽完整人物设定
  - 碧蓝航线世界观
  - 角色关系网
- **台词库**：
  - 游戏内所有台词
  - 分类：登录、日常、战斗、好感度等
  - 情感标签
- **用户记忆库**：
  - 历史对话摘要
  - 重要事件
  - 个性化信息

#### 检索策略
1. **语义检索**：使用向量数据库（如 Chroma、Pinecone）
2. **关键词检索**：快速匹配特定场景
3. **混合检索**：结合语义和关键词

#### 增强生成
- 检索相关台词和记忆
- 结合当前情感状态
- 生成个性化回复

---

## 🏗️ 技术架构

### 数据库设计

#### 1. 用户记忆表（user_memory）
```sql
CREATE TABLE user_memory (
    id INTEGER PRIMARY KEY,
    user_id TEXT NOT NULL,
    memory_type TEXT,  -- 'profile', 'event', 'preference'
    key TEXT,
    value TEXT,
    importance INTEGER,  -- 1-10
    created_at TIMESTAMP,
    last_accessed TIMESTAMP
);
```

#### 2. 对话历史表（chat_history）
```sql
CREATE TABLE chat_history (
    id INTEGER PRIMARY KEY,
    user_id TEXT NOT NULL,
    user_message TEXT,
    bot_reply TEXT,
    emotion TEXT,
    affection_change INTEGER,
    timestamp TIMESTAMP
);
```

#### 3. 情感记录表（emotion_log）
```sql
CREATE TABLE emotion_log (
    id INTEGER PRIMARY KEY,
    user_id TEXT NOT NULL,
    emotion TEXT,
    trigger_event TEXT,
    intensity INTEGER,  -- 1-10
    timestamp TIMESTAMP
);
```

#### 4. 向量存储（Vector Store）
```javascript
// 使用 Chroma 或类似向量数据库
{
    id: "memory_001",
    text: "哥哥喜欢吃草莓蛋糕",
    embedding: [0.1, 0.2, ...],  // 向量
    metadata: {
        user_id: "user_123",
        type: "preference",
        importance: 8,
        timestamp: "2026-03-11"
    }
}
```

---

## 💻 实现方案

### Phase 1: 基础记忆系统（1-2天）

#### 功能
- ✅ SQLite 数据库存储
- ✅ 用户档案管理
- ✅ 对话历史保存
- ✅ 情感状态追踪

#### 文件结构
```
src/
├── memory/
│   ├── memory-manager.js      # 记忆管理器
│   ├── user-profile.js        # 用户档案
│   ├── emotion-tracker.js     # 情感追踪
│   └── database.js            # 数据库操作
```

### Phase 2: RAG 检索系统（3-4天）

#### 功能
- ✅ 向量数据库集成
- ✅ 台词库向量化
- ✅ 语义检索
- ✅ 记忆检索

#### 依赖
```json
{
  "chromadb": "^1.5.0",           // 向量数据库
  "@xenova/transformers": "^2.0", // 本地嵌入模型
  "langchain": "^0.1.0"           // RAG 框架
}
```

#### 文件结构
```
src/
├── rag/
│   ├── vector-store.js        # 向量存储
│   ├── embeddings.js          # 嵌入生成
│   ├── retriever.js           # 检索器
│   └── knowledge-base.js      # 知识库管理
```

### Phase 3: 智能记忆提取（2-3天）

#### 功能
- ✅ 自动提取重要信息
- ✅ 记忆重要性评分
- ✅ 记忆衰减机制
- ✅ 记忆关联

#### 实现
```javascript
// 使用 AI 提取记忆
async function extractMemory(conversation) {
    const prompt = `
    从以下对话中提取重要信息：
    ${conversation}

    提取格式：
    - 类型：[profile/event/preference]
    - 内容：[具体信息]
    - 重要性：[1-10]
    `;

    const memory = await ai.extract(prompt);
    await saveMemory(memory);
}
```

### Phase 4: 个性化生成（2-3天）

#### 功能
- ✅ 基于记忆的个性化回复
- ✅ 情感连贯性
- ✅ 主动提及记忆
- ✅ 关系进度感知

---

## 🎯 使用示例

### 示例 1：记住用户信息
```
用户：我叫小明，今天是我的生日
独角兽：[兴奋]（眼睛发亮）小明哥哥！生日快乐！✨（抱紧优酱）优酱说要给哥哥唱生日歌...的说！

[系统记录]
- 用户昵称：小明
- 生日：3月11日
- 重要性：10
```

### 示例 2：检索相关记忆
```
用户：我们上次聊到哪了？
独角兽：[普通]（歪头想了想）嗯...上次哥哥说喜欢吃草莓蛋糕...（低头）独角兽记得的...优酱也记得哦...

[系统检索]
- 查询向量数据库
- 找到相关记忆："喜欢草莓蛋糕"
- 结合情感生成回复
```

### 示例 3：情感连贯
```
[上次对话：用户提到要出差]
用户：我回来了
独角兽：[兴奋]（小跑过来）哥哥！终于回来了！（抱住）独角兽和优酱...等了好久好久...的说...（眼眶湿润）

[系统逻辑]
- 检索到"出差"记忆
- 情感状态：思念 → 兴奋
- 生成符合情感的回复
```

---

## 📊 数据流程

```
用户消息
    ↓
[记忆检索]
    ├─ 短期记忆（最近对话）
    ├─ 长期记忆（用户档案）
    └─ 向量检索（相关知识）
    ↓
[情感分析]
    ├─ 当前情感状态
    ├─ 情感变化
    └─ 触发事件
    ↓
[AI 生成]
    ├─ 系统提示词
    ├─ 检索到的记忆
    ├─ 情感状态
    └─ 台词库
    ↓
[记忆更新]
    ├─ 保存对话
    ├─ 提取新记忆
    ├─ 更新情感
    └─ 更新好感度
    ↓
回复用户
```

---

## 🔧 配置选项

### memory-config.js
```javascript
module.exports = {
    // 短期记忆
    shortTerm: {
        maxLength: 20,           // 最多保存 20 条
        ttl: 3600000            // 1小时过期
    },

    // 长期记忆
    longTerm: {
        minImportance: 5,       // 重要性 >= 5 才保存
        maxEntries: 1000,       // 最多 1000 条
        decayRate: 0.95         // 每天衰减 5%
    },

    // RAG 检索
    rag: {
        topK: 3,                // 检索前 3 条
        similarityThreshold: 0.7, // 相似度阈值
        useReranking: true      // 使用重排序
    },

    // 情感系统
    emotion: {
        trackHistory: true,     // 追踪情感历史
        affectionDecay: 0.99,   // 好感度衰减
        maxAffection: 100       // 最大好感度
    }
}
```

---

## 📈 实施时间表

| 阶段 | 功能 | 时间 | 优先级 |
|------|------|------|--------|
| Phase 1 | 基础记忆系统 | 1-2天 | 🔴 高 |
| Phase 2 | RAG 检索 | 3-4天 | 🟡 中 |
| Phase 3 | 智能提取 | 2-3天 | 🟡 中 |
| Phase 4 | 个性化生成 | 2-3天 | 🟢 低 |

**总计：8-12 天**

---

## 🚀 快速开始

### 1. 安装依赖
```bash
npm install chromadb @xenova/transformers langchain sqlite3
```

### 2. 初始化数据库
```bash
node src/memory/init-database.js
```

### 3. 启动机器人
```bash
npm start
```

---

## 📝 待办事项

- [ ] 设计数据库表结构
- [ ] 实现记忆管理器
- [ ] 集成向量数据库
- [ ] 实现 RAG 检索
- [ ] 添加情感追踪
- [ ] 实现记忆提取
- [ ] 测试和优化
- [ ] 编写文档

---

## 🔗 参考资料

- [LangChain 文档](https://js.langchain.com/)
- [ChromaDB 文档](https://docs.trychroma.com/)
- [向量数据库对比](https://github.com/erikbern/ann-benchmarks)
- [记忆系统设计](https://arxiv.org/abs/2304.03442)

---

**更新日期：2026-03-11**
**状态：规划中**
