$scriptDir = $PSScriptRoot
if (-not $scriptDir) { $scriptDir = "$HOME\.gemini\antigravity\scratch\mars_pos_bot_latest" }

Write-Host "🔄 Bot qayta yuklanmoqda..." -ForegroundColor Cyan
& (Join-Path $scriptDir "stop_bot.ps1")
Start-Sleep -Seconds 2
& (Join-Path $scriptDir "start_bot.ps1")
