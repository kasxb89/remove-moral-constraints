@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\web-windows.ps1" -Action Start %*
if errorlevel 1 pause
