@echo off
echo 🚀 启动so-vits-svc训练
echo ============================

cd /d "C:\Users\HP\Desktop\CHATBOT_WECHAT\so-vits-svc-4.1-Stable\44k"

echo 📁 当前目录: %CD%
echo 📁 检查点目录: C:\Users\HP\Desktop\CHATBOT_WECHAT\so-vits-svc-4.1-Stable\logs\44k

echo 🔍 验证检查点文件...
if exist "C:\Users\HP\Desktop\CHATBOT_WECHAT\so-vits-svc-4.1-Stable\logs\44k\G_25.pth" (
    echo ✅ G_25.pth 存在
) else (
    echo ❌ G_25.pth 不存在
    pause
    exit /b 1
)

if exist "C:\Users\HP\Desktop\CHATBOT_WECHAT\so-vits-svc-4.1-Stable\logs\44k\D_25.pth" (
    echo ✅ D_25.pth 存在
) else (
    echo ❌ D_25.pth 不存在
    pause
    exit /b 1
)

echo.
echo 🚀 启动训练...
python ../train.py -c config.json -m "C:\Users\HP\Desktop\CHATBOT_WECHAT\so-vits-svc-4.1-Stable\logs\44k"

pause
