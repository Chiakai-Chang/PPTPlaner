import tkinter as tk
from tkinter import filedialog, scrolledtext
import subprocess
import sys
import os
import threading

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PPTPlaner UI Launcher")
        self.geometry("700x500")

        self.source_file_path = tk.StringVar()
        self.slides_file_path = tk.StringVar()

        main_frame = tk.Frame(self, padx=10, pady=10)
        main_frame.pack(fill="x", padx=10, pady=5)

        tk.Label(main_frame, text="原文書檔案 (必要):").grid(row=0, column=0, sticky="w", pady=2)
        tk.Entry(main_frame, textvariable=self.source_file_path, width=70).grid(row=1, column=0, padx=(0, 5))
        tk.Button(main_frame, text="瀏覽...", command=self.browse_source_file).grid(row=1, column=1)

        tk.Label(main_frame, text="已存在的簡報檔案 (選填):").grid(row=2, column=0, sticky="w", pady=2)
        tk.Entry(main_frame, textvariable=self.slides_file_path, width=70).grid(row=3, column=0, padx=(0, 5))
        tk.Button(main_frame, text="瀏覽...", command=self.browse_slides_file).grid(row=3, column=1)

        self.run_button = tk.Button(self, text="開始生成", command=self.run_orchestration, font=("Arial", 12, "bold"), bg="lightblue")
        self.run_button.pack(pady=10, fill="x", padx=10)

        tk.Label(self, text="執行進度:").pack(fill="x", padx=10, anchor="w")
        self.console = scrolledtext.ScrolledText(self, height=15, wrap=tk.WORD, state="disabled", bg="#f0f0f0")
        self.console.pack(pady=10, padx=10, fill="both", expand=True)

    def browse_source_file(self):
        filepath = filedialog.askopenfilename(
            title="選擇原文書檔案",
            filetypes=(("Markdown & Text", "*.md *.txt"), ("All files", "*.*"))
        )
        if filepath:
            self.source_file_path.set(os.path.relpath(filepath))

    def browse_slides_file(self):
        filepath = filedialog.askopenfilename(
            title="選擇簡報檔案",
            filetypes=(("Markdown & Text", "*.md *.txt"), ("All files", "*.*"))
        )
        if filepath:
            self.slides_file_path.set(os.path.relpath(filepath))

    def log_message(self, message):
        self.console.config(state="normal")
        self.console.insert(tk.END, message)
        self.console.see(tk.END)
        self.console.config(state="disabled")
        self.update_idletasks()

    def run_in_thread(self, command):
        with subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            errors='replace',
            bufsize=1,
            universal_newlines=True
        ) as process:
            for line in iter(process.stdout.readline, ''):
                print(line, end='')
                self.log_message(line)
        
        self.log_message("\n====================\n")
        if process.returncode == 0:
            self.log_message("執行成功！\n")
        else:
            self.log_message(f"執行失敗，返回碼：{process.returncode}\n")
        
        self.run_button.config(state="normal", text="開始生成")

    def run_orchestration(self):
        source_file = self.source_file_path.get()
        slides_file = self.slides_file_path.get()

        if not source_file:
            self.log_message("錯誤：請務必選擇原文書檔案。\n")
            return

        orchestrate_script = os.path.join("scripts", "orchestrate.py")
        if not os.path.exists(orchestrate_script):
            self.log_message(f"錯誤：找不到主腳本 {orchestrate_script}。\n")
            return

        command = [sys.executable, orchestrate_script, "--source", source_file]

        self.console.config(state="normal")
        self.console.delete('1.0', tk.END)
        self.console.config(state="disabled")
        self.run_button.config(state="disabled", text="執行中...")

        try:
            if slides_file:
                self.log_message("偵測到已選取簡報檔案，將執行『AI智慧分頁』並生成備忘稿...\n")
                command.extend(["--plan-from-slides", slides_file])
            else:
                self.log_message("將執行「生成簡報+備忘稿」的完整流程...\n")
                command.append("--force")

            thread = threading.Thread(target=self.run_in_thread, args=(command,))
            thread.start()

        except Exception as e:
            self.log_message(f"啟動程序時發生錯誤: {e}\n")
            self.run_button.config(state="normal", text="開始生成")

if __name__ == "__main__":
    app = App()
    app.mainloop()
