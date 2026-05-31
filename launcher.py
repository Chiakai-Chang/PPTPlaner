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
import hashlib

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
    if sys.version_info < (3, 12):
        error("Python 3.12+ required. Please upgrade.")
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


def get_requirements_hash():
    """Compute SHA-256 hash of requirements.txt."""
    if not REQUIREMENTS.exists():
        return ""
    try:
        content = REQUIREMENTS.read_bytes()
        return hashlib.sha256(content).hexdigest()
    except Exception:
        return ""


def check_dependencies():
    """Check if required modules are installed and up-to-date."""
    hash_file = ROOT / ".venv" / ".installed_requirements_hash"
    current_hash = get_requirements_hash()
    
    # 1. Quick check: do we have the hash and can we import all modules?
    hash_matches = False
    if hash_file.exists() and current_hash:
        try:
            saved_hash = hash_file.read_text(encoding="utf-8").strip()
            if saved_hash == current_hash:
                hash_matches = True
        except Exception:
            pass
            
    # Also verify we can actually import them (in case the venv was modified externally)
    missing = []
    for module, desc in REQUIRED_MODULES:
        try:
            __import__(module)
        except ImportError:
            missing.append((module, desc))
            
    if hash_matches and not missing:
        success("依賴套件已是最新且完整安裝")
        return True
        
    # 2. If not matches or missing, perform installation/update
    if missing:
        warning("發現缺失套件，正在自動安裝中...")
    else:
        warning("檢測到 requirements.txt 已更新，正在同步套件中...")
        
    # Check for uv (faster)
    uv_bin = find_uv()
    
    if uv_bin:
        print("  使用 uv 同步安裝套件...")
        cmd = [uv_bin, 'pip', 'install', '-r', str(REQUIREMENTS), '--python', sys.executable, '-q']
    else:
        print("  使用 pip 安裝/更新套件中 (此步驟僅在首次或套件變更時執行，請稍候)...")
        cmd = [sys.executable, '-m', 'pip', 'install', '-r', str(REQUIREMENTS),
               '--disable-pip-version-check', '-q']
               
    try:
        # Increase timeout to 180 seconds
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        if result.returncode == 0:
            success("套件安裝與同步完成！")
            # Write current hash to hash_file so subsequent runs skip installation
            try:
                hash_file.parent.mkdir(parents=True, exist_ok=True)
                hash_file.write_text(current_hash, encoding="utf-8")
            except Exception:
                pass
            # Re-execute cleanly so Python loads the fresh site-packages
            switch_to_venv(sys.executable)
            return True
        else:
            error("套件安裝失敗")
            print(f"  錯誤詳情:\n{result.stderr}")
            print(f"  請嘗試手動執行: {color('.venv/bin/pip install -r requirements.txt', CYAN)}")
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


def find_uv():
    """Find uv executable on PATH or in common local installation directories."""
    # 1. Check PATH
    uv_path = shutil.which('uv')
    if uv_path:
        return uv_path
        
    # 2. Check common local paths
    home = Path.home()
    candidates = []
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA")
        if appdata:
            candidates.append(Path(appdata) / "astral" / "uv" / "bin" / "uv.exe")
        candidates.append(home / ".local" / "bin" / "uv.exe")
        candidates.append(home / ".cargo" / "bin" / "uv.exe")
    else:
        candidates.append(home / ".local" / "bin" / "uv")
        candidates.append(home / ".cargo" / "bin" / "uv")
        candidates.append(Path("/usr/local/bin/uv"))
        candidates.append(Path("/opt/homebrew/bin/uv"))
        
    for cand in candidates:
        if cand.exists() and os.access(cand, os.X_OK):
            # Inject to PATH in current process
            dir_path = str(cand.parent)
            if dir_path not in os.environ.get("PATH", ""):
                os.environ["PATH"] = f"{dir_path}{os.pathsep}{os.environ.get('PATH', '')}"
            return str(cand)
    return None


def bootstrap_venv():
    """Bootstrap virtual environment using uv or standard venv fallback."""
    # Check if already in venv
    in_venv = (sys.prefix != sys.base_prefix) or (os.environ.get("PPTPLANER_IN_VENV") == "1")
    if in_venv:
        return True

    print()
    print("=" * 55)
    print(f"  {color('PPTPlaner 虛擬環境初始化', BOLD)}")
    print("=" * 55)

    venv_dir = ROOT / ".venv"
    
    # Locate uv
    uv_bin = find_uv()
    
    # If .venv already exists and is valid, switch to it immediately
    if venv_dir.exists():
        if sys.platform == "win32":
            venv_python = venv_dir / "Scripts" / "python.exe"
        else:
            venv_python = venv_dir / "bin" / "python"
        
        if venv_python.exists():
            return switch_to_venv(venv_python)
            
    # If we need to create the venv:
    if not uv_bin:
        # Prompt for uv installation
        print()
        print("  " + color("=" * 65, YELLOW))
        print("  " + color("  檢測到系統尚未安裝 uv ( Astral 開發之超高速 Python 套件管理工具 )", BOLD + YELLOW))
        print("  " + color("=" * 65, YELLOW))
        print("  uv 可以將虛擬環境建立與套件下載時間縮短達 10 倍以上，極度推薦安裝！")
        print()
        print("  [Y] 自動下載並安裝 uv (推薦，享受秒級極速體驗)")
        print("  [N] 保持現狀，改用標準 Python venv & pip (免安裝額外工具，但下載較慢)")
        print()
        try:
            choice = input("  請選擇 [Y/N] (直接按 Enter 預設為 Y): ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            print()
            choice = "n"
            
        if choice in ("", "y", "yes"):
            print(f"\n  正在自動安裝 uv 中...")
            success_installed = False
            try:
                if sys.platform == "win32":
                    cmd = ["powershell", "-ExecutionPolicy", "ByPass", "-Command", "irm https://astral.sh/uv/install.ps1 | iex"]
                    res = subprocess.run(cmd, capture_output=True, text=True)
                else:
                    cmd = ["curl -LsSf https://astral.sh/uv/install.sh | sh"]
                    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                    
                if res.returncode == 0:
                    # Search again
                    uv_bin = find_uv()
                    if uv_bin:
                        success("uv 安裝完成！已自動將 uv 加至 PATH。")
                        success_installed = True
                    else:
                        warning("uv 安裝腳本執行完成，但未能自動檢測到可執行檔。將使用 standard venvFallback。")
                else:
                    warning(f"uv 安裝失敗 (代碼 {res.returncode})。將使用 standard venvFallback。")
                    print(f"  錯誤資訊: {res.stderr.strip()[:200]}")
            except Exception as e:
                warning(f"自動安裝 uv 時發生異常: {e}。將使用 standard venvFallback。")
        else:
            print("\n  已選擇保持現狀，使用標準 Python venv。")
            
    # Now create venv
    if uv_bin:
        print(f"  正在使用 uv 建立虛擬環境 .venv...")
        try:
            res = subprocess.run([uv_bin, "venv", str(venv_dir)], capture_output=True, text=True)
            if res.returncode == 0:
                success("使用 uv 建立虛擬環境成功！")
            else:
                raise RuntimeError(res.stderr)
        except Exception as e:
            warning(f"使用 uv 建立虛擬環境失敗: {e}。嘗試以 standard venv 建立...")
            uv_bin = None  # Fallback
            
    if not uv_bin:
        print(f"  正在使用標準 Python venv 建立虛擬環境 .venv (此步驟可能需要 10-30 秒，請稍候)...")
        try:
            import venv
            venv.create(str(venv_dir), with_pip=True)
            success("使用標準 venv 建立虛擬環境成功！")
        except ImportError:
            error("系統中找不到標準函式庫 'venv'。")
            if sys.platform.startswith("linux"):
                print(f"  請先在系統終端機執行: {color('sudo apt install python3-venv', CYAN)}")
            else:
                print("  請重新安裝 Python，並確保勾選了安裝 pip 與標準工具。")
            return False
        except Exception as e:
            error(f"建立虛擬環境失敗: {e}")
            return False

    # Get python executable in venv
    if sys.platform == "win32":
        venv_python = venv_dir / "Scripts" / "python.exe"
    else:
        venv_python = venv_dir / "bin" / "python"
        
    if not venv_python.exists():
        error(f"找不到虛擬環境中的 Python 執行檔: {venv_python}")
        return False
        
    return switch_to_venv(venv_python)


def switch_to_venv(venv_python):
    """Re-execute the launcher script using virtual environment's Python."""
    print(f"  正在切換至虛擬環境執行...")
    
    new_env = os.environ.copy()
    new_env["PPTPLANER_IN_VENV"] = "1"
    new_env["PYTHONUTF8"] = "1"
    
    try:
        cmd = [str(venv_python), str(Path(__file__).resolve())] + sys.argv[1:]
        res = subprocess.run(cmd, env=new_env)
        sys.exit(res.returncode)
    except Exception as e:
        error(f"無法在虛擬環境中啟動 PPTPlaner: {e}")
        return False


# ============================================================================
# Main launcher
# ============================================================================

def main():
    """Run the complete launcher sequence."""
    if not bootstrap_venv():
        return 1

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
