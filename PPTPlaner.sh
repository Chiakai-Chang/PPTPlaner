#!/usr/bin/env bash
# ===================================================================
#  PPTPlaner Unix Launcher (macOS / Linux)
#  - Sets UTF-8 encoding environment
#  - Appends common local binary paths (Homebrew, npm, local bin) to PATH
#  - Detects Python and runs launcher.py
# ===================================================================

# Set UTF-8 encoding
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8
export PYTHONUTF8=1

# Resolve script directory (cross-platform readlink fallback)
TARGET_FILE=$0
cd "$(dirname "$TARGET_FILE")" || exit 1

echo -e "\033[36m=====================================================\033[0m"
echo -e "\033[36;1m  PPTPlaner AI 簡報智慧助手 (macOS / Linux)\033[0m"
echo -e "\033[36m=====================================================\033[0m"

# ===================================================================
#  Add common local paths to PATH
# ===================================================================
PATHS_TO_ADD=(
    "/opt/homebrew/bin"
    "/usr/local/bin"
    "$HOME/.local/bin"
    "$HOME/Library/Application Support/agy/bin"
    "$HOME/Library/Application Support/Claude/bin"
)

for p in "${PATHS_TO_ADD[@]}"; do
    if [ -d "$p" ]; then
        export PATH="$PATH:$p"
    fi
done

# ===================================================================
#  Detect Python
# ===================================================================
PYTHON_CMD=""
if command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
elif command -v python &>/dev/null; then
    # Double check it is python 3
    if python -c "import sys; sys.exit(0 if sys.version_info.major >= 3 else 1)" &>/dev/null; then
        PYTHON_CMD="python"
    fi
fi

if [ -z "$PYTHON_CMD" ]; then
    echo -e "\033[31;1m=====================================================\033[0m"
    echo -e "\033[31;1m❌ 嚴重錯誤：找不到 Python 3 執行環境！\033[0m"
    echo -e "\033[31;1m=====================================================\033[0m"
    echo ""
    echo "PPTPlaner 簡報助手需要 Python 3.12+ 才能正常運作。"
    echo "請按照以下簡單步驟完成安裝，即可啟動："
    echo ""
    echo "1. 開啟終端機並使用 Homebrew 安裝 (推薦 macOS):"
    echo -e "   \033[36mbrew install python\033[0m"
    echo "   (若無 Homebrew，請前往官網下載安裝檔: https://www.python.org/downloads/)"
    echo "2. Linux 用戶請執行:"
    echo -e "   \033[36msudo apt install python3 python3-pip python3-venv\033[0m"
    echo "3. 安裝完成後，重新執行此啟動腳本即可。"
    echo ""
    echo -e "\033[31;1m=====================================================\033[0m"
    read -p "按任意鍵結束..." -n1 -s
    echo ""
    exit 1
fi

# Run the Python launcher
$PYTHON_CMD launcher.py

# Keep window open on completion
echo ""
read -p "按任意鍵關閉終端機..." -n1 -s
echo ""
