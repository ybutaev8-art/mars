Stop-ScheduledTask -TaskName "MarsPosBot" -ErrorAction SilentlyContinue
$procs = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like "*bot.py*" -and $_.Name -like "python*" }
if ($procs) {
    foreach ($p in $procs) {
        Stop-Process -Id $p.ProcessId -Force
        Write-Host "Bot to'xtatildi (PID: $($p.ProcessId))." -ForegroundColor Red
    }
} else {
    Write-Host "Bot hozirda ishlamayapti." -ForegroundColor Yellow
}
