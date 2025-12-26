# Care RAG API - 一鍵建立 ZIP 打包腳本
# 使用方式: powershell -ExecutionPolicy Bypass -File scripts/create_zip.ps1

$projectName = "care_rag_api"
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$zipFileName = "${projectName}_${timestamp}.zip"
$rootDir = Split-Path -Parent $PSScriptRoot

Write-Host "正在建立 ZIP 打包檔案..." -ForegroundColor Green
Write-Host "專案目錄: $rootDir" -ForegroundColor Cyan
Write-Host "輸出檔案: $zipFileName" -ForegroundColor Cyan

# 排除的檔案和目錄
$excludeItems = @(
    "__pycache__",
    "*.pyc",
    ".git",
    ".venv",
    "venv",
    "env",
    ".pytest_cache",
    ".coverage",
    "htmlcov",
    "*.egg-info",
    ".idea",
    ".vscode"
)

# 建立臨時目錄
$tempDir = Join-Path $env:TEMP "care_rag_api_zip_$timestamp"
if (Test-Path $tempDir) {
    Remove-Item -Recurse -Force $tempDir
}
New-Item -ItemType Directory -Path $tempDir | Out-Null

# 複製檔案（排除不需要的項目）
Write-Host "複製專案檔案..." -ForegroundColor Yellow
Get-ChildItem -Path $rootDir -Recurse | Where-Object {
    $shouldExclude = $false
    foreach ($exclude in $excludeItems) {
        if ($_.FullName -like "*$exclude*") {
            $shouldExclude = $true
            break
        }
    }
    return -not $shouldExclude
} | Copy-Item -Destination {
    $_.FullName.Replace($rootDir, $tempDir)
} -Force

# 建立 ZIP 檔案
Write-Host "壓縮檔案..." -ForegroundColor Yellow
$zipPath = Join-Path $rootDir $zipFileName
if (Test-Path $zipPath) {
    Remove-Item -Force $zipPath
}

Compress-Archive -Path "$tempDir\*" -DestinationPath $zipPath -Force

# 清理臨時目錄
Remove-Item -Recurse -Force $tempDir

Write-Host "`n完成！ZIP 檔案已建立: $zipFileName" -ForegroundColor Green
Write-Host "檔案大小: $((Get-Item $zipPath).Length / 1MB) MB" -ForegroundColor Cyan


