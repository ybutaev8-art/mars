@echo off
chcp 65001 > nul
echo ========================================================
echo   MARS BOT: GITHUBGA SAQLASH VA BOTNI TO'XTATISH
echo ========================================================
echo.

echo 1. Bot to'xtatilmoqda...
powershell -ExecutionPolicy Bypass -File .\stop_bot.ps1

echo 2. O'zgarishlar GitHub'ga yuklanmoqda...
git add .
set /p commit_msg="Izoh kiriting (shunchaki Enter bossangiz 'update' deb saqlanadi): "
if "%commit_msg%"=="" set commit_msg=update_%date%_%time%
git commit -m "%commit_msg%"
git push

echo.
echo ========================================================
echo ✅ BARCHA KODLAR GITHUBGA MUVAFFAQIYATLI YUKLANDI!
echo Endi ushbu kompyuterni bemalol o'chirib ketishingiz mumkin.
echo 2-kompyuterga borganingizda pull_from_github.bat ni bosing.
echo ========================================================
pause
