# scripts/resume_svg_generation.py
import sys, os, json, subprocess, re, time, argparse, yaml, shutil
from pathlib import Path

# --- Constants & Helpers from orchestrate.py ---
ROOT = Path(__file__).resolve().parents[1]
AGENTS_MD_PATH = ROOT / "AGENTS.md"
ERROR_LOG_PATH = ROOT / "error.log"

def print_header(title: str):
    bar = "=" * 60; print(f"\n{bar}\n  {title}\n{bar}", flush=True)
def print_success(msg: str): print(f"  ✓ {msg}", flush=True)
def print_info(msg: str): print(f"  ▶ {msg}", flush=True)
def print_error(msg: str, exit_code: int = 1):
    error_message = f"  ✗ [ERROR] {msg}"
    print(error_message, file=sys.stderr, flush=True)
    # Log error logic omitted for this specific script
    if exit_code is not None: sys.exit(exit_code)

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
    for key, value in vars_map.items():
        if key.endswith("_path") and value and os.path.exists(value):
            prompt_parts.append(f"Content for '{os.path.basename(value)}':\n```\n{Path(value).read_text(encoding='utf-8')}\n```")
        elif key.endswith("_content") and value: prompt_parts.append(f"Provided Content for '{key}':\n```\n{value}\n```")
        else: prompt_parts.append(f"- {key}: {value}")
    prompt_parts.append("--- YOUR TASK ---")
    prompt_parts.append("Generate your response. Output ONLY the content required (e.g., pure JSON, pure Markdown). No conversational text.")
    final_prompt = "\n".join(prompt_parts)

    cmd = [found_agent_path]
    if model_name:
        cmd.extend(["-m", model_name])
    if mode in ["VALIDATE_SLIDE_SVG", "VALIDATE_CONCEPTUAL_SVG"]:
        cmd.extend(["--output-format", "json"])

    for attempt in range(retries):
        print_info(f"Calling {agent_cmd.capitalize()} for {mode}... (Attempt {attempt + 1}/{retries})")
        try:
            result = run_command(cmd, input_text=final_prompt)
            output = result.stdout.strip()
            if output:
                return output # Success

            # This case handles empty output, which might not be an error but requires a retry.
            print_error(f"AI returned empty response for {mode}.", exit_code=None)

        except subprocess.CalledProcessError as e:
            # This case handles when the command itself fails (e.g., API error)
            stderr_lower = e.stderr.lower()
            if "authentication" in stderr_lower or "login required" in stderr_lower:
                print_error("認證失敗或過期 (Authentication failed or expired)。", exit_code=None)
                print_info("請在瀏覽器中完成登入，或在另一個終端機中執行 `gemini auth login`。")
                # No longer blocking with input(), let the GUI handle the pause.
            elif "exhausted" in stderr_lower or "quota" in stderr_lower:
                print_error("API quota 已用盡 (API quota exhausted)。", exit_code=None)
                print_info("請在 GUI 中選擇 '繼續' 來等待配額恢復，或選擇 '切換模型' 來嘗試其他模型。")
                # No longer blocking with input(), let the GUI handle the pause.
            else:
                print_error(f"指令執行失敗 (Exit Code: {e.returncode}): {" ".join(e.cmd)}\n  STDERR: {e.stderr.strip()}", exit_code=None)

        if attempt < retries - 1:
            print_info(f"Retrying in {delay}s...")
            time.sleep(delay)

    print_error(f"AI failed to generate a response for {mode} after {retries} attempts.", exit_code=1)
    return "" # Return empty string if all retries fail

def parse_ai_json_output(output: str, mode: str) -> dict:
    """
    Parses the AI's output, handling raw JSON, JSON in markdown fences,
    and the gemini tool's wrapper object.
    """
    try:
        # First, try to strip markdown fences from the entire output string.
        match = re.search(r"```(?:json)?\s*({.*?})\s*```", output, re.DOTALL)
        json_str = match.group(1).strip() if match else output.strip()

        # Now, parse the cleaned/original string.
        data = json.loads(json_str)

        # If the parsed data has a "response" field and it's a string,
        # it's likely the gemini tool's wrapper. The actual payload is inside.
        if "response" in data and isinstance(data["response"], str):
            nested_str = data["response"]
            # The nested string could ALSO have markdown fences.
            nested_match = re.search(r"```(?:json)?\s*({.*?})\s*```", nested_str, re.DOTALL)
            final_json_str = nested_match.group(1).strip() if nested_match else nested_str.strip()
            return json.loads(final_json_str)
        else:
            # Otherwise, the parsed data is the direct payload.
            return data
    except (json.JSONDecodeError, AttributeError) as e:
        print_error(f"{mode} 階段輸出不是有效的 JSON。收到的內容: {output}\nError: {e}", exit_code=1)

# --- Main Resume Logic ---
def main():
    parser = argparse.ArgumentParser(description="Resume SVG generation for a PPTPlaner run.")
    parser.add_argument("--output-dir", required=True, help="The existing output directory to resume work in.")
    parser.add_argument("--agent", default="gemini", help="AI agent to use (e.g., gemini)")
    parser.add_argument("--gemini-model", dest="gemini_model", help="Specific Gemini model to use (e.g., gemini-pro, gemini-1.5-pro-latest)")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    slides_dir = output_dir / "slides"
    notes_dir = output_dir / "notes"
    
    if not all([output_dir.is_dir(), slides_dir.is_dir(), notes_dir.is_dir()]):
        print_error(f"Provided output directory '{output_dir}' is incomplete or does not exist.")

    config_path = ROOT / "config.yaml"
    cfg = yaml.safe_load(config_path.read_text(encoding="utf-8")) if config_path.exists() else {}
    MAX_SLIDE_SVG_REWORKS = cfg.get("slide_svg_max_reworks", 5)
    MAX_CONCEPTUAL_SVG_REWORKS = cfg.get("conceptual_svg_max_reworks", 5)

    # Reconstruct the 'pages' list from the filesystem
    slide_files = sorted([f for f in os.listdir(slides_dir) if f.endswith('.md')])
    pages = []
    for slide_file in slide_files:
        match = re.match(r'(\d+)_(.*)\.md', slide_file)
        if match:
            pages.append({"page": match.group(1), "topic": match.group(2)})

    if not pages:
        print_error(f"Could not find any slide markdown files in '{slides_dir}' to resume from.")

    # --- Progress Tracking Setup ---
    progress_file = output_dir / ".svg_progress.json"
    progress = {}
    if progress_file.exists():
        try:
            progress = json.loads(progress_file.read_text(encoding="utf-8"))
            print_info(f"Resuming from existing progress file: {progress_file.name}")
        except json.JSONDecodeError:
            print_error(f"Could not parse progress file {progress_file.name}. Starting fresh.", exit_code=None)
            progress = {} # Reset progress if file is corrupt
    
    # Ensure all pages are in the progress file
    all_pages_found = True
    for item in pages:
        page_id = item["page"]
        if page_id not in progress:
            all_pages_found = False
            progress[page_id] = {"slide_svg": "pending", "conceptual_svg": "pending"}
    
    if not all_pages_found or not progress_file.exists():
        # Save the initial or updated progress file
        progress_file.write_text(json.dumps(progress, indent=4, ensure_ascii=False), encoding="utf-8")
        print_info("Initialized or updated SVG progress tracking file.")

    # Directly call a copied/adapted version of the generate_svgs logic
    print_header(f"Resuming Run: Generating SVGs ({len(pages)} pages)")

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

            svg_vars = {"slide_content": slide_content}

            for attempt in range(MAX_SLIDE_SVG_REWORKS + 1):
                if attempt > 0:
                    print_info(f"Reworking Slide SVG for page {page}... (Attempt {attempt}/{MAX_SLIDE_SVG_REWORKS})")
                
                raw_svg_attempt = run_agent(args.agent, "CREATE_SLIDE_SVG", svg_vars, retries=1, model_name=args.gemini_model)
                
                # Attempt to extract SVG from a potentially verbose response
                svg_match = re.search(r"<svg.*?</svg>", raw_svg_attempt, re.DOTALL)
                current_svg_attempt = svg_match.group(0) if svg_match else raw_svg_attempt

                if not current_svg_attempt or not current_svg_attempt.strip().startswith("<svg"):
                    print_error(f"Slide SVG generation for page {page} returned invalid content on attempt {attempt}.", exit_code=None)
                    continue
                
                last_slide_svg_attempt = current_svg_attempt

                validation_vars = {"svg_code": last_slide_svg_attempt}
                validation_json = run_agent(args.agent, "VALIDATE_SLIDE_SVG", validation_vars, retries=2, model_name=args.gemini_model)
                validation_result = parse_ai_json_output(validation_json, "VALIDATE_SLIDE_SVG")

                if validation_result.get("is_valid", False):
                    print_success(f"Perfect Slide SVG validation passed for page {page}.")
                    perfect_slide_svg = last_slide_svg_attempt
                    break
                elif validation_result.get("is_acceptable", False):
                    print_success(f"Slide SVG validation 'acceptable' for page {page}.")
                    acceptable_slide_svg = last_slide_svg_attempt
                
                feedback = validation_result.get("feedback", "No feedback provided.")
                print_error(f"Slide SVG validation failed for page {page}. Feedback: {feedback}", exit_code=None)
                svg_vars["rework_feedback"] = feedback

            final_slide_svg = perfect_slide_svg or acceptable_slide_svg or last_slide_svg_attempt
            if final_slide_svg:
                slide_svg_path.write_text(final_slide_svg, encoding="utf-8")
                # Update progress
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

            conceptual_vars = {"slide_content": slide_content, "memo_content": memo_content}

            for attempt in range(MAX_CONCEPTUAL_SVG_REWORKS + 1):
                if attempt > 0:
                    print_info(f"Reworking Conceptual SVG for page {page}... (Attempt {attempt}/{MAX_CONCEPTUAL_SVG_REWORKS})")

                raw_conceptual_svg = run_agent(args.agent, "CREATE_CONCEPTUAL_SVG", conceptual_vars, retries=1, model_name=args.gemini_model)

                if "NO_CONCEPTUAL_SVG_NEEDED" in raw_conceptual_svg:
                    print_info(f"Agent decided no conceptual SVG is needed for page {page}.")
                    last_conceptual_svg_attempt = "NO_CONCEPTUAL_SVG_NEEDED" # Special marker
                    break
                
                if "CONCEPTUAL_SVG_FAILED" in raw_conceptual_svg:
                    print_error(f"Conceptual SVG generation failed for page {page} on attempt {attempt}.", exit_code=None)
                    continue

                # Attempt to extract SVG from a potentially verbose response
                svg_match = re.search(r"<svg.*?</svg>", raw_conceptual_svg, re.DOTALL)
                current_conceptual_svg = svg_match.group(0) if svg_match else raw_conceptual_svg

                if not current_conceptual_svg or not current_conceptual_svg.strip().startswith("<svg"):
                    print_error(f"Conceptual SVG generation for page {page} returned invalid content on attempt {attempt}.", exit_code=None)
                    continue

                last_conceptual_svg_attempt = current_conceptual_svg
                
                validation_vars = {"svg_code": last_conceptual_svg_attempt, "slide_content": slide_content, "memo_content": memo_content}
                validation_json = run_agent(args.agent, "VALIDATE_CONCEPTUAL_SVG", validation_vars, retries=2, model_name=args.gemini_model)
                validation_result = parse_ai_json_output(validation_json, "VALIDATE_CONCEPTUAL_SVG")

                if validation_result.get("is_valid", False):
                    print_success(f"Perfect Conceptual SVG validation passed for page {page}.")
                    perfect_conceptual_svg = last_conceptual_svg_attempt
                    break
                elif validation_result.get("is_acceptable", False):
                    print_success(f"Conceptual SVG validation 'acceptable' for page {page}.")
                    acceptable_conceptual_svg = last_conceptual_svg_attempt

                feedback = validation_result.get("feedback", "No feedback provided.")
                print_error(f"Conceptual SVG validation failed for page {page}. Feedback: {feedback}", exit_code=None)
                conceptual_vars["rework_feedback"] = feedback

            final_conceptual_svg = perfect_conceptual_svg or acceptable_conceptual_svg or last_conceptual_svg_attempt
            
            # If we got a valid SVG, write it.
            if final_conceptual_svg and final_conceptual_svg != "NO_CONCEPTUAL_SVG_NEEDED":
                conceptual_svg_path.write_text(final_conceptual_svg, encoding="utf-8")
                print_success(f"  Conceptual SVG saved for page {page}")

            # If the process finished (either by creating an SVG or deciding one wasn't needed), update progress.
            if final_conceptual_svg:
                progress[page]["conceptual_svg"] = "completed"
                progress_file.write_text(json.dumps(progress, indent=4, ensure_ascii=False), encoding="utf-8")
    
    # --- Final Step: Build Guide ---
    print_header("Phase 3: Finalizing Output")
    build_script_path = ROOT / "scripts" / "build_guide.py"
    if build_script_path.exists():
        run_command([sys.executable, str(build_script_path), f"--output-dir={output_dir}"])
        guide_file = output_dir / "guide.html"
        print_success(f"Guide file created at: {guide_file}")
        # webbrowser.open(guide_file.as_uri()) # Commented out for automated runs
    
    print_header("Resume Run Complete!")

if __name__ == "__main__":
    main()
