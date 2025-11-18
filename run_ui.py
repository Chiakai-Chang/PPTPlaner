import tkinter as tk
from tkinter import filedialog, scrolledtext, font as tkFont
import subprocess
import sys
import os
import threading
import webbrowser

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PPTPlaner v1.5.1")
        # Set window size and position
        screen_height = self.winfo_screenheight()
        window_height = int(screen_height * 0.7)
        if window_height < 620: window_height = 620
        elif window_height > 850: window_height = 850
        window_width = 750
        center_x = int((self.winfo_screenwidth() / 2) - (window_width / 2))
        center_y = int((screen_height / 2) - (window_height / 2))
        self.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')

        self.source_file_path = tk.StringVar()
        self.slides_file_path = tk.StringVar()

        # --- Layout Structure ---
        footer_frame = tk.Frame(self, bg="#e0e0e0")
        footer_frame.pack(fill="x", side="bottom", pady=5, padx=10)
        main_frame = tk.Frame(self, padx=10, pady=10)
        main_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # --- Populate Footer ---
        hyperlink_font = tkFont.Font(footer_frame, tkFont.nametofont("TkDefaultFont")); hyperlink_font.configure(underline=True)
        info_line1 = tk.Frame(footer_frame, bg=footer_frame["bg"]); info_line1.pack(fill="x")
        tk.Label(info_line1, text="Author: Chiakai Chang", bg=footer_frame["bg"]).pack(side="left", padx=(0,10))
        gh_link = tk.Label(info_line1, text="GitHub", fg="blue", cursor="hand2", font=hyperlink_font, bg=footer_frame["bg"]); gh_link.pack(side="left", padx=5)
        gh_link.bind("<Button-1>", lambda e: self.open_link("https://github.com/Chiakai-Chang/PPTPlaner"))
        li_link = tk.Label(info_line1, text="LinkedIn", fg="blue", cursor="hand2", font=hyperlink_font, bg=footer_frame["bg"]); li_link.pack(side="left", padx=5)
        li_link.bind("<Button-1>", lambda e: self.open_link("https://www.linkedin.com/in/chiakai-chang-htciu"))
        mail_link = tk.Label(info_line1, text="Email", fg="blue", cursor="hand2", font=hyperlink_font, bg=footer_frame["bg"]); mail_link.pack(side="left", padx=5)
        mail_link.bind("<Button-1>", lambda e: self.open_link("mailto:lotifv@gmail.com"))
        tk.Label(footer_frame, text="Copyright © 2025 Chiakai Chang. All Rights Reserved.", font=("Arial", 8), bg=footer_frame["bg"]).pack(fill="x", pady=(5,0))

        # --- Populate Main Frame ---
        controls_frame = tk.Frame(main_frame)
        controls_frame.pack(fill="x")

        tk.Label(controls_frame, text="原文書檔案 (必要):").grid(row=0, column=0, sticky="w", pady=2)
        tk.Entry(controls_frame, textvariable=self.source_file_path, width=80).grid(row=1, column=0, padx=(0, 5), columnspan=2, sticky="ew")
        tk.Button(controls_frame, text="瀏覽...", command=self.browse_source_file).grid(row=1, column=2)

        tk.Label(controls_frame, text="已存在的簡報檔案 (選填):").grid(row=2, column=0, sticky="w", pady=2)
        tk.Entry(controls_frame, textvariable=self.slides_file_path, width=80).grid(row=3, column=0, padx=(0, 5), columnspan=2, sticky="ew")
        tk.Button(controls_frame, text="瀏覽...", command=self.browse_slides_file).grid(row=3, column=2)
        
        tk.Label(controls_frame, text="客製化需求 (選填):").grid(row=4, column=0, sticky="w", pady=(10, 2))
        self.custom_instruction_text = tk.Text(controls_frame, height=3, width=80, wrap=tk.WORD)
        self.custom_instruction_text.grid(row=5, column=0, padx=(0,5), columnspan=3, sticky="ew")

        # --- Reworks Frame ---
        rework_frame = tk.Frame(controls_frame)
        rework_frame.grid(row=6, column=0, columnspan=3, sticky="w", pady=5)
        tk.Label(rework_frame, text="最大修正次數 (0-10):").pack(side="left", padx=(0, 10))
        tk.Label(rework_frame, text="簡報:").pack(side="left", padx=(0, 5))
        self.slide_reworks_spinbox = tk.Spinbox(rework_frame, from_=0, to=10, width=5, justify="center")
        self.slide_reworks_spinbox.pack(side="left", padx=(0, 15))
        self.slide_reworks_spinbox.delete(0, "end"); self.slide_reworks_spinbox.insert(0, "5")
        tk.Label(rework_frame, text="備忘稿:").pack(side="left", padx=(0, 5))
        self.memo_reworks_spinbox = tk.Spinbox(rework_frame, from_=0, to=10, width=5, justify="center")
        self.memo_reworks_spinbox.pack(side="left")
        self.memo_reworks_spinbox.delete(0, "end"); self.memo_reworks_spinbox.insert(0, "5")
        controls_frame.grid_columnconfigure(0, weight=1)

        self.run_button = tk.Button(main_frame, text="開始生成", command=self.run_orchestration, font=("Arial", 12, "bold"), bg="#c0d8f0")
        self.run_button.pack(pady=15, fill="x", ipady=5)

        tk.Label(main_frame, text="執行進度:").pack(fill="x", anchor="w")
        self.console = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, state="disabled", bg="#f5f5f5")
        self.console.pack(pady=5, fill="both", expand=True)

    def open_link(self, url): webbrowser.open_new_tab(url)
    def browse_source_file(self): 
        filepath = filedialog.askopenfilename(title="選擇原文書檔案", filetypes=(("Markdown & Text", "*.md *.txt"), ("All files", "*.*")))
        if filepath:
            try:
                # Try to make it a relative path
                display_path = os.path.relpath(filepath)
            except ValueError:
                # If it fails (e.g., different drives), use the absolute path
                display_path = os.path.abspath(filepath)
            self.source_file_path.set(display_path)

    def browse_slides_file(self): 
        filepath = filedialog.askopenfilename(title="選擇簡報檔案", filetypes=(("Markdown & Text", "*.md *.txt"), ("All files", "*.*")))
        if filepath:
            try:
                display_path = os.path.relpath(filepath)
            except ValueError:
                display_path = os.path.abspath(filepath)
            self.slides_file_path.set(display_path)
    def log_message(self, message): self.console.config(state="normal"); self.console.insert(tk.END, message); self.console.see(tk.END); self.console.config(state="disabled"); self.update_idletasks()
    def run_in_thread(self, command): 
        with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace', bufsize=1, universal_newlines=True) as process:
            for line in iter(process.stdout.readline, ''): print(line, end=''); self.log_message(line)
        self.log_message("\n====================\n"); 
        if process.returncode == 0: self.log_message("執行成功！\n")
        else: self.log_message(f"執行失敗，返回碼：{process.returncode}\n")
        self.run_button.config(state="normal", text="開始生成")

    def run_orchestration(self):
        source_file = self.source_file_path.get()
        slides_file = self.slides_file_path.get()
        custom_instruction = self.custom_instruction_text.get("1.0", tk.END).strip()
        slide_reworks = self.slide_reworks_spinbox.get()
        memo_reworks = self.memo_reworks_spinbox.get()

        if not source_file:
            self.log_message("錯誤：請務必選擇原文書檔案。\n")
            return
        
        orchestrate_script = os.path.join("scripts", "orchestrate.py")
        if not os.path.exists(orchestrate_script):
            self.log_message(f"錯誤：找不到主腳本 {orchestrate_script}。\n")
            return

        command = [sys.executable, orchestrate_script, "--source", source_file]
        if custom_instruction: command.extend(["--custom-instruction", custom_instruction])
        if slides_file: command.extend(["--plan-from-slides", slides_file])
        
        # Add rework counts if they are valid integers
        try:
            if int(slide_reworks) >= 0: command.extend(["--slide-reworks", slide_reworks])
        except ValueError:
            self.log_message("警告：簡報修正次數不是有效的數字，將使用預設值。\n")
        
        try:
            if int(memo_reworks) >= 0: command.extend(["--memo-reworks", memo_reworks])
        except ValueError:
            self.log_message("警告：備忘稿修正次數不是有效的數字，將使用預設值。\n")

        self.console.config(state="normal"); self.console.delete('1.0', tk.END); self.console.config(state="disabled")
        self.run_button.config(state="disabled", text="執行中...")

        try:
            thread = threading.Thread(target=self.run_in_thread, args=(command,)); thread.start()
        except Exception as e:
            self.log_message(f"啟動程序時發生錯誤: {e}\n"); self.run_button.config(state="normal", text="開始生成")

if __name__ == "__main__":
    app = App()
    app.mainloop()
