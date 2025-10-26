@echo off

REM Change directory to the script's location to make it robust.
cd /d "%~dp0"

setlocal
title PPTPlaner One-Click Starter

REM =================================================================================
REM  PPTPlaner One-Click Starter (.bat) - Self-Aware PATH Version
REM  - Finds the real Python and its Scripts path.
REM  - Passes the Scripts path to the Python process via an environment variable.
REM =================================================================================

echo.
echo  =========================================================
echo  Welcome to the PPTPlaner AI Presentation Assistant!
echo  =========================================================
echo.

REM --- Step 1: Find the real Python executable and its Scripts path ---
echo [1/4] Finding a valid Python installation...

set "PYTHON_EXE="
for /f "usebackq delims=" %%i in (`where python ^| findstr /v /i "WindowsApps"`) do (
    set "PYTHON_EXE=%%i"
    goto :found_python
)

:found_python
if not defined PYTHON_EXE (
    echo ERROR: A suitable Python installation was not found.
    pause
    exit /b 1
)

REM Get the directory of the python executable
for %%i in ("%PYTHON_EXE%") do set "PYTHON_DIR=%%~dpi"
set "PYTHON_SCRIPTS_PATH=%PYTHON_DIR%Scripts"

echo  - Found Python at: %PYTHON_EXE%
echo  - Deduced Scripts path: %PYTHON_SCRIPTS_PATH%


REM --- Step 2: Install packages globally ---
echo.
echo [2/4] Installing required packages...

"%PYTHON_EXE%" -m pip install -r requirements.txt --quiet --disable-pip-version-check
if %errorlevel% neq 0 (
    echo  - ERROR: Failed to install required packages.
    pause
    exit /b 1
)
echo  - Required packages are installed.


REM --- Step 3: Set environment variable for the Python script ---
echo.
echo [3/4] Configuring environment for subprocess...
set "PPTPLANER_SCRIPTS_PATH=%PYTHON_SCRIPTS_PATH%"
echo  - Scripts path has been set for the program.


REM --- Step 4: Launch the User Interface ---
echo.
echo [4/4] Environment is ready! Launching the UI...
echo.

"%PYTHON_EXE%" run_ui.py


echo.
echo  The program has been closed. Thank you for using PPTPlaner!
echo.
pause
