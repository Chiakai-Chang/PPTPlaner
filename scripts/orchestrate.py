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
    # Get version from config or use default
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
            
            error_msg = f"指令執行失敗 (Exit Code: {e.returncode}): {' '.join(e.cmd)}\n  STDERR: {e.stderr.strip()}"

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
    return ""

def main():
    parser = argparse.ArgumentParser(description="PPTPlaner Orchestrator")
    parser.add_argument("--source", required=True, help="Path to source file")
    parser.add_argument("--manual-title", dest="manual_title")
    parser.add_argument("--manual-author", dest="manual_author")
    parser.add_argument("--manual-url", dest="manual_url")
    parser.add_argument("--no-svg", action="store_true", help="Skip SVG generation")
    parser.add_argument("--custom-instruction", dest="custom_instruction")
    parser.add_argument("--plan-from-slides", dest="plan_from_slides", help="Path to existing slides file")
    parser.add_argument("--gemini-model", dest="gemini_model")
    parser.add_argument("--agent", default="gemini")
    
    # Rework counts
    parser.add_argument("--plan-reworks", type=int, default=3)
    parser.add_argument("--slide-reworks", type=int, default=5)
    parser.add_argument("--memo-reworks", type=int, default=5)
    parser.add_argument("--slide-svg-reworks", type=int, default=3)
    parser.add_argument("--conceptual-svg-reworks", type=int, default=3)
    parser.add_argument("--agent-retries", dest="agent_execution_retries", type=int, default=3)

    args = parser.parse_args()

    # --- Initialization ---
    init_logger(ROOT)
    cfg = get_config(args)
    
    # Log Run Parameters
    run_params = {
        "args": vars(args),
        "config": cfg,
        "source_file": str(args.source),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    rlog_data("Run Configuration & Inputs", run_params)

    print_header(f"PPTPlaner v{cfg.get('version', 'Unknown')} - Started")
    
    source_path = Path(args.source)
    if not source_path.exists():
        print_error(f"Source file not found: {source_path}")

    # --- Phase 1: Analysis & Setup ---
    print_header("Phase 1: Analysis & Planning")
    
    print_info("Analyzing source document and integrating metadata...")
    
    # Always run analysis to get summary, overview, and validate manual inputs
    analysis_vars = {
        "source_file_path": str(source_path),
        "custom_instruction": args.custom_instruction or "",
        "manual_title": args.manual_title or "",
        "manual_author": args.manual_author or "",
        "manual_url": args.manual_url or ""
    }
    
    analysis_data = None
    acceptable_analysis_data = None
    ANALYSIS_REWORKS = 3
    feedback_history = []
    
    for attempt in range(ANALYSIS_REWORKS + 1):
        if attempt > 0: print_info(f"Reworking Analysis... (Attempt {attempt}/{ANALYSIS_REWORKS})")
        
        analysis_json = run_agent(cfg["agent"], "ANALYZE_SOURCE_DOCUMENT", analysis_vars, retries=cfg["agent_execution_retries"], model_name=cfg.get("gemini_model"))
        current_data = parse_ai_json_output(analysis_json, "ANALYZE_SOURCE_DOCUMENT")
        
        if not current_data:
            print_error(f"Analysis generation failed on attempt {attempt}.", exit_code=None)
            continue
            
        # Validate
        val_vars = {
            "analysis_data": json.dumps(current_data, ensure_ascii=False),
            "source_file_path": str(source_path),
            "manual_title": args.manual_title or "",
            "manual_author": args.manual_author or ""
        }
        val_json = run_agent(cfg["agent"], "VALIDATE_ANALYSIS", val_vars, retries=cfg["agent_execution_retries"], model_name=cfg.get("gemini_model"))
        val_res = parse_ai_json_output(val_json, "VALIDATE_ANALYSIS")
        
        feedback = val_res.get("feedback", "No feedback") if val_res else "Invalid response"
        
        if val_res and val_res.get("is_valid"):
            print_success("Analysis validation passed (Perfect).")
            analysis_data = current_data
            break
        elif val_res and val_res.get("is_acceptable"):
            print_success("Analysis validation passed (Acceptable). Striving for perfection...")
            if not acceptable_analysis_data: acceptable_analysis_data = current_data
            # Continue to try to get perfect
        
        print_info(f"Analysis validation feedback: {feedback}")
        feedback_history.append(f"Attempt {attempt+1} Feedback: {feedback}")
        analysis_vars["rework_feedback"] = "\n\n".join(feedback_history)
    
    if not analysis_data and acceptable_analysis_data:
        print_info("Max retries reached. Using best acceptable Analysis result.")
        analysis_data = acceptable_analysis_data

    if analysis_data:
        # AI returns the final decision on these fields (integrating manual input)
        project_title = analysis_data.get("project_title") or analysis_data.get("document_title") or args.manual_title or "Untitled_Project"
        project_author = analysis_data.get("document_authors") or args.manual_author or "Unknown Author"
        source_url = analysis_data.get("source_url") or args.manual_url or ""
        summary = analysis_data.get("summary") or "No summary available."
        overview_text = analysis_data.get("overview") or ""
    else:
        print_error("Analysis failed. Falling back to manual/default values.")
        project_title = args.manual_title or "Untitled_Project"
        project_author = args.manual_author or "Unknown Author"
        source_url = args.manual_url or ""
        summary = "No summary available."
        overview_text = ""

    # Sanitize title for folder name
    safe_title = sanitize_filename(project_title)[:50]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = OUTPUT_ROOT / f"{timestamp}_{safe_title}"
    output_dir.mkdir(parents=True, exist_ok=True)
    slides_dir = output_dir / "slides"
    slides_dir.mkdir(exist_ok=True)
    notes_dir = output_dir / "notes"
    notes_dir.mkdir(exist_ok=True)
    
    print_success(f"Output directory created: {output_dir}")

    # Save Overview
    overview_content = f"# {project_title}\n\n**Author:** {project_author}\n\n**Source:** {source_url}\n\n## Summary\n{summary}\n\n## Overview\n{overview_text}\n"
    (output_dir / "overview.md").write_text(overview_content, encoding="utf-8")

    # --- Phase 2: Planning ---
    print_info("Generating Presentation Plan...")
    plan_data = None
    
    plan_mode = "PLAN_FROM_SLIDES" if args.plan_from_slides else "PLAN"
    plan_vars = {}
    if args.plan_from_slides:
        print_info(f"Deriving plan from existing slides: {args.plan_from_slides}")
        plan_vars["slides_file_path"] = args.plan_from_slides
    else:
        plan_vars["source_file_path"] = str(source_path)
        plan_vars["custom_instruction"] = args.custom_instruction or ""

    feedback_history = []
    for attempt in range(args.plan_reworks + 1):
        if attempt > 0: print_info(f"Reworking Plan... (Attempt {attempt}/{args.plan_reworks})")
        
        plan_json = run_agent(cfg["agent"], plan_mode, plan_vars, retries=cfg["agent_execution_retries"], model_name=cfg.get("gemini_model"))
        plan_data = parse_ai_json_output(plan_json, plan_mode)
        
        if plan_data and "pages" in plan_data and isinstance(plan_data["pages"], list) and len(plan_data["pages"]) > 0:
            print_success("Plan generated successfully.")
            break
        
        feedback = "The previous output was invalid. Please ensure you output a valid JSON object with a 'pages' key containing a list of page objects."
        print_error(f"Plan validation failed on attempt {attempt}: Missing 'pages' list or invalid JSON.", exit_code=None)
        
        feedback_history.append(f"Attempt {attempt+1} Feedback: {feedback}")
        plan_vars["rework_feedback"] = "\n\n".join(feedback_history)

    if not plan_data or "pages" not in plan_data:
        print_error("Failed to generate a valid plan after all retries.")
        sys.exit(1)

    (output_dir / ".plan.json").write_text(json.dumps(plan_data, indent=2, ensure_ascii=False), encoding="utf-8")
    pages_plan = plan_data["pages"]
    print_success(f"Plan generated with {len(pages_plan)} pages.")

    # --- Phase 3: Deck Generation ---
    print_header("Phase 3: Deck Generation (Slides)")
    
    full_deck_content = ""
    # We generate the whole deck at once (or based on plan)
    # The DECK agent usually takes the plan and source and generates all slides.
    
    deck_vars = {
        "source_file_path": str(source_path),
        "plan_json": json.dumps(plan_data, ensure_ascii=False),
        "custom_instruction": args.custom_instruction or ""
    }
    
    last_deck_content = ""
    acceptable_deck_content = ""
    feedback_history = []
    
    for attempt in range(args.slide_reworks + 1):
        if attempt > 0: print_info(f"Reworking Deck... (Attempt {attempt}/{args.slide_reworks})")
        
        deck_json_raw = run_agent(cfg["agent"], "DECK", deck_vars, retries=cfg["agent_execution_retries"], model_name=cfg.get("gemini_model"))
        deck_data = parse_ai_json_output(deck_json_raw, "DECK")
        
        if not deck_data or "slides" not in deck_data:
            print_error(f"Deck generation failed on attempt {attempt}.", exit_code=None)
            continue
            
        # Reconstruct full markdown for validation
        slides_list = deck_data["slides"]
        current_deck_md = ""
        for slide in slides_list:
            current_deck_md += f"<!-- PAGE {slide.get('page')} -->\n{slide.get('content')}\n\n"
        
        # Validate
        val_vars = {"deck_content": current_deck_md, "plan_json": json.dumps(plan_data, ensure_ascii=False)}
        val_json_raw = run_agent(cfg["agent"], "VALIDATE_DECK", val_vars, retries=cfg["agent_execution_retries"], model_name=cfg.get("gemini_model"))
        val_res = parse_ai_json_output(val_json_raw, "VALIDATE_DECK")
        
        feedback = val_res.get("feedback", "No feedback") if val_res else "Invalid response"
        
        if val_res and val_res.get("is_valid"):
            print_success("Deck validation passed (Perfect).")
            last_deck_content = slides_list
            break
        elif val_res and val_res.get("is_acceptable"):
            print_success("Deck validation passed (Acceptable). Striving for perfection...")
            if not acceptable_deck_content: acceptable_deck_content = slides_list
            # Continue
        
        print_info(f"Deck validation feedback: {feedback}")
        
        feedback_history.append(f"Attempt {attempt+1} Feedback: {feedback}")
        deck_vars["rework_feedback"] = "\n\n".join(feedback_history)

    if not last_deck_content and acceptable_deck_content:
        print_info("Max retries reached. Using best acceptable Deck result.")
        last_deck_content = acceptable_deck_content

    # Save Slides
    if not last_deck_content:
        print_error("Failed to generate deck after all retries.")
    
    full_slides_text_for_memo = ""
    for slide in last_deck_content:
        p_num = str(slide.get("page")).zfill(2)
        p_topic = sanitize_filename(slide.get("topic", "Topic"))
        fname = f"{p_num}_{p_topic}.md"
        content = slide.get("content", "")
        (slides_dir / fname).write_text(content, encoding="utf-8")
        full_slides_text_for_memo += f"--- Page {p_num}: {p_topic} ---\n{content}\n\n"

    # --- Phase 4: Memo Generation ---
    print_header("Phase 4: Memo Generation (Speaker Notes)")
    
    for i, slide in enumerate(last_deck_content):
        p_num = str(slide.get("page")).zfill(2)
        p_topic = slide.get("topic", "Topic")
        safe_topic = sanitize_filename(p_topic)
        print_info(f"Generating Memo for Page {p_num}: {p_topic}...")
        
        slide_content = slide.get("content", "")
        
        memo_vars = {
            "source_file_path": str(source_path),
            "current_slide_content": slide_content,
            "full_slides_content": full_slides_text_for_memo,
            "page": p_num,
            "topic": p_topic,
            "custom_instruction": args.custom_instruction or ""
        }
        
        final_memo = ""
        acceptable_memo = ""
        feedback_history = []
        
        for attempt in range(args.memo_reworks + 1):
            if attempt > 0: print_info(f"  Reworking Memo {p_num}... (Attempt {attempt}/{args.memo_reworks})")
            
            memo_raw = run_agent(cfg["agent"], "MEMO", memo_vars, retries=cfg["agent_execution_retries"], model_name=cfg.get("gemini_model"))
            current_memo = memo_raw
            
            # Validate
            val_vars = {"memo_content": current_memo, "slide_content": slide_content}
            val_json_raw = run_agent(cfg["agent"], "VALIDATE_MEMO", val_vars, retries=cfg["agent_execution_retries"], model_name=cfg.get("gemini_model"))
            val_res = parse_ai_json_output(val_json_raw, "VALIDATE_MEMO")
            
            feedback = val_res.get("feedback", "") if val_res else ""
            
            if val_res and val_res.get("is_valid"):
                print_success(f"Memo {p_num} validation passed (Perfect).")
                final_memo = current_memo
                break
            elif val_res and val_res.get("is_acceptable"):
                print_success(f"Memo {p_num} validation passed (Acceptable). Striving for perfection...")
                if not acceptable_memo: acceptable_memo = current_memo
                # Continue retrying
            
            if feedback: print_info(f"  [QA Feedback]: {feedback}")
            
            feedback_history.append(f"Attempt {attempt+1} Feedback: {feedback}")
            memo_vars["rework_feedback"] = "\n\n".join(feedback_history)
        
        if not final_memo and acceptable_memo:
            print_info(f"Max retries reached for Memo {p_num}. Using best acceptable result.")
            final_memo = acceptable_memo
        
        if not final_memo: final_memo = current_memo # Fallback to last attempt if everything failed
        
        (notes_dir / f"note-{p_num}_{safe_topic}-zh.md").write_text(final_memo, encoding="utf-8")

    # --- Phase 5: SVG Generation ---
    if not args.no_svg:
        print_header("Phase 5: SVG Generation")
        
        for i, slide in enumerate(last_deck_content):
            p_num = str(slide.get("page")).zfill(2)
            print_info(f"Generating SVGs for Page {p_num}...")
            
            slide_content = slide.get("content", "")
            memo_content = ""
            memo_file = notes_dir / f"note-{p_num}_{sanitize_filename(slide.get('topic', 'Topic'))}-zh.md"
            if memo_file.exists():
                memo_content = memo_file.read_text(encoding="utf-8")
            
            # --- 1. Slide SVG ---
            svg_vars = {"slide_content": slide_content}
            final_slide_svg = ""
            acceptable_slide_svg = ""
            feedback_history = []
            
            for attempt in range(args.slide_svg_reworks + 1):
                if attempt > 0: print_info(f"  Reworking Slide SVG... (Attempt {attempt}/{args.slide_svg_reworks})")
                
                raw = run_agent(cfg["agent"], "CREATE_SLIDE_SVG", svg_vars, retries=cfg["agent_execution_retries"], model_name=cfg.get("gemini_model"))
                
                current_svg = raw
                svg_match = re.search(r"<svg.*?</svg>", raw, re.DOTALL)
                if svg_match: current_svg = svg_match.group(0)
                
                if not current_svg or "<svg" not in current_svg:
                    print_info("  No valid SVG found in response.")
                    continue

                # Validate
                val_vars = {"svg_code": current_svg}
                val_json = run_agent(cfg["agent"], "VALIDATE_SLIDE_SVG", val_vars, retries=cfg["agent_execution_retries"], model_name=cfg.get("gemini_model"))
                val_res = parse_ai_json_output(val_json, "VALIDATE_SLIDE_SVG")
                
                feedback = val_res.get("feedback", "") if val_res else ""

                if val_res and val_res.get("is_valid"):
                    print_success(f"Slide SVG {p_num} validation passed (Perfect).")
                    final_slide_svg = current_svg
                    break
                elif val_res and val_res.get("is_acceptable"):
                    print_success(f"Slide SVG {p_num} validation passed (Acceptable). Striving for perfection...")
                    if not acceptable_slide_svg: acceptable_slide_svg = current_svg
                    # Continue
                
                if feedback: print_info(f"  [QA Feedback]: {feedback}")
                
                feedback_history.append(f"Attempt {attempt+1} Feedback: {feedback}")
                svg_vars["rework_feedback"] = "\n\n".join(feedback_history)
            
            if not final_slide_svg and acceptable_slide_svg:
                print_info(f"Max retries reached for Slide SVG {p_num}. Using best acceptable result.")
                final_slide_svg = acceptable_slide_svg

            if final_slide_svg:
                (slides_dir / f"slide_{p_num}.svg").write_text(final_slide_svg, encoding="utf-8")

            # --- 2. Conceptual SVG ---
            con_vars = {"slide_content": slide_content, "memo_content": memo_content}
            final_con_svg = ""
            acceptable_con_svg = ""
            feedback_history = []
            
            for attempt in range(args.conceptual_svg_reworks + 1):
                if attempt > 0: print_info(f"  Reworking Conceptual SVG... (Attempt {attempt}/{args.conceptual_svg_reworks})")
                
                raw = run_agent(cfg["agent"], "CREATE_CONCEPTUAL_SVG", con_vars, retries=cfg["agent_execution_retries"], model_name=cfg.get("gemini_model"))
                
                if "NO_CONCEPTUAL_SVG_NEEDED" in raw:
                    print_info("  Agent decided no conceptual SVG is needed.")
                    break
                
                current_svg = raw
                svg_match = re.search(r"<svg.*?</svg>", raw, re.DOTALL)
                if svg_match: current_svg = svg_match.group(0)
                
                if not current_svg or "<svg" not in current_svg:
                    continue

                # Validate
                val_vars = {"svg_code": current_svg, "slide_content": slide_content, "memo_content": memo_content}
                val_json = run_agent(cfg["agent"], "VALIDATE_CONCEPTUAL_SVG", val_vars, retries=cfg["agent_execution_retries"], model_name=cfg.get("gemini_model"))
                val_res = parse_ai_json_output(val_json, "VALIDATE_CONCEPTUAL_SVG")
                
                feedback = val_res.get("feedback", "") if val_res else ""

                if val_res and val_res.get("is_valid"):
                    print_success(f"Conceptual SVG {p_num} validation passed (Perfect).")
                    final_con_svg = current_svg
                    break
                elif val_res and val_res.get("is_acceptable"):
                    print_success(f"Conceptual SVG {p_num} validation passed (Acceptable). Striving for perfection...")
                    if not acceptable_con_svg: acceptable_con_svg = current_svg
                    # Continue
                
                if feedback: print_info(f"  [QA Feedback]: {feedback}")
                
                feedback_history.append(f"Attempt {attempt+1} Feedback: {feedback}")
                con_vars["rework_feedback"] = "\n\n".join(feedback_history)

            if not final_con_svg and acceptable_con_svg:
                print_info(f"Max retries reached for Conceptual SVG {p_num}. Using best acceptable result.")
                final_con_svg = acceptable_con_svg

            if final_con_svg:
                (slides_dir / f"conceptual_{p_num}.svg").write_text(final_con_svg, encoding="utf-8")

    # --- Phase 6: Build Guide ---
    print_header("Phase 6: Finalizing Output")
    build_script_path = ROOT / "scripts" / "build_guide.py"
    guide_file = output_dir / "guide.html"
    
    if build_script_path.exists():
        run_command([sys.executable, str(build_script_path), f"--output-dir={output_dir}"])
        print_success(f"Guide file created at: {guide_file}")
        try:
            webbrowser.open(guide_file.as_uri())
        except: pass
    
    os.startfile(output_dir)
    print_header("Run Complete!")
    rlog("--- RUN COMPLETE ---")

if __name__ == "__main__":
    main()