import os
import re
import sys
import shutil
import subprocess
import threading
import webbrowser
import tkinter as tk
from tkinter import filedialog, scrolledtext, font as tkFont, ttk, messagebox
import base64
import mimetypes

import requests
import yaml
from pathlib import Path

# Ensure project root is in Python path for agent imports
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# version = "v3.3" # Removed hardcoded version

class App(tk.Tk):
    def __init__(self, available_models):
        super().__init__()
        self.available_gemini_models = available_models
        # Agent types supported
        self.agent_types = ["antigravity", "claude", "openai-compatible", "openai"]
        
        # Load version from config.yaml
        config_path = Path(__file__).resolve().parents[0] / "config.yaml"
        cfg = {}
        if config_path.exists():
            try:
                cfg = yaml.safe_load(config_path.read_text(encoding="utf-8"))
            except Exception as e:
                print(f"Error loading config.yaml for version: {e}")
        self.version = cfg.get("version", "Unknown") # Default to Unknown if not found
        
        self.title(f"PPTPlaner {self.version}")
        # Set window size and position
        screen_height = self.winfo_screenheight()
        window_height = int(screen_height * 0.8) # Increased height for the new list view
        if window_height < 700: window_height = 700
        elif window_height > 900: window_height = 900
        window_width = 800 # Increased width
        center_x = int((self.winfo_screenwidth() / 2) - (window_width / 2))
        center_y = int((screen_height / 2) - (window_height / 2))
        self.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')

        # --- Initialize instance variables ---
        self.available_gemini_models = available_models
        self.source_file_path = tk.StringVar()
        self.slides_file_path = tk.StringVar()
        self.input_doc_title = tk.StringVar()
        self.input_doc_author = tk.StringVar()
        self.input_source_url = tk.StringVar()
        self.generate_svg = tk.BooleanVar(value=False)
        self.quota_event = threading.Event()
        self.quota_event.set()
        self.current_gemini_model = None
        
        # Variables for Image Embedding Mode
        self.guide_html_path = tk.StringVar()
        self.slide_image_map = {} # Dictionary to store slide_id -> image_path
        self.slide_rows_frame = None # Frame inside canvas

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
        tk.Label(footer_frame, text="Copyright © 2026 Chiakai Chang. All Rights Reserved.", font=("Arial", 8), bg=footer_frame["bg"]).pack(fill="x", pady=(5,0))

        # --- Populate Main Frame ---
        # --- Mode Selection ---
        self.mode_selection = tk.StringVar(value="new_generation")
        mode_selection_frame = tk.Frame(main_frame)
        mode_selection_frame.pack(fill="x", pady=(10, 5))
        tk.Label(mode_selection_frame, text="選擇操作模式:").pack(side="left", padx=(0, 10))
        tk.Radiobutton(mode_selection_frame, text="全新生成", variable=self.mode_selection, value="new_generation", command=self.toggle_mode_inputs).pack(side="left", padx=5)
        tk.Radiobutton(mode_selection_frame, text="接續生成 SVG", variable=self.mode_selection, value="resume", command=self.toggle_mode_inputs).pack(side="left", padx=5)
        tk.Radiobutton(mode_selection_frame, text="製作圖文簡報 (HTML)", variable=self.mode_selection, value="embed_images", command=self.toggle_mode_inputs).pack(side="left", padx=5)

        # --- Resume Specific Inputs ---
        self.resume_output_dir_frame = tk.Frame(main_frame) 
        tk.Label(self.resume_output_dir_frame, text="選擇現有輸出資料夾 (用於接續生成): ").grid(row=0, column=0, columnspan=3, sticky="w", pady=2)
        self.resume_output_dir_path = tk.StringVar()
        tk.Entry(self.resume_output_dir_frame, textvariable=self.resume_output_dir_path, width=80).grid(row=1, column=0, padx=(0, 5), columnspan=2, sticky="ew")
        tk.Button(self.resume_output_dir_frame, text="瀏覽...", command=self.browse_resume_output_dir).grid(row=1, column=2)
        
        tk.Label(self.resume_output_dir_frame, text="選擇 Gemini 模型:").grid(row=2, column=0, columnspan=3, sticky="w", pady=(10,2))
        self.resume_gemini_model_var = tk.StringVar(value=self.available_gemini_models[0] if self.available_gemini_models else "")
        self.resume_model_combobox = ttk.Combobox(self.resume_output_dir_frame, textvariable=self.resume_gemini_model_var, values=self.available_gemini_models, state="readonly", width=30)
        self.resume_model_combobox.grid(row=3, column=0, columnspan=2, sticky="w", pady=2)
        self.resume_output_dir_frame.grid_columnconfigure(0, weight=1)

        # --- Embed Images Specific Inputs ---
        self.embed_images_frame = tk.Frame(main_frame)
        
        # Top section: File selection
        ei_top_frame = tk.Frame(self.embed_images_frame)
        ei_top_frame.pack(fill="x", pady=5)
        tk.Label(ei_top_frame, text="選擇原始 guide.html:").grid(row=0, column=0, sticky="w")
        tk.Entry(ei_top_frame, textvariable=self.guide_html_path, width=70).grid(row=0, column=1, padx=5, sticky="ew")
        tk.Button(ei_top_frame, text="瀏覽...", command=self.browse_guide_html).grid(row=0, column=2, padx=2)
        tk.Button(ei_top_frame, text="讀取並列出頁面", command=self.load_slides_from_html, bg="#d0f0c0").grid(row=0, column=3, padx=10)
        ei_top_frame.grid_columnconfigure(1, weight=1)

        # Bottom section: Canvas + Scrollbar
        self.image_canvas_frame = tk.Frame(self.embed_images_frame)
        self.image_canvas_frame.pack(fill="both", expand=True)
        self.image_canvas = tk.Canvas(self.image_canvas_frame, bg="white")
        self.image_scrollbar = tk.Scrollbar(self.image_canvas_frame, orient="vertical", command=self.image_canvas.yview)
        self.image_canvas.configure(yscrollcommand=self.image_scrollbar.set)
        self.image_scrollbar.pack(side="right", fill="y")
        self.image_canvas.pack(side="left", fill="both", expand=True)
        self.slide_rows_frame = tk.Frame(self.image_canvas)
        self.slide_rows_frame.pack(fill="both", expand=True, padx=5, pady=5)
        self.image_canvas.create_window((0,0), window=self.slide_rows_frame, anchor="nw")
        self.slide_rows_frame.bind("<Configure>", lambda e: self.image_canvas.configure(scrollregion=self.image_canvas.bbox("all")))
        self.image_canvas.bind("<MouseWheel>", self._on_mousewheel)

        # --- New Generation Specific Inputs ---
        self.new_generation_controls_frame = tk.Frame(main_frame)
        
        # --- Agent Selection (Moved to Top) ---
        agent_selection_frame = tk.Frame(self.new_generation_controls_frame)
        agent_selection_frame.grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 5))
        tk.Label(agent_selection_frame, text="AI Agent:").pack(side="left", padx=(0, 10))
        self.agent_type_var = tk.StringVar(value="antigravity")
        agent_combobox = ttk.Combobox(agent_selection_frame, textvariable=self.agent_type_var, values=self.agent_types, state="readonly", width=20)
        agent_combobox.pack(side="left", padx=(0, 10))
        
        # Agent availability indicator
        self.agent_status_label = tk.Label(agent_selection_frame, text="(偵測中...)", fg="#ff9800")
        self.agent_status_label.pack(side="left")
        
        # Start background detection after UI is shown
        self.after(100, self._start_background_detection)
        
        # Update status when agent changes
        self.agent_type_var.trace_add("write", self._update_agent_status)
        
        # --- Model/API Configuration Frame (conditionally shown) ---
        self.model_config_frame = tk.Frame(self.new_generation_controls_frame)
        self.model_config_frame.grid(row=1, column=0, columnspan=3, sticky="w", pady=5)
        
        # API URL configuration for OpenAI-compatible agents
        self.api_config_frame = tk.Frame(self.model_config_frame)
        tk.Label(self.api_config_frame, text="API 端點 URL:").pack(side="left", padx=(0, 10))
        self.api_base_var = tk.StringVar(value="http://localhost:11434/v1")
        self.api_base_entry = tk.Entry(self.api_config_frame, textvariable=self.api_base_var, width=40)
        self.api_base_entry.pack(side="left", padx=(0, 5))
        self.detect_btn = tk.Button(self.api_config_frame, text="偵測", command=self._detect_local_models, bg="#e0f0e0")
        self.detect_btn.pack(side="left", padx=(0, 5))
        
        # Status label to show detection state
        self.detect_status_label = tk.Label(self.api_config_frame, text="(尚未偵測)", fg="#9e9e9e", font=("Arial", 8))
        self.detect_status_label.pack(side="left", padx=(5, 0))
        
        # Endpoint selection (when multiple endpoints available)
        self.endpoint_select_frame = tk.Frame(self.model_config_frame)
        self.endpoint_select_frame.pack_forget()  # Hidden by default
        tk.Label(self.endpoint_select_frame, text="選擇端點:").pack(side="left", padx=(0, 10))
        self.endpoint_var = tk.StringVar()
        self.endpoint_combobox = ttk.Combobox(self.endpoint_select_frame, textvariable=self.endpoint_var, state="readonly", width=50)
        self.endpoint_combobox.pack(side="left")
        
        # Model selection (shown for agents that support model selection)
        model_selection_frame = tk.Frame(self.model_config_frame)
        tk.Label(model_selection_frame, text="選擇模型:").pack(side="left", padx=(0, 10))
        self.initial_gemini_model_var = tk.StringVar(value=self.available_gemini_models[0] if self.available_gemini_models else "")
        self.initial_model_combobox = ttk.Combobox(model_selection_frame, textvariable=self.initial_gemini_model_var, values=self.available_gemini_models, state="readonly", width=30)
        self.initial_model_combobox.pack(side="left")

        # --- File Selection (Moved Below Agent) ---
        tk.Label(self.new_generation_controls_frame, text="選擇要分析的檔案:").grid(row=2, column=0, sticky="w", pady=2)
        tk.Entry(self.new_generation_controls_frame, textvariable=self.source_file_path, width=80).grid(row=3, column=0, padx=(0, 5), columnspan=2, sticky="ew")
        tk.Button(self.new_generation_controls_frame, text="瀏覽...", command=self.browse_files).grid(row=3, column=2)
        
        # --- Reworks Frame ---
        rework_frame = tk.Frame(self.new_generation_controls_frame)
        rework_frame.grid(row=4, column=0, columnspan=3, sticky="w", pady=5)
        tk.Label(rework_frame, text="最大修正次數 (0-10):").pack(side="left", padx=(0, 10))
        
        tk.Label(rework_frame, text="規劃:").pack(side="left", padx=(0, 5))
        self.plan_reworks_spinbox = tk.Spinbox(rework_frame, from_=0, to=10, width=5, justify="center")
        self.plan_reworks_spinbox.pack(side="left", padx=(0, 15))
        self.plan_reworks_spinbox.delete(0, "end"); self.plan_reworks_spinbox.insert(0, "6")

        tk.Label(rework_frame, text="簡報:").pack(side="left", padx=(0, 5))
        self.slide_reworks_spinbox = tk.Spinbox(rework_frame, from_=0, to=10, width=5, justify="center")
        self.slide_reworks_spinbox.pack(side="left", padx=(0, 15))
        self.slide_reworks_spinbox.delete(0, "end"); self.slide_reworks_spinbox.insert(0, "5")
        
        tk.Label(rework_frame, text="備忘稿:").pack(side="left", padx=(0, 5))
        self.memo_reworks_spinbox = tk.Spinbox(rework_frame, from_=0, to=10, width=5, justify="center")
        self.memo_reworks_spinbox.pack(side="left", padx=(0, 15))
        self.memo_reworks_spinbox.delete(0, "end"); self.memo_reworks_spinbox.insert(0, "5")

        tk.Label(rework_frame, text="執行:").pack(side="left", padx=(0, 5))
        self.exec_reworks_spinbox = tk.Spinbox(rework_frame, from_=0, to=10, width=5, justify="center")
        self.exec_reworks_spinbox.pack(side="left")
        self.exec_reworks_spinbox.delete(0, "end"); self.exec_reworks_spinbox.insert(0, "3")

        # --- SVG Generation Checkbox ---
        options_frame = tk.Frame(self.new_generation_controls_frame)
        options_frame.grid(row=5, column=0, columnspan=3, sticky="w", pady=5)
        self.svg_checkbox = tk.Checkbutton(options_frame, text="生成 SVG (實驗性功能，會增加 token 用量)", variable=self.generate_svg)
        self.svg_checkbox.pack(side="left")
        
        # --- Custom Instructions ---
        instr_frame = tk.Frame(self.new_generation_controls_frame)
        instr_frame.grid(row=6, column=0, columnspan=3, sticky="ew", pady=5)
        tk.Label(instr_frame, text="自訂指令 (選填):").grid(row=0, column=0, sticky="w")
        self.custom_instruction_text = scrolledtext.ScrolledText(instr_frame, height=4, state="normal", bg="#f5f5f5")
        self.custom_instruction_text.grid(row=1, column=0, columnspan=2, sticky="ew", pady=2)
        instr_frame.grid_columnconfigure(0, weight=1)

        self.new_generation_controls_frame.grid_columnconfigure(0, weight=1)

        # Common elements
        self.run_button = tk.Button(main_frame, text="開始生成", command=self.run_orchestration, font=("Arial", 12, "bold"), bg="#c0d8f0")
        self.run_button.pack(pady=10, fill="x", padx=10)
        
        self.progress_label = tk.Label(main_frame, text="執行進度:")
        self.progress_label.pack(pady=5, padx=10)
        
        self.console = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, state="disabled", bg="#f5f5f5")
        self.console.pack(pady=5, padx=10, fill="both", expand=True)

        # Initial toggle to set correct visibility
        self.toggle_mode_inputs()


    def _on_mousewheel(self, event):
        self.image_canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def open_link(self, url: str):
        webbrowser.open(url)

    def browse_files(self):
        filepath = filedialog.askopenfilename(filetypes=[("All Files", "*.*"), ("PDF", "*.pdf"), ("Word", "*.docx"), ("Text", "*.txt"), ("Markdown", "*.md"), ("HTML", "*.html")])
        if filepath: self.source_file_path.set(os.path.abspath(filepath))

    def browse_resume_output_dir(self):
        dirpath = filedialog.askdirectory()
        if dirpath: self.resume_output_dir_path.set(os.path.abspath(dirpath))

    def browse_guide_html(self):
        filepath = filedialog.askopenfilename(filetypes=[("HTML", "*.html"), ("All Files", "*.*")])
        if filepath: self.guide_html_path.set(os.path.abspath(filepath))

    def browse_slides_file(self):
        filepath = filedialog.askopenfilename(filetypes=[("JSON", "*.json"), ("All Files", "*.*")])
        if filepath: self.slides_file_path.set(os.path.abspath(filepath))

    def load_slides_from_html(self):
        filepath = self.guide_html_path.get()
        if not filepath or not os.path.exists(filepath):
            messagebox.showwarning("警告", "請先選擇 guide.html 檔案")
            return

        # Clear previous data
        for widget in self.slide_rows_frame.winfo_children():
            widget.destroy()
        self.slide_image_map = {}

        try:
            html_content = open(filepath, "r", encoding="utf-8").read()
            slide_pattern = re.compile(r'<div[^>]*class="[^"]*slide[^"]*"[^>]*>(.*?)</div>', re.IGNORECASE | re.DOTALL)
            slide_blocks = slide_pattern.findall(html_content)
            print(f"Found {len(slide_blocks)} potential slides.")

            row_index = 0
            for idx, block in enumerate(slide_blocks):
                slide_id = f"slide-{idx+1:02d}"
                
                row_frame = tk.Frame(self.slide_rows_frame)
                row_frame.pack(fill="x", pady=2)

                tk.Label(row_frame, text=f"頁面 {idx+1}:", font=("Arial", 11, "bold"), anchor="w").grid(row=0, column=0, padx=(0,5), sticky="w")
                
                tk.Label(row_frame, text="對應圖片:", anchor="e").grid(row=0, column=1)
                img_var = tk.StringVar()
                img_entry = tk.Entry(row_frame, textvariable=img_var, width=50)
                img_entry.grid(row=0, column=2, padx=5)
                
                btn = tk.Button(row_frame, text="瀏覽", command=lambda p=img_var: self._browse_image_for_slide(p))
                btn.grid(row=0, column=3, padx=2)
                
                self.slide_image_map[slide_id] = img_var
                row_index += 1

            if row_index == 0:
                messagebox.showinfo("提示", "未能自動解析出任何頁面區塊，請確認 HTML 格式。")
            else:
                messagebox.showinfo("成功", f"已解析 {row_index} 個頁面。請為每個頁面選擇對應的圖片。")
        except Exception as e:
            messagebox.showerror("錯誤", f"讀取檔案時發生錯誤:\n{str(e)}")

    def _browse_image_for_slide(self, var: tk.StringVar):
        filepath = filedialog.askopenfilename(filetypes=[("Images", "*.png *.jpg *.jpeg *.gif *.bmp"), ("All Files", "*.*")])
        if filepath: var.set(os.path.abspath(filepath))

    def toggle_mode_inputs(self):
        mode = self.mode_selection.get()
        self.new_generation_controls_frame.pack_forget()
        self.resume_output_dir_frame.pack_forget()
        self.embed_images_frame.pack_forget()
        
        if mode == "new_generation":
            self.new_generation_controls_frame.pack(fill="both", expand=True, pady=10)
        elif mode == "resume":
            self.resume_output_dir_frame.pack(fill="x", pady=10)
        elif mode == "embed_images":
            self.embed_images_frame.pack(fill="both", expand=True, pady=10)

    def _start_background_detection(self):
        """Start background detection for openai-compatible agents.
        
        This runs after UI is shown, so it doesn't block startup.
        """
        if self.agent_type_var.get() in ["openai-compatible", "ollama", "llamacpp"]:
            self.agent_status_label.config(text="(偵測中...)", fg="#ff9800")
            threading.Thread(target=self._background_detect, daemon=True).start()
        else:
            # For CLI agents, check immediately
            self._update_agent_status_sync()
    
    def _background_detect(self):
        """Run detection in background thread."""
        from agents.model_detector import default_detector
        
        try:
            result = default_detector.detect_quick()
            
            if result:
                # Success - update UI on main thread
                def show_success():
                    self.agent_status_label.config(
                        text=f"({result.type} @ {result.url.split(':')[-1]})",
                        fg="#4caf50"
                    )
                    self.agent_status_label.config(cursor="")
                
                self.after(0, show_success)
                print(f"[UI] ✅ Quick check passed: {result.type} at {result.url}")
            else:
                # Failed - auto-trigger full detection
                self._auto_detect_local_models()
        except Exception as e:
            print(f"[UI] ⚠️ Background detection failed: {e}")
            self.after(0, lambda: self.agent_status_label.config(text="(偵測失敗)", fg="#f44336"))
    
    def _update_agent_status(self, *args):
        """Update agent availability indicator based on selected agent."""
        from agents import AgentFactory
        from agents.model_detector import default_detector
        
        agent_name = self.agent_type_var.get()
        print(f"[UI] Checking availability for agent: {agent_name}")
        
        # For OpenAI-compatible agents, start background detection
        if agent_name in ["openai-compatible", "ollama", "llamacpp"]:
            self.agent_status_label.config(text="(偵測中...)", fg="#ff9800")
            threading.Thread(target=self._background_detect, daemon=True).start()
            return
        
        # For CLI agents, check immediately
        self._update_agent_status_sync()
    
    def _update_agent_status_sync(self):
        """Synchronous agent status check for CLI agents."""
        from agents import AgentFactory
        
        agent_name = self.agent_type_var.get()
        status = AgentFactory.get_agent_status(agent_name)
        
        if status.get("available"):
            self.agent_status_label.config(text="(可用)", fg="#4caf50")  # Green
            self.agent_status_label.config(cursor="")
            print(f"[UI] ✅ Agent {agent_name} is available")
        else:
            self.agent_status_label.config(text="(不可用)", fg="#f44336")  # Red
            self.agent_status_label.config(cursor="hand2")
            print(f"[UI] ❌ Agent {agent_name} is not available")
            # Add tooltip with hint
            if "hint" in status:
                self.agent_status_label.bind("<Enter>", lambda e: self._show_tooltip(status["hint"]))
    
    def _update_models_for_agent(self, *args):
        """Update model dropdown based on selected agent."""
        from agents import AgentFactory
        from agents.model_detector import default_detector
        
        agent_name = self.agent_type_var.get()
        print(f"[UI] Agent type changed to: {agent_name}")
        
        # Determine if this is an OpenAI-compatible agent
        is_openai_compat = agent_name in ["openai-compatible", "ollama", "llamacpp"]
        
        # Show/hide API config based on agent type
        if is_openai_compat:
            print("[UI] Showing API configuration for OpenAI-compatible agent")
            self.api_config_frame.pack(side="left", fill="x", expand=True, pady=5)
            # Set default endpoint based on agent type
            if agent_name in ["ollama", "openai-compatible"]:
                self.api_base_var.set("http://localhost:11434/v1")
            elif agent_name == "llamacpp":
                self.api_base_var.set("http://localhost:8080/v1")
            # Don't auto-detect yet - wait for user to click "偵測" or start generation
            print("[UI] Click '偵測' button to scan for local AI servers")
        else:
            print(f"[UI] Hiding API config for CLI agent: {agent_name}")
            self.api_config_frame.pack_forget()
        
        # CLI agents (antigravity, claude) don't need model selector via -p flag
        is_cli_agent = agent_name in ["antigravity", "claude"]
        
        # Get models - use timeout to avoid blocking
        print(f"[UI] Fetching available models for {agent_name}...")
        try:
            agent_config = {"agent": agent_name}
            agent = AgentFactory.create(agent_config)
            
            # Use a thread to fetch models to avoid blocking UI
            def fetch_and_update():
                try:
                    models = agent.get_models()
                    print(f"[UI] Fetched {len(models)} models for {agent_name}")
                    
                    # Update UI on main thread
                    self.after(0, lambda: self._update_model_comboboxes(models))
                except Exception as e:
                    print(f"[UI] Error fetching models: {e}")
            
            threading.Thread(target=fetch_and_update, daemon=True).start()
            
            # Show loading state
            self.after(0, lambda: self._show_model_loading())
            
        except Exception as e:
            print(f"[UI] Failed to create agent: {e}")
    
    def _update_model_comboboxes(self, models):
        """Update model comboboxes with fetched models."""
        if not models:
            return
        
        # Only update once
        self.after(0, lambda: self._do_update_models(models))
    
    def _do_update_models(self, models):
        """Perform the actual model update."""
        for combobox in [self.initial_model_combobox, self.resume_model_combobox]:
            combobox.config(values=models)
        
        if models:
            combobox.set(models[0])  # Select first model by default
            print(f"[UI] ✅ Set model dropdown to: {models[0]}")
    
    def _show_model_loading(self):
        """Show loading state while fetching models."""
        for combobox in [self.initial_model_combobox, self.resume_model_combobox]:
            combobox.config(values=["Loading models..."])
    
    def _auto_detect_local_models(self):
        """Auto-detect local AI models in background."""
        from agents.model_detector import default_detector
        
        print("[Auto-Detect] Starting full model detection...")
        
        try:
            endpoints = default_detector.detect_all()
            self._cached_endpoints = endpoints  # Cache for later use
            available = [e for e in endpoints if e.available]
            
            if available:
                first_endpoint = available[0]
                base_url = first_endpoint.url
                
                # Convert to /v1 format for OpenAI-compatible API
                if "/v1" not in base_url:
                    base_url += "/v1"
                
                # Update UI on main thread
                def update_ui():
                    self.api_base_var.set(base_url)
                    port = first_endpoint.url.split(':')[-1] if ':' in first_endpoint.url else ''
                    self.agent_status_label.config(
                        text=f"({first_endpoint.type} @ {port})",
                        fg="#4caf50"
                    )  # Green
                    
                    if hasattr(self, 'detect_status_label'):
                        self.detect_status_label.config(
                            text=f"({len(available)} 個端點)",
                            fg="#4caf50"
                        )
                    
                    print(f"[Auto-Detect] ✅ Found {first_endpoint.type} at {base_url}")
                    
                    # Update model dropdown with detected models
                    models = [m.name for m in first_endpoint.models] if first_endpoint.models else []
                    if models:
                        self._update_model_comboboxes(models)
                        print(f"[Auto-Detect] ✅ Detected models: {', '.join(models[:5])}")
                    else:
                        print("[Auto-Detect] ⚠️ No models detected, using defaults")
                
                self.after(0, update_ui)
            else:
                def show_error():
                    self.agent_status_label.config(text="(未發現)", fg="#f44336")  # Red
                    if hasattr(self, 'detect_status_label'):
                        self.detect_status_label.config(text="(未發現)", fg="#f44336")
                
                self.after(0, show_error)
                print("[Auto-Detect] ⚠️ No available local models found")
        except Exception as e:
            import traceback
            print(f"[Auto-Detect] ❌ Failed: {e}")
            print(traceback.format_exc())
    
    def _detect_local_models(self):
        """Detect local AI models (Ollama, llama.cpp)."""
        from agents.model_detector import default_detector
        
        # Update status
        self.detect_status_label.config(text="(偵測中...)", fg="#ff9800")
        self.detect_btn.config(state="disabled")
        
        # Run detection in background thread
        def do_detection():
            try:
                endpoints = default_detector.detect_all()
                self._cached_endpoints = endpoints  # Cache for later use
                available = [e for e in endpoints if e.available]
                
                # Update UI on main thread
                def update_ui():
                    if available:
                        # Use first available endpoint
                        first_endpoint = available[0]
                        base_url = first_endpoint.url
                        
                        # Convert to /v1 format for OpenAI-compatible API
                        if "/v1" not in base_url:
                            base_url += "/v1"
                        
                        self.api_base_var.set(base_url)
                        
                        # Show model info
                        if first_endpoint.models:
                            model_names = [m.name for m in first_endpoint.models]
                            print(f"[Detect] Found models: {', '.join(model_names)}")
                        
                        # Update model dropdown
                        self._update_model_comboboxes([m.name for m in first_endpoint.models] if first_endpoint.models else [])
                        
                        # Update status
                        self.detect_status_label.config(
                            text=f"({len(available)} 個端點)",
                            fg="#4caf50"
                        )
                        
                        messagebox.showinfo("偵測完成", f"發現 {len(available)} 個可用端點:\n\n" + 
                                          "\n".join(f"- {ep.type} @ {ep.url}" for ep in available))
                    else:
                        self.detect_status_label.config(
                            text="(未發現)",
                            fg="#f44336"
                        )
                        messagebox.showwarning("偵測結果", "未發現任何可用的本地 AI 模型服務。\n\n請確認:\n- Ollama 已安裝並運行\n- 或 llama.cpp server 已啟動")
                    
                    self.detect_btn.config(state="normal")
                
                self.after(0, update_ui)
            except Exception as e:
                print(f"[Detect] Error: {e}")
                self.after(0, lambda: self.detect_status_label.config(text="(錯誤)", fg="#f44336"))
                self.after(0, lambda: self.detect_btn.config(state="normal"))
        
        threading.Thread(target=do_detection, daemon=True).start()
    
    def _show_tooltip(self, text: str):
        """Show tooltip when hovering over status label."""
        # Simple tooltip implementation
        tooltip_window = tk.Toplevel(self)
        tooltip_window.wm_attributes("-topmost", True)
        tooltip_window.wm_overrideredirect(True)
        tooltip_window.geometry("+{}+{}".format(
            self.winfo_rootx() + 150,
            self.winfo_rooty() + 50
        ))
        label = tk.Label(tooltip_window, text=text, bg="#ffffe0", fg="#333",
                        borderwidth=1, relief="solid", wraplength=300)
        label.pack()
        tooltip_window.after(3000, tooltip_window.destroy)

    def run_orchestration(self):
        import subprocess
        import sys

        if self.mode_selection.get() == "new_generation":
            if not self.source_file_path.get():
                messagebox.showwarning("警告", "請選擇要分析的檔案")
                return
            
            # Prepare command
            command = [sys.executable, "scripts/orchestrate.py"]
            command.extend(["--source", self.source_file_path.get()])
            
            # Add optional arguments
            m_title = self.input_doc_title.get().strip()
            m_author = self.input_doc_author.get().strip()
            m_url = self.input_source_url.get().strip()
            
            if m_title: command.extend(["--manual-title", m_title])
            if m_author: command.extend(["--manual-author", m_author])
            if m_url: command.extend(["--manual-url", m_url])

            if not self.generate_svg.get():
                command.append("--no-svg")
            
            custom_instruction = self.custom_instruction_text.get("1.0", "end-1c").strip()
            slides_file = self.slides_file_path.get().strip()
            
            if custom_instruction: command.extend(["--custom-instruction", custom_instruction])
            if slides_file: command.extend(["--plan-from-slides", slides_file])
            # Only pass model for non-OpenAI-compatible agents
            # OpenAI-compatible agents use detected model from endpoint
            if self.current_gemini_model and self.agent_type_var.get() not in ["openai-compatible", "ollama", "llamacpp"]:
                command.extend(["--gemini-model", self.current_gemini_model])
            
            # Pass API base for OpenAI-compatible agents if configured
            api_base = self.api_base_var.get().strip() if hasattr(self, 'api_base_var') else ""
            if api_base and self.agent_type_var.get() in ["openai-compatible", "ollama", "llamacpp"]:
                command.extend(["--api-base", api_base])
            
            command.extend(["--agent", self.agent_type_var.get()])

            
            # Add rework counts if they are valid integers
            try:
                if int(self.plan_reworks_spinbox.get()) >= 0: command.extend(["--plan-reworks", self.plan_reworks_spinbox.get()])
            except ValueError:
                self.log_message("警告：規劃修正次數不是有效的數字，將使用預設值。\n")
            
            try:
                if int(self.slide_reworks_spinbox.get()) >= 0: command.extend(["--slide-reworks", self.slide_reworks_spinbox.get()])
            except ValueError:
                self.log_message("警告：簡報修正次數不是有效的數字，將使用預設值。\n")
            
            try:
                if int(self.memo_reworks_spinbox.get()) >= 0: command.extend(["--memo-reworks", self.memo_reworks_spinbox.get()])
            except ValueError:
                self.log_message("警告：備忘稿修正次數不是有效的數字，將使用預設值。\n")
            
            try:
                if int(self.exec_reworks_spinbox.get()) >= 0: command.extend(["--exec-reworks", self.exec_reworks_spinbox.get()])
            except ValueError:
                self.log_message("警告：執行修正次數不是有效的數字，將使用預設值。\n")

            self.log_message(f"執行命令: {' '.join(command)}\n")

        elif self.mode_selection.get() == "resume":
            if not self.resume_output_dir_path.get():
                messagebox.showwarning("警告", "請選擇現有輸出資料夾")
                return
            resume_output_dir = self.resume_output_dir_path.get()
            if not os.path.isdir(resume_output_dir):
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
            # Only pass model for non-OpenAI-compatible agents
            # OpenAI-compatible agents use detected model from endpoint
            if self.current_gemini_model and self.agent_type_var.get() not in ["openai-compatible", "ollama", "llamacpp"]:
                command.extend(["--gemini-model", self.current_gemini_model])
            
            # Pass API base for OpenAI-compatible agents if configured
            api_base = self.api_base_var.get().strip() if hasattr(self, 'api_base_var') else ""
            if api_base and self.agent_type_var.get() in ["openai-compatible", "ollama", "llamacpp"]:
                command.extend(["--api-base", api_base])
            
            command.extend(["--agent", self.agent_type_var.get()])
            
            self.log_message(f"執行命令: {' '.join(command)}\n")
        
        else:
            # Embed Images Mode
            if not self.guide_html_path.get():
                messagebox.showwarning("警告", "請先選擇 guide.html 檔案")
                return
            
            command = [sys.executable, "scripts/embed_images.py", "--html", self.guide_html_path.get()]
            self.log_message(f"執行命令: {' '.join(command)}\n")

        # Execute command
        self.run_button.config(state="disabled")
        self.progress_label.config(text="正在執行...請等待...")
        
        def run_process():
            try:
                process = subprocess.Popen(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    bufsize=1,
                    universal_newlines=True
                )
                
                for line in process.stdout:
                    self.after(0, self.log_message, line)
                
                process.wait()
                
                if process.returncode == 0:
                    self.after(0, lambda: self.progress_label.config(text="執行完成！"))
                else:
                    self.after(0, lambda: self.progress_label.config(text=f"執行結束 (Return code: {process.returncode})"))
                    
                self.after(0, lambda: self.run_button.config(state="normal"))
            except Exception as e:
                self.after(0, lambda: self.progress_label.config(text="執行出錯"))
                self.after(0, lambda: self.log_message(f"[錯誤] {str(e)}\n"))
                self.after(0, lambda: self.run_button.config(state="normal"))
        
        threading.Thread(target=run_process, daemon=True).start()

    def log_message(self, message: str):
        self.console.config(state="normal")
        self.console.insert(tk.END, message)
        self.console.see(tk.END)
        self.console.config(state="disabled")


# Main entry point
def main():
    try:
        # No startup detection - let user choose agent first
        # Detection only happens when user selects openai-compatible agent
        print("[Startup] Creating App...")
        app = App(["Loading models..."])
        print("[Startup] App created, starting mainloop...")
        
        # Ensure window is visible
        app.update_idletasks()
        app.lift()  # Bring to front
        app.attributes('-topmost', True)
        app.after(100, lambda: app.attributes('-topmost', False))
        
        app.mainloop()
        print("[Startup] mainloop exited")
    except Exception as e:
        import traceback
        print(f"[Startup ERROR] {e}")
        traceback.print_exc()
        input("Press Enter to exit...")


if __name__ == "__main__":
    main()
