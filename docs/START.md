# 微信 AI 机器人 - 快速启动

## 🚀 快速开始

### 1. 启动 Flask 服务（语音功能）

```bash
python app.py
```

访问：http://localhost:5000

### 2. 启动微信机器人

```bash
npm start
```

扫码登录微信即可。

---

## ✨ 功能特性

### 微信机器人功能
- ✅ **AI 对话** - 支持 Gemini/ChatGPT/Claude
- ✅ **语音回复** - TTS 语音合成（需要 Flask 服务）
- ✅ **智能表情** - 根据回复内容自动添加表情
- ✅ **图片识别** - 发送图片自动识别内容
- ✅ **对话记忆** - 保持上下文对话
- ✅ **模型切换** - 随时切换 AI 模型

### 网页版功能
- ✅ **网页聊天** - 浏览器访问
- ✅ **VITS 语音** - 高质量语音合成
- ✅ **语音识别** - 支持语音输入
- ✅ **模型训练** - 自定义语音模型

---

## 📝 使用命令

在微信中发送：

- `/help` - 查看帮助
- `/clear` - 清除对话历史
- `/service` - 查看当前 AI 服务
- `/switch gemini` - 切换到 Gemini
- `/switch chatgpt` - 切换到 ChatGPT
- `/switch claude` - 切换到 Claude

**发送图片** - 自动识别图片内容

---

## ⚙️ 配置

### 环境变量（.env）

```env
# VectorEngine (Gemini)
AI_API_KEY=sk-cjeKQXbJvi1cLQ7O7a0L43nvJGZvcJnNvQve8T0urA4FdjrA
AI_BASE_URL=https://api.vectorengine.ai/v1

# OpenAI (可选)
OPENAI_API_KEY=your_key
OPENAI_BASE_URL=https://api.openai.com/v1

# Anthropic (可选)
ANTHROPIC_API_KEY=your_key
ANTHROPIC_BASE_URL=your_url
```

### AI 配置（config/ai-config.js）

```javascript
module.exports = {
  currentService: 'gemini',  // 默认使用 Gemini

  gemini: {
    model: 'gemini-3.1-flash-lite-preview',
    maxTokens: 1000
  },

  bot: {
    systemPrompt: '你是一个友好的AI助手。',
    maxHistoryLength: 20
  }
}
```

---

## 📦 启动模式

### 完整功能版（推荐）
```bash
npm start
```
包含：AI对话 + 语音 + 表情 + 图片识别

### 纯文字版
```bash
npm run simple
```
仅包含：AI对话

### 语音版
```bash
npm run voice
```
包含：AI对话 + 语音回复

---

## 🔧 故障排除

### 问题 1：语音功能不可用
**解决**：确保 Flask 服务已启动
```bash
python app.py
```

### 问题 2：微信无法登录
**解决**：网页版微信有限制，建议：
- 使用小号测试
- 或使用其他 Puppet（如 PuppetPadlocal）

### 问题 3：图片识别失败
**解决**：检查 API 是否支持 Vision 功能

### 问题 4：API 调用失败
**解决**：
- 检查 API Key 是否有效
- 检查额度是否充足
- 查看 .env 配置是否正确

---

## 📁 项目结构

```
CHATBOT_WECHAT/
├── src/
│   ├── bot.js           # 纯文字版
│   ├── bot-voice.js     # 语音版
│   ├── bot-full.js      # 完整功能版 ⭐
│   └── ai-service.js    # AI 服务管理
├── config/
│   └── ai-config.js     # AI 配置
├── static/
│   └── index.html       # 网页前端
├── temp/                # 临时文件
├── emojis/              # 表情包
├── app.py               # Flask 服务器
├── .env                 # 环境变量
├── package.json         # Node.js 依赖
└── requirements.txt     # Python 依赖
```

---

## 🎯 下一步

1. ✅ 测试微信机器人
2. ✅ 测试语音功能
3. ✅ 测试图片识别
4. ⏳ 添加更多表情包
5. ⏳ 训练自定义语音模型
6. ⏳ 部署到服务器

---

## 📞 支持

遇到问题？
- 查看日志输出
- 检查配置文件
- 确保依赖已安装

---

## 📄 License

MIT
