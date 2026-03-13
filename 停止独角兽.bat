@echo off
chcp 65001 >nul
title 停止独角兽服务

echo ========================================
echo    停止独角兽微信机器人
echo ========================================
echo.

echo 正在停止 Flask 服务...
taskkill /FI "WINDOWTITLE eq Flask-独角兽后端*" /F >nul 2>&1
if errorlevel 1 (
    echo [提示] Flask 服务未运行
) else (
    echo [✓] Flask 服务已停止
)

echo.
echo 正在停止微信机器人...
taskkill /FI "WINDOWTITLE eq 微信机器人*" /F >nul 2>&1
if errorlevel 1 (
    echo [提示] 微信机器人未运行
) else (
    echo [✓] 微信机器人已停止
)

echo.
echo ========================================
echo    所有服务已停止
echo ========================================
echo.
pause
