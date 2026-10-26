@echo off
chcp 65001 > nul
echo ========================================================
echo   MARS BOT: GITHUB'GA BIRINCHI MARTA YUKLASH (PUSH)
echo ========================================================
echo.
cd /d "%~dp0"
"C:\Program Files\Git\cmd\git.exe" push -u origin main
echo.
echo Jarayon yakunlandi.
pause
