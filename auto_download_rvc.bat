@echo off
echo 启动 RVC 自动下载工具...
echo.
powershell -ExecutionPolicy Bypass -File "%~dp0download_rvc.ps1"
pause
