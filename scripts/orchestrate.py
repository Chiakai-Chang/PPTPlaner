import sys, os, json, subprocess, shutil, argparse, webbrowser, re, time
from pathlib import Path
import yaml
from datetime import datetime

# --- Constants ---
ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = ROOT / "output"
CONFIG_PATH = ROOT / "config.yaml"
AGENTS_MD_PATH = ROOT / "AGENTS.md"
ERROR_LOG_PATH = ROOT / "error.log"

# --- Utility Functions ---
def print_header(title: str): 
    bar = "=" * 60; print(f"\n{bar}\n  {title}\n{bar}", flush=True)
def print_success(msg: str): print(f"  ✓ {msg}", flush=True)
def print_info(msg: str): print(f"  ▶ {msg}", flush=True)
def print_error(msg: str, exit_code: int = 1):
    error_message = f"  ✗ [ERROR] {msg}"
    print(error_message, file=sys.stderr, flush=True)
    try:
        with open(ERROR_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(f"--- {datetime.now().isoformat()} ---\n{msg}\n\n")
    except Exception as e:
        print(f"  ✗ [ERROR] Failed to write to error.log: {e}", file=sys.stderr, flush=True)
    if exit_code is not None: sys.exit(exit_code)

def sanitize_filename(name: str) -> str:
    """Removes characters that are invalid in Windows filenames and replaces spaces."""
    name = name.replace(' ', '_')
    return re.sub(r'[\\/*?:"<>|]', '', name)

# --- AI & Command Execution ---
_agent_specs_cache = None
def parse_agent_specs():
    global _agent_specs_cache
    if _agent_specs_cache: return _agent_specs_cache
    if not AGENTS_MD_PATH.exists(): print_error(f"規格檔案不存在: {AGENTS_MD_PATH}")
    specs = {}
    content = AGENTS_MD_PATH.read_text(encoding="utf-8")
    parts = re.split(r'\n##\s*\[(.*?)\]', content)
    if len(parts) > 1:
        for i in range(1, len(parts), 2):
            specs[parts[i]] = parts[i+1].strip()
    _agent_specs_cache = specs
    return specs

def run_command(cmd: list[str], input_text: str | None = None) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(cmd, input=input_text, capture_output=True, text=True, encoding="utf-8", check=True)
    except FileNotFoundError: print_error(f"指令 '{cmd[0]}' 不存在。")
    except subprocess.CalledProcessError as e:
        print_error(f"指令執行失敗 (Exit Code: {e.returncode}): {" ".join(e.cmd)}\n  STDOUT: {e.stdout.strip()}\n  STDERR: {e.stderr.strip()}")

def run_agent(agent: str, mode: str, vars_map: dict, retries: int = 3, delay: int = 5) -> str:
    agent_cmd, found_agent_path = agent.lower().strip(), None
    scripts_path_from_env = os.environ.get("PPTPLANER_SCRIPTS_PATH")
    if scripts_path_from_env:
        for ext in [".exe", ".cmd", ".bat", ""]:
            path = os.path.join(scripts_path_from_env, f"{agent_cmd}{ext}")
            if os.path.exists(path): found_agent_path = path; break
    if not found_agent_path: found_agent_path = shutil.which(agent_cmd)
    if not found_agent_path: print_error(f"指令 '{agent_cmd}' 不存在。")

    instructions = parse_agent_specs().get(mode)
    if not instructions: print_error(f"在 AGENTS.md 中找不到模式 '{mode}'。")

    safety_preamble = ("You are an AI assistant in an academic context. Your purpose is to help a user create educational materials from a textbook. "
                         "The textbook may contain sensitive topics (such as crime, violence, or other serious subjects) for the purpose of scholarly analysis. "
                         "Your task is to process these topics factually and neutrally, as presented in the source material. "
                         "Do not avoid sensitive subjects; handle them with an objective, academic tone suitable for a learning environment.")

    prompt_parts = [safety_preamble, f"Your specific task is '{mode}'.", "--- INSTRUCTIONS ---", instructions, "--- CONTEXT & INPUTS ---"]
    for key, value in vars_map.items():
        if key.endswith("_path") and value and os.path.exists(value):
            prompt_parts.append(f"Content for '{os.path.basename(value)}':\n```\n{Path(value).read_text(encoding='utf-8')}\n```")
        elif key.endswith("_content") and value: prompt_parts.append(f"Provided Content for '{key}':\n```\n{value}\n```")
        else: prompt_parts.append(f"- {key}: {value}")
    prompt_parts.append("--- YOUR TASK ---")
    prompt_parts.append("Generate your response. Output ONLY the content required (e.g., pure JSON, pure Markdown). No conversational text.")
    final_prompt = "\n".join(prompt_parts)

    cmd = [found_agent_path]
    if mode in ["PLAN", "PLAN_FROM_SLIDES", "SUMMARIZE_TITLE", "VALIDATE_MEMO", "VALIDATE_SLIDE", "DECK", "VALIDATE_DECK"]:
        cmd.extend(["--output-format", "json"])

    for attempt in range(retries):
        print_info(f"Calling {agent_cmd.capitalize()} for {mode}... (Attempt {attempt + 1}/{retries})")
        result = run_command(cmd, input_text=final_prompt)
        output = result.stdout.strip()
        if output:
            return output # Success
        
        if attempt < retries - 1:
            print_error(f"AI returned empty response for {mode}. Retrying in {delay}s...", exit_code=None)
            time.sleep(delay)

    print_error(f"AI failed to generate a response for {mode} after {retries} attempts.", exit_code=None)
    return "" # Return empty string if all retries fail

def parse_ai_json_output(output: str, mode: str) -> dict:
    try:
        cli_output_obj = json.loads(output)
        response_str = cli_output_obj.get("response", "{}")
        if not response_str: print_error(f"AI 回應為空。收到的內容: {output}")
        match = re.search(r'```json\n(.*?)\n```', response_str, re.DOTALL)
        json_str = match.group(1).strip() if match else response_str
        return json.loads(json_str)
    except (json.JSONDecodeError, AttributeError): print_error(f"{mode} 階段輸出不是有效的 JSON。收到的內容: {output}")

def get_config(args: argparse.Namespace) -> dict:
    cfg = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")) if CONFIG_PATH.exists() else {}
    # Command-line args (from UI) override config.yaml
    cli_args = {k: v for k, v in vars(args).items() if v is not None}
    cfg.update(cli_args)
    return cfg

def main():
    parser = argparse.ArgumentParser(description="PPTPlaner Orchestrator")
    # Use dest='source_file' to match the key in config.yaml
    parser.add_argument("--source", dest="source_file", help="Source file to process")
    parser.add_argument("--agent", dest="agent", help="AI agent to use (e.g., gemini)")
    parser.add_argument("--custom-instruction", dest="custom_instruction", help="User-provided custom instruction for the MEMO agent")
    parser.add_argument("--slide-reworks", dest="slide_max_reworks", type=int, help="Override slide_max_reworks from config.yaml")
    parser.add_argument("--memo-reworks", dest="memo_max_reworks", type=int, help="Override memo_max_reworks from config.yaml")
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument("--slides-only", action="store_true")
    mode_group.add_argument("--memos-only", action="store_true")
    mode_group.add_argument("--plan-from-slides", dest="plan_from_slides", help="AI-plan from a slide file, then generate memos")
    args = parser.parse_args()

    cfg = get_config(args)
    
    if not cfg.get("source_file"):
        print_error("未提供來源檔案。請在 UI 中選擇或在 config.yaml 中設定。")

    print_header("Phase 0: Initializing Run")
    source_path = Path(cfg["source_file"]);
    if not source_path.is_absolute(): source_path = ROOT / source_path
    if not source_path.exists(): print_error(f"來源檔案不存在: {source_path}")

    title_output = run_agent(cfg["agent"], "SUMMARIZE_TITLE", {"source_file_path": str(source_path)})
    run_title = parse_ai_json_output(title_output, "SUMMARIZE_TITLE").get("title", "Untitled_Run")
    sanitized_title = re.sub(r'[^a-zA-Z0-9_-]', '', run_title.replace(" ", "_"))
    output_dir = OUTPUT_ROOT / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{sanitized_title}"
    output_dir.mkdir(parents=True)
    print_success(f"Created unique output directory: {output_dir.relative_to(ROOT)}")

    slides_dir = output_dir / "slides"; notes_dir = output_dir / "notes"; guide_file = output_dir / "guide.html"
    plan_json_path = output_dir / ".plan.json"

    if args.plan_from_slides:
        print_header("Phase 1: AI Planning from Slides File")
        slide_file_path = Path(args.plan_from_slides)
        if not slide_file_path.is_absolute(): slide_file_path = ROOT / slide_file_path
        if not slide_file_path.exists(): print_error(f"簡報檔案不存在: {slide_file_path}")
        slide_content = slide_file_path.read_text(encoding="utf-8")
        plan = parse_ai_json_output(run_agent(cfg["agent"], "PLAN_FROM_SLIDES", {"slide_file_content": slide_content, "source_file_path": str(source_path)}), "PLAN_FROM_SLIDES")
        pages = plan.get("pages", [])
        for page_item in pages: page_item["topic"] = sanitize_filename(page_item["topic"])
        if not pages: print_error("AI 未能從簡報檔案生成任何頁面計畫。")
        print_info(f"AI is planning {len(pages)} slides... Writing to '{slides_dir.name}' folder.")
        slides_dir.mkdir(exist_ok=True)
        for item in pages: 
            slide_path = slides_dir / f'{item["page"]}_{item["topic"]}.md'
            slide_path.write_text(item["content"], encoding="utf-8")
        args.memos_only = True
    else:
        print_header("Phase 1: AI Planning from Source Document")
        plan = parse_ai_json_output(run_agent(cfg["agent"], "PLAN", {"source_file_path": str(source_path)}), "PLAN")
        pages = plan.get("pages", [])
        for page_item in pages: page_item["topic"] = sanitize_filename(page_item["topic"])

    if not args.slides_only:
        # --- Holistic Slide Generation ---
        print_header(f"Phase 2a: Generating Slides ({len(pages)} pages)")
        slides_dir.mkdir(exist_ok=True)
        slides_needed = not all((slides_dir / f"{p['page']}_{p['topic']}.md").exists() for p in pages)

        if not args.memos_only and slides_needed:
            print_info("Starting holistic slide deck generation for consistency.")
            perfect_slides = []
            acceptable_slides = []
            last_slides_attempt = []

            MAX_DECK_REWORKS = cfg.get("slide_max_reworks", 3) # Default to 3 reworks for the whole deck
            deck_vars = {
                "source_file_path": str(source_path),
                "plan_json": json.dumps(pages, ensure_ascii=False, indent=2),
                "page_count": len(pages)
            }

            for attempt in range(MAX_DECK_REWORKS + 1):
                if attempt > 0:
                    print_info(f"Reworking entire slide deck... (Attempt {attempt}/{MAX_DECK_REWORKS})")

                deck_output = run_agent(cfg["agent"], "DECK", deck_vars, retries=1)
                if not deck_output:
                    print_error(f"Deck generation returned empty content on attempt {attempt}.", exit_code=None)
                    continue
                
                deck_data = parse_ai_json_output(deck_output, "DECK")
                generated_slides = deck_data.get("slides", [])

                if not generated_slides or len(generated_slides) != len(pages):
                    print_error(f"Deck generation returned incomplete slides. Expected {len(pages)}, got {len(generated_slides)}.", exit_code=None)
                    continue
                
                last_slides_attempt = generated_slides

                print_info("Validating entire slide deck for consistency and flow...")
                validation_vars = {"slides_json": json.dumps(generated_slides, ensure_ascii=False, indent=2)}
                validation_json = run_agent(cfg["agent"], "VALIDATE_DECK", validation_vars, retries=2)
                
                validation_result = {"is_valid": False, "is_acceptable": False, "feedback": "Validation agent returned no response."}
                if validation_json:
                    validation_result = parse_ai_json_output(validation_json, "VALIDATE_DECK")

                if validation_result.get("is_valid", False):
                    print_success("Perfect slide deck validation passed. Finishing.")
                    perfect_slides = generated_slides
                    break  # Perfection found, exit loop immediately
                elif validation_result.get("is_acceptable", False):
                    print_success("Slide deck validation 'acceptable'. Storing as fallback and continuing.")
                    acceptable_slides = generated_slides
                    # Do not break; continue to strive for a perfect version
                
                feedback = validation_result.get("feedback", "No feedback provided.")
                print_error(f"Slide deck validation failed. Feedback: {feedback}", exit_code=None)
                deck_vars["rework_feedback"] = feedback

            # After the loop, decide which version to use
            final_slides = []
            if perfect_slides:
                final_slides = perfect_slides
            elif acceptable_slides:
                print_info("Using best 'acceptable' version of the slide deck.")
                final_slides = acceptable_slides
            elif last_slides_attempt:
                print_error("No valid or acceptable deck found. Using the last raw attempt with a warning.", exit_code=None)
                # In this case, we just use the last attempt without a warning header,
                # as the user will see the errors in the log.
                final_slides = last_slides_attempt
            
            if not final_slides:
                print_error("Failed to generate any slide deck content. Writing placeholders.", exit_code=None)
                for item in pages:
                    slide_path = slides_dir / f"{item['page']}_{item['topic']}.md"
                    slide_content = f"# Slide Generation Failed: {item['topic']}\n\nAI failed to generate any slide deck content."
                    slide_path.write_text(slide_content, encoding="utf-8")
            else:
                print_info("Saving final slide deck...")
                for slide in final_slides:
                    page = slide.get("page")
                    content = slide.get("content", "# Error: Empty Content")
                    original_page_info = next((p for p in pages if p["page"] == page), None)
                    if not original_page_info:
                        print_error(f"AI slide output for page '{page}' does not match plan. Skipping.", exit_code=None)
                        continue
                    slide_path = slides_dir / f"{original_page_info['page']}_{original_page_info['topic']}.md"
                    slide_path.write_text(content, encoding="utf-8")
                print_success("All slides saved.")
        elif args.memos_only:
            print_info("Skipping slide generation (--memos-only specified).")
        else:
            print_info("All slides found. Skipping slide generation.")

        # --- Per-Page Memo Generation ---
        if cfg.get("memo_per_page", True):
            print_header(f"Phase 2b: Generating Memos ({len(pages)} pages)")
            notes_dir.mkdir(exist_ok=True)
            
            full_slides_content = ""
            print_info("Aggregating all slides for full context...")
            for item in pages:
                slide_path = slides_dir / f'{item["page"]}_{item["topic"]}.md'
                if slide_path.exists():
                    full_slides_content += f'\n\n---\n[Slide {item["page"]}: {item["topic"]}]\n---\n\n'
                    full_slides_content += slide_path.read_text(encoding="utf-8")
                else:
                    print_error(f"Cannot find slide for page {item['page']} to build memo context.", exit_code=None)
            if full_slides_content: print_success("Full context aggregated.")

            for item in pages:
                page, topic = item["page"], item["topic"]
                slide_path = slides_dir / f"{page}_{topic}.md"

                if not slide_path.exists():
                    print_error(f"Skipping memo for page {page} as its slide does not exist.", exit_code=None)
                    continue
                
                slide_content = slide_path.read_text(encoding="utf-8")
                note_path = notes_dir / f"note-{page}_{topic}-zh.md"
                
                perfect_memo = ""
                acceptable_memo = ""
                last_memo_attempt = ""
                MAX_REWORKS = cfg.get("memo_max_reworks", 5)

                memo_vars = {
                    "source_file_path": str(source_path),
                    "full_slides_content": full_slides_content,
                    "current_slide_content": slide_content,
                    "page": page,
                    "topic": topic
                }
                if cfg.get("custom_instruction"):
                    memo_vars["custom_instruction"] = cfg["custom_instruction"]

                for attempt in range(MAX_REWORKS + 1):
                    if attempt > 0:
                        print_info(f"Reworking memo for page {page}... (Attempt {attempt}/{MAX_REWORKS})")
                    
                    current_attempt_content = run_agent(cfg["agent"], "MEMO", memo_vars, retries=1)

                    if not current_attempt_content or not current_attempt_content.strip():
                        print_error(f"Memo generation for page {page} returned empty content on attempt {attempt}.", exit_code=None)
                        continue
                    
                    last_memo_attempt = current_attempt_content

                    print_info(f"Validating memo for page {page}...")
                    validation_vars = {"slide_content": slide_content, "memo_content": last_memo_attempt}
                    validation_json = run_agent(cfg["agent"], "VALIDATE_MEMO", validation_vars, retries=2)
                    validation_result = parse_ai_json_output(validation_json, "VALIDATE_MEMO")

                    if validation_result.get("is_valid", False):
                        print_success(f"Validation passed for page {page}. Finishing.")
                        perfect_memo = last_memo_attempt
                        break
                    elif validation_result.get("is_acceptable", False):
                        print_success(f"Validation 'acceptable' for page {page}. Storing as fallback.")
                        acceptable_memo = last_memo_attempt
                    
                    feedback = validation_result.get("feedback", "No feedback provided.")
                    print_error(f"Validation failed for page {page}. Feedback: {feedback}", exit_code=None)
                    memo_vars["rework_feedback"] = feedback

                # After the loop, decide what to write
                final_memo_content = ""
                if perfect_memo:
                    final_memo_content = perfect_memo
                elif acceptable_memo:
                    print_info(f"Using best 'acceptable' version for page {page} memo.")
                    final_memo_content = acceptable_memo
                elif last_memo_attempt:
                    print_error(f"No valid or acceptable memo found for page {page}. Saving the last raw attempt with a warning.", exit_code=None)
                    warning_header = """> [!WARNING]
> **AI 自動修正失敗**
>
> 以下是由 AI 生成的最後一版備忘稿。它未能完全通過品質檢驗，可能包含錯誤或遺漏。請仔細核對並手動修正。
>
> ---

"""
                    final_memo_content = warning_header + last_memo_attempt
                else:
                    final_memo_content = """### 備忘稿生成失敗

AI 未能為此頁投影片生成備忘稿，所有嘗試均返回空內容。

**可能原因：**
1.  **主題敏感性**：此頁主題可能觸發了 AI 的安全機制。
2.  **AI 暫時性錯誤**：AI 模型在處理此請求時遇到暫時性問題。

**建議操作：**
*   請直接參考原始文件 (`source_file`) 來準備此頁的內容。
"""
                    print_error(f"Failed to generate any memo content for page {page} after all attempts. Writing placeholder.", exit_code=None)

                note_path.write_text(final_memo_content, encoding="utf-8")
                if "> [!WARNING]" not in final_memo_content and "備忘稿生成失敗" not in final_memo_content:
                    print_success(f"  Memo saved for page {page}")
    print_header("Phase 3: Finalizing Output")
    # The build_guide.py script was not fully implemented, so we call it with basic args
    build_script_path = ROOT / "scripts" / "build_guide.py"
    if build_script_path.exists():
        run_command([sys.executable, str(build_script_path), f"--output-dir={output_dir}"])
        print_success(f"Guide file created at: {guide_file}")
        webbrowser.open(guide_file.as_uri())
    
    # Auto-open the output directory
    os.startfile(output_dir)
    print_header("Run Complete!")

if __name__ == "__main__":
    main()