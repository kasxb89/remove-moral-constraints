@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\scripts\web-windows.ps1" -Action Start %*
exit /b %errorlevel%
