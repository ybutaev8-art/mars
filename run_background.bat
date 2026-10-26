@echo off
cd /d "%~dp0"
chcp 65001 > nul
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
set "PYEXE=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
if not exist "%PYEXE%" set "PYEXE=python"
"%PYEXE%" -u bot.py >> bot_activity.log 2>&1
