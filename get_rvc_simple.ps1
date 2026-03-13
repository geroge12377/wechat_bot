$releases = Invoke-RestMethod -Uri 'https://api.github.com/repos/RVC-Project/Retrieval-based-Voice-Conversion-WebUI/releases'
$latest = $releases[0]
$version = $latest.tag_name
$asset = $latest.assets | Where-Object { $_.name -like '*win*.7z' -or $_.name -like '*windows*.7z' } | Select-Object -First 1

if ($asset) {
    $fileName = $asset.name
    $fileSize = [math]::Round($asset.size/1MB, 2)
    $downloadUrl = $asset.browser_download_url

    Write-Output "VERSION=$version"
    Write-Output "FILENAME=$fileName"
    Write-Output "SIZE=$fileSize"
    Write-Output "URL=$downloadUrl"
} else {
    Write-Output "ERROR=No Windows package found"
    $latest.assets | ForEach-Object { Write-Output "AVAILABLE=$($_.name)" }
}
