#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PPTPlaner - Build Guide Page (指引.html)
Windows/macOS/Linux 皆可用。

功能：
- 掃描 slides/ 與 notes/ 目錄，依「頁碼」對齊。
- 盡力從檔名或檔案第一個標題行推測 topic。
- 以 Jinja2 模板（templates/guide.html.j2）生成指引頁。
- 若無 Jinja2 或模板檔不存在，改用內建 HTML 備援模板輸出。

用法：
  python scripts/build_guide.py \
    --slides-dir slides \
    --notes-dir notes \
    --output 指引.html \
    [--template templates/guide.html.j2]
"""

from __future__ import annotations
import argparse
import re
from pathlib import Path
from typing import Dict, List, Optional

# --------------------------------
# Helpers
# --------------------------------

def read_text(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return p.read_text(encoding="utf-8", errors="ignore")

def extract_page_topic(filename: str) -> tuple[Optional[str], Optional[str]]:
    """
    盡量從檔名推斷 page 與 topic。
    - page：第一組連續數字（轉成 2 位數 01, 02, ...）
    - topic：檔名最後一段的英數底線片段（_ 或 - 後面）
    """
    name = filename
    if "." in name:
        name = ".".join(name.split(".")[:-1])

    m_page = re.search(r"(\d{1,3})", name)
    page = None
    if m_page:
        page = f"{int(m_page.group(1)):02d}"

    topic = None
    m_topic = re.search(r"(?:^|[_-])([A-Za-z0-9][\w\-]*)$", name)
    if m_topic:
        topic = m_topic.group(1)
    return page, topic

def first_md_heading(text: str) -> Optional[str]:
    """
    抓取 Markdown 檔中的第一行標題（# ... 或 ## ...）
    """
    for line in text.splitlines():
        if re.match(r"^\s*#{1,6}\s+.+", line):
            return re.sub(r"^\s*#{1,6}\s+", "", line).strip()
    return None

def load_files(folder: Path, kinds=("slides", "notes")) -> Dict[str, Dict[str, Path]]:
    """
    掃描目錄，依頁碼建立對應表：
    return: { page: { "slide": Path or None, "note": Path or None } }
    """
    exts = (".md", ".txt")
    data: Dict[str, Dict[str, Path]] = {}
    for kind in kinds:
        base = folder[kind]
        for p in base.rglob("*"):
            if p.is_file() and p.suffix.lower() in exts:
                page, _ = extract_page_topic(p.name)
                if not page:
                    continue
                data.setdefault(page, {})
                # 若同頁有多檔，保留字母序最前（較穩定）
                if kind[:-1] not in data[page] or str(p) < str(data[page][kind[:-1]]):
                    data[page][kind[:-1]] = p
    return data

def ensure_parent(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)

# --------------------------------
# Jinja2 render (with fallback)
# --------------------------------

def render_html_with_jinja(template_path: Path, context: dict) -> Optional[str]:
    try:
        from jinja2 import Environment, FileSystemLoader, select_autoescape
    except Exception:
        return None
    if not template_path.exists():
        return None
    env = Environment(
        loader=FileSystemLoader(str(template_path.parent)),
        autoescape=select_autoescape(['html', 'xml'])
    )
    tmpl = env.get_template(template_path.name)
    return tmpl.render(**context)

FALLBACK_HTML = r"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>指引｜Slides & Notes Guide</title>
<style>
  :root{ --bg:#ffffff; --fg:#111111; --muted:#6b7280; --card:#f8fafc; --accent:#2563eb; --border:#e5e7eb; }
  .dark{ --bg:#0b1220; --fg:#e5e7eb; --muted:#94a3b8; --card:#0f172a; --accent:#60a5fa; --border:#1f2937; }
  *{box-sizing:border-box}
  body{margin:0; font-family:ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,"Noto Sans TC",Arial,"Apple Color Emoji","Segoe UI Emoji"; background:var(--bg); color:var(--fg);}
  header{position:sticky; top:0; z-index:10; backdrop-filter:saturate(180%) blur(10px); background:color-mix(in srgb, var(--bg) 85%, transparent); border-bottom:1px solid var(--border);}
  .container{max-width:1100px; margin:0 auto; padding:16px;}
  h1{margin:6px 0 2px; font-size:22px;}
  p.subtitle{margin:0 0 10px; color:var(--muted); font-size:14px;}
  .toolbar{display:flex; gap:8px; flex-wrap:wrap; align-items:center; margin:6px 0 10px;}
  input[type="text"], input[type="search"]{padding:10px 12px; border:1px solid var(--border); border-radius:10px; background:var(--card); color:var(--fg); outline:none; min-width:220px;}
  button{padding:10px 12px; border:1px solid var(--border); border-radius:10px; background:var(--card); color:var(--fg); cursor:pointer;}
  button.primary{background:var(--accent); color:white;}
  .grid{display:grid; grid-template-columns: 1fr 1fr; gap:10px; align-items:start;}
  .row{background:var(--card); border:1px solid var(--border); border-radius:14px; padding:12px;}
  .row h3{margin:0 0 8px; font-size:15px;}
  .row small{color:var(--muted);}
  .links{display:flex; gap:8px; margin:6px 0 10px; flex-wrap:wrap;}
  a{color:var(--accent); text-decoration:none;}
  a:hover{text-decoration:underline;}
  textarea{width:100%; min-height:120px; padding:10px; border:1px solid var(--border); border-radius:10px; background:var(--bg); color:var(--fg);}
  .pill{display:inline-flex; align-items:center; gap:6px; padding:4px 10px; border:1px solid var(--border); border-radius:999px; background:var(--card); color:var(--muted); font-size:12px;}
  .footer{color:var(--muted); font-size:12px; padding:20px 0 40px; text-align:center;}
  .hint{font-size:12px; color:var(--muted);}
  .section{margin-top:14px; margin-bottom:6px;}
  .kbd{font-family:ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,"Liberation Mono","Courier New",monospace; font-size:12px; background:var(--card); border:1px solid var(--border); padding:2px 6px; border-radius:6px;}
  .hr{height:1px; background:var(--border); margin:10px 0;}
</style>
</head>
<body>
<header>
  <div class="container">
    <h1>指引｜Slides & Notes Guide</h1>
    <p class="subtitle">快速對照 <span class="pill">slides/</span> 與 <span class="pill">notes/</span>，搜尋、複製講稿（Traditional Chinese，保留英文術語）</p>
    <div class="toolbar">
      <input id="search" type="search" placeholder="搜尋頁碼 / 主題 / 檔名（Search page / topic / filename）" />
      <button id="dark" class="primary">🌙 切換深色（Dark Mode）</button>
      <span class="hint">提示：點 <span class="kbd">Copy</span> 可一鍵複製本頁講稿到 Presenter Notes。</span>
    </div>
  </div>
</header>

<main class="container">
  <div class="hr"></div>
  <div id="grid" class="grid"></div>
</main>

<footer class="footer">
  <div class="container"><div class="hr"></div>
    <p>© PPTPlaner · 指引頁（Guide）— 支援 Codex CLI / Gemini CLI / Claude Code</p>
  </div>
</footer>

<script>
(function(){
  const data = {{ rows_json | safe }};

  // Dark mode
  const setDark = (on) => { document.documentElement.classList.toggle('dark', !!on); localStorage.setItem('pp_dark',''+(on?1:0)); };
  setDark(localStorage.getItem('pp_dark')==='1');
  document.getElementById('dark').addEventListener('click', ()=> setDark(!(localStorage.getItem('pp_dark')==='1')));

  const grid = document.getElementById('grid');

  function render(list){
    grid.innerHTML='';
    list.forEach((r)=>{
      const box = document.createElement('div');
      box.className='row';
      box.innerHTML = `
        <h3>第 <b>${r.page}</b> 頁｜${r.topic?('Topic: '+r.topic):''} <small>${r.slide_name}</small></h3>
        <div class="links">
          <span><small>Slide：</small><a href="${r.slide_path}" target="_blank" rel="noopener">${r.slide_path}</a></span>
          <span><small>Note：</small><a href="${r.note_path||'#'}" target="_blank" rel="noopener">${r.note_path||''}</a></span>
        </div>
        <textarea class="memo" placeholder="（把本頁講稿貼在這，再按 Copy）"></textarea>
        <div class="links">
          <button class="copy">Copy</button>
          <span class="hint">${r.heading?('First heading: '+r.heading):''}</span>
        </div>
      `;
      const btn = box.querySelector('.copy');
      const ta  = box.querySelector('.memo');
      btn.addEventListener('click', ()=>{
        ta.select(); document.execCommand('copy');
        btn.textContent='已複製 Copied';
        setTimeout(()=>btn.textContent='Copy', 900);
      });
      grid.appendChild(box);
    });
  }

  // search
  const q = document.getElementById('search');
  q.addEventListener('input', ()=>{
    const s = q.value.toLowerCase().trim();
    if(!s){ render(data); return; }
    const filtered = data.filter(r=>{
      const blob = (r.page+' '+(r.topic||'')+' '+r.slide_path+' '+(r.note_path||'')+' '+(r.heading||'')).toLowerCase();
      return blob.includes(s);
    });
    render(filtered);
  });

  render(data);
})();
</script>
</body>
</html>
"""

# --------------------------------
# Build rows & render
# --------------------------------

def main():
    ap = argparse.ArgumentParser(description="Build 指引.html from slides & notes.")
    ap.add_argument("--slides-dir", required=True, help="slides 目錄")
    ap.add_argument("--notes-dir", required=True, help="notes 目錄")
    ap.add_argument("--output", required=True, help="輸出 HTML 檔名（例如 指引.html）")
    ap.add_argument("--template", default="templates/guide.html.j2", help="Jinja2 模板路徑（可省略）")
    args = ap.parse_args()

    slides_dir = Path(args.slides_dir).resolve()
    notes_dir  = Path(args.notes_dir).resolve()
    output     = Path(args.output).resolve()
    template   = Path(args.template).resolve()

    # 掃描檔案
    slides = []
    for p in slides_dir.rglob("*"):
        if p.is_file() and p.suffix.lower() in (".md", ".txt"):
            slides.append(p)

    notes = []
    for p in notes_dir.rglob("*"):
        if p.is_file() and p.suffix.lower() in (".md", ".txt"):
            notes.append(p)

    # 建立 page => paths 對應
    slide_map: Dict[str, Path] = {}
    for p in sorted(slides):
        page, _ = extract_page_topic(p.name)
        if page and (page not in slide_map):
            slide_map[page] = p

    note_map: Dict[str, Path] = {}
    for p in sorted(notes):
        page, _ = extract_page_topic(p.name)
        if page and (page not in note_map):
            note_map[page] = p

    pages_all = sorted(set(slide_map.keys()) | set(note_map.keys()))

    # 準備 rows
    rows = []
    for page in pages_all:
        slide_p = slide_map.get(page)
        note_p  = note_map.get(page)
        topic_guess = None
        slide_name = slide_p.name if slide_p else ''
        if slide_p:
            _, topic_guess = extract_page_topic(slide_p.name)
            heading = first_md_heading(read_text(slide_p)) or ""
        else:
            heading = ""

        rows.append({
            "page": page,
            "topic": topic_guess or "",
            "slide_path": str(slide_p.relative_to(output.parent)) if slide_p else "",
            "note_path":  str(note_p.relative_to(output.parent))  if note_p else "",
            "slide_name": slide_name,
            "heading": heading
        })

    context = {
        "rows": rows,
        "rows_json": __import__("json").dumps(rows, ensure_ascii=False)
    }

    # 先嘗試用 Jinja2 模板
    html = render_html_with_jinja(template, context)
    if html is None:
        # 用內建模板
        html = FALLBACK_HTML.replace("{{ rows_json | safe }}", context["rows_json"])

    ensure_parent(output)
    output.write_text(html, encoding="utf-8")
    print(f"✓ 指引頁已生成：{output}")

if __name__ == "__main__":
    main()
