$scriptDir = $PSScriptRoot
if (-not $scriptDir) { $scriptDir = "$HOME\.gemini\antigravity\scratch\mars_pos_bot_latest" }

$procs = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like "*bot.py*" -and $_.Name -like "python*" }
if ($procs) {
    Write-Host "✅ BOT HOZIRDA KOMPYUTERDA ISHLAMOQDA!" -ForegroundColor Green
    foreach ($p in $procs) {
        Write-Host ("   • Jarayon ID (PID): " + $p.ProcessId) -ForegroundColor Cyan
        Write-Host ("   • Ishga tushgan vaqti: " + $p.CreationDate) -ForegroundColor Gray
    }
} else {
    Write-Host "❌ BOT HOZIRDA TO'XTATILGAN (Ishlamayapti)." -ForegroundColor Red
    Write-Host "   Uni ishga tushirish uchun 'start_bot.ps1' yoki 'run_background.bat' faylini bosing." -ForegroundColor Yellow
}

Write-Host "`n------------------------------------------------------------" -ForegroundColor DarkGray
Write-Host "So'nggi bot faollik loglari:" -ForegroundColor White
Write-Host "------------------------------------------------------------" -ForegroundColor DarkGray

$logPath = Join-Path $scriptDir "bot_activity.log"
if (Test-Path $logPath) {
    Get-Content $logPath -Tail 15
} else {
    Write-Host "Log fayli hali yaratilmagan." -ForegroundColor Gray
}
Write-Host "------------------------------------------------------------" -ForegroundColor DarkGray
