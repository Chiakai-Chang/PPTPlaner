@echo off
REM ===================================================================
REM  PPTPlaner Launcher
REM  - Sets UTF-8 encoding
REM  - Calls Python launcher (all logic in launcher.py)
REM ===================================================================

REM Set Python UTF-8 mode
set PYTHONUTF8=1

REM Set code page to UTF-8
chcp 65001 > nul

REM Change to script directory
cd /d "%~dp0"

title PPTPlaner

REM Start Python launcher
python launcher.py

REM Wait for user
pause
