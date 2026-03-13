@echo off
REM 独角兽微信机器人启动脚本 (Windows)

echo ==========================================
echo   独角兽微信机器人 - 启动脚本
echo ==========================================
echo.

REM 检查 Python
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ❌ 错误: 未找到 Python
    pause
    exit /b 1
)

REM 检查 Node.js
where node >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ❌ 错误: 未找到 Node.js
    pause
    exit /b 1
)

REM 检查 .env 文件
if not exist .env (
    echo ❌ 错误: 未找到 .env 文件
    echo 请创建 .env 文件并配置 API 密钥
    pause
    exit /b 1
)

echo ✓ 环境检查通过
echo.

REM 启动 Flask 服务
echo 1️⃣  启动 Flask 服务 (端口 5000)...
start "Flask-Unicorn" python wechat_bot_integrated.py server

REM 等待 Flask 启动
echo    等待 Flask 服务启动...
timeout /t 5 /nobreak >nul

REM 检查 Flask 是否启动成功
curl -s http://localhost:5000/health >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo    ✓ Flask 服务启动成功
) else (
    echo    ❌ Flask 服务启动失败
    pause
    exit /b 1
)

echo.

REM 启动 Wechaty Bot
echo 2️⃣  启动微信机器人...
start "Wechaty-Bot" node src/bot-unicorn.js

echo.
echo ==========================================
echo   启动完成！
echo ==========================================
echo.
echo Flask 服务: http://localhost:5000
echo.
echo 两个窗口已打开：
echo   - Flask-Unicorn (Python 服务)
echo   - Wechaty-Bot (微信机器人)
echo.
echo 关闭窗口即可停止服务
echo.
pause
