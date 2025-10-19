#!/usr/bin/env python3
"""
PPTPlaner Orchestrator (Windows-friendly, cross-platform)
- Reads config.yaml
- Invokes selected Agent (codex/gemini/claude) with PLAN/SLIDE/MEMO modes
- Generates slides/ & notes/ page-by-page
- Runs validation & builds the guide (指引.html)
"""

import sys, os, json, subprocess, shutil, argparse, textwrap, time
from pathlib import Path

# --------------------------
# Utilities
# --------------------------

ROOT = Path(__file__).resolve().parents[1]
CFG = ROOT / "config.yaml"
PLAN_JSON = ROOT / ".plan.json"

def fail(msg: str, code: int = 1):
    print(f"✗ {msg}", file=sys.stderr)
    sys.exit(code)

def good(msg: str):
    print(f"✓ {msg}")

def log(msg: str):
    print(f"▶ {msg}")

def read_yaml(path: Path) -> dict:
    try:
        import yaml  # PyYAML
    except ImportError:
        fail("缺少套件：PyYAML。請先執行 `pip install pyyaml` 後再試。")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def ensure_cmd(name: str):
    if shutil.which(name) is None:
        fail(f"找不到指令：{name}。請先安裝或確保在 PATH 中。")

def run_checked(cmd: list[str], input_text: str | None = None) -> subprocess.CompletedProcess:
    """Run a command and raise on non-zero return code."""
    try:
        cp = subprocess.run(
            cmd,
            input=input_text.encode("utf-8") if input_text else None,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False
        )
    except FileNotFoundError:
        fail(f"無法執行指令：{' '.join(cmd)}（檔案或指令不存在）")
    if cp.returncode != 0:
        err = cp.stderr.decode("utf-8", errors="ignore")
        out = cp.stdout.decode("utf-8", errors="ignore")
        fail(f"指令失敗：{' '.join(cmd)}\nSTDOUT:\n{out}\nSTDERR:\n{err}")
    return cp

# --------------------------
# Agent invocation
# --------------------------

def run_agent(agent: str, mode: str, vars_map: dict) -> str:
    """
    呼叫對應 CLI Agent：
      codex: codex run -p MODE -f AGENTS.md --vars key=value ...
      gemini: gemini run -p MODE -f AGENTS.md --vars ...
      claude: claude run -p MODE -f AGENTS.md --vars ...
    備註：實際參數格式可依你的 CLI 做微調。
    """
    agentspec = str(ROOT / "AGENTS.md")

    # 將變數轉換成 --vars key=value 形式
    vars_list = []
    for k, v in vars_map.items():
        vars_list.extend(["--vars", f"{k}={v}"])

    if agent == "codex":
        cmd = ["codex", "run", "-p", mode, "-f", agentspec, *vars_list]
    elif agent == "gemini":
        cmd = ["gemini", "run", "-p", mode, "-f", agentspec, *vars_list]
    elif agent == "claude":
        cmd = ["claude", "run", "-p", mode, "-f", agentspec, *vars_list]
    else:
        fail(f"未知 Agent：{agent}（請使用 codex|gemini|claude）")

    cp = run_checked(cmd)
    return cp.stdout.decode("utf-8", errors="ignore")

# --------------------------
# Main flow
# --------------------------

def main():
    parser = argparse.ArgumentParser(
        description="PPTPlaner Orchestrator (Windows-friendly)"
    )
    parser.add_argument("--source", help="覆寫 config.yaml 的 source_file")
    parser.add_argument("--agent", help="覆寫 config.yaml 的 agent")
    parser.add_argument("--force", action="store_true", help="允許覆寫既有檔案")
    parser.add_argument("--plan-only", action="store_true", help="只做切頁規劃（PLAN）")
    args = parser.parse_args()

    if not CFG.exists():
        fail(f"找不到設定檔：{CFG}")

    cfg = read_yaml(CFG)

    # 讀 config
    source_file = args.source or cfg.get("source_file")
    agent = (args.agent or cfg.get("agent") or "").lower().strip()
    notes_locale = cfg.get("notes_locale", "zh-TW")
    preserve_en = bool(cfg.get("preserve_english_terms", True))
    split_strategy = cfg.get("split_strategy", "semantic")
    max_pages = int(cfg.get("max_pages_per_file", 10))
    memo_per_page = bool(cfg.get("memo_per_page", True))
    memo_tmin = int(cfg.get("memo_target_time_min", 2))
    memo_tmax = int(cfg.get("memo_target_time_max", 3))

    slides_dir = cfg.get("slides_dir", "slides")
    notes_dir = cfg.get("notes_dir", "notes")
    diagrams_dir = cfg.get("diagrams_dir", "diagrams")
    guide_file = cfg.get("guide_file", "指引.html")

    slides_naming = cfg.get("slides_naming", "slides/{page}_{topic}.md")
    notes_naming = cfg.get("notes_naming", "notes/note-{page}_{topic}-zh.md")

    build_guide = bool(cfg.get("build_guide", True))
    auto_open_guide = bool(cfg.get("auto_open_guide", True))

    validate_alignment = bool(cfg.get("validate_alignment", True))
    validate_keywords = bool(cfg.get("validate_keywords", True))
    validate_time = bool(cfg.get("validate_time_estimate", True))

    dual_lang = bool(cfg.get("dual_language", False))
    zip_out = bool(cfg.get("zip_output", True))
    zip_name = cfg.get("zip_name", "PPTPlaner_Package.zip")

    tone = cfg.get("tone", "academic-friendly")

    if not source_file:
        fail("config.yaml 未指定 source_file，或未以 --source 覆寫。")

    source_path = ROOT / source_file
    if not source_path.exists():
        fail(f"找不到來源檔案：{source_path}")

    # 確保資料夾
    (ROOT / slides_dir).mkdir(parents=True, exist_ok=True)
    (ROOT / notes_dir).mkdir(parents=True, exist_ok=True)
    (ROOT / diagrams_dir).mkdir(parents=True, exist_ok=True)

    log(f"讀取設定：{CFG}")
    print(f"  Source: {source_file}")
    print(f"  Agent : {agent}")
    print(f"  Strategy: {split_strategy} | Memo per page: {memo_per_page}")

    # 基本指令提示（可選）
    for needed in []:  # 若要檢查特定 CLI 指令，填在這行
        ensure_cmd(needed)

    # 1) PLAN
    log("規劃切頁（PLAN）…")
    if args.force or not PLAN_JSON.exists():
        out = run_agent(agent, "PLAN", {
            "source_file": str(source_path),
            "split_strategy": split_strategy,
            "max_pages": str(max_pages),
            "notes_locale": notes_locale,
            "memo_per_page": "true" if memo_per_page else "false",
            "preserve_english_terms": "true" if preserve_en else "false",
            "tone": tone
        })
        try:
            plan = json.loads(out)
        except json.JSONDecodeError:
            fail("PLAN 階段輸出不是有效的 JSON。請檢查 AGENTS.md 的 PLAN 規格。")
        with open(PLAN_JSON, "w", encoding="utf-8") as f:
            json.dump(plan, f, ensure_ascii=False, indent=2)
        good(f"已產生切頁計畫：{PLAN_JSON}")
    else:
        with open(PLAN_JSON, "r", encoding="utf-8") as f:
            plan = json.load(f)
        print("  沿用現有 .plan.json（--force 可重建）")

    pages = plan.get("pages") or []
    if not pages:
        fail("PLAN 無任何頁面（pages[] 為空）。")

    if args.plan_only:
        good(f"僅完成 PLAN。頁數：{len(pages)}")
        return

    # 2) 逐頁產出
    log(f"開始逐頁產出（共 {len(pages)} 頁）…")
    for item in pages:
        page = f'{int(item.get("page")):02d}' if str(item.get("page", "")).isdigit() else str(item.get("page"))
        topic = (item.get("topic") or "topic").strip().replace(" ", "_")

        slide_rel = slides_naming.replace("{page}", page).replace("{topic}", topic)
        note_rel  = notes_naming.replace("{page}", page).replace("{topic}", topic)

        slide_abs = ROOT / slide_rel
        note_abs  = ROOT / note_rel

        slide_abs.parent.mkdir(parents=True, exist_ok=True)
        note_abs.parent.mkdir(parents=True, exist_ok=True)

        print(f"— Page {page} · {topic}")

        # SLIDE
        if args.force or not slide_abs.exists():
            slide_out = run_agent(agent, "SLIDE", {
                "source_file": str(source_path),
                "page": page,
                "topic": topic,
                "max_pages": str(max_pages),
                "notes_locale": notes_locale
            })
            slide_abs.write_text(slide_out, encoding="utf-8")
            good(f"Slide 產出：{slide_rel}")
        else:
            print(f"  (略過，已存在) {slide_rel}")

        # MEMO (zh)
        if memo_per_page:
            if args.force or not note_abs.exists():
                memo_out = run_agent(agent, "MEMO", {
                    "source_file": str(source_path),
                    "page": page,
                    "topic": topic,
                    "notes_locale": notes_locale,
                    "preserve_english_terms": "true" if preserve_en else "false",
                    "tone": tone,
                    "memo_time_min": str(memo_tmin),
                    "memo_time_max": str(memo_tmax)
                })
                note_abs.write_text(memo_out, encoding="utf-8")
                good(f"Note 產出：{note_rel}")
            else:
                print(f"  (略過，已存在) {note_rel}")

        # MEMO (en, optional)
        if dual_lang:
            note_en_rel = note_rel.replace("-zh.md", "-en.md")
            note_en_abs = ROOT / note_en_rel
            if args.force or not note_en_abs.exists():
                memo_en_out = run_agent(agent, "MEMO_EN", {
                    "source_file": str(source_path),
                    "page": page,
                    "topic": topic,
                    "notes_locale": "en",
                    "preserve_english_terms": "true",
                    "tone": "academic",
                    "memo_time_min": str(memo_tmin),
                    "memo_time_max": str(memo_tmax)
                })
                note_en_abs.write_text(memo_en_out, encoding="utf-8")
                good(f"Note(EN) 產出：{note_en_rel}")

    # 3) 驗證
    if validate_alignment or validate_keywords or validate_time:
        log("執行驗證（scripts/validate.py）…")
        val_script = ROOT / "scripts" / "validate.py"
        if not val_script.exists():
            print("  （提示）validate.py 尚未建立，本步驟將略過。")
        else:
            cmd = [
                sys.executable, str(val_script),
                "--slides-dir", str(ROOT / slides_dir),
                "--notes-dir", str(ROOT / notes_dir),
                "--check-alignment", str(validate_alignment).lower(),
                "--check-keywords", str(validate_keywords).lower(),
                "--check-time", str(validate_time).lower(),
                "--time-min", str(memo_tmin),
                "--time-max", str(memo_tmax)
            ]
            run_checked(cmd)
            good("驗證通過。")

    # 4) 產出指引
    if build_guide:
        log("產出指引頁（scripts/build_guide.py）…")
        guide_script = ROOT / "scripts" / "build_guide.py"
        if not guide_script.exists():
            print("  （提示）build_guide.py 尚未建立，本步驟將略過。")
        else:
            cmd = [
                sys.executable, str(guide_script),
                "--slides-dir", str(ROOT / slides_dir),
                "--notes-dir", str(ROOT / notes_dir),
                "--output", str(ROOT / guide_file)
            ]
            run_checked(cmd)
            good(f"已產出：{guide_file}")

            if auto_open_guide:
                try:
                    if sys.platform.startswith("win"):
                        os.startfile(str(ROOT / guide_file))  # type: ignore[attr-defined]
                    elif sys.platform == "darwin":
                        run_checked(["open", str(ROOT / guide_file)])
                    else:
                        run_checked(["xdg-open", str(ROOT / guide_file)])
                except Exception:
                    pass

    # 5) 打包
    if zip_out:
        log("打包交付…")
        import zipfile
        with zipfile.ZipFile(ROOT / zip_name, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for rel in (slides_dir, notes_dir, diagrams_dir, guide_file):
                p = ROOT / rel
                if p.is_dir():
                    for fp in p.rglob("*"):
                        if fp.is_file():
                            zf.write(fp, fp.relative_to(ROOT))
                elif p.is_file():
                    zf.write(p, p.relative_to(ROOT))
        good(f"打包完成：{zip_name}")

    print()
    good(f"全部完成！請開啟 {guide_file} 將講稿貼到簡報 Presenter Notes。")

if __name__ == "__main__":
    main()
