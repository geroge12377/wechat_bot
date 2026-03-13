@echo off
chcp 65001 >nul
title 独角兽服务状态检查

echo ========================================
echo    独角兽服务状态检查
echo ========================================
echo.

:: 检查 Python
echo [Python]
python --version 2>nul
if errorlevel 1 (
    echo   状态: ❌ 未安装
) else (
    echo   状态: ✅ 已安装
)
echo.

:: 检查 Node.js
echo [Node.js]
node --version 2>nul
if errorlevel 1 (
    echo   状态: ❌ 未安装
) else (
    echo   状态: ✅ 已安装
)
echo.

:: 检查 Flask 服务
echo [Flask 服务]
curl -s http://localhost:5000/health >nul 2>&1
if errorlevel 1 (
    echo   状态: ❌ 未运行
) else (
    echo   状态: ✅ 运行中
    echo   地址: http://localhost:5000
)
echo.

:: 检查依赖
echo [Python 依赖]
python -c "import pilk" 2>nul
if errorlevel 1 (
    echo   pilk: ❌ 未安装 (运行: pip install pilk)
) else (
    echo   pilk: ✅ 已安装
)

python -c "import flask" 2>nul
if errorlevel 1 (
    echo   flask: ❌ 未安装 (运行: pip install -r requirements.txt)
) else (
    echo   flask: ✅ 已安装
)
echo.

:: 检查关键文件
echo [关键文件]
if exist "wechat_bot_integrated.py" (
    echo   wechat_bot_integrated.py: ✅
) else (
    echo   wechat_bot_integrated.py: ❌
)

if exist "src\bot-unicorn.js" (
    echo   src\bot-unicorn.js: ✅
) else (
    echo   src\bot-unicorn.js: ❌
)

if exist "unicorn_scheduler.py" (
    echo   unicorn_scheduler.py: ✅
) else (
    echo   unicorn_scheduler.py: ❌
)
echo.

echo ========================================
echo    检查完成
echo ========================================
echo.
pause
