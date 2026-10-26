# MARS BOTNI HOZIRGI (BARQAROR) HOLATIGA QAYTARISH SKRIPTI
$ErrorActionPreference = "Stop"

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  MARS BOTNI BARQAROR HOLATIGA QAYTARISH (RESTORE)" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""

$botDir = $PSScriptRoot
$stableDir = Join-Path $botDir "backups\stable_2026-10-20"

if (-not (Test-Path $stableDir)) {
    Write-Host "❌ Xatolik: Barqaror versiya papkasi topilmadi: $stableDir" -ForegroundColor Red
    pause
    exit 1
}

Write-Host "1. Bot to'xtatilmoqda..." -ForegroundColor Yellow
& (Join-Path $botDir "stop_bot.ps1")
Start-Sleep -Seconds 2

Write-Host "2. Barcha kodlar va sozlamalar barqaror nusxadan tiklanmoqda..." -ForegroundColor Yellow
$files = Get-ChildItem -Path $stableDir -File
foreach ($file in $files) {
    Copy-Item -Path $file.FullName -Destination $botDir -Force
    Write-Host "   -> Qaytarildi: $($file.Name)" -ForegroundColor DarkGray
}

Write-Host "3. Bot qayta ishga tushirilmoqda..." -ForegroundColor Yellow
& (Join-Path $botDir "start_bot.ps1")

Write-Host ""
Write-Host "========================================================" -ForegroundColor Green
Write-Host "✅ BOT MUVAFFAQIYATLI HOZIRGI BARQAROR HOLATIGA QAYTARILDI!" -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Green
