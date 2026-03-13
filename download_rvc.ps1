# RVC 自动下载脚本
# PowerShell 版本

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "RVC 整合包自动下载工具" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 设置下载目录
$downloadDir = "$env:USERPROFILE\Desktop\RVC_Download"
$extractDir = "$env:USERPROFILE\Desktop\RVC"

if (-not (Test-Path $downloadDir)) {
    New-Item -ItemType Directory -Path $downloadDir -Force | Out-Null
    Write-Host "[创建] 下载目录: $downloadDir" -ForegroundColor Green
}

Write-Host "[信息] 下载目录: $downloadDir" -ForegroundColor Yellow
Write-Host ""

# 获取最新 release
Write-Host "[步骤 1/4] 获取最新版本信息..." -ForegroundColor Cyan

try {
    $apiUrl = "https://api.github.com/repos/RVC-Project/Retrieval-based-Voice-Conversion-WebUI/releases"
    $releases = Invoke-RestMethod -Uri $apiUrl -UseBasicParsing

    $latest = $releases[0]
    $version = $latest.tag_name

    Write-Host "[成功] 最新版本: $version" -ForegroundColor Green
    Write-Host ""

    # 查找 Windows 整合包
    Write-Host "[步骤 2/4] 查找 Windows 整合包..." -ForegroundColor Cyan

    $asset = $latest.assets | Where-Object {
        $_.name -like "*win*.7z" -or
        $_.name -like "*windows*.7z" -or
        $_.name -like "*Win*.7z"
    } | Select-Object -First 1

    if (-not $asset) {
        Write-Host "[警告] 未找到 Windows 整合包" -ForegroundColor Yellow
        Write-Host "[信息] 可用的文件:" -ForegroundColor Yellow
        $latest.assets | ForEach-Object { Write-Host "  - $($_.name)" }
        Write-Host ""
        Write-Host "[提示] 请手动下载" -ForegroundColor Yellow
        Write-Host "[打开] Release 页面..." -ForegroundColor Cyan
        Start-Process "https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI/releases"
        exit 1
    }

    $fileName = $asset.name
    $fileSize = [math]::Round($asset.size / 1MB, 2)
    $downloadUrl = $asset.browser_download_url
    $outputPath = Join-Path $downloadDir $fileName

    Write-Host "[找到] 文件名: $fileName" -ForegroundColor Green
    Write-Host "[大小] $fileSize MB" -ForegroundColor Green
    Write-Host ""

    # 检查是否已下载
    if (Test-Path $outputPath) {
        $existingSize = [math]::Round((Get-Item $outputPath).Length / 1MB, 2)
        Write-Host "[检查] 文件已存在: $outputPath" -ForegroundColor Yellow
        Write-Host "[大小] $existingSize MB" -ForegroundColor Yellow

        $overwrite = Read-Host "[询问] 是否重新下载? (y/n)"
        if ($overwrite -ne "y") {
            Write-Host "[跳过] 使用现有文件" -ForegroundColor Yellow
            Write-Host ""
            Write-Host "[完成] 文件位置: $outputPath" -ForegroundColor Green
            Write-Host ""
            Write-Host "[下一步] 运行 extract_rvc.bat 解压文件" -ForegroundColor Cyan
            Read-Host "按 Enter 键退出"
            exit 0
        }
    }

    # 下载文件
    Write-Host "[步骤 3/4] 开始下载..." -ForegroundColor Cyan
    Write-Host "[保存到] $outputPath" -ForegroundColor Yellow
    Write-Host ""

    # 使用 WebClient 显示进度
    $webClient = New-Object System.Net.WebClient

    # 注册进度事件
    Register-ObjectEvent -InputObject $webClient -EventName DownloadProgressChanged -SourceIdentifier WebClient.DownloadProgressChanged -Action {
        $percent = $EventArgs.ProgressPercentage
        $received = [math]::Round($EventArgs.BytesReceived / 1MB, 2)
        $total = [math]::Round($EventArgs.TotalBytesToReceive / 1MB, 2)
        Write-Progress -Activity "下载中" -Status "$received MB / $total MB" -PercentComplete $percent
    } | Out-Null

    # 开始下载
    $webClient.DownloadFileAsync($downloadUrl, $outputPath)

    # 等待下载完成
    while ($webClient.IsBusy) {
        Start-Sleep -Milliseconds 100
    }

    # 清理事件
    Unregister-Event -SourceIdentifier WebClient.DownloadProgressChanged
    $webClient.Dispose()

    Write-Progress -Activity "下载中" -Completed
    Write-Host ""
    Write-Host "[成功] 下载完成!" -ForegroundColor Green
    Write-Host "[文件] $outputPath" -ForegroundColor Green
    Write-Host ""

    # 询问是否解压
    Write-Host "[步骤 4/4] 解压文件" -ForegroundColor Cyan
    $extract = Read-Host "[询问] 是否立即解压? (y/n)"

    if ($extract -eq "y") {
        Write-Host ""
        Write-Host "[解压] 正在解压到: $extractDir" -ForegroundColor Cyan

        if (-not (Test-Path $extractDir)) {
            New-Item -ItemType Directory -Path $extractDir -Force | Out-Null
        }

        # 检查 7-Zip
        $sevenZip = $null
        $possiblePaths = @(
            "C:\Program Files\7-Zip\7z.exe",
            "C:\Program Files (x86)\7-Zip\7z.exe"
        )

        foreach ($path in $possiblePaths) {
            if (Test-Path $path) {
                $sevenZip = $path
                break
            }
        }

        if ($sevenZip) {
            Write-Host "[使用] 7-Zip: $sevenZip" -ForegroundColor Yellow
            & $sevenZip x $outputPath "-o$extractDir" -y

            if ($LASTEXITCODE -eq 0) {
                Write-Host ""
                Write-Host "========================================" -ForegroundColor Green
                Write-Host "安装完成！" -ForegroundColor Green
                Write-Host "========================================" -ForegroundColor Green
                Write-Host ""
                Write-Host "[位置] $extractDir" -ForegroundColor Green
                Write-Host ""
                Write-Host "[下一步]" -ForegroundColor Cyan
                Write-Host "  1. 打开文件夹: $extractDir" -ForegroundColor Yellow
                Write-Host "  2. 找到并运行 go-web.bat" -ForegroundColor Yellow
                Write-Host "  3. 等待浏览器自动打开" -ForegroundColor Yellow
                Write-Host ""

                $openFolder = Read-Host "[询问] 是否打开文件夹? (y/n)"
                if ($openFolder -eq "y") {
                    Start-Process explorer $extractDir
                }
            } else {
                Write-Host "[错误] 解压失败" -ForegroundColor Red
            }
        } else {
            Write-Host "[错误] 未找到 7-Zip" -ForegroundColor Red
            Write-Host "[提示] 请安装 7-Zip: https://www.7-zip.org/" -ForegroundColor Yellow
            Write-Host "[或者] 手动解压 $outputPath 到 $extractDir" -ForegroundColor Yellow
        }
    } else {
        Write-Host ""
        Write-Host "[完成] 文件已下载到: $outputPath" -ForegroundColor Green
        Write-Host "[下一步] 运行 extract_rvc.bat 解压文件" -ForegroundColor Cyan
    }

} catch {
    Write-Host ""
    Write-Host "[错误] $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Write-Host "[建议] 手动下载:" -ForegroundColor Yellow
    Write-Host "  1. 访问: https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI/releases" -ForegroundColor Yellow
    Write-Host "  2. 下载最新的 Windows 整合包 (.7z 文件)" -ForegroundColor Yellow
    Write-Host "  3. 保存到: $downloadDir" -ForegroundColor Yellow
    Write-Host ""

    $openBrowser = Read-Host "[询问] 是否打开下载页面? (y/n)"
    if ($openBrowser -eq "y") {
        Start-Process "https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI/releases"
    }
}

Write-Host ""
Read-Host "按 Enter 键退出"
