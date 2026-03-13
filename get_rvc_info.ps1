$releases = Invoke-RestMethod -Uri 'https://api.github.com/repos/RVC-Project/Retrieval-based-Voice-Conversion-WebUI/releases'
$latest = $releases[0]
Write-Host "最新版本: $($latest.tag_name)"
Write-Host ""

$asset = $latest.assets | Where-Object {
    $_.name -like '*win*.7z' -or
    $_.name -like '*windows*.7z' -or
    $_.name -like '*Win*.7z'
} | Select-Object -First 1

if ($asset) {
    Write-Host "文件名: $($asset.name)"
    Write-Host "大小: $([math]::Round($asset.size/1MB, 2)) MB"
    Write-Host "下载链接: $($asset.browser_download_url)"
} else {
    Write-Host "未找到 Windows 整合包"
    Write-Host ""
    Write-Host "可用文件:"
    $latest.assets | ForEach-Object {
        Write-Host "  - $($_.name) ($([math]::Round($_.size/1MB, 2)) MB)"
    }
}
