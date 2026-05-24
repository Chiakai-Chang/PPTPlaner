@echo off
REM ===================================================================
REM  PPTPlaner Launcher
REM  - Sets UTF-8 encoding
REM  - Adds required paths to PATH
REM  - Calls Python launcher (all logic in launcher.py)
REM ===================================================================

REM Set Python UTF-8 mode
set PYTHONUTF8=1

REM Set code page to UTF-8
chcp 65001 > nul

REM Change to script directory
cd /d "%~dp0"

title PPTPlaner

REM ===================================================================
REM  Add required executables to PATH
REM ===================================================================

REM Add agy (Antigravity CLI) to PATH
if exist "%LOCALAPPDATA%\agy\bin\agy.EXE" (
    set "PATH=%PATH%;%LOCALAPPDATA%\agy\bin"
)

REM Add Claude Code to PATH
if exist "%LOCALAPPDATA%\Claude\bin\claude.EXE" (
    set "PATH=%PATH%;%LOCALAPPDATA%\Claude\bin"
)

REM Add Ollama to PATH (if installed)
if exist "%LOCALAPPDATA%\Programs\Ollama\ollama.EXE" (
    set "PATH=%PATH%;%LOCALAPPDATA%\Programs\Ollama"
)

REM Add FFmpeg to PATH (if installed in common locations)
if exist "%PROGRAMFILES%\ffmpeg\bin\ffmpeg.EXE" (
    set "PATH=%PATH%;%PROGRAMFILES%\ffmpeg\bin"
)
if exist "%LOCALAPPDATA%\Programs\ffmpeg\bin\ffmpeg.EXE" (
    set "PATH=%PATH%;%LOCALAPPDATA%\Programs\ffmpeg\bin"
)

REM Start Python launcher
python launcher.py

REM Wait for user
pause
