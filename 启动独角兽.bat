@echo off
chcp 65001 >nul
title 独角兽微信机器人 - 一键启动

echo ========================================
echo    独角兽微信机器人 - 一键启动
echo ========================================
echo.

:: 检查 Python
echo [1/4] 检查 Python 环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.8+
    pause
    exit /b 1
)
echo [✓] Python 已安装
echo.

:: 检查 Node.js
echo [2/4] 检查 Node.js 环境...
node --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Node.js，请先安装 Node.js
    pause
    exit /b 1
)
echo [✓] Node.js 已安装
echo.

:: 启动 Flask 服务
echo [3/4] 启动 Flask 服务...
start "Flask-独角兽后端" cmd /k "python wechat_bot_integrated.py server"
echo [✓] Flask 服务已启动
timeout /t 3 /nobreak >nul
echo.

:: 启动微信机器人
echo [4/4] 启动微信机器人...
start "微信机器人" cmd /k "cd src && node bot-unicorn.js"
echo [✓] 微信机器人已启动
echo.

echo ========================================
echo    启动完成！
echo ========================================
echo.
echo 两个窗口已打开：
echo   1. Flask 后端服务 (端口 5000)
echo   2. 微信机器人客户端
echo.
echo 请在微信机器人窗口扫码登录
echo.
echo 关闭此窗口不会影响服务运行
echo 如需停止服务，请关闭对应的窗口
echo.
pause
