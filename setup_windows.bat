@echo off
setlocal
REM Windows 一鍵啟動：呼叫 PowerShell 腳本
set PS1=%~dp0setup_windows.ps1

if not exist "%PS1%" (
  echo [ERROR] 找不到 %PS1%
  exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -File "%PS1%"
endlocal
