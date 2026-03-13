# 独角兽微信机器人 - 启动指南

## 架构说明

```
微信用户
    ↓
Wechaty (Node.js) - 处理微信消息
    ↓
Flask API (Python) - UnicornScheduler
    ↓
DeepSeek API + SoVITS TTS
    ↓
返回文字 + 语音
```

## 前置要求

1. **Python 环境**
   - Python 3.8+
   - 已安装依赖：`pip install -r requirements.txt`

2. **Node.js 环境**
   - Node.js 14+
   - 已安装依赖：`npm install`

3. **SoVITS 服务**
   - 必须运行在 `http://localhost:9872`
   - 启动命令：参考 SoVITS 文档

4. **环境变量配置**
   - 创建 `.env` 文件
   - 配置 `AI_API_KEY` 和 `AI_BASE_URL`

## 启动步骤

### 方式 1：使用启动脚本（推荐）

**Windows:**
```bash
start-bot.bat
```

**Linux/Mac:**
```bash
chmod +x start-bot.sh
./start-bot.sh
```

### 方式 2：手动启动

**步骤 1：启动 SoVITS 服务**
```bash
# 在 SoVITS 目录下
python api.py
```

**步骤 2：启动 Flask 服务**
```bash
# 在项目根目录
python wechat_bot_integrated.py server
```

等待看到：
```
 * Running on http://0.0.0.0:5000
```

**步骤 3：启动微信机器人**
```bash
# 新开一个终端
node src/bot-unicorn.js
```

**步骤 4：扫码登录**
- 终端会显示二维码链接
- 用微信扫码登录
- 登录成功后即可使用

## 使用说明

### 基本对话
直接发送消息给机器人，独角兽会回复文字 + 语音

示例：
```
用户: 哥哥回来啦
独��兽: [害羞]（抱着优酱小跑过来）哥哥！欢迎回来...优酱今天也很乖哦...的说
      + 语音消息
```

### 命令列表

- `/help` - 显示帮助信息
- `/ping` - 测试服务连接状态

## 测试 API

在启动 Flask 服务后，可以测试 API：

```bash
# 健康检查
curl http://localhost:5000/health

# 测试对话
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "你好", "user_id": "test"}'
```

## 故障排查

### 1. Flask 服务启动失败
- 检查端口 5000 是否被占用
- 检查 `.env` 文件是否存在
- 检查 Python 依赖是否安装完整

### 2. SoVITS 连接失败
- 确认 SoVITS 服务运行在 `http://localhost:9872`
- 检查 `unicorn.list` 文件是否存在
- 查看 Flask 日志中的错误信息

### 3. 微信机器人无法登录
- 确认网络连接正常
- 尝试删除 `*.memory-card.json` 文件后重新登录
- 检查 wechaty-puppet-wechat4u 是否正常工作

### 4. 语音发送失败
- 检查音频文件是否生成（`audio_cache/` 目录）
- 确认文件路径正确
- 查看 Node.js 日志中的错误信息

## 日志位置

- **Flask 日志**: 终端输出
- **Bot 日志**: 终端输出
- **音频文件**: `audio_cache/` 目录

## 停止服务

### 使用脚本启动的
- 按 `Ctrl+C` 停止所有服务

### 手动启动的
- 分别在各个终端按 `Ctrl+C`

## 性能优化

1. **消息队列**: Flask 服务已实现消息队列，自动串行处理
2. **音频缓存**: 生成的音频保存在 `audio_cache/` 目录
3. **超时设置**: API 调用超时设为 60 秒（TTS 生成需要时间）

## 注意事项

1. **微信限制**: 网页微信协议可能被限制，建议使用小号测试
2. **消息频率**: 避免频繁发送消息，可能触发微信风控
3. **语音大小**: 微信语音有大小限制，过长的文本可能导致语音过大
4. **API 配额**: 注意 DeepSeek API 的调用配额

## 更新日志

### v2.0.0 (当前版本)
- ✅ 集成 UnicornScheduler
- ✅ 支持《碧蓝航线》独角兽人设
- ✅ 支持情感化语音回复
- ✅ 使用 SoVITS TTS
- ✅ RAG 记忆系统
- ✅ 消息队列处理

## 技术栈

- **微信接入**: Wechaty + wechaty-puppet-wechat4u
- **后端服务**: Flask (Python)
- **AI 模型**: DeepSeek API
- **语音合成**: SoVITS
- **向量数据库**: ChromaDB
- **消息队列**: asyncio.Queue
