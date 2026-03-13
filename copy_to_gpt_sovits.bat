@echo off
chcp 65001 >nul
echo ========================================
echo 复制 unicorn.list 到 GPT-SoVITS
echo ========================================
echo.

set SOURCE="%~dp0python_scripts\unicorn_gpt_sovits_fixed.list"
set TARGET="D:\GPT_SoVITS\output\asr_opt\unicorn.list"

echo 源文件: %SOURCE%
echo 目标文件: %TARGET%
echo.

if not exist %SOURCE% (
    echo [错误] 源文件不存在！
    pause
    exit /b 1
)

echo 正在复制...
copy /Y %SOURCE% %TARGET%

if %ERRORLEVEL% EQU 0 (
    echo.
    echo [成功] 文件已复制！
    echo.
    echo 验证文件:
    dir %TARGET%
) else (
    echo.
    echo [失败] 复制失败，可能原因:
    echo 1. 文件被其他程序占用
    echo 2. 需要管理员权限
    echo.
    echo 请尝试:
    echo 1. 关闭占用文件的程序（如文本编辑器、GPT-SoVITS程序）
    echo 2. 右键此批处理文件，选择"以管理员身份运行"
)

echo.
pause
