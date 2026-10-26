@echo off
chcp 65001 > nul
powershell -ExecutionPolicy Bypass -File "%~dp0restore_stable.ps1"
pause
