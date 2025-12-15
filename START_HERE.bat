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
REM  - Installs or updates the Google Gemini CLI.
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
echo  ERROR: Node.js and npm not found. Please install using one of the options below:
echo.
echo  Option 1: Install Node.js directly (recommended for most users)
echo  1. Go to: https://nodejs.org/
echo  2. Download and run the installer for the latest LTS version.
echo.
echo  Option 2: Install via nvm-windows (for developers managing multiple versions)
echo  1. Go to: https://github.com/coreybutler/nvm-windows/releases
echo  2. Download 'nvm-setup.zip' and run the installer.
echo  3. Open a NEW terminal and run: nvm install lts
echo  4. Then run: nvm use [version_number] (e.g., nvm use 18.18.0)
echo.
echo  After installation is complete, please re-run this script.
echo.
pause
exit /b 1

:npm_found
echo  - Found npm.


REM --- Step 3: Install/Update Google Gemini CLI ---
echo.
echo [3/5] Installing/Updating Google Gemini CLI...

where gemini >nul 2>nul
if %errorlevel% neq 0 (
    echo  - Gemini CLI not found. Installing...
    call npm install -g @google/gemini-cli
    if !errorlevel! neq 0 (
        echo.
        echo  - ERROR: Failed to install @google/gemini-cli. Please check your npm installation.
        echo  - You might need to run your terminal as an administrator.
        echo.
        pause
        exit /b 1
    )
    echo  - Gemini CLI installed successfully.
) else (
    echo  - Google Gemini CLI is already installed.
    set /p update_choice="  - Do you want to check for updates? (y/N): "
    if /i "!update_choice!"=="y" (
        echo  - Checking for updates...
        call npm install -g @google/gemini-cli
        if !errorlevel! neq 0 (
            echo.
            echo  - ERROR: Failed to update @google/gemini-cli. Please check your npm installation.
            echo  - You might need to run your terminal as an administrator.
            echo.
            pause
            exit /b 1
        )
        echo  - Update check complete.
    ) else (
        echo  - Skipping update.
    )
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
