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
REM  - Validates Python installation
REM  - Installs required Python packages
REM  - Launches the main application
REM =================================================================================

echo.
echo  =========================================================
echo  Welcome to the PPTPlaner AI Presentation Assistant
REM ==================================================================================

REM --- Step 1: Find Python ---
echo.
echo [1/3] Finding Python installation...

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


REM --- Step 2: Install Python packages ---
echo.
echo [2/3] Installing required Python packages...

REM Check if uv is available (faster than pip)
set "USE_UV=0"
where uv >nul 2>&1
if %errorlevel% equ 0 (
    set "USE_UV=1"
    echo  - Using uv (fast installer)
)

if "%USE_UV%"=="1" (
    uv pip install -r requirements.txt --system -q
) else (
    echo  - Using pip
    "%PYTHON_EXE%" -m pip install -r requirements.txt --disable-pip-version-check -q
)

if %errorlevel% neq 0 (
    echo  - ERROR: Failed to install required packages.
    pause
    exit /b 1
)
echo  - Packages ready.


REM --- Step 3: Launch the User Interface ---
echo.
echo [3/3] Launching the UI...
echo.

set "PPTPLANER_SCRIPTS_PATH=%PYTHON_SCRIPTS_PATH%"

"%PYTHON_EXE%" run_ui.py


echo.
echo  Program closed. Thank you for using PPTPlaner!
echo.
pause
endlocal
