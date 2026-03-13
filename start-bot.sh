#!/bin/bash
# 独角兽微信机器人启动脚本

echo "=========================================="
echo "  独角兽微信机器人 - 启动脚本"
echo "=========================================="
echo ""

# 检查 Python 环境
if ! command -v python &> /dev/null; then
    echo "❌ 错误: 未找到 Python"
    exit 1
fi

# 检查 Node.js 环境
if ! command -v node &> /dev/null; then
    echo "❌ 错误: 未找到 Node.js"
    exit 1
fi

# 检查 .env 文件
if [ ! -f .env ]; then
    echo "❌ 错误: 未找到 .env 文件"
    echo "请创建 .env 文件并配置 API 密钥"
    exit 1
fi

echo "✓ 环境检查通过"
echo ""

# 启动 Flask 服务
echo "1️⃣  启动 Flask 服务 (端口 5000)..."
python wechat_bot_integrated.py server &
FLASK_PID=$!
echo "   Flask PID: $FLASK_PID"

# 等待 Flask 启动
echo "   等待 Flask 服务启动..."
sleep 5

# 检查 Flask 是否启动成功
if curl -s http://localhost:5000/health > /dev/null; then
    echo "   ✓ Flask 服务启动成功"
else
    echo "   ❌ Flask 服务启动失败"
    kill $FLASK_PID 2>/dev/null
    exit 1
fi

echo ""

# 启动 Wechaty Bot
echo "2️⃣  启动微信机器人..."
node src/bot-unicorn.js &
BOT_PID=$!
echo "   Bot PID: $BOT_PID"

echo ""
echo "=========================================="
echo "  启动完成！"
echo "=========================================="
echo ""
echo "Flask 服务: http://localhost:5000"
echo "Flask PID: $FLASK_PID"
echo "Bot PID: $BOT_PID"
echo ""
echo "按 Ctrl+C 停止所有服务"
echo ""

# 等待用户中断
trap "echo ''; echo '正在停止服务...'; kill $FLASK_PID $BOT_PID 2>/dev/null; echo '已停止'; exit 0" INT

# 保持脚本运行
wait
