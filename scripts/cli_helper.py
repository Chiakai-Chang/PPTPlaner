"""CLI Helper — 改進的終端機輸出與用戶體驗."""

from __future__ import annotations

import sys
from pathlib import Path


# ANSI 色彩代碼
COLORS = {
    "reset": "\033[0m",
    "bold": "\033[1m",
    "red": "\033[91m",
    "green": "\033[92m",
    "yellow": "\033[93m",
    "blue": "\033[94m",
    "magenta": "\033[95m",
    "cyan": "\033[96m",
}

# Windows 兼容
if sys.platform == "win32":
    import ctypes
    
    def enable_vt_processing():
        """Enable ANSI escape sequences on Windows."""
        try:
            kernel = ctypes.windll.kernel32
            kernel.SetConsoleMode(kernel.GetStdHandle(-11), 7)
        except Exception:
            pass
    
    enable_vt_processing()


def colorize(text: str, color: str) -> str:
    """Add color to text."""
    if color not in COLORS:
        return text
    return f"{COLORS[color]}{text}{COLORS['reset']}"


def print_header(title: str, width: int = 60) -> None:
    """Print a formatted header."""
    print(f"\n{colorize('=' * width, 'cyan')}")
    print(f"{colorize(title.center(width), 'bold')}")
    print(f"{colorize('=' * width, 'cyan')}")


def print_success(msg: str) -> None:
    """Print a success message."""
    print(f"{colorize('✅', 'green')} {colorize(msg, 'green')}")


def print_error(msg: str, exit_code: int = 1) -> None:
    """Print an error message and exit."""
    print(f"{colorize('❌', 'red')} {colorize(msg, 'red')}")
    sys.exit(exit_code)


def print_warning(msg: str) -> None:
    """Print a warning message."""
    print(f"{colorize('⚠️', 'yellow')} {colorize(msg, 'yellow')}")


def print_info(msg: str) -> None:
    """Print an info message."""
    print(f"{colorize('ℹ️', 'blue')} {colorize(msg, 'blue')}")


def print_progress(current: int, total: int, msg: str = "") -> None:
    """Print a progress indicator."""
    percentage = (current / total) * 100 if total > 0 else 0
    bar_width = 30
    filled = int(bar_width * current / total) if total > 0 else 0
    bar = "█" * filled + "░" * (bar_width - filled)
    
    progress_str = f"{colorize(bar, 'blue')} {percentage:.1f}%"
    print(f"{progress_str} | {colorize(msg, 'cyan')}")


def print_separator(char: str = "─", width: int = 60) -> None:
    """Print a separator line."""
    print(colorize(char * width, 'cyan'))


def print_banner(title: str, subtitle: str = "") -> None:
    """Print a formatted banner."""
    print(f"\n{colorize('╔' + '═' * 50 + '╗', 'cyan')}")
    print(f"{colorize('║', 'cyan')} {colorize(title.center(46), 'bold')} {colorize('║', 'cyan')}")
    if subtitle:
        print(f"{colorize('║', 'cyan')} {colorize(subtitle.center(46), 'yellow')} {colorize('║', 'cyan')}")
    print(f"{colorize('╚' + '═' * 50 + '╝', 'cyan')}")


def print_table(headers: list[str], rows: list[list[str]]) -> None:
    """Print a formatted table."""
    # Calculate column widths
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            if i < len(col_widths):
                col_widths[i] = max(col_widths[i], len(cell))
    
    # Print header
    header_str = " | ".join(h.ljust(w) for h, w in zip(headers, col_widths))
    print(colorize(header_str, 'cyan'))
    print(colorize("-+-".join("-" * w for w in col_widths), 'cyan'))
    
    # Print rows
    for row in rows:
        row_str = " | ".join(str(c).ljust(w) for c, w in zip(row, col_widths))
        print(row_str)


def check_file_exists(path: Path, name: str = "") -> None:
    """Check if a file exists, exit with error if not."""
    if not path.exists():
        error_msg = f"檔案不存在: {path}"
        if name:
            error_msg += f" ({name})"
        print_error(error_msg)


def check_directory_exists(path: Path, name: str = "") -> None:
    """Check if a directory exists, exit with error if not."""
    if not path.exists():
        error_msg = f"目錄不存在: {path}"
        if name:
            error_msg += f" ({name})"
        print_error(error_msg)
