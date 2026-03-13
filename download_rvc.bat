@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo RVC 整合包下载工具
echo ========================================
echo.

:: 设置下载目录
set "DOWNLOAD_DIR=%USERPROFILE%\Desktop\RVC_Download"
if not exist "%DOWNLOAD_DIR%" mkdir "%DOWNLOAD_DIR%"

echo 下载目录: %DOWNLOAD_DIR%
echo.

:: RVC 项目地址
set "REPO_URL=https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI"
set "RELEASES_URL=%REPO_URL%/releases"

echo ========================================
echo 方式 1: 手动下载（推荐）
echo ========================================
echo.
echo 1. 即将打开 RVC Releases 页面
echo 2. 找到最新版本（通常在页面顶部）
echo 3. 下载文件名包含以下关键词的压缩包：
echo    - RVC
echo    - win32.7z 或 windows.7z
echo    - 例如: RVC-beta-v2-xxx-win32.7z
echo.
echo 4. 下载到: %DOWNLOAD_DIR%
echo.
echo 按任意键打开下载页面...
pause >nul
start %RELEASES_URL%
echo.
echo ========================================
echo 方式 2: 使用 PowerShell 下载（自动）
echo ========================================
echo.
echo 注意: 需要知道确切的下载链接
echo.
set /p "USE_PS=是否尝试自动下载? (y/n): "

if /i "%USE_PS%"=="y" (
    echo.
    echo 正在获取最新版本信息...

    :: 使用 PowerShell 获取最新 release
    powershell -Command "$releases = Invoke-RestMethod -Uri 'https://api.github.com/repos/RVC-Project/Retrieval-based-Voice-Conversion-WebUI/releases'; $latest = $releases[0]; Write-Host '最新版本:' $latest.tag_name; $asset = $latest.assets | Where-Object { $_.name -like '*win*.7z' -or $_.name -like '*windows*.7z' } | Select-Object -First 1; if ($asset) { Write-Host '文件名:' $asset.name; Write-Host '大小:' ([math]::Round($asset.size/1MB, 2)) 'MB'; Write-Host '下载链接:' $asset.browser_download_url; $downloadUrl = $asset.browser_download_url; $outputPath = '%DOWNLOAD_DIR%\' + $asset.name; Write-Host ''; Write-Host '开始下载...'; Write-Host '保存到:' $outputPath; try { Invoke-WebRequest -Uri $downloadUrl -OutFile $outputPath -UseBasicParsing; Write-Host ''; Write-Host '下载完成!' -ForegroundColor Green; Write-Host '文件位置:' $outputPath; } catch { Write-Host ''; Write-Host '下载失败:' $_.Exception.Message -ForegroundColor Red; Write-Host '请使用方式 1 手动下载'; } } else { Write-Host '未找到 Windows 整合包'; Write-Host '请使用方式 1 手动下载'; }"

    echo.
    echo 按任意键打开下载目录...
    pause >nul
    explorer "%DOWNLOAD_DIR%"
) else (
    echo.
    echo 请手动下载后，将文件保存到:
    echo %DOWNLOAD_DIR%
    echo.
    echo 下载完成后，运行 extract_rvc.bat 进行解压
)

echo.
echo ========================================
echo 下载完成后的步骤:
echo ========================================
echo.
echo 1. 解压下载的 .7z 文件
echo    - 需要 7-Zip 或 WinRAR
echo    - 解压到: %USERPROFILE%\Desktop\RVC\
echo.
echo 2. 进入解压后的目录
echo.
echo 3. 双击运行 go-web.bat
echo.
echo 4. 等待启动，浏览器会自动打开
echo.
echo ========================================
pause
