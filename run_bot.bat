@echo off
chcp 65001 > nul
cd /d "%~dp0"
title MARS ELEKTRON TEXNIKA - Telegram Boti
echo ======================================================
echo    MARS ELEKTRON TEXNIKA MCHJ - BOT ISHGA TUSHMOQDA
echo ======================================================
set "PYEXE=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
if not exist "%PYEXE%" set "PYEXE=python"
"%PYEXE%" bot.py
pause
