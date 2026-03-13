# 项目结构说明

## 📁 核心文件

### 微信机器人（Node.js）
```
src/
├── bot.js           # 纯文字版
├── bot-voice.js     # 语音版
├── bot-full.js      # 完整功能版 ⭐ (默认)
└── ai-service.js    # AI 服务管理

config/
└── ai-config.js     # AI 配置

.env                 # 环境变量配置
package.json         # Node.js 依赖
```

### 网页版（Python Flask）
```
app.py               # Flask 主程序 ⭐
app_simple.py        # 简化版

static/              # 网页前端
├── index.html       # 聊天界面
└── *.jpg           # 图片资源

voice_models/        # VITS 语音模型
audio_cache/         # 音频缓存
uploads/             # 上传文件

requirements.txt     # Python 依赖
```

## 📂 辅助目录

### 开发相关
```
test/                # 测试文件
├── test-api.js
├── test-claude.js
├── test-gemini.js
└── test-vectorengine.js

python_scripts/      # Python 工具脚本
├── vits_trainer.py
├── voice_trainer.py
├── sovits_voice_manager.py
└── ...其他训练脚本

temp/                # 临时文件（自动生成）
emojis/              # 表情包资源
logs/                # 日志文件
```

### 语音训练相关
```
vits/                # VITS 模型代码
vits_configs/        # VITS 配置文件
vits_checkpoints/    # 训练检查点
vits_training_data/  # 训练数据
so-vits-svc-4.1-Stable/  # So-VITS-SVC 模型
```

### 文档和旧文件
```
docs/                # 文档
├── 1.pdf
├── 2.pdf
├── README.md
├── README_FULL.md
├── START.md         # 快速启动指南 ⭐
└── training_guide.md

old_files/           # 旧文件备份
├── bot.js           # 旧版机器人
├── output.txt
└── python-3.9-installer.exe
```

### 数据库
```
unicorn_data.db      # SQLite 数据库
wechat-bot.memory-card.json  # 微信登录缓存
```

## 🚀 快速启动

### 1. 启动微信机器人
```bash
npm start
```

### 2. 启动网页版
```bash
python app.py
```

## 📝 重要文件说明

| 文件 | 用途 | 必需 |
|------|------|------|
| `.env` | 环境变量（API Key） | ✅ |
| `package.json` | Node.js 依赖配置 | ✅ |
| `requirements.txt` | Python 依赖配置 | ✅ |
| `src/bot-full.js` | 微信机器人主程序 | ✅ |
| `app.py` | Flask 服务器 | ✅ |
| `config/ai-config.js` | AI 配置 | ✅ |
| `docs/START.md` | 使用指南 | 📖 |

## 🗑️ 可以删除的文件

- `__pycache__/` - Python 缓存（可重新生成）
- `old_files/` - 旧文件备份
- `temp/` - 临时文件
- `logs/` - 日志文件（可清空）

## 📦 依赖安装

### Node.js
```bash
npm install
```

### Python
```bash
pip install -r requirements.txt
```

## 🎯 下一步

1. 查看 `docs/START.md` 了解详细使用方法
2. 配置 `.env` 文件
3. 启动服务测试功能
