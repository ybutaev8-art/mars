$scriptDir = $PSScriptRoot
if (-not $scriptDir) { $scriptDir = "$HOME\.gemini\antigravity\scratch\mars_pos_bot_latest" }

$procs = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like "*bot.py*" -and $_.Name -like "python*" }
if ($procs) {
    Write-Host "Bot allaqachon fonda faol ishlab turibdi!" -ForegroundColor Yellow
    foreach ($p in $procs) {
        Write-Host ("   • PID: " + $p.ProcessId) -ForegroundColor Cyan
    }
} else {
    Write-Host "Bot fonda (yashirin rejimda) ishga tushirilmoqda..." -ForegroundColor Cyan
    Start-ScheduledTask -TaskName "MarsPosBot" -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 3
    $check = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like "*bot.py*" -and $_.Name -like "python*" }
    if ($check) {
        Write-Host "MARS Telegram Boti fonda (ekranda hech qanday oyna chiqmasdan) muvaffaqiyatli ishga tushdi!" -ForegroundColor Green
        foreach ($p in $check) {
            Write-Host ("   • PID: " + $p.ProcessId) -ForegroundColor Cyan
        }
    } else {
        Start-Process -FilePath "wscript.exe" -ArgumentList "start_bot_background.vbs" -WorkingDirectory $scriptDir
        Start-Sleep -Seconds 4
        $check2 = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like "*bot.py*" -and $_.Name -like "python*" }
        if ($check2) {
            Write-Host "MARS Telegram Boti fonda (yashirin) muvaffaqiyatli ishga tushdi!" -ForegroundColor Green
        } else {
            Write-Host "Botni ishga tushirishda xatolik yuz berdi. bot_activity.log faylini tekshiring." -ForegroundColor Red
        }
    }
}
