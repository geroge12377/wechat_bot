@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo RVC 整合包解压工具
echo ========================================
echo.

:: 设置路径
set "DOWNLOAD_DIR=%USERPROFILE%\Desktop\RVC_Download"
set "EXTRACT_DIR=%USERPROFILE%\Desktop\RVC"

echo 下载目录: %DOWNLOAD_DIR%
echo 解压目录: %EXTRACT_DIR%
echo.

:: 检查下载目录
if not exist "%DOWNLOAD_DIR%" (
    echo [错误] 下载目录不存在: %DOWNLOAD_DIR%
    echo 请先运行 download_rvc.bat 下载文件
    pause
    exit /b 1
)

:: 查找 .7z 文件
echo 正在查找 .7z 文件...
set "FOUND_FILE="
for %%f in ("%DOWNLOAD_DIR%\*.7z") do (
    set "FOUND_FILE=%%f"
    echo 找到文件: %%~nxf
)

if not defined FOUND_FILE (
    echo.
    echo [错误] 未找到 .7z 文件
    echo 请确保已下载 RVC 整合包到: %DOWNLOAD_DIR%
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo 准备解压
echo ========================================
echo 源文件: %FOUND_FILE%
echo 目标目录: %EXTRACT_DIR%
echo.

:: 创建解压目录
if not exist "%EXTRACT_DIR%" mkdir "%EXTRACT_DIR%"

:: 检查 7-Zip
set "SEVENZIP="
if exist "C:\Program Files\7-Zip\7z.exe" set "SEVENZIP=C:\Program Files\7-Zip\7z.exe"
if exist "C:\Program Files (x86)\7-Zip\7z.exe" set "SEVENZIP=C:\Program Files (x86)\7-Zip\7z.exe"

if defined SEVENZIP (
    echo 使用 7-Zip 解压...
    echo.
    "%SEVENZIP%" x "%FOUND_FILE%" -o"%EXTRACT_DIR%" -y

    if !errorlevel! equ 0 (
        echo.
        echo ========================================
        echo 解压完成！
        echo ========================================
        echo.
        echo 文件位置: %EXTRACT_DIR%
        echo.
        echo 下一步:
        echo 1. 打开文件夹: %EXTRACT_DIR%
        echo 2. 找到并运行 go-web.bat
        echo 3. 等待浏览器自动打开
        echo.
        set /p "OPEN_FOLDER=是否打开文件夹? (y/n): "
        if /i "!OPEN_FOLDER!"=="y" explorer "%EXTRACT_DIR%"
    ) else (
        echo.
        echo [错误] 解压失败
        pause
        exit /b 1
    )
) else (
    echo [错误] 未找到 7-Zip
    echo.
    echo 请安装 7-Zip:
    echo 1. 访问: https://www.7-zip.org/
    echo 2. 下载并安装 7-Zip
    echo 3. 重新运行此脚本
    echo.
    echo 或者手动解压:
    echo 1. 右键点击: %FOUND_FILE%
    echo 2. 选择"解压到..."
    echo 3. 选择目标目录: %EXTRACT_DIR%
    echo.
    set /p "OPEN_7ZIP_SITE=是否打开 7-Zip 下载页面? (y/n): "
    if /i "!OPEN_7ZIP_SITE!"=="y" start https://www.7-zip.org/
)

echo.
pause
