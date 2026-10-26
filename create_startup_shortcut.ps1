$startupDir = [Environment]::GetFolderPath("Startup")
$shortcutPath = Join-Path $startupDir "MarsPosBot.lnk"

$wsh = New-Object -ComObject WScript.Shell
$shortcut = $wsh.CreateShortcut($shortcutPath)
$shortcut.TargetPath = "wscript.exe"
$shortcut.Arguments = "$HOME\.gemini\antigravity\scratch\mars_pos_bot_latest\start_bot_background.vbs"
$shortcut.WorkingDirectory = "$HOME\.gemini\antigravity\scratch\mars_pos_bot_latest"
$shortcut.WindowStyle = 7
$shortcut.Description = "MARS POS Telegram Boti (Fon rejimida avtostart)"
$shortcut.Save()

Write-Host "Startup shortcut created successfully: $shortcutPath"
