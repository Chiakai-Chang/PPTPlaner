@echo off
REM Set Python to use UTF-8 mode
set PYTHONUTF8=1
chcp 65001 > nul
cd /d "%~dp0"
setlocal EnableDelayedExpansion

REM ===================================================================
REM  PPTPlaner - Complete Launcher
REM  - Environment validation
REM  - Version checking
REM  - Dependency installation
REM  - UI launch
REM ===================================================================

title PPTPlaner

REM --- Color definitions ---
set "CYAN=\033[36m"
set "GREEN=\033[32m"
set "YELLOW=\033[33m"
set "RED=\033[31m"
set "RESET=\033[0m"

REM --- Step 1: Python Check ---
echo.
echo  ===================================================================
echo  %CYAN%PPTPlaner AI 簡報助手%RESET%
echo  ===================================================================
echo.
echo [1/5] 檢查 Python 環境...

set "PYTHON_EXE="
for /f "usebackq delims=" %%i in (`where python 2^>nul ^| findstr /v /i "WindowsApps"`) do (
    set "PYTHON_EXE=%%i"
    goto :found_python
)

:found_python
if not defined PYTHON_EXE (
    echo.
    echo %RED%❌ 錯誤: 未找到 Python%RESET%
    echo.
    echo 請安裝 Python 3.8+：https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

for %%i in ("%PYTHON_EXE%") do set "PYTHON_DIR=%%~dpi"
set "PYTHON_SCRIPTS_PATH=%PYTHON_DIR%Scripts"

for /f "tokens=2" %%v in ('%PYTHON_EXE% -c "import sys; print(sys.version_info.major, sys.version_info.minor)" 2^>nul') do set "PYTHON_VER=%%v"
echo  ✓ 找到 Python !PYTHON_VER!

REM --- Step 2: Version Check ---
echo.
echo [2/5] 檢查版本資訊...

set "CONFIG_VERSION="
if exist "config.yaml" (
    for /f "tokens=2" %%v in ('%PYTHON_EXE% -c "import yaml; c=yaml.safe_load(open('config.yaml')); print(c.get('version', ''))" 2^>nul') do set "CONFIG_VERSION=%%v"
)

set "LATEST_VERSION="
set "UPDATE_AVAILABLE=0"

REM Try to fetch latest version from GitHub (non-blocking)
set "TMPFILE=%TEMP%\pptplaner_ver.txt"
curl -s "https://raw.githubusercontent.com/Chiakai-Chang/PPTPlaner/main/config.yaml" -o "%TMPFILE%" 2>nul
if exist "%TMPFILE%" (
    for /f "tokens=2" %%v in ('%PYTHON_EXE% -c "import yaml; c=yaml.safe_load(open('%TMPFILE%')); print(c.get('version', ''))" 2^>nul') do set "LATEST_VERSION=%%v"
    del "%TMPFILE%" 2>nul
    
    if not "!CONFIG_VERSION!" == "!LATEST_VERSION!" (
        if not "!LATEST_VERSION!" == "" (
            set "UPDATE_AVAILABLE=1"
        )
    )
)

if defined CONFIG_VERSION (
    echo  ✓ 當前版本: !CONFIG_VERSION!
    if "!UPDATE_AVAILABLE!" == "1" (
        echo  %YELLOW%⚠ 有新版本可用: !LATEST_VERSION!%RESET%
        echo  請執行: git pull
    )
) else (
    echo  %YELLOW%⚠ 未偵測到版本資訊%RESET%
)

REM --- Step 3: Dependency Check ---
echo.
echo [3/5] 檢查依賴套件...

set "PACKAGES_OK=1"

%PYTHON_EXE% -c "import requests, yaml, edge_tts, PIL, jinja2" 2>nul
if %errorlevel% neq 0 (
    echo  %YELLOW%需要安裝套件...%RESET%
    set "PACKAGES_OK=0"
)

if "!PACKAGES_OK!" == "0" (
    echo  正在安裝依賴套件...
    
    where uv >nul 2>&1
    if %errorlevel% equ 0 (
        echo  - 使用 uv (快速安裝器)
        uv pip install -r requirements.txt --system -q 2>nul
    ) else (
        echo  - 使用 pip
        "%PYTHON_EXE%" -m pip install -r requirements.txt --disable-pip-version-check -q 2>nul
    )
    
    if %errorlevel% neq 0 (
        echo  %RED%❌ 安裝失敗!%RESET%
        echo  請手動執行: pip install -r requirements.txt
        pause
        exit /b 1
    )
    echo  ✓ 套件安裝完成
) else (
    echo  ✓ 所有套件已安裝
)

REM --- Step 4: FFmpeg Check ---
echo.
echo [4/5] 檢查 FFmpeg (影片生成用)...

set "FFMPEG_OK=0"
where ffmpeg >nul 2>&1
if %errorlevel% equ 0 (
    echo  ✓ FFmpeg 已安裝
    set "FFMPEG_OK=1"
) else (
    echo  %YELLOW%⚠ FFmpeg 未安裝 (影片生成需要)%RESET%
    echo.
    echo  安裝選項:
    echo  1. 手動安裝: https://ffmpeg.org/download.html
    echo  2. 使用安裝腳本: scripts\install_ffmpeg.ps1
    echo.
    echo  %YELLOW%提示: 您可以稍後安裝，不影響簡報生成功能%RESET%
)

REM --- Step 5: Config Migration Check ---
echo.
echo [5/6] 檢查配置更新...

if not exist "config.yaml" (
    if exist "config.yaml.example" (
        echo  %YELLOW%⚠ 未找到 config.yaml，正在建立...%RESET%
        copy "config.yaml.example" "config.yaml" >nul
        echo  ✓ 已建立 config.yaml
        echo  請編輯 config.yaml 配置您的設定
    ) else (
        echo  %RED%❌ 錯誤: 找不到 config.yaml 範本%RESET%
        pause
        exit /b 1
    )
)

REM Check for config updates
if exist "scripts\config_migrator.py" (
    %PYTHON_EXE% scripts\config_migrator.py >nul 2>&1
    if %errorlevel% equ 0 (
        echo  ✓ 配置已是最新版本
    )
)

echo.
echo [6/6] 啟動 PPTPlaner...
echo.
echo  %GREEN%啟動中...%RESET%
echo.

%PYTHON_EXE% run_ui.py

REM --- Exit ---
echo.
echo  %GREEN%PPTPlaner 已關閉%RESET%
echo.
pause
endlocal
