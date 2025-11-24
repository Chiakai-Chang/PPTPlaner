import os
import re
import sys
import subprocess
import threading
import webbrowser
import tkinter as tk
from tkinter import filedialog, scrolledtext, font as tkFont, ttk

import requests

version = "v2.3"

class App(tk.Tk):
    def __init__(self, available_models):
        super().__init__()
        self.available_gemini_models = available_models
        self.title(f"PPTPlaner {version}")
        # Set window size and position
        screen_height = self.winfo_screenheight()
        window_height = int(screen_height * 0.7)
        if window_height < 620: window_height = 620
        elif window_height > 850: window_height = 850
        window_width = 750
        center_x = int((self.winfo_screenwidth() / 2) - (window_width / 2))
        center_y = int((screen_height / 2) - (window_height / 2))
        self.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')

        # --- Initialize instance variables ---
        self.available_gemini_models = available_models
        self.source_file_path = tk.StringVar()
        self.slides_file_path = tk.StringVar()
        self.generate_svg = tk.BooleanVar(value=False) # Add this line
        self.quota_event = threading.Event()
        self.quota_event.set() # Initially, no quota error, so allow to proceed
        self.current_gemini_model = None # Stores the currently selected Gemini model. None means default.

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
        # --- Mode Selection ---
        self.mode_selection = tk.StringVar(value="new_generation")
        mode_selection_frame = tk.Frame(main_frame)
        mode_selection_frame.pack(fill="x", pady=(10, 5))
        tk.Label(mode_selection_frame, text="選擇操作模式:").pack(side="left", padx=(0, 10))
        tk.Radiobutton(mode_selection_frame, text="全新生成", variable=self.mode_selection, value="new_generation", command=self.toggle_mode_inputs).pack(side="left", padx=5)
        tk.Radiobutton(mode_selection_frame, text="接續生成 SVG", variable=self.mode_selection, value="resume", command=self.toggle_mode_inputs).pack(side="left", padx=5)

        # --- Resume Specific Inputs ---
        self.resume_output_dir_frame = tk.Frame(main_frame) 
        tk.Label(self.resume_output_dir_frame, text="選擇現有輸出資料夾 (用於接續生成):").grid(row=0, column=0, columnspan=3, sticky="w", pady=2)
        self.resume_output_dir_path = tk.StringVar()
        tk.Entry(self.resume_output_dir_frame, textvariable=self.resume_output_dir_path, width=80).grid(row=1, column=0, padx=(0, 5), columnspan=2, sticky="ew")
        tk.Button(self.resume_output_dir_frame, text="瀏覽...", command=self.browse_resume_output_dir).grid(row=1, column=2)
        
        # Add model selection for resume mode
        tk.Label(self.resume_output_dir_frame, text="選擇 Gemini 模型:").grid(row=2, column=0, columnspan=3, sticky="w", pady=(10,2))
        self.resume_gemini_model_var = tk.StringVar(value=self.available_gemini_models[0] if self.available_gemini_models else "")
        self.resume_model_combobox = ttk.Combobox(self.resume_output_dir_frame, textvariable=self.resume_gemini_model_var, values=self.available_gemini_models, state="readonly", width=30)
        self.resume_model_combobox.grid(row=3, column=0, columnspan=2, sticky="w", pady=2)

        self.resume_output_dir_frame.grid_columnconfigure(0, weight=1)

        # --- New Generation Controls ---
        self.new_generation_controls_frame = tk.Frame(main_frame)
        tk.Label(self.new_generation_controls_frame, text="原文書檔案 (必要):").grid(row=0, column=0, sticky="w", pady=2)
        tk.Entry(self.new_generation_controls_frame, textvariable=self.source_file_path, width=80).grid(row=1, column=0, padx=(0, 5), columnspan=2, sticky="ew")
        tk.Button(self.new_generation_controls_frame, text="瀏覽...", command=self.browse_source_file).grid(row=1, column=2)
        tk.Label(self.new_generation_controls_frame, text="已存在的簡報檔案 (選填):").grid(row=2, column=0, sticky="w", pady=2)
        tk.Entry(self.new_generation_controls_frame, textvariable=self.slides_file_path, width=80).grid(row=3, column=0, padx=(0, 5), columnspan=2, sticky="ew")
        tk.Button(self.new_generation_controls_frame, text="瀏覽...", command=self.browse_slides_file).grid(row=3, column=2)
        tk.Label(self.new_generation_controls_frame, text="客製化需求 (選填):").grid(row=4, column=0, sticky="w", pady=(10, 2))
        self.custom_instruction_text = tk.Text(self.new_generation_controls_frame, height=3, width=80, wrap=tk.WORD)
        self.custom_instruction_text.grid(row=5, column=0, padx=(0,5), columnspan=3, sticky="ew")

        # --- Gemini Model Selection ---
        model_selection_frame = tk.Frame(self.new_generation_controls_frame)
        model_selection_frame.grid(row=6, column=0, columnspan=3, sticky="w", pady=5)
        tk.Label(model_selection_frame, text="選擇 Gemini 模型:").pack(side="left", padx=(0, 10))
        self.initial_gemini_model_var = tk.StringVar(value=self.available_gemini_models[0] if self.available_gemini_models else "")
        self.initial_model_combobox = ttk.Combobox(model_selection_frame, textvariable=self.initial_gemini_model_var, values=self.available_gemini_models, state="readonly", width=30)
        self.initial_model_combobox.pack(side="left")

        # --- Reworks Frame ---
        rework_frame = tk.Frame(self.new_generation_controls_frame)
        rework_frame.grid(row=7, column=0, columnspan=3, sticky="w", pady=5)
        tk.Label(rework_frame, text="最大修正次數 (0-10):").pack(side="left", padx=(0, 10))
        tk.Label(rework_frame, text="簡報:").pack(side="left", padx=(0, 5))
        self.slide_reworks_spinbox = tk.Spinbox(rework_frame, from_=0, to=10, width=5, justify="center")
        self.slide_reworks_spinbox.pack(side="left", padx=(0, 15))
        self.slide_reworks_spinbox.delete(0, "end"); self.slide_reworks_spinbox.insert(0, "5")
        tk.Label(rework_frame, text="備忘稿:").pack(side="left", padx=(0, 5))
        self.memo_reworks_spinbox = tk.Spinbox(rework_frame, from_=0, to=10, width=5, justify="center")
        self.memo_reworks_spinbox.pack(side="left")
        self.memo_reworks_spinbox.delete(0, "end"); self.memo_reworks_spinbox.insert(0, "5")

        # --- SVG Generation Checkbox ---
        options_frame = tk.Frame(self.new_generation_controls_frame)
        options_frame.grid(row=8, column=0, columnspan=3, sticky="w", pady=5)
        self.svg_checkbox = tk.Checkbutton(options_frame, text="生成 SVG (實驗性功能，會增加 token 用量)", variable=self.generate_svg)
        self.svg_checkbox.pack(side="left")

        self.new_generation_controls_frame.grid_columnconfigure(0, weight=1)

        # Common elements packing will be handled by toggle_mode_inputs to ensure correct order
        self.run_button = tk.Button(main_frame, text="開始生成", command=self.run_orchestration, font=("Arial", 12, "bold"), bg="#c0d8f0")
        self.progress_label = tk.Label(main_frame, text="執行進度:")
        self.console = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, state="disabled", bg="#f5f5f5")

        # Initial toggle to set correct visibility
        self.toggle_mode_inputs()


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

    def browse_resume_output_dir(self):
        dirpath = filedialog.askdirectory(title="選擇現有輸出資料夾")
        if dirpath:
            try:
                display_path = os.path.relpath(dirpath)
            except ValueError:
                display_path = os.path.abspath(dirpath)
            self.resume_output_dir_path.set(display_path)

    def toggle_mode_inputs(self):
        # Forget common elements to ensure correct packing order later
        self.run_button.pack_forget()
        self.progress_label.pack_forget()
        self.console.pack_forget()

        selected_mode = self.mode_selection.get()
        if selected_mode == "new_generation":
            self.new_generation_controls_frame.pack(fill="x")
            self.resume_output_dir_frame.pack_forget()
        else: # selected_mode == "resume"
            self.new_generation_controls_frame.pack_forget()
            self.resume_output_dir_frame.pack(fill="x")

        # Pack common elements after the mode-specific frame
        self.run_button.pack(pady=15, fill="x", ipady=5)
        self.progress_label.pack(fill="x", anchor="w")
        self.console.pack(pady=5, fill="both", expand=True)

    def log_message(self, message): self.console.config(state="normal"); self.console.insert(tk.END, message); self.console.see(tk.END); self.console.config(state="disabled"); self.update_idletasks()
    def _show_quota_dialog(self, quota_reset_time: str | None = None): # Add parameter
        # Log to console as well
        self.log_message("\n====================\n")
        self.log_message("API配額已耗盡！請等待配額重置或更換帳戶。\n")
        if quota_reset_time:
            self.log_message(f"預計配額將在 {quota_reset_time} 後重置。\n")
        self.log_message("點擊 '繼續' 或 '切換模型並繼續' 後程序將嘗試繼續運行。\n")
        self.log_message("====================\n")

        # Create a Toplevel window for the dialog
        dialog = tk.Toplevel(self)
        dialog.title("API 配額錯誤")
        dialog.transient(self) # Make dialog transient to its parent
        dialog.grab_set() # Make dialog modal

        message = "Gemini API 配額已耗盡。\n"
        if quota_reset_time:
            message += f"預計配額將在 {quota_reset_time} 後重置。\n"
        else:
            message += "您的配額將在一段時間後重置。\n"
        
        message += (
            "您可以選擇等待配額恢復，或嘗試切換到不同的 Gemini 模型。\n"
            "點擊 '繼續' 將使用當前模型重試；\n"
            "選擇一個模型並點擊 '切換模型並繼續' 將嘗試使用新模型。"
        )
        tk.Label(dialog, text=message, padx=20, pady=10, justify=tk.LEFT).pack()

        # Model selection dropdown
        model_frame = tk.Frame(dialog)
        model_frame.pack(pady=5)
        tk.Label(model_frame, text="選擇 Gemini 模型:").pack(side=tk.LEFT, padx=5)
        
        self.selected_gemini_model_var = tk.StringVar(value=self.current_gemini_model if self.current_gemini_model else self.available_gemini_models[0])
        self.model_combobox = ttk.Combobox(model_frame, textvariable=self.selected_gemini_model_var, values=self.available_gemini_models, state="readonly")
        self.model_combobox.pack(side=tk.LEFT, padx=5)

        # Continue button (for current model)
        continue_button = tk.Button(dialog, text="繼續 (使用當前模型)", command=lambda: self._on_continue_from_quota(dialog, use_selected_model=False))
        continue_button.pack(pady=(10, 5))

        # Switch Model and Continue button
        switch_model_button = tk.Button(dialog, text="切換模型並繼續", command=lambda: self._on_continue_from_quota(dialog, use_selected_model=True))
        switch_model_button.pack(pady=(0, 10))

        # Center the dialog
        self.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - (dialog.winfo_width() // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")

        self.wait_window(dialog) # Wait until the dialog is closed

    def _on_continue_from_quota(self, dialog, use_selected_model: bool):
        if use_selected_model:
            selected_model = self.selected_gemini_model_var.get()
            self.current_gemini_model = selected_model
            self.log_message(f"已選擇切換至模型: {self.current_gemini_model}\n")
        else:
            self.log_message("將使用當前模型重試。\n")
        
        dialog.destroy()
        self.quota_event.set() # Allow the background thread to continue

    def run_in_thread(self, command):
        # Always set the event before starting a new execution block to ensure it's unblocked initially
        self.quota_event.set()
        quota_reset_time_str = None # Initialize outside loop
        
        with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace', bufsize=1, universal_newlines=True) as process:
            for line in iter(process.stdout.readline, ''):
                print(line, end='')
                self.log_message(line)
                
                # Check for API quota error and extract time
                quota_match = re.search(r"Your quota will reset after ([\w\d:]+).", line)
                if quota_match:
                    quota_reset_time_str = quota_match.group(1)

                if "Error when talking to Gemini API" in line and "You have exhausted your capacity on this model" in line:
                    self.quota_event.clear() # Block the thread
                    # Call the dialog in the main thread using after to avoid blocking the GUI
                    self.after(0, lambda: self._show_quota_dialog(quota_reset_time_str))
                    self.quota_event.wait() # Wait for the user to click 'Continue' in the dialog
        
        # Explicitly wait for the process to terminate and get the return code
        return_code = process.wait()

        self.log_message("\n====================\n");
        if return_code == 0:
            self.log_message("執行成功！\n")
        else:
            self.log_message(f"執行失敗，返回碼：{return_code}\n")
        self.run_button.config(state="normal", text="開始生成")

    def run_orchestration(self):
        selected_mode = self.mode_selection.get()
        command = []

        # Set the current model from the initial selection
        if selected_mode == "new_generation":
            self.current_gemini_model = self.initial_gemini_model_var.get()
        elif selected_mode == "resume":
            self.current_gemini_model = self.resume_gemini_model_var.get()

        if selected_mode == "new_generation":
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
            if not self.generate_svg.get():
                command.append("--no-svg")
            if custom_instruction: command.extend(["--custom-instruction", custom_instruction])
            if slides_file: command.extend(["--plan-from-slides", slides_file])
            if self.current_gemini_model: command.extend(["--gemini-model", self.current_gemini_model])

            
            # Add rework counts if they are valid integers
            try:
                if int(slide_reworks) >= 0: command.extend(["--slide-reworks", slide_reworks])
            except ValueError:
                self.log_message("警告：簡報修正次數不是有效的數字，將使用預設值。\n")
            
            try:
                if int(memo_reworks) >= 0: command.extend(["--memo-reworks", memo_reworks])
            except ValueError:
                self.log_message("警告：備忘稿修正次數不是有效的數字，將使用預設值。\n")

        elif selected_mode == "resume":
            resume_output_dir = self.resume_output_dir_path.get()
            if not resume_output_dir:
                self.log_message("錯誤：請務必選擇現有輸出資料夾。\n")
                return
            if not os.path.isdir(resume_output_dir):
                self.log_message(f"錯誤：資料夾 '{resume_output_dir}' 不存在或無效。\n")
                return
            
            resume_script = os.path.join("scripts", "resume_svg_generation.py")
            if not os.path.exists(resume_script):
                self.log_message(f"錯誤：找不到接續腳本 {resume_script}。\n")
                return
            
            command = [sys.executable, resume_script, "--output-dir", resume_output_dir]
            if self.current_gemini_model: command.extend(["--gemini-model", self.current_gemini_model])

        
        if not command:
            self.log_message("錯誤：無法建構執行指令。\n")
            return
        
        self.console.config(state="normal"); self.console.delete('1.0', tk.END); self.console.config(state="disabled")
        self.run_button.config(state="disabled", text="執行中...")

        try:
            thread = threading.Thread(target=self.run_in_thread, args=(command,)); thread.start()
        except Exception as e:
            self.log_message(f"啟動程序時發生錯誤: {e}\n"); self.run_button.config(state="normal", text="開始生成")

def fetch_available_models():
    """Fetches available Gemini model names from the gemini-cli GitHub documentation."""
    print("正在從 GitHub 官方文件讀取可用的 Gemini 模型，請稍候...")
    # I've updated the URL to the 'main' branch for the latest version.
    model_url = "https://raw.githubusercontent.com/google-gemini/gemini-cli/main/docs/cli/model.md"
    try:
        response = requests.get(model_url, timeout=30, verify=False)
        response.raise_for_status()
        
        # Find all strings that look like gemini model IDs (e.g., gemini-2.5-pro)
        models = set(re.findall(r'gemini-[\w\.-]+', response.text))
        models = sorted(list(models))
        models = [m for m in models if m[-3:] != ".md"]
        
        if models:
            sorted_models = sorted(list(models))
            print(f"模型讀取完成。可用的模型: {', '.join(sorted_models)}")
            return sorted_models
        else:
            print("在文件中未找到匹配的模型名稱。")

    except requests.exceptions.RequestException as e:
        print(f"無法從網路讀取模型列表: {e}")
    except Exception as e:
        print(f"解析模型列表時發生未知錯誤: {e}")
    
    print("將使用預設的模型列表。")
    return [
        "gemini-2.5-flash-lite",
        "gemini-2.5-flash",
        "gemini-2.5-pro",
    ]

if __name__ == "__main__":
    available_models = fetch_available_models()
    app = App(available_models=available_models)
    app.mainloop()
