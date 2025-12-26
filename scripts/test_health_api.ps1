# 健康檢查 API 測試腳本 (PowerShell)
# 更新時間：2025-12-26 17:46

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Care RAG API 健康檢查測試" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

$baseUrl = "http://localhost:8000"

Write-Host "1. 測試根端點 (/)" -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "${baseUrl}/" -Method GET -UseBasicParsing
    $response.Content | ConvertFrom-Json | ConvertTo-Json -Depth 10
} catch {
    Write-Host "錯誤: $_" -ForegroundColor Red
}
Write-Host ""

Write-Host "2. 測試健康檢查端點 (/api/v1/health)" -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "${baseUrl}/api/v1/health" -Method GET -UseBasicParsing
    $response.Content | ConvertFrom-Json | ConvertTo-Json -Depth 10
} catch {
    Write-Host "錯誤: $_" -ForegroundColor Red
}
Write-Host ""

Write-Host "3. 測試就緒檢查端點 (/api/v1/health/ready)" -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "${baseUrl}/api/v1/health/ready" -Method GET -UseBasicParsing
    $response.Content | ConvertFrom-Json | ConvertTo-Json -Depth 10
} catch {
    Write-Host "錯誤: $_" -ForegroundColor Red
}
Write-Host ""

Write-Host "4. 測試存活檢查端點 (/api/v1/health/live)" -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "${baseUrl}/api/v1/health/live" -Method GET -UseBasicParsing
    $response.Content | ConvertFrom-Json | ConvertTo-Json -Depth 10
} catch {
    Write-Host "錯誤: $_" -ForegroundColor Red
}
Write-Host ""

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "測試完成" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

