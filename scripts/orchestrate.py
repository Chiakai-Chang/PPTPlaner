import sys, os, json, subprocess, shutil, argparse, webbrowser, re, time
from pathlib import Path
import yaml
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Ensure UTF-8 output on Windows
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass # Fallback for older python

# --- Constants ---
ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = ROOT / "output"
CONFIG_PATH = ROOT / "config.yaml"
PROMPTS_DIR = ROOT / "scripts" / "prompts"
ERROR_LOG_PATH = ROOT / "error.log"
PAUSE_LOCK_PATH = ROOT / ".pause_lock"
RUNTIME_CONFIG_PATH = ROOT / ".runtime_config.json"

# --- Research Logger ---
class ResearchLogger:
    def __init__(self, root_dir):
        self.log_dir = root_dir / "logs"
        self.log_dir.mkdir(exist_ok=True)
        self.log_file = self.log_dir / f"{datetime.now().strftime('%Y%m%d%H%M%S')}.log"
        print(f"  ▶ [Research Log] Detailed log being written to: {self.log_file.name}", flush=True)

    def log(self, msg: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] {msg}\n")
        except Exception as e:
            print(f"[Logger Error] {e}", file=sys.stderr)

    def log_separator(self, title: str = ""):
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(f"\n{'='*80}\n{title}\n{'='*80}\n")
        except Exception: pass

    def log_block(self, title: str, content: str):
        self.log(f"--- {title} ---")
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(f"{content}\n")
            self.log(f"--- End of {title} ---\n")
        except Exception: pass

    def log_json(self, title: str, data: dict | list):
        self.log_block(title, json.dumps(data, ensure_ascii=False, indent=2))

_research_logger = None

def init_logger(root_dir: Path):
    global _research_logger
    _research_logger = ResearchLogger(root_dir)

def rlog(msg: str):
    if _research_logger: _research_logger.log(msg)

def rlog_phase(phase_name: str):
    if _research_logger: _research_logger.log_separator(phase_name)

def rlog_data(title: str, data):
    if _research_logger: _research_logger.log_json(title, data)

def rlog_block(title: str, content: str):
    if _research_logger: _research_logger.log_block(title, content)


# --- Utility Functions ---
def print_header(title: str):
    bar = "=" * 80; print(f"\n{bar}\n  ▶ {title}\n{bar}", flush=True)
    rlog_phase(title) # Log header

def print_success(msg: str):
    print(f"  ✓ {msg}", flush=True)
    rlog(f"SUCCESS: {msg}")

def print_info(msg: str):
    print(f"  ℹ {msg}", flush=True)
    rlog(f"INFO: {msg}")

def print_error(msg: str, exit_code: int = 1):
    error_message = f"  ✗ [ERROR] {msg}"
    print(error_message, file=sys.stderr, flush=True)
    rlog(f"ERROR: {msg}")
    try:
        with open(ERROR_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(f"--- {datetime.now().isoformat()} ---\n{msg}\n\n")
    except Exception as e:
        print(f"  ✗ [ERROR] Failed to write to error.log: {e}", file=sys.stderr, flush=True)
    if exit_code is not None: sys.exit(exit_code)

def sanitize_filename(name: str) -> str:
    """Removes characters that are invalid in Windows filenames and replaces spaces."""
    if not name: return "Untitled"
    name = name.replace(' ', '_')
    return re.sub(r'[\\/*?:\"<>|]', '', name)

def fix_svg_layout(svg_code: str) -> str:
    """Ensures SVG has a viewBox and safe padding."""
    if not svg_code or "<svg" not in svg_code: return svg_code
    
    # 1. Ensure viewBox (default 16:9 960x540)
    if 'viewBox="' not in svg_code:
        svg_code = svg_code.replace('<svg', '<svg viewBox="0 0 960 540"', 1)
    
    # 2. Add safe padding by wrapping content in a <g> tag
    # Find the end of the <svg...> tag and start of content
    match = re.search(r'<svg[^>]*>', svg_code)
    if match:
        header_end = match.end()
        # Check if already has our padding group to avoid double wrapping
        if 'id="safe_padding_group"' not in svg_code:
            content = svg_code[header_end:].strip()
            # Remove closing </svg>
            if content.endswith('</svg>'):
                content = content[:-6].strip()
            
            wrapped_content = f'\n  <g id="safe_padding_group" transform="translate(40, 40) scale(0.92)">\n    {content}\n  </g>\n</svg>'
            return svg_code[:header_end] + wrapped_content
            
    return svg_code

# --- AI & Command Execution ---
_agent_specs_cache = None
def parse_agent_specs():
    global _agent_specs_cache
    if _agent_specs_cache: return _agent_specs_cache
    
    if not PROMPTS_DIR.exists():
        print_error(f"Prompts directory not found: {PROMPTS_DIR}")
        
    specs = {}
    for prompt_file in PROMPTS_DIR.glob("*.md"):
        if prompt_file.name.lower() == "readme.md": continue
        mode_name = prompt_file.stem
        try:
            content = prompt_file.read_text(encoding="utf-8").strip()
            specs[mode_name] = content
        except Exception as e:
            print_error(f"Failed to read prompt file {prompt_file.name}: {e}", exit_code=None)

    if not specs: print_error(f"No agent prompts found in {PROMPTS_DIR}")
    _agent_specs_cache = specs
    return specs

def run_command(cmd: list[str], input_text: str | None = None) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(cmd, input=input_text, capture_output=True, text=True, encoding="utf-8", check=True)
    except FileNotFoundError: print_error(f"指令 '{cmd[0]}' 不存在。")
    except subprocess.CalledProcessError as e: raise e

def wait_for_user_action() -> str | None:
    try:
        PAUSE_LOCK_PATH.touch()
    except Exception as e:
        print_error(f"Failed to create pause lock file: {e}", exit_code=None)
        return None

    print(f"  !! [PAUSE_REQUIRED] Execution paused. Waiting for user action...", flush=True)
    rlog("EXECUTION PAUSED: Waiting for user intervention...")

    while PAUSE_LOCK_PATH.exists():
        time.sleep(1)

    print_info("Resuming execution...")
    rlog("EXECUTION RESUMED")

    if RUNTIME_CONFIG_PATH.exists():
        try:
            config = json.loads(RUNTIME_CONFIG_PATH.read_text(encoding="utf-8"))
            new_model = config.get("gemini_model")
            if new_model:
                print_info(f"Switched model to: {new_model}")
                RUNTIME_CONFIG_PATH.unlink() 
                return new_model
        except Exception:
            RUNTIME_CONFIG_PATH.unlink(missing_ok=True)
    
    return None

def run_agent(agent: str, mode: str, vars_map: dict, retries: int = 3, delay: int = 5, model_name: str | None = None) -> str:
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

    safety_preamble_path = PROMPTS_DIR / "_SAFETY_PREAMBLE.md"
    safety_preamble = safety_preamble_path.read_text(encoding="utf-8").strip() if safety_preamble_path.exists() else "You are an AI assistant."

    prompt_parts = [safety_preamble, f"Your specific task is '{mode}'.", "--- INSTRUCTIONS ---", instructions, "--- CONTEXT & INPUTS ---"]
    log_inputs = {}
    rework_feedback = vars_map.get("rework_feedback")

    for key, value in vars_map.items():
        if key == "rework_feedback":
            log_inputs[key] = value
            continue
        if key.endswith("_path") and value and os.path.exists(value):
            file_content = Path(value).read_text(encoding='utf-8')
            prompt_parts.append(f"Content for '{os.path.basename(value)}':\n```\n{file_content}\n```")
            log_inputs[key] = f"[File Content from {os.path.basename(value)}]"
        elif key.endswith("_content") and value: 
            prompt_parts.append(f"Provided Content for '{key}':\n```\n{value}\n```")
            log_inputs[key] = value
        else: 
            prompt_parts.append(f"- {key}: {value}")
            log_inputs[key] = value
    
    if rework_feedback:
        prompt_parts.append("\n" + "="*40 + "\n!!! CRITICAL FEEDBACK !!!\n" + rework_feedback + "\n" + "="*40 + "\n")

    prompt_parts.append("--- YOUR TASK ---")
    prompt_parts.append("Generate your response. Output ONLY the content required (e.g., pure JSON, pure Markdown). No conversational text.")
    final_prompt = "\n".join(prompt_parts)

    current_model_name = model_name
    attempt = 0
    while attempt < retries:
        cmd = [found_agent_path]
        if current_model_name: cmd.extend(["-m", current_model_name])
        if mode in ["PLAN", "PLAN_FROM_SLIDES", "ANALYZE_SOURCE_DOCUMENT", "VALIDATE_ANALYSIS", "VALIDATE_MEMO", "DECK", "VALIDATE_DECK", "VALIDATE_SLIDE_SVG", "VALIDATE_CONCEPTUAL_SVG"]:
            cmd.extend(["--output-format", "json"])

        print_info(f"Calling {agent_cmd.capitalize()} for {mode}... (Attempt {attempt + 1}/{retries})")
        rlog_data(f"Agent Inputs ({mode})", log_inputs)

        try:
            result = run_command(cmd, input_text=final_prompt)
            output = result.stdout.strip()
            rlog_block(f"Agent Raw Output ({mode})", output)
            if output: return output
            attempt += 1
        except subprocess.CalledProcessError as e:
            stderr_lower = e.stderr.lower()
            is_auth_error = "authentication" in stderr_lower or "login required" in stderr_lower
            is_quota_error = "exhausted" in stderr_lower or "quota" in stderr_lower
            
            if is_auth_error: print_error("認證失敗或過期。", exit_code=None)
            elif is_quota_error: print_error("API quota 已用盡。", exit_code=None)
            else: print_error(f"指令執行失敗: {e.stderr.strip()}", exit_code=None)

            new_model = wait_for_user_action()
            if new_model: current_model_name = new_model
            if is_auth_error or is_quota_error or new_model: continue
            attempt += 1

        if attempt < retries: time.sleep(delay)

    print_error(f"AI failed to generate a response for {mode} after {retries} attempts.", exit_code=1)
    return ""

def parse_ai_json_output(output: str, mode: str) -> dict | None:
    json_match = re.search(r'(\{.*\})', output, re.DOTALL)
    if json_match:
        try:
            outer_data = json.loads(json_match.group(1))
            if isinstance(outer_data, dict) and "response" in outer_data and isinstance(outer_data["response"], str):
                 return parse_ai_json_output(outer_data["response"], f"{mode} (Nested)")
        except: pass

    clean_output = output.strip()
    match = re.search(r"```(?:json)?\s*(.*?)```", clean_output, re.DOTALL)
    if match: clean_output = match.group(1).strip()
    else:
        json_match_inner = re.search(r'(\{.*\})', clean_output, re.DOTALL)
        if json_match_inner: clean_output = json_match_inner.group(1).strip()

    try:
        data = json.loads(clean_output)
        if isinstance(data, dict) and "response" in data and isinstance(data["response"], str):
             return parse_ai_json_output(data["response"], f"{mode} (Nested)")
        return data
    except json.JSONDecodeError:
        rlog(f"Standard JSON parse failed for {mode}.")
    
    # Heuristic fallback (simplified for brevity, original logic was preserved)
    if any(x in mode for x in ["DECK", "slides", "PLAN"]):
        extracted_items = []
        raw_text = clean_output
        chunks = re.split(r',?\s*\{\s*"page":', raw_text)
        for chunk in chunks:
            if not chunk.strip(): continue
            item = {}
            p_m = re.search(r'^\s*"(\d+)"', chunk)
            if p_m: item["page"] = p_m.group(1)
            else: continue
            t_m = re.search(r'"topic":\s*"(.*?)"', chunk)
            if t_m: item["topic"] = t_m.group(1)
            c_m = re.search(r'"content":\s*"', chunk)
            if c_m:
                start = c_m.end()
                end = chunk.rfind('"')
                if end > start: item["content"] = chunk[start:end].replace('\\"', '"').replace('\\n', '\n')
            if item.get("page"): extracted_items.append(item)
        if extracted_items:
            if "PLAN" in mode: return {"pages": extracted_items}
            return {"slides": extracted_items}
    return None

def get_config(args: argparse.Namespace) -> dict:
    cfg = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")) if CONFIG_PATH.exists() else {}
    defaults = {'version': '3.9.0', 'plan_max_reworks': 3, 'slide_svg_max_reworks': 5, 'conceptual_svg_max_reworks': 5, 'agent_execution_retries': 3}
    for k, v in defaults.items():
        if k not in cfg: cfg[k] = v
    cfg.update({k: v for k, v in vars(args).items() if v is not None})
    return cfg

def process_memo_page(i, slide, source_path, full_slides_content, notes_dir, glossary_text, cfg, args):
    p_num = str(slide.get("page")).zfill(2)
    p_topic = slide.get("topic", "Topic")
    safe_topic = sanitize_filename(p_topic)
    memo_path = notes_dir / f"note-{p_num}_{safe_topic}-zh.md"

    if memo_path.exists() and memo_path.stat().st_size > 100:
        return p_num, f"Skipped (Exists)"

    memo_vars = {
        "source_file_path": str(source_path),
        "current_slide_content": slide.get("content", ""),
        "full_slides_content": full_slides_content,
        "page": p_num, "topic": p_topic, "glossary": glossary_text,
        "custom_instruction": args.custom_instruction or ""
    }
    
    final_memo, acceptable_memo, feedback_history = "", "", []
    for attempt in range(args.memo_reworks + 1):
        raw = run_agent(cfg["agent"], "MEMO", memo_vars, retries=cfg["agent_execution_retries"], model_name=cfg.get("gemini_model"))
        val_json = run_agent(cfg["agent"], "VALIDATE_MEMO", {"memo_content": raw, "slide_content": slide.get("content", "")}, retries=cfg["agent_execution_retries"], model_name=cfg.get("gemini_model"))
        val_res = parse_ai_json_output(val_json, "VALIDATE_MEMO")
        
        if val_res and val_res.get("is_valid"):
            final_memo = raw; break
        elif val_res and val_res.get("is_acceptable"):
            if not acceptable_memo: acceptable_memo = raw
        
        feedback = val_res.get("feedback", "") if val_res else "Validation failed"
        feedback_history.append(f"Attempt {attempt+1}: {feedback}")
        memo_vars["rework_feedback"] = "\n\n".join(feedback_history)

    memo_content = final_memo or acceptable_memo or raw
    memo_path.write_text(memo_content, encoding="utf-8")
    return p_num, "Generated"

def process_svg_page(i, slide, source_path, slides_dir, notes_dir, glossary_text, cfg, args):
    p_num = str(slide.get("page")).zfill(2)
    p_topic = slide.get("topic", "Topic")
    safe_topic = sanitize_filename(p_topic)
    
    # 1. Slide SVG
    slide_svg_path = slides_dir / f"{p_num}_{safe_topic}.svg"
    if not (slide_svg_path.exists() and slide_svg_path.stat().st_size > 500):
        svg_vars = {"slide_content": slide.get("content", ""), "glossary": glossary_text}
        final_svg = ""
        for attempt in range(args.slide_svg_reworks + 1):
            raw = run_agent(cfg["agent"], "CREATE_SLIDE_SVG", svg_vars, retries=cfg["agent_execution_retries"], model_name=cfg.get("gemini_model"))
            match = re.search(r"<svg.*?</svg>", raw, re.DOTALL)
            if match:
                current_svg = fix_svg_layout(match.group(0))
                val_json = run_agent(cfg["agent"], "VALIDATE_SLIDE_SVG", {"svg_code": current_svg}, retries=cfg["agent_execution_retries"], model_name=cfg.get("gemini_model"))
                val_res = parse_ai_json_output(val_json, "VALIDATE_SLIDE_SVG")
                if val_res and (val_res.get("is_valid") or val_res.get("is_acceptable")):
                    final_svg = current_svg; break
        if final_svg: slide_svg_path.write_text(final_svg, encoding="utf-8")

    # 2. Conceptual SVG
    conceptual_svg_path = slides_dir / f"{p_num}_{safe_topic}_conceptual.svg"
    if not (conceptual_svg_path.exists() and conceptual_svg_path.stat().st_size > 500):
        memo_file = notes_dir / f"note-{p_num}_{safe_topic}-zh.md"
        memo_content = memo_file.read_text(encoding="utf-8") if memo_file.exists() else ""
        con_vars = {"slide_content": slide.get("content", ""), "memo_content": memo_content, "glossary": glossary_text}
        final_con = ""
        for attempt in range(args.conceptual_svg_reworks + 1):
            raw = run_agent(cfg["agent"], "CREATE_CONCEPTUAL_SVG", con_vars, retries=cfg["agent_execution_retries"], model_name=cfg.get("gemini_model"))
            if "NO_CONCEPTUAL_SVG_NEEDED" in raw: break
            match = re.search(r"<svg.*?</svg>", raw, re.DOTALL)
            if match:
                current_con = fix_svg_layout(match.group(0))
                val_json = run_agent(cfg["agent"], "VALIDATE_CONCEPTUAL_SVG", {"svg_code": current_con}, retries=cfg["agent_execution_retries"], model_name=cfg.get("gemini_model"))
                val_res = parse_ai_json_output(val_json, "VALIDATE_CONCEPTUAL_SVG")
                if val_res and (val_res.get("is_valid") or val_res.get("is_acceptable")):
                    final_con = current_con; break
        if final_con: conceptual_svg_path.write_text(final_con, encoding="utf-8")
    
    return p_num, "Processed"

def main():
    parser = argparse.ArgumentParser(description="PPTPlaner Orchestrator")
    parser.add_argument("--source", required=True)
    parser.add_argument("--manual-title")
    parser.add_argument("--manual-author")
    parser.add_argument("--manual-url")
    parser.add_argument("--no-svg", action="store_true")
    parser.add_argument("--custom-instruction")
    parser.add_argument("--plan-from-slides")
    parser.add_argument("--gemini-model")
    parser.add_argument("--agent", default="gemini")
    parser.add_argument("--analysis-reworks", type=int, default=3)
    parser.add_argument("--plan-reworks", type=int, default=3)
    parser.add_argument("--slide-reworks", type=int, default=5)
    parser.add_argument("--memo-reworks", type=int, default=5)
    parser.add_argument("--slide-svg-reworks", type=int, default=3)
    parser.add_argument("--conceptual-svg-reworks", type=int, default=3)
    parser.add_argument("--agent-retries", dest="agent_execution_retries", type=int, default=3)
    args = parser.parse_args()

    init_logger(ROOT)
    cfg = get_config(args)
    print_header(f"PPTPlaner v{cfg['version']} - Started")
    
    source_path = Path(args.source)
    if not source_path.exists(): print_error(f"Source file not found: {source_path}")

    # Phase 1: Analysis
    print_header("Phase 1: Analysis & Planning")
    analysis_vars = {"source_file_path": str(source_path), "custom_instruction": args.custom_instruction or "", "manual_title": args.manual_title or "", "manual_author": args.manual_author or "", "manual_url": args.manual_url or ""}
    
    analysis_data, acceptable_analysis, analysis_feedback_history = {}, {}, []
    for attempt in range(args.analysis_reworks + 1):
        raw = run_agent(cfg["agent"], "ANALYZE_SOURCE_DOCUMENT", analysis_vars, retries=cfg["agent_execution_retries"], model_name=cfg.get("gemini_model"))
        current_analysis = parse_ai_json_output(raw, "ANALYZE_SOURCE_DOCUMENT")
        
        if not current_analysis:
            analysis_feedback_history.append(f"Attempt {attempt+1}: Failed to parse JSON output.")
            analysis_vars["rework_feedback"] = "\n\n".join(analysis_feedback_history)
            continue

        val_json = run_agent(cfg["agent"], "VALIDATE_ANALYSIS", {"analysis_data": json.dumps(current_analysis, ensure_ascii=False), "source_file_path": str(source_path)}, retries=cfg["agent_execution_retries"], model_name=cfg.get("gemini_model"))
        val_res = parse_ai_json_output(val_json, "VALIDATE_ANALYSIS")
        
        if val_res and val_res.get("is_valid"):
            analysis_data = current_analysis; break
        elif val_res and val_res.get("is_acceptable"):
            if not acceptable_analysis: acceptable_analysis = current_analysis
        
        feedback = val_res.get("feedback", "") if val_res else "Validation failed"
        analysis_feedback_history.append(f"Attempt {attempt+1}: {feedback}")
        analysis_vars["rework_feedback"] = "\n\n".join(analysis_feedback_history)

    analysis_data = analysis_data or acceptable_analysis or current_analysis or {}

    # Distinguish between display title and folder title
    document_title = analysis_data.get("document_title") or args.manual_title or "Untitled"
    project_folder_name = analysis_data.get("project_title") or sanitize_filename(document_title)[:30]
    
    glossary = analysis_data.get("glossary") or []
    glossary_text = "\n".join([f"- {g['term']}: {g['translation'] or g['term']}" for g in glossary]) if glossary else "None"

    safe_title = sanitize_filename(project_folder_name)[:50]
    existing_dirs = sorted(list(OUTPUT_ROOT.glob(f"*_{safe_title}")), reverse=True)
    output_dir = existing_dirs[0] if existing_dirs else OUTPUT_ROOT / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{safe_title}"
    output_dir.mkdir(parents=True, exist_ok=True)
    slides_dir, notes_dir = output_dir / "slides", output_dir / "notes"
    slides_dir.mkdir(exist_ok=True); notes_dir.mkdir(exist_ok=True)

    if glossary: (output_dir / "glossary.json").write_text(json.dumps(glossary, indent=2, ensure_ascii=False), encoding="utf-8")
    
    # Write overview.md with proper formatting for build_guide.py
    # Use document_title for the main display heading
    overview_md = f"# {document_title}\n\n"
    if analysis_data.get("document_authors"):
        overview_md += f"**Author:** {analysis_data.get('document_authors')}\n"
    if analysis_data.get("source_url"):
        overview_md += f"**Source:** {analysis_data.get('source_url')}\n"
    
    overview_md += f"\n## Summary\n{analysis_data.get('summary') or 'No summary available.'}\n"
    overview_md += f"\n## Overview\n{analysis_data.get('overview') or 'No overview available.'}\n"
    (output_dir / "overview.md").write_text(overview_md, encoding="utf-8")

    # Phase 2: Planning
    print_header("Phase 2: Planning")
    plan_path = output_dir / ".plan.json"
    if plan_path.exists():
        plan_data = json.loads(plan_path.read_text(encoding="utf-8"))
    else:
        plan_vars = {"source_file_path": str(source_path), "glossary": glossary_text, "custom_instruction": args.custom_instruction or ""}
        plan_data, acceptable_plan, plan_feedback_history = {}, {}, []
        for attempt in range(args.plan_reworks + 1):
            raw = run_agent(cfg["agent"], "PLAN", plan_vars, retries=cfg["agent_execution_retries"], model_name=cfg.get("gemini_model"))
            current_plan = parse_ai_json_output(raw, "PLAN")
            
            if not current_plan:
                plan_feedback_history.append(f"Attempt {attempt+1}: Failed to parse JSON output.")
                plan_vars["rework_feedback"] = "\n\n".join(plan_feedback_history)
                continue

            val_json = run_agent(cfg["agent"], "VALIDATE_PLAN", {"plan_json": json.dumps(current_plan, ensure_ascii=False), "source_file_path": str(source_path)}, retries=cfg["agent_execution_retries"], model_name=cfg.get("gemini_model"))
            val_res = parse_ai_json_output(val_json, "VALIDATE_PLAN")
            
            if val_res and val_res.get("is_valid"):
                plan_data = current_plan; break
            elif val_res and val_res.get("is_acceptable"):
                if not acceptable_plan: acceptable_plan = current_plan
            
            feedback = val_res.get("feedback", "") if val_res else "Validation failed"
            plan_feedback_history.append(f"Attempt {attempt+1}: {feedback}")
            plan_vars["rework_feedback"] = "\n\n".join(plan_feedback_history)
        
        plan_data = plan_data or acceptable_plan or current_plan or {}
        if plan_data: plan_path.write_text(json.dumps(plan_data, indent=2, ensure_ascii=False), encoding="utf-8")

    if not plan_data: print_error("Planning failed.")

    # Phase 3: Deck
    print_header("Phase 3: Deck Generation")
    deck_vars = {"source_file_path": str(source_path), "plan_json": json.dumps(plan_data, ensure_ascii=False), "glossary": glossary_text}
    
    deck_data, acceptable_deck, deck_feedback_history = {}, {}, []
    for attempt in range(args.slide_reworks + 1):
        raw = run_agent(cfg["agent"], "DECK", deck_vars, retries=cfg["agent_execution_retries"], model_name=cfg.get("gemini_model"))
        current_deck = parse_ai_json_output(raw, "DECK")
        
        if not (current_deck and current_deck.get("slides")):
            deck_feedback_history.append(f"Attempt {attempt+1}: Failed to parse slides from JSON output.")
            deck_vars["rework_feedback"] = "\n\n".join(deck_feedback_history)
            continue

        val_json = run_agent(cfg["agent"], "VALIDATE_DECK", {"deck_json": json.dumps(current_deck, ensure_ascii=False), "source_file_path": str(source_path)}, retries=cfg["agent_execution_retries"], model_name=cfg.get("gemini_model"))
        val_res = parse_ai_json_output(val_json, "VALIDATE_DECK")
        
        if val_res and val_res.get("is_valid"):
            deck_data = current_deck; break
        elif val_res and val_res.get("is_acceptable"):
            if not acceptable_deck: acceptable_deck = current_deck
        
        feedback = val_res.get("feedback", "") if val_res else "Validation failed"
        deck_feedback_history.append(f"Attempt {attempt+1}: {feedback}")
        deck_vars["rework_feedback"] = "\n\n".join(deck_feedback_history)

    deck_data = deck_data or acceptable_deck or current_deck or {"slides": []}
    last_deck_content = deck_data.get("slides", [])
    
    full_slides_content = ""
    for slide in last_deck_content:
        p_num, topic = str(slide.get("page")).zfill(2), slide.get("topic", "Topic")
        (slides_dir / f"{p_num}_{sanitize_filename(topic)}.md").write_text(slide.get("content", ""), encoding="utf-8")
        full_slides_content += f"### {p_num}: {topic}\n{slide.get('content')}\n\n"

    # Phase 4 & 5: Parallel Generation
    print_header("Phase 4 & 5: Parallel Memo & SVG Generation")
    with ThreadPoolExecutor(max_workers=4) as executor:
        memo_futures = [executor.submit(process_memo_page, i, s, source_path, full_slides_content, notes_dir, glossary_text, cfg, args) for i, s in enumerate(last_deck_content)]
        for future in as_completed(memo_futures):
            p_num, status = future.result()
            print_success(f"Memo Page {p_num}: {status}")

    if not args.no_svg:
        with ThreadPoolExecutor(max_workers=3) as executor:
            svg_futures = [executor.submit(process_svg_page, i, s, source_path, slides_dir, notes_dir, glossary_text, cfg, args) for i, s in enumerate(last_deck_content)]
            for future in as_completed(svg_futures):
                p_num, status = future.result()
                print_success(f"SVG Page {p_num}: {status}")

    # Finalize
    print_header("Phase 6: Finalizing")
    build_script = ROOT / "scripts" / "build_guide.py"
    if build_script.exists():
        subprocess.run([sys.executable, str(build_script), f"--output-dir={output_dir}"])
    
    os.startfile(output_dir)
    print_header("Run Complete!")

if __name__ == "__main__":
    main()
