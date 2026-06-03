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
        
        # --- Theme Config / Color System ---
        self.COLOR_BG_WINDOW = "#f8fafc"      # Slate 50
        self.COLOR_BG_CARD = "#ffffff"        # White
        self.COLOR_BORDER = "#e2e8f0"         # Slate 200
        self.COLOR_TEXT_PRIMARY = "#0f172a"   # Slate 900
        self.COLOR_TEXT_MUTED = "#64748b"     # Slate 500
        self.COLOR_ACCENT = "#2563eb"         # Blue 600
        self.COLOR_ACCENT_HOVER = "#1d4ed8"  # Blue 700
        self.COLOR_ACCENT_LIGHT = "#eff6ff"  # Blue 50
        self.COLOR_SUCCESS = "#10b981"        # Green 500
        self.COLOR_SUCCESS_LIGHT = "#ecfdf5" # Green 50
        self.COLOR_DANGER = "#ef4444"         # Red 500
        self.COLOR_DANGER_LIGHT = "#fef2f2"   # Red 50
        self.COLOR_BORDER_FOCUS = "#3b82f6"   # Blue 500
        
        # Set Window background
        self.configure(bg=self.COLOR_BG_WINDOW)
        
        # --- Fonts ---
        self.FONT_TITLE = ("Microsoft JhengHei", 11, "bold")
        self.FONT_SECTION = ("Microsoft JhengHei", 10, "bold")
        self.FONT_BODY = ("Microsoft JhengHei", 10)
        self.FONT_BODY_BOLD = ("Microsoft JhengHei", 10, "bold")
        self.FONT_SMALL = ("Microsoft JhengHei", 9)
        self.FONT_CONSOLE = ("Consolas", 10)
        
        # Set window size and position based on screen dimensions
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        window_width = int(screen_width * 0.7)
        if window_width < 1100: window_width = 1100
        elif window_width > 1300: window_width = 1300
        
        window_height = int(screen_height * 0.75)
        if window_height < 750: window_height = 750
        elif window_height > 900: window_height = 900
        
        center_x = int((screen_width / 2) - (window_width / 2))
        center_y = int((screen_height / 2) - (window_height / 2))
        self.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')

        # --- TTK Styles ---
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TCombobox", 
                        fieldbackground="#ffffff", 
                        background="#e2e8f0", 
                        foreground="#0f172a", 
                        bordercolor="#e2e8f0", 
                        lightcolor="#e2e8f0", 
                        darkcolor="#e2e8f0",
                        arrowcolor="#64748b")
        style.map("TCombobox", 
                  fieldbackground=[("readonly", "#ffffff"), ("active", "#f8fafc")],
                  selectbackground=[("readonly", "#eff6ff"), ("active", "#eff6ff")],
                  selectforeground=[("readonly", "#2563eb"), ("active", "#2563eb")])
                  
        style.configure("TScrollbar",
                        background="#cbd5e1",
                        bordercolor="#e2e8f0",
                        troughcolor="#f8fafc",
                        arrowcolor="#64748b")

        # --- Initialize instance variables ---
        self.source_file_path = tk.StringVar()
        self.slides_file_path = tk.StringVar()
        self.input_doc_title = tk.StringVar()
        self.input_doc_author = tk.StringVar()
        self.input_source_url = tk.StringVar()
        self.generate_svg = tk.BooleanVar(value=False)
        self.quota_event = threading.Event()
        self.quota_event.set()
        self.current_gemini_model = None
        self.resume_output_dir_path = tk.StringVar()
        self.video_output_dir_path = tk.StringVar()
        
        # Variables for Image Embedding Mode
        self.guide_html_path = tk.StringVar()
        self.slide_image_map = {} # Dictionary to store slide_id -> image_path
        self.slide_rows_frame = None # Frame inside canvas

        # --- Layout Structure ---
        # Footer separator line
        footer_divider = tk.Frame(self, height=1, bg=self.COLOR_BORDER, bd=0)
        footer_divider.pack(fill="x", side="bottom")
        
        footer_frame = tk.Frame(self, bg=self.COLOR_BG_WINDOW)
        footer_frame.pack(fill="x", side="bottom", pady=10, padx=15)
        
        main_frame = tk.Frame(self, bg=self.COLOR_BG_WINDOW)
        main_frame.pack(fill="both", expand=True, padx=15, pady=(15, 5))

        # --- Populate Footer ---
        footer_left = tk.Frame(footer_frame, bg=self.COLOR_BG_WINDOW)
        footer_left.pack(side="left")
        
        footer_right = tk.Frame(footer_frame, bg=self.COLOR_BG_WINDOW)
        footer_right.pack(side="right")
        
        tk.Label(footer_left, text=f"PPTPlaner {self.version}", font=("Segoe UI", 9, "bold"), fg=self.COLOR_TEXT_MUTED, bg=self.COLOR_BG_WINDOW).pack(side="left")
        tk.Label(footer_left, text="  |  ", font=("Segoe UI", 9), fg="#cbd5e1", bg=self.COLOR_BG_WINDOW).pack(side="left")
        tk.Label(footer_left, text="Copyright © 2026 Chiakai Chang. All Rights Reserved.", font=("Segoe UI", 9), fg=self.COLOR_TEXT_MUTED, bg=self.COLOR_BG_WINDOW).pack(side="left")
        
        tk.Label(footer_right, text="Author: Chiakai Chang", font=("Segoe UI", 9), fg=self.COLOR_TEXT_MUTED, bg=self.COLOR_BG_WINDOW).pack(side="left", padx=(0, 15))
        
        gh_lbl = tk.Label(footer_right, text="GitHub", font=("Segoe UI", 9, "bold"), fg=self.COLOR_TEXT_MUTED, bg=self.COLOR_BG_WINDOW, cursor="hand2")
        gh_lbl.pack(side="left", padx=8)
        gh_lbl.bind("<Button-1>", lambda e: self.open_link("https://github.com/Chiakai-Chang/PPTPlaner"))
        
        li_lbl = tk.Label(footer_right, text="LinkedIn", font=("Segoe UI", 9, "bold"), fg=self.COLOR_TEXT_MUTED, bg=self.COLOR_BG_WINDOW, cursor="hand2")
        li_lbl.pack(side="left", padx=8)
        li_lbl.bind("<Button-1>", lambda e: self.open_link("https://www.linkedin.com/in/chiakai-chang-htciu"))
        
        mail_lbl = tk.Label(footer_right, text="Email", font=("Segoe UI", 9, "bold"), fg=self.COLOR_TEXT_MUTED, bg=self.COLOR_BG_WINDOW, cursor="hand2")
        mail_lbl.pack(side="left", padx=8)
        mail_lbl.bind("<Button-1>", lambda e: self.open_link("mailto:lotifv@gmail.com"))
        
        def make_link_hoverable(widget):
            widget.bind("<Enter>", lambda e: widget.config(fg=self.COLOR_ACCENT, font=("Segoe UI", 9, "bold", "underline")))
            widget.bind("<Leave>", lambda e: widget.config(fg=self.COLOR_TEXT_MUTED, font=("Segoe UI", 9, "bold")))
        
        make_link_hoverable(gh_lbl)
        make_link_hoverable(li_lbl)
        make_link_hoverable(mail_lbl)

        # --- Populate Main Frame ---
        # Split main_frame into left_pane (controls) and right_pane (console/log) with grid for precise ratio
        main_frame.grid_columnconfigure(0, weight=45, minsize=460)
        main_frame.grid_columnconfigure(1, weight=55, minsize=550)
        main_frame.grid_rowconfigure(0, weight=1)
        
        self.left_pane = tk.Frame(main_frame, bg=self.COLOR_BG_WINDOW)
        self.left_pane.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        self.right_pane = tk.Frame(main_frame, bg=self.COLOR_BG_WINDOW)
        self.right_pane.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        # --- Mode Selection ---
        self.mode_selection = tk.StringVar(value="new_generation")
        mode_selection_frame = tk.Frame(self.left_pane, bg=self.COLOR_BG_WINDOW)
        mode_selection_frame.pack(fill="x", pady=(5, 10))
        
        tk.Label(mode_selection_frame, text="⚙️ 選擇操作模式 (Select Mode):", font=self.FONT_TITLE, fg=self.COLOR_TEXT_PRIMARY, bg=self.COLOR_BG_WINDOW).pack(anchor="w", pady=(0, 6))
        
        radio_container = tk.Frame(mode_selection_frame, bg=self.COLOR_BG_WINDOW)
        radio_container.pack(fill="x")
        
        for text, val in [("全新生成", "new_generation"), 
                          ("接續生成 SVG", "resume"), 
                          ("製作圖文簡報", "embed_images"), 
                          ("影片生成", "video_generation")]:
            rb = tk.Radiobutton(radio_container, text=text, variable=self.mode_selection, value=val,
                                command=self.toggle_mode_inputs, bg=self.COLOR_BG_WINDOW, activebackground=self.COLOR_BG_WINDOW,
                                fg=self.COLOR_TEXT_PRIMARY, selectcolor="#ffffff", font=self.FONT_BODY_BOLD, cursor="hand2")
            rb.pack(side="left", padx=(0, 15))

        # --- Resume Specific Inputs ---
        self.resume_output_dir_frame = tk.Frame(self.left_pane, bg=self.COLOR_BG_CARD, highlightbackground=self.COLOR_BORDER, highlightthickness=1, bd=0)
        
        tk.Label(self.resume_output_dir_frame, text="🔁 接續簡報生成", font=self.FONT_TITLE, fg=self.COLOR_TEXT_PRIMARY, bg=self.COLOR_BG_CARD).pack(anchor="w", padx=15, pady=(15, 8))
        
        dir_label_row = tk.Frame(self.resume_output_dir_frame, bg=self.COLOR_BG_CARD)
        dir_label_row.pack(fill="x", padx=15, pady=(4, 2))
        tk.Label(dir_label_row, text="選擇現有輸出資料夾 (用於接續生成):", font=self.FONT_BODY_BOLD, fg=self.COLOR_TEXT_PRIMARY, bg=self.COLOR_BG_CARD).pack(side="left")
        
        dir_input_row = tk.Frame(self.resume_output_dir_frame, bg=self.COLOR_BG_CARD)
        dir_input_row.pack(fill="x", padx=15, pady=4)
        
        self.resume_dir_entry = tk.Entry(dir_input_row, textvariable=self.resume_output_dir_path, font=self.FONT_BODY, bg="#f1f5f9", fg=self.COLOR_TEXT_PRIMARY,
                                         insertbackground=self.COLOR_TEXT_PRIMARY, relief="flat", highlightthickness=1,
                                         highlightbackground=self.COLOR_BORDER, highlightcolor=self.COLOR_BORDER_FOCUS)
        self.resume_dir_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        def on_rdir_focus_in(e): self.resume_dir_entry.config(highlightbackground=self.COLOR_BORDER_FOCUS)
        def on_rdir_focus_out(e): self.resume_dir_entry.config(highlightbackground=self.COLOR_BORDER)
        self.resume_dir_entry.bind("<FocusIn>", on_rdir_focus_in)
        self.resume_dir_entry.bind("<FocusOut>", on_rdir_focus_out)
        
        browse_rdir_btn = self.create_button(dir_input_row, "瀏覽...", self.browse_resume_output_dir, btn_type="secondary")
        browse_rdir_btn.pack(side="right")
        
        model_label_row = tk.Frame(self.resume_output_dir_frame, bg=self.COLOR_BG_CARD)
        model_label_row.pack(fill="x", padx=15, pady=(10, 2))
        tk.Label(model_label_row, text="選擇 Gemini 模型:", font=self.FONT_BODY_BOLD, fg=self.COLOR_TEXT_PRIMARY, bg=self.COLOR_BG_CARD).pack(side="left")
        
        model_input_row = tk.Frame(self.resume_output_dir_frame, bg=self.COLOR_BG_CARD)
        model_input_row.pack(fill="x", padx=15, pady=(2, 15))
        
        self.resume_gemini_model_var = tk.StringVar(value=self.available_gemini_models[0] if self.available_gemini_models else "")
        self.resume_model_combobox = ttk.Combobox(model_input_row, textvariable=self.resume_gemini_model_var, values=self.available_gemini_models, state="readonly", width=30)
        self.resume_model_combobox.pack(side="left")

        # --- Embed Images Specific Inputs ---
        self.embed_images_frame = tk.Frame(self.left_pane, bg=self.COLOR_BG_CARD, highlightbackground=self.COLOR_BORDER, highlightthickness=1, bd=0)
        
        tk.Label(self.embed_images_frame, text="🖼️ 製作圖文簡報 (HTML)", font=self.FONT_TITLE, fg=self.COLOR_TEXT_PRIMARY, bg=self.COLOR_BG_CARD).pack(anchor="w", padx=15, pady=(15, 8))
        
        html_label_row = tk.Frame(self.embed_images_frame, bg=self.COLOR_BG_CARD)
        html_label_row.pack(fill="x", padx=15, pady=(4, 2))
        tk.Label(html_label_row, text="選擇原始 guide.html 檔案:", font=self.FONT_BODY_BOLD, fg=self.COLOR_TEXT_PRIMARY, bg=self.COLOR_BG_CARD).pack(side="left")
        
        html_input_row = tk.Frame(self.embed_images_frame, bg=self.COLOR_BG_CARD)
        html_input_row.pack(fill="x", padx=15, pady=4)
        
        self.guide_html_entry = tk.Entry(html_input_row, textvariable=self.guide_html_path, font=self.FONT_BODY, bg="#f1f5f9", fg=self.COLOR_TEXT_PRIMARY,
                                         insertbackground=self.COLOR_TEXT_PRIMARY, relief="flat", highlightthickness=1,
                                         highlightbackground=self.COLOR_BORDER, highlightcolor=self.COLOR_BORDER_FOCUS)
        self.guide_html_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        def on_html_focus_in(e): self.guide_html_entry.config(highlightbackground=self.COLOR_BORDER_FOCUS)
        def on_html_focus_out(e): self.guide_html_entry.config(highlightbackground=self.COLOR_BORDER)
        self.guide_html_entry.bind("<FocusIn>", on_html_focus_in)
        self.guide_html_entry.bind("<FocusOut>", on_html_focus_out)
        
        browse_html_btn = self.create_button(html_input_row, "瀏覽...", self.browse_guide_html, btn_type="secondary")
        browse_html_btn.pack(side="right", padx=(0, 5))
        
        load_slides_btn = self.create_button(html_input_row, "讀取並列出頁面", self.load_slides_from_html, btn_type="success")
        load_slides_btn.pack(side="right")
        
        self.image_canvas_frame = tk.Frame(self.embed_images_frame, bg=self.COLOR_BG_CARD, highlightbackground=self.COLOR_BORDER, highlightthickness=1, bd=0)
        self.image_canvas_frame.pack(fill="both", expand=True, padx=15, pady=(10, 15))
        
        self.image_canvas = tk.Canvas(self.image_canvas_frame, bg="#f8fafc", bd=0, highlightthickness=0)
        self.image_scrollbar = ttk.Scrollbar(self.image_canvas_frame, orient="vertical", command=self.image_canvas.yview)
        self.image_canvas.configure(yscrollcommand=self.image_scrollbar.set)
        
        self.image_scrollbar.pack(side="right", fill="y")
        self.image_canvas.pack(side="left", fill="both", expand=True)
        
        self.slide_rows_frame = tk.Frame(self.image_canvas, bg="#f8fafc")
        
        def configure_canvas(e):
            self.image_canvas.configure(scrollregion=self.image_canvas.bbox("all"))
            self.image_canvas.itemconfig(canvas_window, width=e.width)
            
        canvas_window = self.image_canvas.create_window((0,0), window=self.slide_rows_frame, anchor="nw")
        self.image_canvas.bind("<Configure>", configure_canvas)
        self.slide_rows_frame.bind("<Configure>", lambda e: self.image_canvas.configure(scrollregion=self.image_canvas.bbox("all")))
        self.image_canvas.bind("<MouseWheel>", self._on_mousewheel)

        # --- Video Generation Specific Inputs ---
        self.video_generation_frame = tk.Frame(self.left_pane, bg=self.COLOR_BG_CARD, highlightbackground=self.COLOR_BORDER, highlightthickness=1, bd=0)
        
        tk.Label(self.video_generation_frame, text="🎥 簡報語音影片生成", font=self.FONT_TITLE, fg=self.COLOR_TEXT_PRIMARY, bg=self.COLOR_BG_CARD).pack(anchor="w", padx=15, pady=(15, 8))
        
        vdir_label_row = tk.Frame(self.video_generation_frame, bg=self.COLOR_BG_CARD)
        vdir_label_row.pack(fill="x", padx=15, pady=(4, 2))
        tk.Label(vdir_label_row, text="選擇簡報輸出資料夾 (必須包含 slides/ 和 notes/):", font=self.FONT_BODY_BOLD, fg=self.COLOR_TEXT_PRIMARY, bg=self.COLOR_BG_CARD).pack(side="left")
        
        vdir_input_row = tk.Frame(self.video_generation_frame, bg=self.COLOR_BG_CARD)
        vdir_input_row.pack(fill="x", padx=15, pady=4)
        
        self.video_dir_entry = tk.Entry(vdir_input_row, textvariable=self.video_output_dir_path, font=self.FONT_BODY, bg="#f1f5f9", fg=self.COLOR_TEXT_PRIMARY,
                                         insertbackground=self.COLOR_TEXT_PRIMARY, relief="flat", highlightthickness=1,
                                         highlightbackground=self.COLOR_BORDER, highlightcolor=self.COLOR_BORDER_FOCUS)
        self.video_dir_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        def on_vdir_focus_in(e): self.video_dir_entry.config(highlightbackground=self.COLOR_BORDER_FOCUS)
        def on_vdir_focus_out(e): self.video_dir_entry.config(highlightbackground=self.COLOR_BORDER)
        self.video_dir_entry.bind("<FocusIn>", on_vdir_focus_in)
        self.video_dir_entry.bind("<FocusOut>", on_vdir_focus_out)
        
        browse_vdir_btn = self.create_button(vdir_input_row, "瀏覽...", self.browse_video_output_dir, btn_type="secondary")
        browse_vdir_btn.pack(side="right")
        
        options_grid = tk.Frame(self.video_generation_frame, bg=self.COLOR_BG_CARD)
        options_grid.pack(fill="x", padx=15, pady=10)
        options_grid.grid_columnconfigure(1, weight=1)
        
        tk.Label(options_grid, text="語音類型:", font=self.FONT_BODY_BOLD, fg=self.COLOR_TEXT_PRIMARY, bg=self.COLOR_BG_CARD).grid(row=0, column=0, sticky="w", pady=6, padx=(0, 10))
        self.video_tts_provider = tk.StringVar(value="edge-tts")
        tts_combobox = ttk.Combobox(options_grid, textvariable=self.video_tts_provider, values=["edge-tts"], state="readonly", width=18)
        tts_combobox.grid(row=0, column=1, sticky="w", pady=6)
        
        tk.Label(options_grid, text="圖像類型:", font=self.FONT_BODY_BOLD, fg=self.COLOR_TEXT_PRIMARY, bg=self.COLOR_BG_CARD).grid(row=1, column=0, sticky="w", pady=6, padx=(0, 10))
        self.video_image_provider = tk.StringVar(value="none")
        image_label = tk.Label(options_grid, text="文字覆疊 (預設，不需額外模組)", font=self.FONT_BODY, fg=self.COLOR_TEXT_MUTED, bg=self.COLOR_BG_CARD)
        image_label.grid(row=1, column=1, sticky="w", pady=6)
        
        v_alert = tk.Frame(self.video_generation_frame, bg=self.COLOR_DANGER_LIGHT, highlightbackground="#fecaca", highlightthickness=1, bd=0)
        v_alert.pack(fill="x", padx=15, pady=(5, 10), ipady=6, ipadx=8)
        tk.Label(v_alert, text="💡 提示：圖像生成需要額外安裝 ComfyUI 或 RunningHub 並下載模型。", font=self.FONT_SMALL, fg=self.COLOR_DANGER, bg=self.COLOR_DANGER_LIGHT, justify="left", wraplength=400).pack(fill="x")
        
        vg_status_frame = tk.Frame(self.video_generation_frame, bg=self.COLOR_BG_CARD)
        vg_status_frame.pack(fill="x", padx=15, pady=(5, 15))
        self.video_status_label = tk.Label(vg_status_frame, text="", font=self.FONT_SMALL, fg=self.COLOR_TEXT_MUTED, bg=self.COLOR_BG_CARD)
        self.video_status_label.pack(side="left")

        # --- New Generation Specific Inputs ---
        self.new_generation_controls_frame = tk.Frame(self.left_pane, bg=self.COLOR_BG_WINDOW)
        
        # --- Card 1: AI Agent & Model Setup ---
        self.card_agent = tk.Frame(self.new_generation_controls_frame, bg=self.COLOR_BG_CARD, highlightbackground=self.COLOR_BORDER, highlightthickness=1, bd=0)
        self.card_agent.pack(fill="x", pady=(0, 10), ipady=8, ipadx=10)
        
        tk.Label(self.card_agent, text="🤖 AI Agent 與模型設定", font=self.FONT_TITLE, fg=self.COLOR_TEXT_PRIMARY, bg=self.COLOR_BG_CARD).pack(anchor="w", padx=10, pady=(10, 8))
        
        agent_row = tk.Frame(self.card_agent, bg=self.COLOR_BG_CARD)
        agent_row.pack(fill="x", padx=10, pady=4)
        
        tk.Label(agent_row, text="AI Agent 類型:", font=self.FONT_BODY_BOLD, fg=self.COLOR_TEXT_PRIMARY, bg=self.COLOR_BG_CARD).pack(side="left")
        
        self.agent_type_var = tk.StringVar(value="antigravity")
        self.agent_combobox = ttk.Combobox(agent_row, textvariable=self.agent_type_var, values=self.agent_types, state="readonly", width=18)
        self.agent_combobox.pack(side="left", padx=10)
        
        self.agent_status_label = tk.Label(agent_row, text="(偵測中...)", font=self.FONT_BODY_BOLD, fg="#ff9800", bg=self.COLOR_BG_CARD)
        self.agent_status_label.pack(side="left")
        
        self.after(100, self._start_background_detection)
        self.agent_type_var.trace_add("write", self._update_agent_status)
        
        # Model config frame
        self.model_config_frame = tk.Frame(self.card_agent, bg=self.COLOR_BG_CARD)
        self.model_config_frame.pack(fill="x", padx=10, pady=4)
        
        self.api_config_frame = tk.Frame(self.model_config_frame, bg=self.COLOR_BG_CARD)
        tk.Label(self.api_config_frame, text="API 端點 URL:", font=self.FONT_BODY, fg=self.COLOR_TEXT_PRIMARY, bg=self.COLOR_BG_CARD).pack(side="left", padx=(0, 10))
        self.api_base_var = tk.StringVar(value="http://localhost:11434/v1")
        self.api_base_entry = tk.Entry(self.api_config_frame, textvariable=self.api_base_var, font=self.FONT_BODY, bg="#f1f5f9", fg=self.COLOR_TEXT_PRIMARY,
                                       insertbackground=self.COLOR_TEXT_PRIMARY, relief="flat", highlightthickness=1,
                                       highlightbackground=self.COLOR_BORDER, highlightcolor=self.COLOR_BORDER_FOCUS, width=32)
        self.api_base_entry.pack(side="left", padx=(0, 5))
        def on_api_focus_in(e): self.api_base_entry.config(highlightbackground=self.COLOR_BORDER_FOCUS)
        def on_api_focus_out(e): self.api_base_entry.config(highlightbackground=self.COLOR_BORDER)
        self.api_base_entry.bind("<FocusIn>", on_api_focus_in)
        self.api_base_entry.bind("<FocusOut>", on_api_focus_out)
        
        self.detect_btn = self.create_button(self.api_config_frame, "偵測", self._detect_local_models, btn_type="secondary")
        self.detect_btn.pack(side="left", padx=(0, 5))
        
        self.detect_status_label = tk.Label(self.api_config_frame, text="(尚未偵測)", font=self.FONT_SMALL, fg=self.COLOR_TEXT_MUTED, bg=self.COLOR_BG_CARD)
        self.detect_status_label.pack(side="left", padx=(5, 0))
        
        self.endpoint_select_frame = tk.Frame(self.model_config_frame, bg=self.COLOR_BG_CARD)
        self.endpoint_select_frame.pack_forget()
        tk.Label(self.endpoint_select_frame, text="選擇端點:", font=self.FONT_BODY, fg=self.COLOR_TEXT_PRIMARY, bg=self.COLOR_BG_CARD).pack(side="left", padx=(0, 10))
        self.endpoint_var = tk.StringVar()
        self.endpoint_combobox = ttk.Combobox(self.endpoint_select_frame, textvariable=self.endpoint_var, state="readonly", width=50)
        self.endpoint_combobox.pack(side="left")
        
        self.model_select_row = tk.Frame(self.model_config_frame, bg=self.COLOR_BG_CARD)
        self.model_select_row.pack(fill="x", pady=4)
        tk.Label(self.model_select_row, text="選擇 AI 模型:", font=self.FONT_BODY_BOLD, fg=self.COLOR_TEXT_PRIMARY, bg=self.COLOR_BG_CARD).pack(side="left", padx=(0, 10))
        self.initial_gemini_model_var = tk.StringVar(value=self.available_gemini_models[0] if self.available_gemini_models else "")
        self.initial_model_combobox = ttk.Combobox(self.model_select_row, textvariable=self.initial_gemini_model_var, values=self.available_gemini_models, state="readonly", width=25)
        self.initial_model_combobox.pack(side="left")

        # --- Card 2: Document & Parser Setup ---
        self.pdf_parser_map = {
            "線上轉檔 (推薦免安裝 - 最輕鬆)": "online",
            "輕量化本地提取 (pypdf - 僅限文字PDF)": "pypdf",
            "高精度本地解析 (MinerU - 支援多格式/CPU/GPU)": "mineru",
            "本地 Marker 解析 (僅限PDF/極耗GPU)": "marker"
        }
        
        self.card_document = tk.Frame(self.new_generation_controls_frame, bg=self.COLOR_BG_CARD, highlightbackground=self.COLOR_BORDER, highlightthickness=1, bd=0)
        self.card_document.pack(fill="x", pady=10, ipady=8, ipadx=10)
        
        tk.Label(self.card_document, text="📄 文件解析與來源設定", font=self.FONT_TITLE, fg=self.COLOR_TEXT_PRIMARY, bg=self.COLOR_BG_CARD).pack(anchor="w", padx=10, pady=(10, 8))
        
        parser_row = tk.Frame(self.card_document, bg=self.COLOR_BG_CARD)
        parser_row.pack(fill="x", padx=10, pady=4)
        
        tk.Label(parser_row, text="選擇解析方式:", font=self.FONT_BODY_BOLD, fg=self.COLOR_TEXT_PRIMARY, bg=self.COLOR_BG_CARD).pack(side="left", padx=(0, 10))
        
        self.pdf_parser_combobox = ttk.Combobox(
            parser_row, 
            values=list(self.pdf_parser_map.keys()), 
            state="readonly", 
            width=36
        )
        self.pdf_parser_combobox.set("線上轉檔 (推薦免安裝 - 最輕鬆)")
        self.pdf_parser_combobox.pack(side="left")
        self.pdf_parser_combobox.bind("<<ComboboxSelected>>", self._on_pdf_parser_changed)
        
        self.alert_frame = tk.Frame(self.card_document, bg=self.COLOR_ACCENT_LIGHT, highlightbackground="#bfdbfe", highlightthickness=1, bd=0)
        self.alert_frame.pack(fill="x", padx=10, pady=8, ipady=6, ipadx=8)
        
        self.pdf_desc_label = tk.Label(self.alert_frame, text="", justify="left", anchor="w", wraplength=420, font=self.FONT_SMALL, fg="#1e40af", bg=self.COLOR_ACCENT_LIGHT)
        self.pdf_desc_label.pack(fill="x", expand=True)
        
        self.pdf_link_label = tk.Label(self.card_document, text="🔗 前往 MinerU 線上轉檔平台", fg=self.COLOR_ACCENT, cursor="hand2", font=("Segoe UI", 9, "underline"), bg=self.COLOR_BG_CARD)
        self.pdf_link_label.pack(anchor="w", padx=10, pady=(0, 5))
        self.pdf_link_label.bind("<Button-1>", lambda e: self.open_link("https://mineru.net/OpenSourceTools/Extractor"))
        
        self.file_label_row = tk.Frame(self.card_document, bg=self.COLOR_BG_CARD)
        self.file_label_row.pack(fill="x", padx=10, pady=(8, 2))
        tk.Label(self.file_label_row, text="選擇要分析的檔案:", font=self.FONT_BODY_BOLD, fg=self.COLOR_TEXT_PRIMARY, bg=self.COLOR_BG_CARD).pack(side="left")
        
        file_input_row = tk.Frame(self.card_document, bg=self.COLOR_BG_CARD)
        file_input_row.pack(fill="x", padx=10, pady=4)
        
        self.source_file_entry = tk.Entry(file_input_row, textvariable=self.source_file_path, font=self.FONT_BODY, bg="#f1f5f9", fg=self.COLOR_TEXT_PRIMARY,
                                          insertbackground=self.COLOR_TEXT_PRIMARY, relief="flat", highlightthickness=1,
                                          highlightbackground=self.COLOR_BORDER, highlightcolor=self.COLOR_BORDER_FOCUS)
        self.source_file_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        def on_src_focus_in(e): self.source_file_entry.config(highlightbackground=self.COLOR_BORDER_FOCUS)
        def on_src_focus_out(e): self.source_file_entry.config(highlightbackground=self.COLOR_BORDER)
        self.source_file_entry.bind("<FocusIn>", on_src_focus_in)
        self.source_file_entry.bind("<FocusOut>", on_src_focus_out)
        
        browse_file_btn = self.create_button(file_input_row, "瀏覽...", self.browse_files, btn_type="secondary")
        browse_file_btn.pack(side="right")
        
        # Trigger description init
        self._on_pdf_parser_changed()

        # --- Card 3: Quality & Custom Settings ---
        self.card_settings = tk.Frame(self.new_generation_controls_frame, bg=self.COLOR_BG_CARD, highlightbackground=self.COLOR_BORDER, highlightthickness=1, bd=0)
        self.card_settings.pack(fill="x", pady=(10, 0), ipady=8, ipadx=10)
        
        tk.Label(self.card_settings, text="⚙️ 生成品質與自訂指令", font=self.FONT_TITLE, fg=self.COLOR_TEXT_PRIMARY, bg=self.COLOR_BG_CARD).pack(anchor="w", padx=10, pady=(10, 8))
        
        rework_title_row = tk.Frame(self.card_settings, bg=self.COLOR_BG_CARD)
        rework_title_row.pack(fill="x", padx=10, pady=2)
        tk.Label(rework_title_row, text="設定最大修正審查次數 (0-10):", font=self.FONT_BODY_BOLD, fg=self.COLOR_TEXT_PRIMARY, bg=self.COLOR_BG_CARD).pack(side="left")
        
        rework_grid = tk.Frame(self.card_settings, bg=self.COLOR_BG_CARD)
        rework_grid.pack(fill="x", padx=10, pady=4)
        rework_grid.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="rework_col")
        
        def add_spinbox(grid, text, row, col, default_val):
            cell = tk.Frame(grid, bg=self.COLOR_BG_CARD)
            cell.grid(row=row, column=col, sticky="nsew", padx=4, pady=2)
            tk.Label(cell, text=text, font=self.FONT_BODY, fg=self.COLOR_TEXT_MUTED, bg=self.COLOR_BG_CARD).pack(side="left", padx=(0, 5))
            sb = tk.Spinbox(cell, from_=0, to=10, width=4, font=self.FONT_BODY_BOLD, justify="center",
                            bg="#f1f5f9", fg=self.COLOR_TEXT_PRIMARY, relief="flat", highlightthickness=1,
                            highlightbackground=self.COLOR_BORDER, highlightcolor=self.COLOR_BORDER_FOCUS)
            sb.pack(side="left")
            sb.delete(0, "end")
            sb.insert(0, str(default_val))
            
            def on_sb_focus_in(e, widget=sb): widget.config(highlightbackground=self.COLOR_BORDER_FOCUS)
            def on_sb_focus_out(e, widget=sb): widget.config(highlightbackground=self.COLOR_BORDER)
            sb.bind("<FocusIn>", on_sb_focus_in)
            sb.bind("<FocusOut>", on_sb_focus_out)
            return sb
            
        self.analysis_reworks_spinbox = add_spinbox(rework_grid, "分析", 0, 0, 6)
        self.plan_reworks_spinbox = add_spinbox(rework_grid, "規劃", 0, 1, 5)
        self.slide_reworks_spinbox = add_spinbox(rework_grid, "簡報", 0, 2, 5)
        self.memo_reworks_spinbox = add_spinbox(rework_grid, "講稿", 0, 3, 3)

        options_row = tk.Frame(self.card_settings, bg=self.COLOR_BG_CARD)
        options_row.pack(fill="x", padx=10, pady=6)
        self.svg_checkbox = tk.Checkbutton(options_row, text="生成視覺 SVG 素材 (實驗性功能，會增加 token 用量)",
                                           variable=self.generate_svg, font=self.FONT_BODY, fg=self.COLOR_TEXT_PRIMARY,
                                           bg=self.COLOR_BG_CARD, activebackground=self.COLOR_BG_CARD, selectcolor="#ffffff")
        self.svg_checkbox.pack(side="left")
        
        instr_label_row = tk.Frame(self.card_settings, bg=self.COLOR_BG_CARD)
        instr_label_row.pack(fill="x", padx=10, pady=(6, 2))
        tk.Label(instr_label_row, text="自訂指令 (選填):", font=self.FONT_BODY_BOLD, fg=self.COLOR_TEXT_PRIMARY, bg=self.COLOR_BG_CARD).pack(side="left")
        
        instr_text_row = tk.Frame(self.card_settings, bg=self.COLOR_BG_CARD)
        instr_text_row.pack(fill="x", padx=10, pady=(0, 8))
        self.custom_instruction_text = scrolledtext.ScrolledText(
            instr_text_row, height=2, state="normal", font=self.FONT_BODY,
            bg="#f1f5f9", fg=self.COLOR_TEXT_PRIMARY, insertbackground=self.COLOR_TEXT_PRIMARY, relief="flat",
            highlightthickness=1, highlightbackground=self.COLOR_BORDER, highlightcolor=self.COLOR_BORDER_FOCUS
        )
        self.custom_instruction_text.pack(fill="x", expand=True)
        def on_txt_focus_in(e): self.custom_instruction_text.config(highlightbackground=self.COLOR_BORDER_FOCUS)
        def on_txt_focus_out(e): self.custom_instruction_text.config(highlightbackground=self.COLOR_BORDER)
        self.custom_instruction_text.bind("<FocusIn>", on_txt_focus_in)
        self.custom_instruction_text.bind("<FocusOut>", on_txt_focus_out)

        self.new_generation_controls_frame.grid_columnconfigure(0, weight=1)

        # Common elements (will be packed in toggle_mode_inputs)
        self.run_button = self.create_button(self.left_pane, "🚀 開始簡報生成 (Start Generation)", self.run_orchestration, btn_type="primary")
        self.progress_label = tk.Label(self.right_pane, text="📊 執行進度與詳細日誌 (Console Log):", font=self.FONT_TITLE, fg=self.COLOR_TEXT_PRIMARY, bg=self.COLOR_BG_WINDOW)
        
        # --- AI Auditor Dashboard Panel ---
        self.auditor_frame = tk.Frame(self.right_pane, bg=self.COLOR_BG_CARD, highlightbackground=self.COLOR_BORDER, highlightthickness=1, bd=0)
        self.auditor_frame.pack(fill="x", pady=(0, 15), padx=10, ipady=8)
        
        header_row = tk.Frame(self.auditor_frame, bg=self.COLOR_BG_CARD)
        header_row.pack(fill="x", padx=15, pady=(10, 8))
        tk.Label(header_row, text="🤖 AI 品質審查看板 (AI Auditor Dashboard)", font=self.FONT_TITLE, fg=self.COLOR_ACCENT, bg=self.COLOR_BG_CARD).pack(side="left")
        
        dashboard_grid = tk.Frame(self.auditor_frame, bg=self.COLOR_BG_CARD)
        dashboard_grid.pack(fill="x", padx=15, pady=5)
        
        tk.Label(dashboard_grid, text="審查階段", font=self.FONT_BODY_BOLD, bg=self.COLOR_BG_CARD, fg=self.COLOR_TEXT_MUTED).grid(row=0, column=0, sticky="w", pady=6)
        tk.Label(dashboard_grid, text="審查狀態與當前處理", font=self.FONT_BODY_BOLD, bg=self.COLOR_BG_CARD, fg=self.COLOR_TEXT_MUTED).grid(row=0, column=1, sticky="w", padx=30, pady=6)
        tk.Label(dashboard_grid, text="重製次數", font=self.FONT_BODY_BOLD, bg=self.COLOR_BG_CARD, fg=self.COLOR_TEXT_MUTED).grid(row=0, column=2, sticky="e", pady=6)
        
        self.phase_status_vars = {}
        self.phase_rework_counts = {}
        self.phase_status_labels = {}
        self.phase_rework_labels = {}
        
        phases_info = [
            ("phase1", "1. 文獻分析審查 (Analysis)"),
            ("phase2", "2. 教學架構審查 (Planning)"),
            ("phase3", "3. 簡報排版審查 (Slide Gen)"),
            ("phase4", "4. 備忘講稿審查 (Speaker Notes)"),
            ("phase5", "5. 視覺素材審查 (Visual SVGs)")
        ]
        
        for idx, (key, name) in enumerate(phases_info):
            row = idx + 1
            tk.Label(dashboard_grid, text=name, font=self.FONT_BODY, bg=self.COLOR_BG_CARD, fg=self.COLOR_TEXT_PRIMARY).grid(row=row, column=0, sticky="w", pady=5)
            
            status_var = tk.StringVar(value="⚪ 待命 (Idle)")
            self.phase_status_vars[key] = status_var
            lbl = tk.Label(dashboard_grid, textvariable=status_var, font=self.FONT_BODY_BOLD, bg=self.COLOR_BG_CARD, fg=self.COLOR_TEXT_MUTED)
            lbl.grid(row=row, column=1, sticky="w", padx=30, pady=5)
            self.phase_status_labels[key] = lbl
            
            rework_var = tk.StringVar(value="0")
            self.phase_rework_counts[key] = 0
            rlbl = tk.Label(dashboard_grid, textvariable=rework_var, font=self.FONT_BODY_BOLD, bg=self.COLOR_BG_CARD, fg=self.COLOR_TEXT_PRIMARY)
            rlbl.grid(row=row, column=2, sticky="e", pady=5)
            self.phase_rework_labels[key] = (rework_var, rlbl)
            
        dashboard_grid.grid_columnconfigure(0, weight=3)
        dashboard_grid.grid_columnconfigure(1, weight=3)
        dashboard_grid.grid_columnconfigure(2, weight=1)

        # Console
        self.console = scrolledtext.ScrolledText(self.right_pane, wrap=tk.WORD, state="disabled", bg="#0f172a", fg="#f8fafc",
                                                 font=self.FONT_CONSOLE, insertbackground="white", bd=0, highlightthickness=1, highlightbackground=self.COLOR_BORDER)

        # Initial toggle
        self.toggle_mode_inputs()

    def create_button(self, parent, text, command, btn_type="primary"):
        if btn_type == "primary":
            bg_color = self.COLOR_ACCENT
            fg_color = "#ffffff"
            hover_color = self.COLOR_ACCENT_HOVER
        elif btn_type == "success":
            bg_color = self.COLOR_SUCCESS
            fg_color = "#ffffff"
            hover_color = "#059669"
        else:  # secondary
            bg_color = "#f1f5f9"
            fg_color = self.COLOR_TEXT_PRIMARY
            hover_color = "#e2e8f0"
        
        btn = tk.Button(parent, text=text, command=command, font=self.FONT_BODY_BOLD, bg=bg_color, fg=fg_color,
                        activebackground=hover_color, activeforeground=fg_color, relief="flat", bd=0, padx=12, pady=6, cursor="hand2")
        
        def on_enter(e):
            btn.config(bg=hover_color)
        def on_leave(e):
            btn.config(bg=bg_color)
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        return btn

    def _on_mousewheel(self, event):
        self.image_canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def open_link(self, url: str):
        webbrowser.open(url)

    def browse_files(self):
        # Check selected parser in combobox
        parser_key = self.pdf_parser_combobox.get()
        internal_parser = self.pdf_parser_map.get(parser_key, "online")
        
        if internal_parser == "online":
            # Restrict to plain text formats
            filetypes = [
                ("Text/Markdown Files", "*.txt;*.md;*.html;*.htm"),
                ("Markdown", "*.md"),
                ("Text", "*.txt"),
                ("HTML", "*.html"),
                ("All Files", "*.*")
            ]
        else:
            # Allow all files including PDF, DOCX, PPTX, XLSX
            filetypes = [
                ("All Supported Files", "*.txt;*.md;*.html;*.htm;*.pdf;*.docx;*.pptx;*.xlsx"),
                ("PDF", "*.pdf"),
                ("Word/PPT/Excel", "*.docx;*.pptx;*.xlsx"),
                ("Text/Markdown", "*.txt;*.md;*.html"),
                ("All Files", "*.*")
            ]
            
        filepath = filedialog.askopenfilename(filetypes=filetypes)
        if filepath: self.source_file_path.set(os.path.abspath(filepath))


    def _on_pdf_parser_changed(self, *args):
        parser_key = self.pdf_parser_combobox.get()
        internal_parser = self.pdf_parser_map.get(parser_key, "online")
        
        descriptions = {
            "online": (
                "🌐 推薦免安裝方案：完全不需要在您的電腦安裝任何機器學習套件！\n\n"
                "💡 做法：請點擊下方連結前往 MinerU 線上轉換平台，將您的 PDF/Office 檔案上傳轉檔，"
                "下載取得 Markdown (.md) 檔案後，在上方重新點選該 .md 檔案即可開始生成。"
            ),
            "pypdf": (
                "⚡ 特點：提取速度極快（毫秒級），套件僅約 1.5MB，完全在本地安全執行，不需額外權重。\n\n"
                "⚠️ 限制：僅適用於數位直接生成的 PDF（非掃描圖片檔）。不支援公式 Latex 轉換，"
                "多欄位或複雜表格的提取排版可能會錯亂。\n"
                "⚙️ 需求：專案啟動時會自動在虛擬環境中安裝 `pypdf`（已整合於 requirements 中）。"
            ),
            "mineru": (
                "🧠 特點：最強大的本地開源多格式解析引擎。支援公式 Latex 轉換、表格轉 HTML、多欄排版與 OCR 識別，"
                "原生支援 PDF/DOCX/PPTX/XLSX。\n\n"
                "⚠️ 限制：需要在本地下載約 20GB 模型。CPU 模式可用，但強烈建議電腦記憶體大於 16GB。\n"
                "⚙️ 需求：需在虛擬環境手動執行 `pip install mineru[all]` 並配置環境。"
            ),
            "marker": (
                "🔬 特點：專門針對 PDF 轉 Markdown 設計的高精度引擎，對科學論文、排版與公式 Latex 支援佳。\n\n"
                "⚠️ 限制：在 CPU 下執行非常慢（單頁需 10-20 秒），必須配合 Nvidia/Apple GPU，且商用授權有限制。\n"
                "⚙️ 需求：需手動執行 `pip install marker-pdf` 並配置 PyTorch 和權重下載。"
            )
        }
        
        self.pdf_desc_label.config(text=descriptions.get(internal_parser, ""))
        
        # Show link only for online mode
        if internal_parser == "online":
            self.pdf_link_label.pack(anchor="w", padx=10, pady=(0, 5), before=self.file_label_row)
        else:
            self.pdf_link_label.pack_forget()

    def browse_resume_output_dir(self):
        dirpath = filedialog.askdirectory()
        if dirpath: self.resume_output_dir_path.set(os.path.abspath(dirpath))

    def browse_video_output_dir(self):
        dirpath = filedialog.askdirectory(title="選擇簡報輸出資料夾 (必須包含 slides/ 和 notes/)")
        if dirpath: self.video_output_dir_path.set(os.path.abspath(dirpath))

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
                
                row_frame = tk.Frame(self.slide_rows_frame, bg="#f8fafc")
                row_frame.pack(fill="x", pady=4, padx=5)

                tk.Label(row_frame, text=f"頁面 {idx+1}:", font=self.FONT_BODY_BOLD, bg="#f8fafc", fg=self.COLOR_TEXT_PRIMARY, anchor="w").grid(row=0, column=0, padx=(5,5), sticky="w")
                
                tk.Label(row_frame, text="對應圖片:", font=self.FONT_BODY, bg="#f8fafc", fg=self.COLOR_TEXT_MUTED, anchor="e").grid(row=0, column=1, padx=(5,5))
                img_var = tk.StringVar()
                img_entry = tk.Entry(row_frame, textvariable=img_var, font=self.FONT_BODY, bg="#ffffff", fg=self.COLOR_TEXT_PRIMARY,
                                     insertbackground=self.COLOR_TEXT_PRIMARY, relief="flat", highlightthickness=1,
                                     highlightbackground=self.COLOR_BORDER, highlightcolor=self.COLOR_BORDER_FOCUS)
                img_entry.grid(row=0, column=2, padx=5, sticky="ew")
                
                def on_ie_focus_in(e, widget=img_entry): widget.config(highlightbackground=self.COLOR_BORDER_FOCUS)
                def on_ie_focus_out(e, widget=img_entry): widget.config(highlightbackground=self.COLOR_BORDER)
                img_entry.bind("<FocusIn>", on_ie_focus_in)
                img_entry.bind("<FocusOut>", on_ie_focus_out)
                
                btn = self.create_button(row_frame, "瀏覽", lambda p=img_var: self._browse_image_for_slide(p), btn_type="secondary")
                btn.grid(row=0, column=3, padx=5)
                
                row_frame.grid_columnconfigure(2, weight=1)
                
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
        
        # Remove all mode frames
        self.new_generation_controls_frame.pack_forget()
        self.resume_output_dir_frame.pack_forget()
        self.embed_images_frame.pack_forget()
        self.video_generation_frame.pack_forget()
        
        # Remove common elements (they'll be re-added)
        self.run_button.pack_forget()
        self.progress_label.pack_forget()
        self.console.pack_forget()
        
        # Pack mode-specific frame
        if mode == "new_generation":
            self.new_generation_controls_frame.pack(fill="both", expand=True, pady=10)
        elif mode == "resume":
            self.resume_output_dir_frame.pack(fill="x", pady=10)
        elif mode == "embed_images":
            self.embed_images_frame.pack(fill="both", expand=True, pady=10)
        elif mode == "video_generation":
            self.video_generation_frame.pack(fill="both", expand=True, pady=10)
        
        # Pack common elements AFTER mode frame
        self.run_button.pack(pady=10, fill="x", padx=10, side="bottom")
        self.progress_label.pack(pady=5, padx=10, anchor="w")
        self.console.pack(pady=5, padx=10, fill="both", expand=True)

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
                    port = result.url.split(':')[-1] if ':' in result.url else ''
                    self.agent_status_label.config(
                        text=f"({result.type} @ {port})",
                        fg="#4caf50"
                    )
                    self.agent_status_label.config(cursor="")
                    
                    # Update API base URL
                    base_url = result.url
                    if "/v1" not in base_url:
                        base_url += "/v1"
                    self.api_base_var.set(base_url)
                
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
            source_file = self.source_file_path.get().strip()
            command.extend(["--source", source_file])
            
            # PDF/Document parser parameter handling
            ext = os.path.splitext(source_file)[1].lower()
            if ext in [".pdf", ".docx", ".pptx", ".xlsx"]:
                parser_key = self.pdf_parser_combobox.get()
                internal_parser = self.pdf_parser_map.get(parser_key, "online")
                if internal_parser == "online":
                    messagebox.showinfo(
                        "線上轉檔說明", 
                        "您選擇了「線上轉檔」模式。\n\n"
                        "請按照以下步驟操作：\n"
                        "1. 點擊介面中的連結，或前往瀏覽器開啟：\n   https://mineru.net/OpenSourceTools/Extractor\n"
                        "2. 上傳您的檔案進行轉檔，完成後下載 Markdown (.md) 檔案。\n"
                        "3. 點擊「瀏覽」重新選擇該轉檔後的 .md 檔案，再點擊「開始生成」。"
                    )
                    return
                else:
                    # Check for missing dependencies
                    missing_dep = None
                    install_command = ""
                    
                    if internal_parser == "pypdf":
                        try:
                            import pypdf
                        except ImportError:
                            missing_dep = "pypdf"
                            install_command = "pip install pypdf"
                    elif internal_parser == "mineru":
                        import shutil
                        if not shutil.which("mineru"):
                            missing_dep = "MinerU"
                            install_command = "pip install mineru[all]"
                    elif internal_parser == "marker":
                        import shutil
                        if not shutil.which("marker_single"):
                            missing_dep = "Marker"
                            install_command = "pip install marker-pdf"
                    
                    if missing_dep:
                        messagebox.showwarning(
                            "缺少依賴套件", 
                            f"您選擇的解析方式【{parser_key}】需要安裝額外的系統依賴，但系統在您的環境中找不到該套件。\n\n"
                            "建議解決方案：\n"
                            "1. 🌐 使用免安裝方案：\n"
                            "   點擊連結前往線上平台轉檔為 Markdown 後下載回來使用（最推薦）：\n"
                            "   https://mineru.net/OpenSourceTools/Extractor\n\n"
                            "2. 💻 安裝本地套件（依照您的電腦硬體需求）：\n"
                            "   請在您的 Python 虛擬環境中執行以下安裝指令：\n"
                            f"   {install_command}"
                        )
                        return
                    
                    command.extend(["--pdf-parser", internal_parser])
            
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
                if int(self.analysis_reworks_spinbox.get()) >= 0: command.extend(["--analysis-reworks", self.analysis_reworks_spinbox.get()])
            except ValueError:
                self.log_message("警告：分析修正次數不是有效的數字，將使用預設值。\n")
            
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
        
        elif self.mode_selection.get() == "video_generation":
            # Video Generation Mode
            if not self.video_output_dir_path.get():
                messagebox.showwarning("警告", "請選擇簡報輸出資料夾")
                return
            
            output_dir = self.video_output_dir_path.get()
            if not os.path.isdir(output_dir):
                messagebox.showerror("錯誤", f"資料夾不存在: {output_dir}")
                return
            
            # Check for slides/ and notes/ directories
            if not os.path.isdir(os.path.join(output_dir, "slides")):
                messagebox.showerror("錯誤", "找不到 slides/ 資料夾\n\n請先使用「全新生成」模式產生簡報")
                return
            
            if not os.path.isdir(os.path.join(output_dir, "notes")):
                messagebox.showerror("錯誤", "找不到 notes/ 資料夾\n\n請先使用「全新生成」模式產生簡報")
                return
            
            command = [sys.executable, "scripts/video_pipeline.py", "--output-dir", output_dir, "--enable-video"]
            self.log_message(f"開始生成影片...\n")
            self.log_message(f"DEBUG output_dir type: {type(output_dir)} value: {repr(output_dir)}\n")
            self.log_message(f"DEBUG command: {command}\n")
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
        
        # Clear previous console output
        self.console.config(state="normal")
        self.console.delete("1.0", tk.END)
        self.console.config(state="disabled")
        
        # Reset auditor dashboard
        for k in ["phase1", "phase2", "phase3", "phase4", "phase5"]:
            self._set_phase_status(k, "⚪ 待命 (Idle)", "#70757a")
            self.phase_rework_counts[k] = 0
            self.phase_rework_labels[k][0].set("0")
            self.phase_rework_labels[k][1].config(fg="#202124")
        
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
        
        # Parse message to update quality auditing dashboard in real time
        self._update_auditor_dashboard(message)

    def _set_phase_status(self, phase_key: str, status_text: str, color: str):
        self.phase_status_vars[phase_key].set(status_text)
        self.phase_status_labels[phase_key].config(fg=color)

    def _update_auditor_dashboard(self, message: str):
        # Clean ANSI codes
        clean_msg = re.sub(r'\x1b\[[0-9;]*[mK]', '', message)
        
        # 1. Match Phase transitions
        if "Phase 1: Analysis" in clean_msg:
            self._set_phase_status("phase1", "🔄 審查與分析中...", "#ff9800")
        elif "Phase 2: Planning" in clean_msg:
            self._set_phase_status("phase1", "✅ 審查通過 (OK)", "#4caf50")
            self._set_phase_status("phase2", "🔄 審查與規劃中...", "#ff9800")
        elif "Phase 3: Deck Generation" in clean_msg:
            self._set_phase_status("phase2", "✅ 審查通過 (OK)", "#4caf50")
            self._set_phase_status("phase3", "🔄 簡報生成與排版中...", "#ff9800")
        elif "Phase 4 & 5" in clean_msg or "Parallel Memo & SVG" in clean_msg:
            self._set_phase_status("phase3", "✅ 審查通過 (OK)", "#4caf50")
            self._set_phase_status("phase4", "🔄 備忘稿寫作中...", "#ff9800")
            self._set_phase_status("phase5", "🔄 視覺素材設計中...", "#ff9800")
        elif "Phase 6: Finalizing" in clean_msg:
            for k in ["phase4", "phase5"]:
                current = self.phase_status_vars[k].get()
                if "🔄" in current or "❌" in current or "待命" in current:
                    self._set_phase_status(k, "✅ 審查通過 (OK)", "#4caf50")
            
        # 2. Match QA PASS / REWORK / FAILED tags
        active_phase = None
        for k in ["phase1", "phase2", "phase3", "phase4", "phase5"]:
            current_status = self.phase_status_vars[k].get()
            if "🔄" in current_status or "❌" in current_status:
                active_phase = k
                # If in Phase 4 & 5 parallel run, determine which sub-phase based on log text
                if active_phase == "phase4" and "SVG" in clean_msg:
                    active_phase = "phase5"
                break
        
        if active_phase:
            if "[QA PERFECT PASS]" in clean_msg or "[QA ACCEPTABLE PASS]" in clean_msg or "[QA ACCEPTABLE FALLBACK]" in clean_msg:
                self._set_phase_status(active_phase, "✅ 審查通過 (OK)", "#4caf50")
            elif "[QA REWORK REQUIRED]" in clean_msg or "[QA FAILED]" in clean_msg:
                self.phase_rework_counts[active_phase] += 1
                self.phase_rework_labels[active_phase][0].set(str(self.phase_rework_counts[active_phase]))
                self.phase_rework_labels[active_phase][1].config(fg="#f44336") # Highlight rework count in red
                self._set_phase_status(active_phase, f"❌ 駁回重製 (退回第 {self.phase_rework_counts[active_phase]} 次)", "#f44336")


# Main entry point
def check_dependencies():
    """Check required dependencies before starting UI."""
    missing = []
    
    required_modules = [
        ("requests", "API communication"),
        ("yaml", "Configuration (PyYAML)"),
        ("edge_tts", "TTS generation"),
        ("PIL", "Image processing (Pillow)"),
        ("jinja2", "Template rendering"),
    ]
    
    for module, name in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing.append(name)
    
    if missing:
        return False, missing
    
    return True, []

def check_ffmpeg():
    """Check if FFmpeg is available."""
    import shutil
    return shutil.which("ffmpeg") is not None

def main():
    try:
        # Check dependencies
        print("[Startup] Checking dependencies...")
        ok, missing = check_dependencies()
        
        if not ok:
            print("\n[ERROR] Missing required packages:")
            for pkg in missing:
                print(f"  - {pkg}")
            print("\nPlease install them:")
            print("  pip install -r requirements.txt")
            print("\nOr use the launcher: PPTPlaner.bat")
            import time
            time.sleep(5)
            return
        
        print("[Startup] Creating App...")
        app = App(["Loading models..."])
        print("[Startup] App created, starting mainloop...")
        
        # Check FFmpeg availability
        if not check_ffmpeg():
            import tkinter.messagebox as mb
            mb.showwarning(
                "FFmpeg 未安裝",
                "FFmpeg 未安裝或不在 PATH 中。\n\n"
                "這將影響影片生成功能。\n"
                "您可以稍後安裝，不影響簡報生成。\n\n"
                "安裝選項:\n"
                "1. 手動安裝: https://ffmpeg.org/download.html\n"
                "2. 使用安裝腳本: scripts\\install_ffmpeg.ps1"
            )
        
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
