# 微信 AI 机器人 v2.0

支持多种 AI 模型的微信聊天机器人

## 功能特性

- ✅ 支持多种 AI 服务（Gemini、ChatGPT、Claude）
- ✅ 动态切换 AI 模型
- ✅ 对话上下文管理
- ✅ 命令系统
- ✅ 模块化架构

## 快速开始

### 1. 安装依赖

```bash
npm install
```

### 2. 配置环境变量

创建 `.env` 文件：

```env
# VectorEngine (Gemini)
AI_API_KEY=your_api_key_here
AI_BASE_URL=https://api.vectorengine.ai/v1

# OpenAI (可选)
OPENAI_API_KEY=your_openai_key
OPENAI_BASE_URL=https://api.openai.com/v1

# Anthropic (可选)
ANTHROPIC_API_KEY=your_anthropic_key
ANTHROPIC_BASE_URL=your_base_url
```

### 3. 运行机器人

```bash
npm start
```

## 可用命令

- `/clear` - 清除对话历史
- `/help` - 显示帮助信息
- `/service` - 查看当前使用的 AI 服务
- `/switch <gemini|chatgpt|claude>` - 切换 AI 服务

## 项目结构

```
CHATBOT_WECHAT/
├── src/
│   ├── bot.js           # 主程序
│   └── ai-service.js    # AI 服务管理
├── config/
│   └── ai-config.js     # 配置文件
├── test/
│   └── test-api.js      # API 测试
├── .env                 # 环境变量
├── package.json
└── README.md
```

## 配置说明

在 `config/ai-config.js` 中可以配置：

- `currentService`: 默认使用的 AI 服务
- 各服务的模型参数
- 系统提示词
- 对话历史长度

## 注意事项

- wechat4u 使用微信网页版协议，可能会遇到登录限制
- 建议使用 VectorEngine 中转服务，无需代理
- 确保 API Key 有足够的额度

## 开发

### 测试 API

```bash
npm test
```

### 添加新的 AI 服务

1. 在 `config/ai-config.js` 添加配置
2. 在 `src/ai-service.js` 实现接口
3. 更新环境变量

## License

MIT
