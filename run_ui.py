import os
import re
import sys
import subprocess
import threading
import webbrowser
import tkinter as tk
from tkinter import filedialog, scrolledtext, font as tkFont, ttk, messagebox
import base64
import mimetypes

import requests

version = "v2.8"

class App(tk.Tk):
    def __init__(self, available_models):
        super().__init__()
        self.available_gemini_models = available_models
        self.title(f"PPTPlaner {version}")
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
        tk.Label(footer_frame, text="Copyright © 2025 Chiakai Chang. All Rights Reserved.", font=("Arial", 8), bg=footer_frame["bg"]).pack(fill="x", pady=(5,0))

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
        tk.Label(self.resume_output_dir_frame, text="選擇現有輸出資料夾 (用於接續生成):").grid(row=0, column=0, columnspan=3, sticky="w", pady=2)
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

        # YouTube Input Section
        yt_frame = tk.Frame(self.embed_images_frame)
        yt_frame.pack(fill="x", padx=5, pady=(0, 5))
        tk.Label(yt_frame, text="YouTube 影片 ID (選填):").pack(side="left")
        self.youtube_id_var = tk.StringVar()
        tk.Entry(yt_frame, textvariable=self.youtube_id_var, width=25).pack(side="left", padx=5)
        tk.Label(yt_frame, text="(例如: dQw4w9WgXcQ)", fg="gray", font=("Arial", 9)).pack(side="left")
        
        # Source URL Input Section
        url_frame = tk.Frame(self.embed_images_frame)
        url_frame.pack(fill="x", padx=5, pady=(0, 5))
        tk.Label(url_frame, text="原文連結 URL (選填):   ").pack(side="left")
        self.source_url_var = tk.StringVar()
        tk.Entry(url_frame, textvariable=self.source_url_var, width=50).pack(side="left", padx=5)

        # Middle section: Scrollable list of slides
        self.slide_list_container = tk.Frame(self.embed_images_frame, bd=2, relief="groove")
        self.slide_list_container.pack(fill="both", expand=True, pady=10)
        
        # Canvas for scrolling
        self.slide_canvas = tk.Canvas(self.slide_list_container)
        self.scrollbar = ttk.Scrollbar(self.slide_list_container, orient="vertical", command=self.slide_canvas.yview)
        self.scrollable_frame = tk.Frame(self.slide_canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.slide_canvas.configure(scrollregion=self.slide_canvas.bbox("all"))
        )
        self.slide_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.slide_canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.slide_canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Bottom section: Generate Button
        ei_bottom_frame = tk.Frame(self.embed_images_frame)
        ei_bottom_frame.pack(fill="x", pady=10)
        tk.Label(ei_bottom_frame, text="注意: 生成後檔案將存為 slide.html，預設位於同一目錄下。").pack(side="left", padx=5)
        tk.Button(ei_bottom_frame, text="生成圖文切換簡報 (slide.html)", command=self.generate_image_slide_html, font=("Arial", 11, "bold"), bg="#c0d8f0").pack(side="right", padx=10)


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
        
        tk.Label(rework_frame, text="規劃:").pack(side="left", padx=(0, 5))
        self.plan_reworks_spinbox = tk.Spinbox(rework_frame, from_=0, to=10, width=5, justify="center")
        self.plan_reworks_spinbox.pack(side="left", padx=(0, 15))
        self.plan_reworks_spinbox.delete(0, "end"); self.plan_reworks_spinbox.insert(0, "3")

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

        # Common elements
        self.run_button = tk.Button(main_frame, text="開始生成", command=self.run_orchestration, font=("Arial", 12, "bold"), bg="#c0d8f0")
        self.progress_label = tk.Label(main_frame, text="執行進度:")
        self.console = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, state="disabled", bg="#f5f5f5")

        # Initial toggle to set correct visibility
        self.toggle_mode_inputs()


    def open_link(self, url): webbrowser.open_new_tab(url)
    def browse_source_file(self): 
        filepath = filedialog.askopenfilename(title="選擇原文書檔案", filetypes=(("Markdown & Text", "*.md *.txt"), ("All files", "*.*")))
        if filepath: self.source_file_path.set(os.path.abspath(filepath))

    def browse_slides_file(self): 
        filepath = filedialog.askopenfilename(title="選擇簡報檔案", filetypes=(("Markdown & Text", "*.md *.txt"), ("All files", "*.*")))
        if filepath: self.slides_file_path.set(os.path.abspath(filepath))

    def browse_resume_output_dir(self):
        dirpath = filedialog.askdirectory(title="選擇現有輸出資料夾")
        if dirpath: self.resume_output_dir_path.set(os.path.abspath(dirpath))

    def browse_guide_html(self):
        filepath = filedialog.askopenfilename(title="選擇 guide.html", filetypes=(("HTML files", "*.html"), ("All files", "*.*")))
        if filepath: self.guide_html_path.set(os.path.abspath(filepath))

    def toggle_mode_inputs(self):
        # Forget everything first
        self.new_generation_controls_frame.pack_forget()
        self.resume_output_dir_frame.pack_forget()
        self.embed_images_frame.pack_forget()
        self.run_button.pack_forget()
        self.progress_label.pack_forget()
        self.console.pack_forget()

        selected_mode = self.mode_selection.get()
        if selected_mode == "new_generation":
            self.new_generation_controls_frame.pack(fill="x")
            self.run_button.pack(pady=15, fill="x", ipady=5)
            self.progress_label.pack(fill="x", anchor="w")
            self.console.pack(pady=5, fill="both", expand=True)
        elif selected_mode == "resume":
            self.resume_output_dir_frame.pack(fill="x")
            self.run_button.pack(pady=15, fill="x", ipady=5)
            self.progress_label.pack(fill="x", anchor="w")
            self.console.pack(pady=5, fill="both", expand=True)
        elif selected_mode == "embed_images":
            self.embed_images_frame.pack(fill="both", expand=True)
            # Note: "run_button" and "console" are NOT used in this mode, 
            # as it has its own "Generate" button and logic.

    def load_slides_from_html(self):
        html_path = self.guide_html_path.get()
        if not html_path or not os.path.exists(html_path):
            messagebox.showerror("錯誤", "請選擇有效的 guide.html 檔案。")
            return

        # Clear existing list
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.slide_image_map = {}

        try:
            with open(html_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Updated regex to find slides with either <h1> or <h2>. 
            # Matches <h1>Slide X</h1> or <h2>Slide X</h2>
            matches = re.findall(r'<h[12]>Slide\s+(.*?)</h[12]>', content)
            
            if not matches:
                messagebox.showinfo("提示", "在檔案中找不到 '<h1>Slide X</h1>' 或 '<h2>Slide X</h2>' 格式的標題。")
                return

            tk.Label(self.scrollable_frame, text=f"找到 {len(matches)} 頁投影片", font=("Arial", 10, "bold")).pack(pady=5, anchor="w")

            for slide_id in matches:
                row_frame = tk.Frame(self.scrollable_frame, pady=2)
                row_frame.pack(fill="x", expand=True)
                
                tk.Label(row_frame, text=f"Slide {slide_id}:", width=10, anchor="w").pack(side="left")
                
                path_var = tk.StringVar()
                self.slide_image_map[slide_id] = path_var
                
                entry = tk.Entry(row_frame, textvariable=path_var)
                entry.pack(side="left", fill="x", expand=True, padx=5)
                
                btn = tk.Button(row_frame, text="選擇圖片", command=lambda sv=path_var: self.browse_image_for_slide(sv))
                btn.pack(side="left")

            # Attempt to auto-match images in the same folder
            self.auto_match_images(html_path, matches)

        except Exception as e:
            messagebox.showerror("錯誤", f"讀取 HTML 時發生錯誤: {e}")

    def browse_image_for_slide(self, string_var):
        f = filedialog.askopenfilename(filetypes=(("Images", "*.png *.jpg *.jpeg *.webp"), ("All files", "*.*")))
        if f: string_var.set(f)

    def auto_match_images(self, html_path, slide_ids):
        """Attempts to find images like 'Slide 1.png' or '1.png' in the same folder."""
        folder = os.path.dirname(html_path)
        count = 0
        for sid in slide_ids:
            # Try various naming conventions
            candidates = [
                f"{sid}.png", f"{sid}.jpg", 
                f"Slide {sid}.png", f"Slide {sid}.jpg",
                f"slide_{sid}.png", f"slide_{sid}.jpg" # standard export format often used
            ]
            for cand in candidates:
                full_path = os.path.join(folder, cand)
                if os.path.exists(full_path):
                    self.slide_image_map[sid].set(full_path)
                    count += 1
                    break
        if count > 0:
             tk.Label(self.scrollable_frame, text=f"已自動匹配 {count} 張圖片", fg="green").pack(anchor="w")

    def generate_image_slide_html(self):
        html_path = self.guide_html_path.get()
        if not html_path or not os.path.exists(html_path):
            messagebox.showerror("錯誤", "原始 guide.html 路徑無效。")
            return

        # Determine output path (default to slide.html in same dir)
        output_dir = os.path.dirname(html_path)
        output_path = filedialog.asksaveasfilename(
            initialdir=output_dir, initialfile="slide.html",
            defaultextension=".html", filetypes=(("HTML files", "*.html"),)
        )
        if not output_path: return

        try:
            with open(html_path, "r", encoding="utf-8") as f:
                content = f.read()

            # --- Source URL Injection ---
            source_url = self.source_url_var.get().strip()
            if source_url:
                # Styled button HTML - Compact version
                # Uses a smaller pill design, inline-flex to sit nicely with other elements
                url_btn_html = f"""
                <a href="{source_url}" target="_blank" style="display: inline-flex; align-items: center; gap: 4px; padding: 4px 10px; margin-top: 8px; background-color: var(--pill); color: var(--accent); text-decoration: none; border-radius: 12px; font-size: 12px; font-weight: 500; border: 1px solid var(--border); transition: all 0.2s;">
                    <span style="font-size: 14px;">🔗</span> 原文連結
                </a>
                """
                # Inject it right after the </em> tag (Author info) to keep it compact
                # If </em> exists, append it there. Otherwise fall back to previous method.
                if '</em>' in content:
                    content = content.replace('</em>', f'</em><br>{url_btn_html}', 1)
                elif '</header>' in content:
                    header_end_idx = content.find('</header>')
                    container_end_idx = content.rfind('</div>', 0, header_end_idx)
                    if container_end_idx != -1:
                        content = content[:container_end_idx] + url_btn_html + content[container_end_idx:]
            
            # --- YouTube Injection ---
            yt_id = self.youtube_id_var.get().strip()
            if yt_id:
                # Simple parser to extract ID if user pastes full URL
                if "v=" in yt_id:
                    try: yt_id = yt_id.split("v=")[1].split("&")[0]
                    except: pass
                elif "youtu.be/" in yt_id:
                    try: yt_id = yt_id.split("youtu.be/")[1].split("?")[0]
                    except: pass
                
                # Responsive Video HTML Block
                # Standard youtube domain is often more reliable for local file playback than nocookie
                video_html = f"""
                <div class="video-section" style="margin-bottom: 30px; margin-top: 10px;">
                    <style>
                        .video-responsive-wrapper {{
                            position: relative;
                            padding-bottom: 56.25%; /* 16:9 Ratio */
                            height: 0;
                            overflow: hidden;
                            border-radius: 12px;
                            background: #000;
                            box-shadow: 0 4px 10px rgba(0,0,0,0.1);
                        }}
                        .video-responsive-wrapper iframe {{
                            position: absolute;
                            top: 0;
                            left: 0;
                            width: 100%;
                            height: 100%;
                            border: 0;
                        }}
                    </style>
                    <div class="video-responsive-wrapper">
                        <iframe 
                            src="https://www.youtube.com/embed/{yt_id}?rel=0" 
                            title="YouTube video player" 
                            frameborder="0" 
                            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" 
                            allowfullscreen>
                        </iframe>
                    </div>
                    <div class="hr" style="margin-top: 20px;"></div>
                </div>
                """
                # Inject immediately after <main class="container">
                if '<main class="container">' in content:
                    content = content.replace('<main class="container">', f'<main class="container">\n{video_html}', 1)

            # Inject CSS and JS
            # We define styles for the toggle button and the image container.
            # We also add sticky positioning to the left column (.slide) so it stays visible 
            # while scrolling through long notes in the right column (.notes).
            style_script = """
            <style>
                :root {
                    --header-height: 80px; /* Fallback initial value */
                }

                .img-text-toggle-btn {
                    padding: 6px 12px;
                    cursor: pointer;
                    background: #4f46e5; /* Indigo-600 */
                    color: white;
                    border: none;
                    border-radius: 6px;
                    font-size: 14px;
                    transition: background 0.2s;
                }
                .img-text-toggle-btn:hover { background: #4338ca; }
                
                .slide-img-container img {
                    max-width: 100%;
                    height: auto;
                    border: 1px solid #e5e7eb;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                }

                /* Layout Improvements for Sticky Slide */
                .page {
                    display: flex;
                    border-bottom: 1px solid var(--border);
                    padding: 30px 0;
                    margin-bottom: 0;
                    align-items: flex-start; /* Align to top */
                }
                
                .slide {
                    flex: 1;
                    padding-right: 30px;
                    border-right: 1px solid var(--border);
                    min-width: 0;
                    position: sticky; /* Make the left column sticky */
                    /* Dynamic top position: Header height + 20px buffer */
                    top: calc(var(--header-height) + 20px);
                    height: fit-content; 
                    /* Dynamic max-height to fit in viewport */
                    max-height: calc(100vh - var(--header-height) - 40px);
                    overflow-y: auto;
                }
                
                .notes {
                    flex: 1;
                    padding-left: 30px;
                    min-width: 0;
                }
                
                /* Mobile Responsiveness: Stack them on small screens */
                @media (max-width: 768px) {
                    .page { display: block; }
                    .slide { 
                        padding-right: 0; 
                        border-right: none; 
                        border-bottom: 1px solid var(--border); 
                        margin-bottom: 20px; 
                        padding-bottom: 20px;
                        position: static; /* Disable sticky on mobile */
                        max-height: none;
                    }
                    .notes { padding-left: 0; }
                }
            </style>
            <script>
                function toggleImageText(id) {
                    var imgDiv = document.getElementById('img-view-' + id);
                    var textDiv = document.getElementById('text-view-' + id);
                    var btn = document.getElementById('btn-toggle-' + id);
                    
                    if (imgDiv.style.display !== 'none') {
                        // Currently showing image, switch to text
                        imgDiv.style.display = 'none';
                        textDiv.style.display = 'block';
                        btn.innerText = '切換為圖片 (Show Image)';
                    } else {
                        // Currently showing text, switch to image
                        imgDiv.style.display = 'block';
                        textDiv.style.display = 'none';
                        btn.innerText = '切換為文字 (Show Text)';
                    }
                }

                // Dynamic Header Height Calculation
                function updateHeaderHeight() {
                    const header = document.querySelector('header');
                    if (header) {
                        const height = header.offsetHeight;
                        document.documentElement.style.setProperty('--header-height', height + 'px');
                    }
                }
                // Update on load and resize
                window.addEventListener('load', updateHeaderHeight);
                window.addEventListener('resize', updateHeaderHeight);
            </script>
            """
            if "</head>" in content:
                content = content.replace("</head>", f"{style_script}</head>")
            else:
                content = style_script + content

            processed_count = 0
            
            # Iterate through map and replace
            for slide_id, path_var in self.slide_image_map.items():
                img_path = path_var.get()
                if not img_path or not os.path.exists(img_path):
                    continue # Skip if no image selected

                # Encode image
                mime_type, _ = mimetypes.guess_type(img_path)
                if not mime_type: mime_type = "image/png"
                with open(img_path, "rb") as img_f:
                    b64_data = base64.b64encode(img_f.read()).decode('utf-8')
                    img_src = f"data:{mime_type};base64,{b64_data}"

                # Robust replacement logic using string search
                # 1. Find the exact string for the text div opening tag
                # We look for the ID pattern to locate it
                search_pattern = re.compile(rf'(<div[^>]*id="text-view-{re.escape(slide_id)}"[^>]*>)')
                match = search_pattern.search(content)
                
                if match:
                    original_tag = match.group(1) # e.g. <div class="..." id="text-view-01">
                    
                    # 2. Construct insertion content
                    insertion = f"""
                    <div class="slide-controls" style="text-align: right; margin-bottom: 8px;">
                    <button id="btn-toggle-{slide_id}" class="img-text-toggle-btn" onclick="toggleImageText('{slide_id}')">切換為文字 (Show Text)</button>
                    </div>
                    <div id="img-view-{slide_id}" class="slide-img-container" style="display:block; margin-bottom:10px;">
                    <img src="{img_src}">
                    </div>
                    """
                    
                    # 3. Create the new block: Insertion + Original Tag + Script to hide text
                    new_block = f'{insertion}{original_tag}<script>document.getElementById("text-view-{slide_id}").style.display="none";</script>'
                    
                    # 4. Replace ONLY the original tag with the new block
                    # Using string replace ensures we don't duplicate surrounding content
                    content = content.replace(original_tag, new_block, 1)
                    processed_count += 1
            
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(content)
            
            messagebox.showinfo("成功", f"已生成 {output_path}\n共處理 {processed_count} 頁投影片。")
            webbrowser.open(output_path)

        except Exception as e:
            messagebox.showerror("錯誤", f"生成過程發生錯誤: {e}")

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

    def _show_generic_api_error_dialog(self, error_type: str, message: str):
        # Log to console as well
        self.log_message(f"\\n====================\\n")
        self.log_message(f"API錯誤 ({error_type})！\\n")
        self.log_message(f"{message}\\n")
        self.log_message(f"點擊 '繼續' 或 '切換模型並繼續' 後程序將嘗試繼續運行。\\n")
        self.log_message(f"====================\\n")

        # Create a Toplevel window for the dialog
        dialog = tk.Toplevel(self)
        dialog.title(f"API 錯誤: {error_type}")
        dialog.transient(self) # Make dialog transient to its parent
        dialog.grab_set() # Make dialog modal

        full_message = (
            f"Gemini API 遇到問題: {error_type}\\n{message}\\n\\n"
            "您可以選擇重新嘗試，或嘗試切換到不同的 Gemini 模型。\\n"
            "點擊 '繼續' 將使用當前模型重試；\\n"
            "選擇一個模型並點擊 '切換模型並繼續' 將嘗試使用新模型。"
        )
        tk.Label(dialog, text=full_message, padx=20, pady=10, justify=tk.LEFT).pack()

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

                # Enhanced Error Detection
                is_quota = (
                    ("Error when talking to Gemini API" in line and "You have exhausted your capacity" in line) or
                    ("API Error" in line and "429" in line)
                )
                
                if is_quota:
                    self.quota_event.clear() # Block the thread
                    self.after(0, lambda: self._show_quota_dialog(quota_reset_time_str))
                    self.quota_event.wait() # Wait for the user to click 'Continue' in the dialog
                
                elif "ECONNRESET" in line or "connection reset" in line:
                    self.quota_event.clear()
                    self.after(0, lambda: self._show_generic_api_error_dialog("網路連線錯誤", "連線被重置 (ECONNRESET)。請檢查網路或稍後重試。"))
                    self.quota_event.wait()
                
                elif "[API Error:" in line:
                    self.quota_event.clear()
                    self.after(0, lambda: self._show_generic_api_error_dialog("API 錯誤", f"發生未預期的 API 錯誤: {line.strip()}"))
                    self.quota_event.wait()
        
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
            plan_reworks = self.plan_reworks_spinbox.get()
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
                if int(plan_reworks) >= 0: command.extend(["--plan-reworks", plan_reworks])
            except ValueError:
                self.log_message("警告：規劃修正次數不是有效的數字，將使用預設值。\n")

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
