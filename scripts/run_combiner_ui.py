import tkinter as tk
from tkinter import filedialog, scrolledtext, font
from pathlib import Path
import subprocess
import threading
import sys

# --- Constants ---
# Get the root directory of the script (or the bundled executable)
if getattr(sys, 'frozen', False):
    ROOT = Path(sys.executable).resolve().parent
else:
    ROOT = Path(__file__).resolve().parent

SCRIPTS_DIR = ROOT / "scripts"
COMBINER_SCRIPT_PATH = SCRIPTS_DIR / "combine_slides.py"
if sys.platform == "win32":
    VENV_PYTHON_EXE = ROOT / ".venv" / "Scripts" / "python.exe"
else:
    VENV_PYTHON_EXE = ROOT / ".venv" / "bin" / "python"
PYTHON_EXE = str(VENV_PYTHON_EXE) if VENV_PYTHON_EXE.exists() else "python"

# --- Main Application Class ---
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("投影片合併工具 (Slide Combiner)")
        self.geometry("700x450")
        self.minsize(500, 300)

        # --- Style ---
        default_font = font.nametofont("TkDefaultFont")
        default_font.configure(family="Arial", size=10)
        self.option_add("*Font", default_font)

        # --- Widgets ---
        self.main_frame = tk.Frame(self, padx=15, pady=15)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        self.main_frame.grid_rowconfigure(1, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        self.select_button = tk.Button(
            self.main_frame,
            text="📂 選擇要合併的 'slides' 資料夾",
            font=("Arial", 12, "bold"),
            command=self.select_folder_and_run,
            pady=10
        )
        self.select_button.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        self.output_text = scrolledtext.ScrolledText(
            self.main_frame,
            wrap=tk.WORD,
            state="disabled",
            bg="#f5f5f5",
            font=("Courier New", 10),
            bd=1,
            relief="solid"
        )
        self.output_text.grid(row=1, column=0, sticky="nsew")

        # --- Pre-flight Checks ---
        self.log("="*60)
        self.log("  歡迎使用 PPTPlaner 投影片合併工具！")
        self.log("="*60)

        if not COMBINER_SCRIPT_PATH.exists():
            self.log("❌ 嚴重錯誤：找不到核心合併腳本！")
            self.log(f"   請確認 'scripts/combine_slides.py' 檔案存在於專案中。")
            self.select_button.config(state="disabled", text="❌ 核心檔案遺失")
        elif str(PYTHON_EXE) == "python" and not VENV_PYTHON_EXE.exists():
             self.log("⚠️ 警告：未找到 .venv 中的 Python 環境。")
             self.log("   腳本將嘗試使用系統預設的 'python'。")
             self.log("   如果合併失敗，請先執行 'START_HERE.bat' 以建立虛擬環境。")
             self.log("▶ 請點擊上方按鈕，選擇一個 'slides' 資料夾。")
        else:
            self.log("▶ 請點擊上方按鈕，選擇一個 'slides' 資料夾。")
            self.log("▶ 腳本會將所有投影片按數字順序合併成一個檔案。")

    def log(self, message: str):
        """Thread-safe method to append a message to the output text widget."""
        def _log():
            self.output_text.config(state="normal")
            self.output_text.insert(tk.END, message + "\n")
            self.output_text.see(tk.END) # Auto-scroll
            self.output_text.config(state="disabled")
        self.after(0, _log)

    def select_folder_and_run(self):
        """Opens a dialog to select a folder and then runs the combiner script."""
        initial_dir = ROOT / "output"
        folder_path = filedialog.askdirectory(
            title="請選擇一個 'slides' 資料夾",
            initialdir=initial_dir if initial_dir.exists() else ROOT
        )

        if not folder_path:
            self.log("\n🟡 操作已取消。")
            return

        self.log("\n" + "="*60)
        self.log(f"📂 已選擇資料夾: {folder_path}")
        self.log("🚀 開始執行合併腳本...")
        self.select_button.config(state="disabled", text="⏳ 處理中，請稍候...")

        # Run the script in a separate thread to avoid freezing the GUI
        thread = threading.Thread(
            target=self.run_script_in_thread,
            args=(folder_path,),
            daemon=True
        )
        thread.start()

    def run_script_in_thread(self, folder_path: str):
        """The actual script execution logic to be run in a thread."""
        try:
            command = [
                PYTHON_EXE,
                str(COMBINER_SCRIPT_PATH),
                folder_path
            ]

            # For Windows, hide the console window that subprocess might create
            popen_kwargs = {
                "stdout": subprocess.PIPE,
                "stderr": subprocess.STDOUT,
                "text": True,
                "encoding": "utf-8",
            }
            if sys.platform == "win32":
                popen_kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

            process = subprocess.Popen(command, **popen_kwargs)

            # Read and log output line by line in real-time
            for line in iter(process.stdout.readline, ''):
                self.log(line.strip())
            
            process.wait() # Wait for the process to complete
            
            if process.returncode != 0:
                 self.log(f"\n❌ 腳本執行出錯 (Exit Code: {process.returncode})。")

        except FileNotFoundError:
            self.log(f"\n❌ 嚴重錯誤：找不到執行檔 '{PYTHON_EXE}' 或腳本 '{COMBINER_SCRIPT_PATH}'。")
            self.log("   請確認專案結構是否完整。")
        except Exception as e:
            self.log(f"\n❌ 執行時發生未預期的錯誤: {e}")
        finally:
            # Re-enable the button on the main thread
            self.after(0, lambda: self.select_button.config(state="normal", text="📂 選擇要合併的 'slides' 資料夾"))

# --- Main Execution ---
if __name__ == "__main__":
    app = App()
    app.mainloop()
