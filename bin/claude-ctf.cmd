@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\scripts\start-claude.ps1" %*
exit /b %errorlevel%
