@echo off
chcp 65001 > nul
powershell -ExecutionPolicy Bypass -File "%~dp0create_backup.ps1"
pause
