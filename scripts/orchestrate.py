import sys, os, json, subprocess, shutil, argparse, webbrowser, re, time
from pathlib import Path
import yaml
from datetime import datetime

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
    
    if not PROMPTS_DIR.exists():
        print_error(f"Prompts directory not found: {PROMPTS_DIR}")
        
    specs = {}
    # Iterate over all .md files in the prompts directory
    for prompt_file in PROMPTS_DIR.glob("*.md"):
        if prompt_file.name.lower() == "readme.md": continue # Skip README
        
        mode_name = prompt_file.stem # Filename without extension serves as the key
        try:
            content = prompt_file.read_text(encoding="utf-8").strip()
            specs[mode_name] = content
        except Exception as e:
            print_error(f"Failed to read prompt file {prompt_file.name}: {e}", exit_code=None)

    if not specs:
        print_error(f"No agent prompts found in {PROMPTS_DIR}")

    _agent_specs_cache = specs
    return specs

def run_command(cmd: list[str], input_text: str | None = None) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(cmd, input=input_text, capture_output=True, text=True, encoding="utf-8", check=True)
    except FileNotFoundError: print_error(f"指令 '{cmd[0]}' 不存在。")
    except subprocess.CalledProcessError as e:
        # Rethrow to be handled by run_agent's retry/pause logic
        raise e

def wait_for_user_action() -> str | None:
    """
    Creates a pause lock file and waits for the user to remove it (via UI).
    Checks for runtime config updates (e.g., model switch).
    Returns the new model name if changed, else None.
    """
    try:
        PAUSE_LOCK_PATH.touch()
    except Exception as e:
        print_error(f"Failed to create pause lock file: {e}", exit_code=None)
        return None

    print(f"  !! [PAUSE_REQUIRED] Execution paused due to error. Waiting for user action...", flush=True)
    rlog("EXECUTION PAUSED: Waiting for user intervention...")

    while PAUSE_LOCK_PATH.exists():
        time.sleep(1)

    print_info("Resuming execution...")
    rlog("EXECUTION RESUMED")

    # Check for runtime config update (e.g. model switch)
    if RUNTIME_CONFIG_PATH.exists():
        try:
            config = json.loads(RUNTIME_CONFIG_PATH.read_text(encoding="utf-8"))
            new_model = config.get("gemini_model")
            if new_model:
                print_info(f"Switched model to: {new_model}")
                rlog(f"MODEL SWITCHED: {new_model}")
                # Clean up config
                RUNTIME_CONFIG_PATH.unlink() 
                return new_model
        except Exception as e:
            print_error(f"Failed to read runtime config: {e}", exit_code=None)
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

    # Load Safety Preamble
    safety_preamble_path = PROMPTS_DIR / "_SAFETY_PREAMBLE.md"
    if safety_preamble_path.exists():
        safety_preamble = safety_preamble_path.read_text(encoding="utf-8").strip()
    else:
        # Fallback if file is missing (though it should be there)
        safety_preamble = "You are an AI assistant. Please process the content objectively."

    prompt_parts = [safety_preamble, f"Your specific task is '{mode}'.", "--- INSTRUCTIONS ---", instructions, "--- CONTEXT & INPUTS ---"]
    
    # Prepare log for inputs
    log_inputs = {}

    # Extract rework_feedback to handle it separately/prominently
    rework_feedback = vars_map.get("rework_feedback")

    for key, value in vars_map.items():
        if key == "rework_feedback":
            log_inputs[key] = value
            continue # Skip adding to prompt here, we add it later

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
    
    # Add rework_feedback prominently if it exists
    if rework_feedback:
        prompt_parts.append("\n" + "="*40)
        prompt_parts.append("!!! CRITICAL FEEDBACK FROM PREVIOUS ATTEMPT !!!")
        prompt_parts.append(f"Your previous generation was rejected. You MUST address the following feedback in this new attempt:\n\n{rework_feedback}")
        prompt_parts.append("="*40 + "\n")

    prompt_parts.append("--- YOUR TASK ---")
    prompt_parts.append("Generate your response. Output ONLY the content required (e.g., pure JSON, pure Markdown). No conversational text.")
    final_prompt = "\n".join(prompt_parts)

    current_model_name = model_name

    attempt = 0
    while attempt < retries:
        cmd = [found_agent_path]
        if current_model_name:
            cmd.extend(["-m", current_model_name])
        if mode in ["PLAN", "PLAN_FROM_SLIDES", "ANALYZE_SOURCE_DOCUMENT", "VALIDATE_ANALYSIS", "VALIDATE_MEMO", "DECK", "VALIDATE_DECK", "VALIDATE_SLIDE_SVG", "VALIDATE_CONCEPTUAL_SVG"]:
            cmd.extend(["--output-format", "json"])

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
            attempt += 1 # Empty response counts as a failed attempt

        except subprocess.CalledProcessError as e:
            # This case handles when the command itself fails (e.g., API error)
            stderr_lower = e.stderr.lower()
            rlog(f"AGENT ERROR: {e.stderr.strip()}")
            
            # Detect error types
            is_auth_error = "authentication" in stderr_lower or "login required" in stderr_lower
            is_quota_error = "exhausted" in stderr_lower or "quota" in stderr_lower
            
            error_msg = f"指令執行失敗 (Exit Code: {e.returncode}): {" ".join(e.cmd)}\n  STDERR: {e.stderr.strip()}"

            if is_auth_error:
                print_error("認證失敗或過期 (Authentication failed or expired)。", exit_code=None)
                print_info("請在瀏覽器中完成登入，或在另一個終端機中執行 `gemini auth login`。")
            elif is_quota_error:
                print_error("API quota 已用盡 (API quota exhausted)。", exit_code=None)
                print_info("請等待配額恢復，或切換模型。")
            else:
                print_error(error_msg, exit_code=None)

            # Trigger Pause/Resume Mechanism
            # We pause here to let the user fix the issue (Auth, Quota, or Model Switch)
            # instead of just burning through retries.
            new_model = wait_for_user_action()
            if new_model:
                current_model_name = new_model
                print_info(f"Retrying with new model: {current_model_name}")
            
            # If it was an auth or quota error (or user switched model), we DO NOT count this as a failed attempt.
            # We assume the user fixed it and we should retry immediately without penalty.
            if is_auth_error or is_quota_error or new_model:
                print_info("Retrying current attempt after intervention...")
                continue
            
            # For other errors (e.g. 500, timeouts that aren't quota), we count the attempt.
            attempt += 1

        if attempt < retries:
            print_info(f"Retrying in {delay}s...")
            rlog(f"Waiting {delay}s before retry...")
            time.sleep(delay)

    print_error(f"AI failed to generate a response for {mode} after {retries} attempts.", exit_code=1)
    return "" # Return empty string if all retries fail

def parse_ai_json_output(output: str, mode: str) -> dict | None:
    """
    Parses the AI's output, handling raw JSON, JSON in markdown fences,
    and the gemini tool's wrapper object. Returns None on failure.
    Includes robust fallback parsing for common AI JSON errors.
    """
    
    # 0. Pre-check for Gemini Wrapper (Standard JSON structure)
    # Sometimes the wrapper itself is valid JSON, we should peel it first.
    try:
        # Attempt to parse the outer layer just to check for "response" wrapper
        # This is separate from the main logic because 'output' might be messy text
        # but the wrapper is usually clean JSON.
        outer_data = json.loads(output)
        if isinstance(outer_data, dict) and "response" in outer_data and isinstance(outer_data["response"], str):
             # Recurse with the inner string
             return parse_ai_json_output(outer_data["response"], f"{mode} (Nested)")
    except:
        pass # Not a clean wrapper, proceed to standard cleanup

    # 1. Clean up Markdown fences
    clean_output = output.strip()
    match = re.search(r"```(?:json)?\s*(.*?)```", clean_output, re.DOTALL)
    if match:
        clean_output = match.group(1).strip()
    
    # 2. Try standard parsing (on cleaned output)
    try:
        data = json.loads(clean_output)
        # Double check wrapper inside cleaned output (rare but possible)
        if isinstance(data, dict) and "response" in data and isinstance(data["response"], str):
             return parse_ai_json_output(data["response"], f"{mode} (Nested)")
        rlog_data(f"Parsed JSON Data ({mode})", data)
        return data
    except json.JSONDecodeError as e:
        rlog(f"Standard JSON parse failed for {mode}: {e}")
        pass # Continue to fallback

    rlog(f"Attempting regex fallback for {mode}...")
    
    # 3. Fallback: List Extraction (for DECK, PLAN, PLAN_FROM_SLIDES)
    # Used when we expect a list of items (e.g., slides or pages)
    if any(x in mode for x in ["DECK", "slides", "PLAN"]):
        rlog(f"Attempting list regex parsing for {mode}...")
        extracted_items = []
        
        # Determine list item boundaries based on common keys
        # DECK/slides usually have "page" and "content"
        # PLAN usually has "page" and "topic"
        
        raw_text = clean_output
        # Remove outer array brackets if partially present
        if raw_text.startswith('[') and raw_text.endswith(']'):
             raw_text = raw_text[1:-1]
        elif raw_text.startswith('{') and raw_text.endswith('}'):
             raw_text = raw_text[1:-1] # Try to unwrap object if list is inside
             
        # Split chunks by "page": which is the most consistent anchor
        chunks = re.split(r',?\s*\{\s*"page":', raw_text)
        
        for chunk in chunks:
            if not chunk.strip(): continue
            
            item = {}
            try:
                # Recover 'page' (since we split by it, it's at the start of chunk or we need to add it back)
                # Actually, the regex consumes {"page": so chunk starts with the value
                # e.g. "01", "topic": ...
                
                # Extract Page
                page_m = re.search(r'^\s*"(\d+)"', chunk)
                if page_m:
                    item["page"] = page_m.group(1)
                else:
                    continue # Skip if no page found
                
                # Extract Topic
                topic_m = re.search(r'"topic":\s*"(.*?)"', chunk)
                if topic_m:
                    item["topic"] = topic_m.group(1)
                
                # Extract Content (Crucial for DECK)
                # Content is usually the longest field and might have unescaped quotes
                # We capture from "content": " until the last quote of the chunk
                content_start_m = re.search(r'"content":\s*"', chunk)
                if content_start_m:
                    start_idx = content_start_m.end()
                    end_idx = chunk.rfind('"') # Naive end finding
                    if end_idx > start_idx:
                        content = chunk[start_idx:end_idx]
                        # Basic cleanup
                        content = content.replace('\\"', '"').replace('\\n', '\n')
                        item["content"] = content
                
                if item.get("page"):
                    extracted_items.append(item)
                    
            except Exception as e:
                rlog(f"Failed to parse chunk in {mode}: {e}")
                continue
        
        if extracted_items:
            rlog(f"Loose parsing recovered {len(extracted_items)} items.")
            # Return consistent structure
            if "PLAN" in mode: return {"pages": extracted_items}
            return {"slides": extracted_items}

    # 4. Fallback: Dict Extraction (for ANALYZE_SOURCE_DOCUMENT, VALIDATE)
    # Used when we expect a single object with specific keys
    expected_keys = []
    if "ANALYZE_SOURCE_DOCUMENT" in mode:
        expected_keys = ["document_title", "project_title", "summary", "overview", "document_authors"]
    elif "VALIDATE" in mode:
        expected_keys = ["is_valid", "is_acceptable", "feedback"]
        
    if expected_keys:
        rlog(f"Attempting dict key extraction for {mode}...")
        extracted_data = {}
        raw_text = clean_output
        
        for key in expected_keys:
            # Pattern: "key": "VALUE"
            # We capture until the next quote that is followed by comma or brace
            # This is a heuristic: look for the value between " and "
            # But the value might contain quotes.
            # We try to find "key":\s*" then find the next property start or end of object
            
            try:
                key_pattern = fr'"{key}":\s*"'
                start_m = re.search(key_pattern, raw_text)
                if start_m:
                    start_idx = start_m.end()
                    
                    # Find potential end of this value.
                    # It ends before the next key or end of object.
                    # This is hard. Let's try a greedy approach:
                    # Find the LAST quote before a comma-newline or brace-newline sequence?
                    # Or find the next known key.
                    
                    min_end_idx = len(raw_text)
                    
                    # Check positions of other keys to boundary the current value
                    for other_key in expected_keys:
                        if other_key == key: continue
                        other_m = re.search(fr'"{other_key}":', raw_text[start_idx:])
                        if other_m:
                            # The start of the next key is a hard stop
                            # We need to find the last quote before this
                            found_idx = start_idx + other_m.start()
                            if found_idx < min_end_idx:
                                min_end_idx = found_idx
                    
                    # Also check for end of object }
                    close_m = raw_text.rfind('}')
                    if close_m != -1 and close_m > start_idx and close_m < min_end_idx:
                         min_end_idx = close_m

                    # Now look backwards from min_end_idx for the closing quote
                    candidate_chunk = raw_text[start_idx:min_end_idx]
                    last_quote = candidate_chunk.rfind('"')
                    if last_quote != -1:
                        val = candidate_chunk[:last_quote]
                        # Cleanup
                        val = val.replace('\\"', '"').replace('\\n', '\n')
                        extracted_data[key] = val
                        
                        # Special handling for booleans in VALIDATE
                        if key.startswith("is_"):
                             if "true" in val.lower(): extracted_data[key] = True
                             elif "false" in val.lower(): extracted_data[key] = False
                             
            except Exception as e:
                 rlog(f"Failed to extract key {key}: {e}")
        
        if extracted_data:
            rlog(f"Loose parsing extracted {len(extracted_data)} keys.")
            return extracted_data
        else:
            rlog(f"Loose parsing failed to extract any keys for {mode}.")

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
    if 'agent_execution_retries' not in cfg:
        cfg['agent_execution_retries'] = 3
        
    # Command-line args (from UI) override config.yaml
    cli_args = {k: v for k, v in vars(args).items() if v is not None}
    cfg.update(cli_args)
    return cfg

# ... (omitted) ...

def run_agent(agent: str, mode: str, vars_map: dict, retries: int = 3, delay: int = 5, model_name: str | None = None) -> str:
    # ... (omitted setup code) ...
    
    prompt_parts.append("--- YOUR TASK ---")
    prompt_parts.append("Generate your response. Output ONLY the content required (e.g., pure JSON, pure Markdown). No conversational text.")
    final_prompt = "\n".join(prompt_parts)

    current_model_name = model_name

    attempt = 0
    while attempt < retries:
        cmd = [found_agent_path]
        if current_model_name:
            cmd.extend(["-m", current_model_name])
        if mode in ["PLAN", "PLAN_FROM_SLIDES", "ANALYZE_SOURCE_DOCUMENT", "VALIDATE_ANALYSIS", "VALIDATE_MEMO", "DECK", "VALIDATE_DECK", "VALIDATE_SLIDE_SVG", "VALIDATE_CONCEPTUAL_SVG"]:
            cmd.extend(["--output-format", "json"])

        print_info(f"Calling {agent_cmd.capitalize()} for {mode}... (Attempt {attempt + 1}/{retries})")
        
        rlog(f"AGENT CALL START: {mode} (Attempt {attempt + 1})")
        rlog_data(f"Agent Inputs ({mode})", log_inputs)

        try:
            result = run_command(cmd, input_text=final_prompt)
            output = result.stdout.strip()
            
            rlog_block(f"Agent Raw Output ({mode})", output)
            rlog("AGENT CALL END")

            if output:
                return output

            # Empty output case
            print_error(f"AI returned empty response for {mode}.", exit_code=None)
            attempt += 1

        except subprocess.CalledProcessError as e:
            stderr_lower = e.stderr.lower()
            rlog(f"AGENT ERROR: {e.stderr.strip()}")
            
            error_msg = f"指令執行失敗 (Exit Code: {e.returncode}): {' '.join(e.cmd)}\n  STDERR: {e.stderr.strip()}"
            print_error(error_msg, exit_code=None) # Print error but don't exit script

            # Hint for known errors
            if "authentication" in stderr_lower or "login required" in stderr_lower:
                print_info("Hint: Authentication failed. Please login.")
            elif "exhausted" in stderr_lower or "quota" in stderr_lower:
                print_info("Hint: Quota exhausted. Wait or switch model.")

            # PAUSE for ANY execution error to allow user intervention
            new_model = wait_for_user_action()
            if new_model:
                current_model_name = new_model
                print_info(f"Retrying with new model: {current_model_name}")
            
            print_info("Resuming current attempt...")
            # Do NOT increment attempt count, infinite retries as long as user resumes
            continue

        if attempt < retries:
            print_info(f"Retrying in {delay}s...")
            rlog(f"Waiting {delay}s before retry...")
            time.sleep(delay)

    print_error(f"AI failed to generate a response for {mode} after {retries} attempts.", exit_code=1)
    return ""

# ... (omitted) ...

def main():
    # ... (omitted) ...
    parser.add_argument("--agent-retries", dest="agent_execution_retries", type=int, help="Override agent_execution_retries from config.yaml")
    # ... (omitted) ...

    # ... (inside main logic, replacing hardcoded retries) ...
    
    # ...
    # analysis_output = run_agent(cfg["agent"], "ANALYZE_SOURCE_DOCUMENT", analysis_vars, retries=cfg.get("agent_execution_retries", 3), model_name=cfg.get("gemini_model"))
    
    # ...
    # output = run_agent(cfg["agent"], "PLAN_FROM_SLIDES", ..., retries=cfg.get("agent_execution_retries", 3), ...)
    # output = run_agent(cfg["agent"], "PLAN", ..., retries=cfg.get("agent_execution_retries", 3), ...)
    
    # ...
    # deck_output = run_agent(cfg["agent"], "DECK", deck_vars, retries=cfg.get("agent_execution_retries", 3), model_name=cfg.get("gemini_model"))
    
    # ...
    # current_attempt_content = run_agent(cfg["agent"], "MEMO", memo_vars, retries=cfg.get("agent_execution_retries", 3), model_name=cfg.get("gemini_model"))
    
    # ...
    # raw_svg_attempt = run_agent(cfg["agent"], "CREATE_SLIDE_SVG", svg_vars, retries=cfg.get("agent_execution_retries", 3), model_name=model_name)
    
    # ...
    # raw_conceptual_svg = run_agent(cfg["agent"], "CREATE_CONCEPTUAL_SVG", conceptual_vars, retries=cfg.get("agent_execution_retries", 3), model_name=model_name)


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