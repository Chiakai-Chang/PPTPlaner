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

REM ===================================================================
REM  Start Python launcher with auto-detection and fallback
REM ===================================================================

where python >nul 2>nul
if %errorlevel% equ 0 (
    python launcher.py
    goto :end
)

where py >nul 2>nul
if %errorlevel% equ 0 (
    py launcher.py
    goto :end
)

REM If neither is found
echo =======================================================================
echo ❌ 嚴重錯誤：系統找不到 Python 執行環境！
echo =======================================================================
echo.
echo PPTPlaner 簡報助手需要 Python 3.12+ 才能正常運作。
echo 請按照以下簡單步驟完成安裝，即可一鍵啟動：
echo.
echo 1. 前往 Python 官方網站下載：https://www.python.org/downloads/
echo 2. 下載並執行安裝檔（推薦 Python 3.12+ 穩定版本）。
echo 3. 【最重要的一步】安裝時請務必勾選 "Add Python to PATH" 複選框！
echo 4. 安裝完成後，重新按兩下執行這個 PPTPlaner.bat 檔案即可。
echo.
echo =======================================================================
pause

:end
