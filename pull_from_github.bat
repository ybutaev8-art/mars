@echo off
chcp 65001 > nul
echo ========================================================
echo   MARS BOT: GITHUB'DAN YANGILANISHLARNI OLISH VA BOTNI ISHGA TUSHIRISH
echo ========================================================
echo.

echo 1. GitHub'dan eng so'nggi o'zgarishlar olinmoqda...
git pull

echo 2. Bot fonda ishga tushirilmoqda...
powershell -ExecutionPolicy Bypass -File .\start_bot.ps1

echo.
echo ========================================================
echo ✅ BOT YANGILANDI VA ISHGA TUSHIRILDI!
echo Antigravity'da ishlashni davom ettirishingiz mumkin.
echo ========================================================
pause
