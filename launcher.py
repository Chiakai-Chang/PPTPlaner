#!/usr/bin/env python3
"""PPTPlaner Launcher - Complete environment validation and UI startup.

This module handles all launcher logic:
- Python version check
- Version detection (current vs latest)
- Dependency installation
- FFmpeg availability check
- Config migration
- UI launch
"""
import os
import sys
import subprocess
import shutil
import urllib.request
import urllib.error
from pathlib import Path

# ============================================================================
# Configuration
# ============================================================================

ROOT = Path(__file__).resolve().parent
CONFIG = ROOT / "config.yaml"
CONFIG_EXAMPLE = ROOT / "config.yaml.example"
REQUIREMENTS = ROOT / "requirements.txt"

# Required Python modules
REQUIRED_MODULES = [
    ("requests", "API communication"),
    ("yaml", "Configuration (PyYAML)"),
    ("edge_tts", "TTS generation"),
    ("PIL", "Image processing (Pillow)"),
    ("jinja2", "Template rendering"),
]

# GitHub raw URL for version check
GITHUB_CONFIG_URL = (
    "https://raw.githubusercontent.com/Chiakai-Chang/PPTPlaner/main/config.yaml"
)


# ============================================================================
# Color helpers (ANSI - works in modern Windows terminals)
# ============================================================================

RESET = "\033[0m"
BOLD = "\033[1m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
CYAN = "\033[36m"
BLUE = "\033[34m"


def color(text, color_code):
    """Wrap text with ANSI color code."""
    return f"{color_code}{text}{RESET}"


def step_header(num, total, text):
    """Print a step header."""
    print(f"\n[{num}/{total}] {color(text, BLUE)}")


def success(text):
    """Print a success message."""
    print(f"  ✓ {color(text, GREEN)}")


def warning(text):
    """Print a warning message."""
    print(f"  ⚠ {color(text, YELLOW)}")


def error(text):
    """Print an error message."""
    print(f"  ❌ {color(text, RED)}")


# ============================================================================
# Check functions
# ============================================================================

def check_python():
    """Check Python version."""
    ver = f"{sys.version_info.major}.{sys.version_info.minor}"
    print(f"  Python: {ver} ({sys.executable})")
    if sys.version_info < (3, 8):
        error("Python 3.8+ required. Please upgrade.")
        return False
    success("Python version OK")
    return True


def load_config():
    """Load config.yaml safely."""
    try:
        import yaml
        with open(CONFIG, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}


def fetch_version():
    """Fetch latest version from GitHub."""
    try:
        import yaml
        with urllib.request.urlopen(GITHUB_CONFIG_URL, timeout=5) as resp:
            data = resp.read().decode('utf-8')
        cfg = yaml.safe_load(data)
        return cfg.get('version', '')
    except Exception:
        return ''


def check_version():
    """Check current version vs latest."""
    current_cfg = load_config()
    current_ver = current_cfg.get('version', 'unknown')
    
    latest_ver = fetch_version()
    
    if latest_ver:
        if current_ver != latest_ver:
            warning(f"新版本可用: {latest_ver} (當前: {current_ver})")
            print(f"  請執行: {color('git pull', CYAN)}")
    
    print(f"  版本: {current_ver}")
    return True


def check_dependencies():
    """Check if required modules are installed."""
    missing = []
    
    for module, desc in REQUIRED_MODULES:
        try:
            __import__(module)
        except ImportError:
            missing.append((module, desc))
    
    if not missing:
        success("所有依賴套件已安裝")
        return True
    
    # Try to install missing packages
    warning("發現缺失套件，正在安裝...")
    
    # Check for uv (faster)
    use_uv = shutil.which('uv') is not None
    
    if use_uv:
        print("  使用 uv 安裝...")
        cmd = ['uv', 'pip', 'install', '-r', str(REQUIREMENTS), '--system', '-q']
    else:
        print("  使用 pip 安裝...")
        cmd = [sys.executable, '-m', 'pip', 'install', '-r', str(REQUIREMENTS),
               '--disable-pip-version-check', '-q']
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode == 0:
            success("套件安裝完成")
            return True
        else:
            error("套件安裝失敗")
            print(f"  請手動執行: {color('pip install -r requirements.txt', CYAN)}")
            return False
    except subprocess.TimeoutExpired:
        error("安裝超時")
        return False
    except Exception as e:
        error(f"安裝錯誤: {e}")
        return False


def check_ffmpeg():
    """Check FFmpeg availability."""
    if shutil.which('ffmpeg') is not None:
        success("FFmpeg 已安裝")
        return True
    
    warning("FFmpeg 未安裝")
    print("  這將影響影片生成功能。")
    print(f"  安裝: {color('https://ffmpeg.org/download.html', CYAN)}")
    print("  提示: 您可以稍後安裝，不影響簡報生成功能")
    return False


def check_config():
    """Check and migrate config.yaml."""
    if not CONFIG.exists():
        if CONFIG_EXAMPLE.exists():
            warning("未找到 config.yaml，正在從範本建立...")
            import shutil as sh
            sh.copy2(CONFIG_EXAMPLE, CONFIG)
            success("已建立 config.yaml")
            print("  請編輯 config.yaml 配置您的設定")
            return True
        else:
            error("找不到 config.yaml 範本")
            return False
    
    # Run config migration
    migrator = ROOT / "scripts" / "config_migrator.py"
    if migrator.exists():
        try:
            result = subprocess.run(
                [sys.executable, str(migrator)],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                success("配置已是最新版本")
            else:
                output = result.stdout.strip()
                if output:
                    print(f"  {output}")
        except Exception:
            pass
    
    return True


# ============================================================================
# Main launcher
# ============================================================================

def main():
    """Run the complete launcher sequence."""
    print()
    print("=" * 55)
    print(f"  {color('PPTPlaner AI 簡報助手', BOLD)}")
    print("=" * 55)
    
    steps = [
        ("檢查 Python 環境", check_python),
        ("檢查版本資訊", check_version),
        ("檢查依賴套件", check_dependencies),
        ("檢查 FFmpeg", check_ffmpeg),
        ("檢查配置", check_config),
    ]
    
    for i, (name, func) in enumerate(steps, 1):
        step_header(i, len(steps), name)
        try:
            if not func():
                error(f"{name} 失敗")
                input("\n按 Enter 關閉...")
                return 1
        except Exception as e:
            error(f"{name} 發生錯誤: {e}")
            input("\n按 Enter 關閉...")
            return 1
    
    # Launch UI
    print()
    step_header(6, 6, "啟動 PPTPlaner")
    success("啟動中...")
    print()
    
    # Ensure working directory is project root
    os.chdir(ROOT)
    
    ui_script = ROOT / "run_ui.py"
    if not ui_script.exists():
        error("找不到 run_ui.py")
        input("按 Enter 關閉...")
        return 1
    
    try:
        # Import and run UI directly
        sys.path.insert(0, str(ROOT))
        import run_ui
        run_ui.main()
    except Exception as e:
        error(f"UI 啟動失敗: {e}")
        import traceback
        traceback.print_exc()
        input("按 Enter 關閉...")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
