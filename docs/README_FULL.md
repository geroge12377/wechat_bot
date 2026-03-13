# 微信 AI 机器人项目

本项目包含两个独立的应用：

## 1. 微信机器人（Node.js）

使用 Wechaty 连接微信，支持多种 AI 模型。

### 启动方式

```bash
npm start
```

### 功能
- 自动回复微信消息
- 支持切换 AI 模型（Gemini/ChatGPT/Claude）
- 对话历史管理
- 命令系统

### 配置文件
- `src/bot.js` - 主程序
- `config/ai-config.js` - AI 配置
- `.env` - 环境变量

---

## 2. 网页版聊天（Python Flask）

带语音功能的网页聊天界面，支持 VITS 语音合成。

### 启动方式

```bash
python app.py
```

然后访问：http://localhost:5000

### 功能
- 网页聊天界面
- VITS 语音合成
- 语音识别
- 语音模型训练
- 对话历史保存

### 配置
在 `app.py` 中修改：
- `API_BASE_URL` - API 地址
- `API_KEY` - API 密钥
- `API_MODEL` - 模型名称

---

## 环境变量配置

创建 `.env` 文件：

```env
# VectorEngine (Gemini) - 两个应用共用
AI_API_KEY=sk-cjeKQXbJvi1cLQ7O7a0L43nvJGZvcJnNvQve8T0urA4FdjrA
AI_BASE_URL=https://api.vectorengine.ai/v1

# OpenAI (可选)
OPENAI_API_KEY=your_key
OPENAI_BASE_URL=https://api.openai.com/v1

# Anthropic (可选)
ANTHROPIC_API_KEY=your_key
ANTHROPIC_BASE_URL=your_url
```

---

## 项目结构

```
CHATBOT_WECHAT/
├── src/                    # Node.js 微信机器人
│   ├── bot.js             # 微信机器人主程序
│   └── ai-service.js      # AI 服务管理
├── config/                 # 配置文件
│   └── ai-config.js       # AI 配置
├── test/                   # 测试文件
├── static/                 # 网页前端
│   └── index.html         # 聊天界面
├── app.py                  # Flask 网页服务器
├── voice_models/           # VITS 语音模型
├── audio_cache/            # 音频缓存
├── .env                    # 环境变量
├── package.json            # Node.js 依赖
├── requirements.txt        # Python 依赖
└── README_FULL.md          # 本文件
```

---

## 安装依赖

### Node.js 依赖
```bash
npm install
```

### Python 依赖
```bash
pip install -r requirements.txt
```

---

## 使用场景

### 场景 1：微信自动回复
启动微信机器人，扫码登录后自动回复好友消息。

```bash
npm start
```

### 场景 2：网页聊天 + 语音
启动 Flask 服务器，在浏览器中聊天，支持语音合成。

```bash
python app.py
```

### 场景 3：同时运行
可以同时运行两个应用，互不干扰。

```bash
# 终端 1
npm start

# 终端 2
python app.py
```

---

## 注意事项

1. **微信机器人**：使用网页版协议，可能遇到登录限制
2. **语音功能**：需要安装 PyTorch 和 VITS 相关依赖
3. **API 额度**：注意 VectorEngine 的使用额度
4. **端口占用**：Flask 默认使用 5000 端口

---

## 常见问题

### Q: 微信无法登录？
A: 网页版微信有限制，建议使用小号测试。

### Q: 语音功能不可用？
A: 检查是否安装了 PyTorch 和 VITS 依赖。

### Q: API 调用失败？
A: 检查 API Key 是否有效，额度是否充足。

---

## License

MIT
