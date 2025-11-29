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
    bar = "=" * 60; print(f"\n{bar}\n  {title}\n{bar}", flush=True)
    rlog_phase(title) # Log header

def print_success(msg: str):
    print(f"  ✓ {msg}", flush=True)
    rlog(f"SUCCESS: {msg}")

def print_info(msg: str):
    print(f"  ▶ {msg}", flush=True)
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
    name = name.replace(' ', '_')
    return re.sub(r'[\\/*?:\"<>|]', '', name)

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

    safety_preamble = ("You are an AI assistant in an academic context. Your purpose is to help a user create educational materials from a textbook. "
                         "The textbook may contain sensitive topics (such as crime, violence, or other serious subjects) for the purpose of scholarly analysis. "
                         "Your task is to process these topics factually and neutrally, as presented in the source material. "
                         "Do not avoid sensitive subjects; handle them with an objective, academic tone suitable for a learning environment.")

    prompt_parts = [safety_preamble, f"Your specific task is '{mode}'.", "--- INSTRUCTIONS ---", instructions, "--- CONTEXT & INPUTS ---"]
    
    # Prepare log for inputs
    log_inputs = {}

    for key, value in vars_map.items():
        if key.endswith("_path") and value and os.path.exists(value):
            file_content = Path(value).read_text(encoding='utf-8')
            prompt_parts.append(f"Content for '{os.path.basename(value)}':\n```\n{file_content}\n```")
            log_inputs[key] = f"[File Content from {os.path.basename(value)}]" # Don't double log huge files in inputs section if possible, or just reference
        elif key.endswith("_content") and value: 
            prompt_parts.append(f"Provided Content for '{key}':\n```\n{value}\n```")
            log_inputs[key] = value # Log the content for analysis
        else: 
            prompt_parts.append(f"- {key}: {value}")
            log_inputs[key] = value
    
    prompt_parts.append("--- YOUR TASK ---")
    prompt_parts.append("Generate your response. Output ONLY the content required (e.g., pure JSON, pure Markdown). No conversational text.")
    final_prompt = "\n".join(prompt_parts)

    cmd = [found_agent_path]
    if model_name:
        cmd.extend(["-m", model_name])
    if mode in ["PLAN", "PLAN_FROM_SLIDES", "ANALYZE_SOURCE_DOCUMENT", "VALIDATE_ANALYSIS", "VALIDATE_MEMO", "DECK", "VALIDATE_DECK", "VALIDATE_SLIDE_SVG", "VALIDATE_CONCEPTUAL_SVG"]:
        cmd.extend(["--output-format", "json"])

    for attempt in range(retries):
        print_info(f"Calling {agent_cmd.capitalize()} for {mode}... (Attempt {attempt + 1}/{retries})")
        
        # --- LOGGING AGENT CALL ---
        rlog(f"AGENT CALL START: {mode} (Attempt {attempt + 1})")
        rlog_data(f"Agent Inputs ({mode})", log_inputs)
        # --------------------------

        try:
            result = run_command(cmd, input_text=final_prompt)
            output = result.stdout.strip()
            
            # --- LOGGING AGENT RESPONSE ---
            rlog_block(f"Agent Raw Output ({mode})", output)
            rlog("AGENT CALL END")
            # ------------------------------

            if output:
                return output # Success

            # This case handles empty output, which might not be an error but requires a retry.
            print_error(f"AI returned empty response for {mode}.", exit_code=None)

        except subprocess.CalledProcessError as e:
            # This case handles when the command itself fails (e.g., API error)
            stderr_lower = e.stderr.lower()
            rlog(f"AGENT ERROR: {e.stderr.strip()}")
            if "authentication" in stderr_lower or "login required" in stderr_lower:
                print_error("認證失敗或過期 (Authentication failed or expired)。", exit_code=None)
                print_info("請在瀏覽器中完成登入，或在另一個終端機中執行 `gemini auth login`。")
            elif "exhausted" in stderr_lower or "quota" in stderr_lower:
                print_error("API quota 已用盡 (API quota exhausted)。", exit_code=None)
                print_info("請在 GUI 中選擇 '繼續' 來等待配額恢復，或選擇 '切換模型' 來嘗試其他模型。")
            else:
                print_error(f"指令執行失敗 (Exit Code: {e.returncode}): {" ".join(e.cmd)}\n  STDERR: {e.stderr.strip()}", exit_code=None)

        if attempt < retries - 1:
            print_info(f"Retrying in {delay}s...")
            rlog(f"Waiting {delay}s before retry...")
            time.sleep(delay)

    print_error(f"AI failed to generate a response for {mode} after {retries} attempts.", exit_code=1)
    return "" # Return empty string if all retries fail

def parse_ai_json_output(output: str, mode: str) -> dict | None:
    """
    Parses the AI's output, handling raw JSON, JSON in markdown fences,
    and the gemini tool's wrapper object. Returns None on failure.
    """
    try:
        # Helper to try loading JSON
        def try_load(text):
            return json.loads(text)

        data = None
        # 1. Try direct parse
        try: data = try_load(output); 
        except: pass

        if data is None:
            # 2. Try stripping markdown fences
            match = re.search(r"```(?:json)?\s*(.*?)```", output, re.DOTALL)
            if match:
                try: data = try_load(match.group(1).strip())
                except: pass
        
        if data is None:
            # 3. Try finding outer braces/brackets
            output_strip = output.strip()
            for start_char, end_char in [('{', '}'), ('[', ']')]:
                start = output_strip.find(start_char)
                end = output_strip.rfind(end_char)
                if start != -1 and end != -1 and end > start:
                    try: 
                        candidate = output_strip[start:end+1]
                        data = try_load(candidate)
                        if data is not None: break
                    except: pass
        
        if data is None:
            raise ValueError("Could not extract valid JSON from output.")

        # If the parsed data has a "response" field and it's a string... (Gemini wrapper handling)
        if isinstance(data, dict) and "response" in data and isinstance(data["response"], str):
            nested_str = data["response"]
            # Recursive call to parse the inner string
            nested_data = parse_ai_json_output(nested_str, f"{mode} (Nested)")
            return nested_data if nested_data is not None else data 
        
        rlog_data(f"Parsed JSON Data ({mode})", data) # Log parsed data
        return data

    except Exception as e:
        # Log error
        print_error(f"{mode} JSON parse failed. Error: {e}", exit_code=None)
        rlog(f"JSON PARSE FAILURE: {e}")
        
        # Save debug info
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        debug_dir = OUTPUT_ROOT / "debug"
        debug_dir.mkdir(parents=True, exist_ok=True)
        debug_file = debug_dir / f"parse_fail_{mode}_{timestamp}.txt"
        try:
            debug_file.write_text(f"ERROR: {e}\n\n--- RAW OUTPUT ---\n{output}", encoding="utf-8")
            print_info(f"Failed output saved to: {debug_file.relative_to(ROOT)}")
        except Exception as write_err:
            print_error(f"Failed to save debug file: {write_err}", exit_code=None)
            
        return None

def get_config(args: argparse.Namespace) -> dict:
    cfg = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")) if CONFIG_PATH.exists() else {}
    # Add default version if not in config, useful for metadata
    if 'version' not in cfg:
        cfg['version'] = '1.6.0'
    if 'plan_max_reworks' not in cfg:
        cfg['plan_max_reworks'] = 3
    # Add defaults for new SVG settings
    if 'slide_svg_max_reworks' not in cfg:
        cfg['slide_svg_max_reworks'] = 5
    if 'conceptual_svg_max_reworks' not in cfg:
        cfg['conceptual_svg_max_reworks'] = 5
        
    # Command-line args (from UI) override config.yaml
    cli_args = {k: v for k, v in vars(args).items() if v is not None}
    cfg.update(cli_args)
    return cfg

def generate_svgs(cfg: dict, pages: list, output_dir: Path, slides_dir: Path, notes_dir: Path, model_name: str | None = None):
    """Generates Slide SVGs and Conceptual SVGs for each page, with progress tracking."""
    print_header(f"Phase 2c: Generating SVGs ({len(pages)} pages)")

    # --- Progress Tracking Setup ---
    progress_file = output_dir / ".svg_progress.json"
    progress = {}
    if progress_file.exists():
        try:
            progress = json.loads(progress_file.read_text(encoding="utf-8"))
            print_info(f"Resuming from existing SVG progress file: {progress_file.name}")
        except json.JSONDecodeError:
            print_error(f"Could not parse SVG progress file {progress_file.name}. Starting fresh.", exit_code=None)
            progress = {}
            
    # Ensure all pages are in the progress file
    all_pages_in_progress = True
    for item in pages:
        page_id = item["page"]
        if page_id not in progress:
            all_pages_in_progress = False
            progress[page_id] = {"slide_svg": "pending", "conceptual_svg": "pending"}
    
    if not all_pages_in_progress or not progress_file.exists():
        progress_file.write_text(json.dumps(progress, indent=4, ensure_ascii=False), encoding="utf-8")
        print_info("Initialized or updated SVG progress tracking file.")

    for item in pages:
        page, topic = item["page"], item["topic"]
        slide_path = slides_dir / f"{page}_{topic}.md"
        note_path = notes_dir / f"note-{page}_{topic}-zh.md"

        if not slide_path.exists():
            print_error(f"Skipping SVG generation for page {page} as its slide MD file does not exist.", exit_code=None)
            continue
        
        slide_content = slide_path.read_text(encoding="utf-8")
        memo_content = note_path.read_text(encoding="utf-8") if note_path.exists() else ""

        # --- 1. Slide SVG Generation ---
        slide_svg_path = slides_dir / f"slide_{page}.svg"
        if progress.get(page, {}).get("slide_svg") == "completed":
            print_info(f"Skipping Slide SVG for page {page} (already completed).")
        else:
            print_info(f"Generating Slide SVG for page {page}...")
            perfect_slide_svg = ""
            acceptable_slide_svg = ""
            last_slide_svg_attempt = ""
            MAX_SLIDE_SVG_REWORKS = cfg.get("slide_svg_max_reworks", 5)

            svg_vars = {"slide_content": slide_content}

            for attempt in range(MAX_SLIDE_SVG_REWORKS + 1):
                if attempt > 0:
                    print_info(f"Reworking Slide SVG for page {page}... (Attempt {attempt}/{MAX_SLIDE_SVG_REWORKS})")
                    rlog(f"Page {page}: Reworking Slide SVG (Attempt {attempt})")
                
                raw_svg_attempt = run_agent(cfg["agent"], "CREATE_SLIDE_SVG", svg_vars, retries=1, model_name=model_name)
                
                svg_match = re.search(r"<svg.*?</svg>", raw_svg_attempt, re.DOTALL)
                current_svg_attempt = svg_match.group(0) if svg_match else raw_svg_attempt

                if not current_svg_attempt or not current_svg_attempt.strip().startswith("<svg"):
                    print_error(f"Slide SVG generation for page {page} returned invalid content on attempt {attempt}.", exit_code=None)
                    continue
                
                last_slide_svg_attempt = current_svg_attempt

                validation_vars = {"svg_code": last_slide_svg_attempt}
                validation_json = run_agent(cfg["agent"], "VALIDATE_SLIDE_SVG", validation_vars, retries=2, model_name=model_name)
                validation_result = parse_ai_json_output(validation_json, "VALIDATE_SLIDE_SVG")
                
                if not validation_result:
                     print_error(f"Validation JSON parse failed for page {page} on attempt {attempt}.", exit_code=None)
                     continue

                feedback = validation_result.get("feedback", "No feedback provided.")
                rlog(f"Page {page} Slide SVG Validation: Valid={validation_result.get('is_valid')}, Acceptable={validation_result.get('is_acceptable')}")
                rlog(f"Feedback: {feedback}")

                if validation_result.get("is_valid", False):
                    print_success(f"Perfect Slide SVG validation passed for page {page}.")
                    rlog(f"DECISION: Perfect Slide SVG found. Stopping loop.")
                    perfect_slide_svg = last_slide_svg_attempt
                    break
                elif validation_result.get("is_acceptable", False):
                    print_success(f"Slide SVG validation 'acceptable' for page {page}.")
                    rlog(f"DECISION: Acceptable Slide SVG found. Storing and continuing to seek perfection.")
                    acceptable_slide_svg = last_slide_svg_attempt
                else:
                    rlog(f"DECISION: Slide SVG rejected. Retrying.")
                
                print_error(f"Slide SVG validation failed for page {page}. Feedback: {feedback}", exit_code=None)
                svg_vars["rework_feedback"] = feedback

            final_slide_svg = perfect_slide_svg or acceptable_slide_svg or last_slide_svg_attempt
            if final_slide_svg:
                slide_svg_path.write_text(final_slide_svg, encoding="utf-8")
                progress[page]["slide_svg"] = "completed"
                progress_file.write_text(json.dumps(progress, indent=4, ensure_ascii=False), encoding="utf-8")
                print_success(f"  Slide SVG saved for page {page}")

        # --- 2. Conceptual SVG Generation ---
        conceptual_svg_path = slides_dir / f"conceptual_{page}.svg"
        if progress.get(page, {}).get("conceptual_svg") == "completed":
            print_info(f"Skipping Conceptual SVG for page {page} (already completed).")
        else:
            print_info(f"Generating Conceptual SVG for page {page}...")
            perfect_conceptual_svg = ""
            acceptable_conceptual_svg = ""
            last_conceptual_svg_attempt = ""
            MAX_CONCEPTUAL_SVG_REWORKS = cfg.get("conceptual_svg_max_reworks", 5)

            conceptual_vars = {"slide_content": slide_content, "memo_content": memo_content}

            for attempt in range(MAX_CONCEPTUAL_SVG_REWORKS + 1):
                if attempt > 0:
                    print_info(f"Reworking Conceptual SVG for page {page}... (Attempt {attempt}/{MAX_CONCEPTUAL_SVG_REWORKS})")
                    rlog(f"Page {page}: Reworking Conceptual SVG (Attempt {attempt})")

                raw_conceptual_svg = run_agent(cfg["agent"], "CREATE_CONCEPTUAL_SVG", conceptual_vars, retries=1, model_name=model_name)

                if "NO_CONCEPTUAL_SVG_NEEDED" in raw_conceptual_svg:
                    print_info(f"Agent decided no conceptual SVG is needed for page {page}.")
                    rlog(f"Page {page}: Agent decided NO_CONCEPTUAL_SVG_NEEDED.")
                    last_conceptual_svg_attempt = "NO_CONCEPTUAL_SVG_NEEDED" # Special marker
                    break
                
                if "CONCEPTUAL_SVG_FAILED" in raw_conceptual_svg:
                    print_error(f"Conceptual SVG generation failed for page {page} on attempt {attempt}.", exit_code=None)
                    rlog(f"Page {page}: Agent reported CONCEPTUAL_SVG_FAILED.")
                    continue

                svg_match = re.search(r"<svg.*?</svg>", raw_conceptual_svg, re.DOTALL)
                current_conceptual_svg = svg_match.group(0) if svg_match else raw_conceptual_svg

                if not current_conceptual_svg or not current_conceptual_svg.strip().startswith("<svg"):
                    print_error(f"Conceptual SVG generation for page {page} returned invalid content on attempt {attempt}.", exit_code=None)
                    continue

                last_conceptual_svg_attempt = current_conceptual_svg
                
                validation_vars = {"svg_code": last_conceptual_svg_attempt, "slide_content": slide_content, "memo_content": memo_content}
                validation_json = run_agent(cfg["agent"], "VALIDATE_CONCEPTUAL_SVG", validation_vars, retries=2, model_name=model_name)
                validation_result = parse_ai_json_output(validation_json, "VALIDATE_CONCEPTUAL_SVG")
                
                if not validation_result:
                     print_error(f"Validation JSON parse failed for page {page} on attempt {attempt}.", exit_code=None)
                     continue

                feedback = validation_result.get("feedback", "No feedback provided.")
                rlog(f"Page {page} Conceptual SVG Validation: Valid={validation_result.get('is_valid')}, Acceptable={validation_result.get('is_acceptable')}")
                rlog(f"Feedback: {feedback}")

                if validation_result.get("is_valid", False):
                    print_success(f"Perfect Conceptual SVG validation passed for page {page}.")
                    rlog(f"DECISION: Perfect Conceptual SVG found. Stopping loop.")
                    perfect_conceptual_svg = last_conceptual_svg_attempt
                    break
                elif validation_result.get("is_acceptable", False):
                    print_success(f"Conceptual SVG validation 'acceptable' for page {page}.")
                    rlog(f"DECISION: Acceptable Conceptual SVG found. Storing and continuing.")
                    acceptable_conceptual_svg = last_conceptual_svg_attempt
                else:
                    rlog(f"DECISION: Conceptual SVG rejected. Retrying.")

                print_error(f"Conceptual SVG validation failed for page {page}. Feedback: {feedback}", exit_code=None)
                conceptual_vars["rework_feedback"] = feedback

            final_conceptual_svg = perfect_conceptual_svg or acceptable_conceptual_svg or last_conceptual_svg_attempt
            
            if final_conceptual_svg and final_conceptual_svg != "NO_CONCEPTUAL_SVG_NEEDED":
                conceptual_svg_path.write_text(final_conceptual_svg, encoding="utf-8")
                print_success(f"  Conceptual SVG saved for page {page}")
            
            if final_conceptual_svg:
                progress[page]["conceptual_svg"] = "completed"
                progress_file.write_text(json.dumps(progress, indent=4, ensure_ascii=False), encoding="utf-8")


def _combine_slides_into_single_file(slides_dir: Path):
    """Finds all .md files, sorts them numerically, and combines them."""
    if not slides_dir.is_dir():
        print_error(f"Combine slides failed: Directory '{slides_dir}' not found.", exit_code=None)
        return

    slide_files = sorted(slides_dir.glob("*.md"))
    if not slide_files:
        return # No slides to combine, just exit quietly.

    def get_numeric_prefix(p: Path) -> int:
        match = re.match(r'^(\d+)', p.name)
        return int(match.group(1)) if match else 9999
    slide_files.sort(key=get_numeric_prefix)

    all_content = [p.read_text(encoding="utf-8") for p in slide_files]
    combined_content = "\n\n---\n\n".join(all_content)
    
    output_file = slides_dir.parent / "combined_slides.md"
    try:
        output_file.write_text(combined_content, encoding="utf-8")
        print_success(f"All {len(slide_files)} slides combined into: {output_file.name}")
    except Exception as e:
        print_error(f"Failed to write combined slides file: {e}", exit_code=None)

def main():
    # Initialize logger as early as possible
    init_logger(ROOT)
    rlog("--- NEW RUN STARTED ---")

    parser = argparse.ArgumentParser(description="PPTPlaner Orchestrator")
    # Use dest='source_file' to match the key in config.yaml
    parser.add_argument("--source", dest="source_file", help="Source file to process")
    parser.add_argument("--agent", dest="agent", help="AI agent to use (e.g., gemini)")
    parser.add_argument("--gemini-model", dest="gemini_model", help="Specific Gemini model to use (e.g., gemini-pro, gemini-1.5-pro-latest)")
    parser.add_argument("--custom-instruction", dest="custom_instruction", help="User-provided custom instruction for the MEMO agent")
    parser.add_argument("--plan-reworks", dest="plan_max_reworks", type=int, help="Override plan_max_reworks from config.yaml")
    parser.add_argument("--slide-reworks", dest="slide_max_reworks", type=int, help="Override slide_max_reworks from config.yaml")
    parser.add_argument("--memo-reworks", dest="memo_max_reworks", type=int, help="Override memo_max_reworks from config.yaml")
    parser.add_argument("--slide-svg-reworks", dest="slide_svg_max_reworks", type=int, help="Override slide_svg_max_reworks from config.yaml")
    parser.add_argument("--conceptual-svg-reworks", dest="conceptual_svg_max_reworks", type=int, help="Override conceptual_svg_max_reworks from config.yaml")
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument("--slides-only", action="store_true")
    mode_group.add_argument("--memos-only", action="store_true")
    mode_group.add_argument("--plan-from-slides", dest="plan_from_slides", help="AI-plan from a slide file, then generate memos")
    # Add the --no-svg flag
    parser.add_argument("--no-svg", action="store_true", help="Skip the experimental SVG generation phase.")
    args = parser.parse_args()

    cfg = get_config(args)
    rlog_data("Configuration", cfg) # Log configuration
    
    if not cfg.get("source_file"):
        print_error("未提供來源檔案。請在 UI 中選擇或在 config.yaml 中設定。")

    print_header("Phase 0: Initializing Run & Analyzing Source Document")
    source_path = Path(cfg["source_file"])
    if not source_path.is_absolute():
        source_path = ROOT / source_path
    if not source_path.exists():
        print_error(f"來源檔案不存在: {source_path}")
    
    rlog(f"Source File: {source_path}")

    # --- ANALYZE_SOURCE_DOCUMENT with Rework Loop ---
    perfect_analysis_data = {}
    acceptable_analysis_data = {}
    last_analysis_data_attempt = {}
    MAX_ANALYSIS_REWORKS = 5

    analysis_vars = {"source_file_path": str(source_path)}
    current_analysis_data = {}

    for attempt in range(MAX_ANALYSIS_REWORKS + 1):
        if attempt > 0:
            print_info(f"Reworking source document analysis... (Attempt {attempt}/{MAX_ANALYSIS_REWORKS})")
            rlog(f"Reworking Analysis (Attempt {attempt})")
        
        analysis_output = run_agent(cfg["agent"], "ANALYZE_SOURCE_DOCUMENT", analysis_vars, retries=1, model_name=cfg.get("gemini_model"))
        if not analysis_output:
            print_error(f"ANALYZE_SOURCE_DOCUMENT returned empty content on attempt {attempt}.", exit_code=None)
            continue
        
        current_analysis_data = parse_ai_json_output(analysis_output, "ANALYZE_SOURCE_DOCUMENT")
        if not current_analysis_data: continue
        last_analysis_data_attempt = current_analysis_data

        print_info("Validating source document analysis...")
        validation_vars = {
            "analysis_data": json.dumps(current_analysis_data, ensure_ascii=False, indent=2),
            "source_file_path": str(source_path)
        }
        validation_json = run_agent(cfg["agent"], "VALIDATE_ANALYSIS", validation_vars, retries=2, model_name=cfg.get("gemini_model"))
        
        validation_result = {"is_valid": False, "is_acceptable": False, "feedback": "Validation agent returned no response."}
        if validation_json:
            validation_result = parse_ai_json_output(validation_json, "VALIDATE_ANALYSIS") or {}

        feedback = validation_result.get("feedback", "No feedback provided.")
        rlog(f"Analysis Validation: Valid={validation_result.get('is_valid')}, Acceptable={validation_result.get('is_acceptable')}")
        rlog(f"Feedback: {feedback}")

        if validation_result.get("is_valid", False):
            print_success("Perfect source document analysis passed. Finishing.")
            rlog("DECISION: Perfect Analysis found. Stopping loop.")
            perfect_analysis_data = current_analysis_data
            break
        elif validation_result.get("is_acceptable", False):
            print_success("Source document analysis 'acceptable'. Storing as fallback and continuing.")
            rlog("DECISION: Acceptable Analysis found. Storing and continuing.")
            acceptable_analysis_data = current_analysis_data
        else:
            rlog("DECISION: Analysis rejected. Retrying.")
        
        print_error(f"Source document analysis failed. Feedback: {feedback}", exit_code=None)
        analysis_vars["rework_feedback"] = feedback

    # After the loop, decide which version to use
    final_analysis_data = {}
    if perfect_analysis_data:
        final_analysis_data = perfect_analysis_data
    elif acceptable_analysis_data:
        print_info("Using best 'acceptable' version of the source document analysis.")
        final_analysis_data = acceptable_analysis_data
    elif last_analysis_data_attempt:
        print_error("No valid or acceptable analysis found. Using the last raw attempt with a warning.", exit_code=None)
        final_analysis_data = last_analysis_data_attempt
    
    if not final_analysis_data:
        print_error("Failed to generate any analysis content. Using placeholders.", exit_code=1)

    rlog_data("Final Analysis Data Selected", final_analysis_data)

    # --- Create Output Directory and Save Overview ---
    project_title = final_analysis_data.get("project_title", "Untitled_Run")
    sanitized_title = re.sub(r'[^a-zA-Z0-9_-]', '', project_title.replace(" ", "_"))
    
    run_datetime = datetime.now()
    output_dir = OUTPUT_ROOT / f"{run_datetime.strftime('%Y%m%d_%H%M%S')}_{sanitized_title}"
    output_dir.mkdir(parents=True)
    print_success(f"Created unique output directory: {output_dir.relative_to(ROOT)}")
    rlog(f"Output Directory: {output_dir}")

    # Prepare and save the rich overview.md
    doc_title = final_analysis_data.get('document_title', 'N/A')
    doc_subtitle = final_analysis_data.get('document_subtitle')
    doc_authors = final_analysis_data.get('document_authors', 'N/A')
    pub_info = final_analysis_data.get('publication_info', 'N/A')
    summary = final_analysis_data.get('summary', 'No summary was generated.')
    overview = final_analysis_data.get('overview', 'No overview was generated.')
    
    front_matter = {
        "project_title": project_title,
        "document_title": doc_title,
        "document_subtitle": doc_subtitle,
        "document_authors": doc_authors,
        "publication_info": pub_info,
        "generation_date": run_datetime.strftime('%Y-%m-%d'),
        "generated_by": f"PPTPlaner {cfg.get('version', 'N/A')}",
        "source_file": source_path.name
    }
    overview_yaml = yaml.dump(front_matter, allow_unicode=True, default_flow_style=False, sort_keys=False)

    body_title_line = f"# Project Overview: {doc_title}"
    body_author_line = f"> *By {doc_authors}, {pub_info}*" if doc_authors and pub_info and doc_authors != 'N/A' and pub_info != 'N/A' else ""
    body_summary_section = f"## 摘要 (Summary)\n\n{summary}"
    body_overview_section = f"## 總覽 (Overview)\n\n{overview}"
    
    overview_content = f"---\n{overview_yaml}---\n\n{body_title_line}\n\n{body_author_line}\n\n{body_summary_section}\n\n{body_overview_section}\n".replace("\n\n\n", "\n\n")

    overview_path = output_dir / "overview.md"
    overview_path.write_text(overview_content, encoding="utf-8")
    print_success(f"Rich project overview saved to: {overview_path.name}")

    slides_dir = output_dir / "slides"; notes_dir = output_dir / "notes"; guide_file = output_dir / "guide.html"
    plan_json_path = output_dir / ".plan.json"

    plan = None
    pages = []
    MAX_PLAN_REWORKS = cfg.get("plan_max_reworks", 3)

    if args.plan_from_slides:
        print_header("Phase 1: AI Planning from Slides File")
        slide_file_path = Path(args.plan_from_slides)
        if not slide_file_path.is_absolute(): slide_file_path = ROOT / slide_file_path
        if not slide_file_path.exists(): print_error(f"簡報檔案不存在: {slide_file_path}")
        slide_content = slide_file_path.read_text(encoding="utf-8")
        
        for attempt in range(MAX_PLAN_REWORKS):
            if attempt > 0: print_info(f"Retrying PLAN_FROM_SLIDES... (Attempt {attempt+1}/{MAX_PLAN_REWORKS})")
            output = run_agent(cfg["agent"], "PLAN_FROM_SLIDES", {"slide_file_content": slide_content, "source_file_path": str(source_path)}, model_name=cfg.get("gemini_model"))
            plan = parse_ai_json_output(output, "PLAN_FROM_SLIDES")
            if plan and plan.get("pages"): break
        
        if not plan or not plan.get("pages"): print_error("AI 未能從簡報檔案生成任何頁面計畫。", exit_code=1)
        
        pages = plan.get("pages", [])
        for page_item in pages: page_item["topic"] = sanitize_filename(page_item["topic"])
        print_info(f"AI is planning {len(pages)} slides... Writing to '{slides_dir.name}' folder.")
        slides_dir.mkdir(exist_ok=True)
        for item in pages: 
            slide_path = slides_dir / f'{item["page"]}_{item["topic"]}.md'
            slide_path.write_text(item["content"], encoding="utf-8")
        args.memos_only = True
    else:
        print_header("Phase 1: AI Planning from Source Document")
        for attempt in range(MAX_PLAN_REWORKS):
            if attempt > 0: print_info(f"Retrying PLAN... (Attempt {attempt+1}/{MAX_PLAN_REWORKS})")
            output = run_agent(cfg["agent"], "PLAN", {"source_file_path": str(source_path)}, model_name=cfg.get("gemini_model"))
            plan = parse_ai_json_output(output, "PLAN")
            if plan and plan.get("pages"): break

        if not plan or not plan.get("pages"): print_error("AI 未能生成任何頁面計畫。", exit_code=1)

        pages = plan.get("pages", [])
        for page_item in pages: page_item["topic"] = sanitize_filename(page_item["topic"])

    rlog_data("Final Plan Pages", pages)

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
                    rlog(f"Reworking Deck (Attempt {attempt})")

                deck_output = run_agent(cfg["agent"], "DECK", deck_vars, retries=1, model_name=cfg.get("gemini_model"))
                if not deck_output:
                    print_error(f"Deck generation returned empty content on attempt {attempt}.", exit_code=None)
                    continue
                
                deck_data = parse_ai_json_output(deck_output, "DECK")
                if not deck_data: continue
                generated_slides = deck_data.get("slides", [])

                if not generated_slides or len(generated_slides) != len(pages):
                    print_error(f"Deck generation returned incomplete slides. Expected {len(pages)}, got {len(generated_slides)}.", exit_code=None)
                    continue
                
                last_slides_attempt = generated_slides

                print_info("Validating entire slide deck for consistency and flow...")
                validation_vars = {"slides_json": json.dumps(generated_slides, ensure_ascii=False, indent=2)}
                validation_json = run_agent(cfg["agent"], "VALIDATE_DECK", validation_vars, retries=2, model_name=cfg.get("gemini_model"))
                
                validation_result = {"is_valid": False, "is_acceptable": False, "feedback": "Validation agent returned no response."}
                if validation_json:
                    validation_result = parse_ai_json_output(validation_json, "VALIDATE_DECK") or {}
                
                feedback = validation_result.get("feedback", "No feedback provided.")
                rlog(f"Deck Validation: Valid={validation_result.get('is_valid')}, Acceptable={validation_result.get('is_acceptable')}")
                rlog(f"Feedback: {feedback}")

                if validation_result.get("is_valid", False):
                    print_success("Perfect slide deck validation passed. Finishing.")
                    rlog("DECISION: Perfect Deck found. Stopping loop.")
                    perfect_slides = generated_slides
                    break  # Perfection found, exit loop immediately
                elif validation_result.get("is_acceptable", False):
                    print_success("Slide deck validation 'acceptable'. Storing as fallback and continuing.")
                    rlog("DECISION: Acceptable Deck found. Storing and continuing.")
                    acceptable_slides = generated_slides
                    # Do not break; continue to strive for a perfect version
                else:
                    rlog("DECISION: Deck rejected. Retrying.")
                
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
                        rlog(f"Page {page}: Reworking Memo (Attempt {attempt})")
                    
                    current_attempt_content = run_agent(cfg["agent"], "MEMO", memo_vars, retries=1, model_name=cfg.get("gemini_model"))

                    if not current_attempt_content or not current_attempt_content.strip():
                        print_error(f"Memo generation for page {page} returned empty content on attempt {attempt}.", exit_code=None)
                        continue
                    
                    # Pre-process to strip markdown fences before validation and saving
                    match = re.search(r'^```(?:markdown)?\n(.*?)\n```$', current_attempt_content, re.DOTALL | re.IGNORECASE)
                    if match:
                        print_info("Stripping markdown fences from AI-generated memo.")
                        last_memo_attempt = match.group(1).strip()
                    else:
                        last_memo_attempt = current_attempt_content

                    print_info(f"Validating memo for page {page}...")
                    validation_vars = {"slide_content": slide_content, "memo_content": last_memo_attempt}
                    validation_json = run_agent(cfg["agent"], "VALIDATE_MEMO", validation_vars, retries=2, model_name=cfg.get("gemini_model"))
                    validation_result = parse_ai_json_output(validation_json, "VALIDATE_MEMO") or {}
                    
                    feedback = validation_result.get("feedback", "No feedback provided.")
                    rlog(f"Page {page} Memo Validation: Valid={validation_result.get('is_valid')}, Acceptable={validation_result.get('is_acceptable')}")
                    rlog(f"Feedback: {feedback}")

                    if validation_result.get("is_valid", False):
                        print_success(f"Validation passed for page {page}. Finishing.")
                        rlog(f"DECISION: Perfect Memo found for page {page}. Stopping loop.")
                        perfect_memo = last_memo_attempt
                        break
                    elif validation_result.get("is_acceptable", False):
                        print_success(f"Validation 'acceptable' for page {page}. Storing as fallback.")
                        rlog(f"DECISION: Acceptable Memo found for page {page}. Storing and continuing.")
                        acceptable_memo = last_memo_attempt
                    else:
                        rlog(f"DECISION: Memo rejected for page {page}. Retrying.")
                    
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
                    warning_header = "> [!WARNING]\n> **AI 自動修正失敗**\n>\n> 以下是由 AI 生成的最後一版備忘稿。它未能完全通過品質檢驗，可能包含錯誤或遺漏。請仔細核對並手動修正。\n>\n> ---\n\n"
                    final_memo_content = warning_header + last_memo_attempt
                else:
                    final_memo_content = "### 備忘稿生成失敗\n\nAI 未能為此頁投影片生成備忘稿，所有嘗試均返回空內容。\n\n**可能原因：**\n1.  **主題敏感性**：此頁主題可能觸發了 AI 的安全機制。\n2.  **AI 暫時性錯誤**：AI 模型在處理此請求時遇到暫時性問題。\n\n**建議操作：**\n*   請直接參考原始文件 (`source_file`) 來準備此頁的內容。"
                    print_error(f"Failed to generate any memo content for page {page} after all attempts. Writing placeholder.", exit_code=None)

                note_path.write_text(final_memo_content, encoding="utf-8")
                if "> [!WARNING]" not in final_memo_content and "備忘稿生成失敗" not in final_memo_content:
                    print_success(f"  Memo saved for page {page}")
    
    # --- SVG Generation ---
    if args.no_svg:
        print_header("Phase 2c: Skipping SVG Generation")
        print_info("SVG generation was skipped due to the --no-svg flag.")
    elif not args.slides_only:
        generate_svgs(cfg, pages, output_dir, slides_dir, notes_dir, model_name=cfg.get("gemini_model"))

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
    rlog("--- RUN COMPLETE ---")

if __name__ == "__main__":
    main()