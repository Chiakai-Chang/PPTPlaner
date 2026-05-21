@echo off

REM Set Python to use UTF-8 mode, which is more reliable than chcp
set PYTHONUTF8=1

REM Set code page to UTF-8 to prevent encoding issues.
chcp 65001 > nul

REM Change directory to the script's location to make it robust.
cd /d "%~dp0"

setlocal EnableDelayedExpansion
title PPTPlaner One-Click Starter

REM =================================================================================
REM  PPTPlaner One-Click Starter (.bat)
REM  - Ensures UTF-8 encoding for compatibility.
REM  - Validates Python and Node.js/npm installations, providing guidance if missing.
REM  - Checks for supported AI agents (optional).
REM  - Installs required Python packages.
REM  - Launches the main application.
REM =================================================================================

echo.
echo  =========================================================
echo  Welcome to the PPTPlaner AI Presentation Assistant!
echo  =========================================================
echo.

REM --- Step 1: Find Python ---
echo [1/5] Finding a valid Python installation...

set "PYTHON_EXE="
for /f "usebackq delims=" %%i in (`where python ^| findstr /v /i "WindowsApps"`) do (
    set "PYTHON_EXE=%%i"
    goto :found_python
)

:found_python
if not defined PYTHON_EXE (
    echo.
    echo  ERROR: Python is not installed or not found in your PATH.
    echo  Please install Python from: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

REM Get the directory of the python executable and set Scripts path
for %%i in ("%PYTHON_EXE%") do set "PYTHON_DIR=%%~dpi"
set "PYTHON_SCRIPTS_PATH=%PYTHON_DIR%Scripts"

echo  - Found Python at: %PYTHON_EXE%


REM --- Step 2: Check for Node.js and npm ---
echo.
echo [2/5] Checking for Node.js and npm installation...

where npm >nul 2>nul
if %errorlevel% equ 0 goto npm_found

:npm_not_found
echo.
echo  WARNING: Node.js and npm not found.
echo  This is ONLY required if you plan to use CLI-based agents:
echo    - Antigravity CLI (Google)
echo    - Claude Code CLI (Anthropic)
echo.
echo  For local models (Ollama, llama.cpp) or OpenAI API, Node.js is NOT required.
echo.

:npm_found
echo  - Found npm.


REM --- Step 3: Check for AI Agent (Optional) ---
echo.
echo [3/5] Checking for supported AI agents...
echo.
echo  PPTPlaner supports multiple AI backends. You need at least ONE:
echo.
echo  1. Antigravity CLI (Google)  - Official installer:
echo     irm https://antigravity.google/cli/install.ps1 | iex
echo.
echo  2. Claude Code CLI (Anthropic):
echo     npm install -g @anthropic-ai/claude-code
echo.
echo  3. Local Models (no installation needed):
echo     - Ollama: https://ollama.ai/
echo     - llama.cpp: Run server with --host flag
echo.
echo  4. OpenAI API:
echo     - Just need an API key
echo.

REM Check what agents are available
set "AGENT_COUNT=0"

where agy >nul 2>nul
if %errorlevel% equ 0 (
    echo  [OK] Antigravity CLI (agy) - Found
    set /a AGENT_COUNT+=1
) else (
    echo  [--] Antigravity CLI (agy) - Not found
)

where claude >nul 2>nul
if %errorlevel% equ 0 (
    echo  [OK] Claude Code CLI - Found
    set /a AGENT_COUNT+=1
) else (
    echo  [--] Claude Code CLI - Not found
)

echo.
echo  Local models will be auto-detected at runtime.

if !AGENT_COUNT! equ 0 (
    echo.
    echo  WARNING: No CLI-based agents found.
    echo  You can still use PPTPlaner with:
    echo    - Local models (Ollama, llama.cpp) - auto-detected
    echo    - OpenAI API - configure in UI
    echo.
) else (
    echo.
    echo  Found !AGENT_COUNT! CLI agent(s) ready to use.
)


REM --- Step 4: Install Python packages ---
echo.
echo [4/5] Installing required Python packages...

"%PYTHON_EXE%" -m pip install -r requirements.txt --disable-pip-version-check
if %errorlevel% neq 0 (
    echo  - ERROR: Failed to install required packages.
    pause
    exit /b 1
)
echo  - Required packages are installed.


REM --- Step 5: Launch the User Interface ---
echo.
echo [5/5] Environment is ready! Launching the UI...
echo.

set "PPTPLANER_SCRIPTS_PATH=%PYTHON_SCRIPTS_PATH%"

"%PYTHON_EXE%" run_ui.py


echo.
echo  The program has been closed. Thank you for using PPTPlaner!
echo.
pause
endlocal
