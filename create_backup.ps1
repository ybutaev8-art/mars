# MARS BOTDAN YANGI ZAXIRA NUSXA OLISH SKRIPTI
$ErrorActionPreference = "Stop"

$timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$botDir = $PSScriptRoot
$backupDir = Join-Path $botDir "backups\backup_$timestamp"

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  MARS BOT: YANGI ZAXIRA NUSXA (BACKUP) YARATISH" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan

if (-not (Test-Path $backupDir)) {
    New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
}

Write-Host "Fayllar nusxalanmoqda: $backupDir ..." -ForegroundColor Yellow
$files = Get-ChildItem -Path $botDir -File | Where-Object { $_.Extension -ne '.log' }
foreach ($file in $files) {
    Copy-Item -Path $file.FullName -Destination $backupDir -Force
}

$zipPath = Join-Path $botDir "backups\mars_pos_bot_$timestamp.zip"
Compress-Archive -Path "$backupDir\*" -DestinationPath $zipPath -Force

Write-Host ""
Write-Host "========================================================" -ForegroundColor Green
Write-Host "✅ ZAXIRA NUSXA MUVAFFAQIYATLI YARATILDI!" -ForegroundColor Green
Write-Host "📁 Papka: $backupDir" -ForegroundColor White
Write-Host "📦 ZIP arxiv: $zipPath" -ForegroundColor White
Write-Host "========================================================" -ForegroundColor Green
