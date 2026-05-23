# C.A.S.E. Framework — System Protocol for AI Agents

> **Audience:** AI agents (Coding Agents, local LLMs, automated tools) operating within the C.A.S.E. framework.
> **Language:** English (to maximize instruction-following compliance across all LLM backends).
> **Authority:** This document is a Layer 2 (Macro Layer) protocol. It MUST be followed by all Layer 3 (Micro Layer) agents.

---

## 1. Core Axioms (Non-Negotiable)

These three axioms are the foundation of C.A.S.E. Violating any axiom is a critical error.

| Axiom | Rule |
|-------|------|
| **Tiered Intelligence** | Layer 3 agents MUST NOT attempt macro-level planning. Only interpret and execute the assigned Atomic Task Package. |
| **File as State** | All memory, progress, and context MUST be materialized as files. Never rely on conversational context as the sole source of truth. |
| **Dual-track Verification** | Worker and Checker roles MUST be separate. A Worker MUST NOT self-approve its own output as final. |

---

## 2. Directory Structure — Standard Layout

All C.A.S.E. projects MUST conform to the following directory schema:

```
<project_root>/
├── 00_Constitution/          # READ-ONLY for all agents
│   └── core.md               # Human-authored global constraints and mission objective
│
├── 01_Roadmap/               # READ-ONLY for Layer 3 agents
│   ├── roadmap.md            # Phase breakdown and milestone definitions
│   └── global_dod.md         # Global Definition of Done — final acceptance criteria
│
└── 02_Task_Queue/            # READ-WRITE for Layer 3 agents (own task folder only)
    └── Task_<NNN>_<slug>/    # Atomic Task Package
        ├── role.md           # Agent persona for this task (System Prompt equivalent)
        ├── recipe.md         # Task instructions + local Definition of Done (DoD)
        ├── status.txt        # State machine file — see Section 4
        ├── inputs/           # Source data or symlinks to prior task outputs
        ├── output.md         # Agent's primary deliverable
        ├── feedback.md       # Checker's review notes (written by Checker role only)
        └── action_log.jsonl  # Append-only tool call log (one JSON object per line)
```

---

## 3. Atomic Task Package — Required Files

Every task folder MUST contain all of the following before a Layer 3 agent begins work:

### `role.md`
- Defines the agent's persona and scope for this task.
- Written by Layer 2 (cloud model).
- Agents MUST load this as their effective System Prompt for the task.
- Example: `"You are a rigorous data extraction specialist. Your sole focus is the inputs/ directory."`

### `recipe.md`
Required sections (in order):
1. **Objective** — What this task must produce.
2. **Input Sources** — Which files in `inputs/` to process and how.
3. **Output Specification** — Exact format and content required in `output.md`.
4. **Local Definition of Done (DoD)** — Checklist the Checker will use. Each item MUST be verifiable.
5. **Constraints** — Anything the agent MUST NOT do.
6. **Escalation Trigger** — Conditions under which the agent MUST call `escalate_issue`.

### `status.txt`
- Contains exactly one of the five allowed status tokens (see Section 4).
- No other content is permitted in this file.

### `inputs/`
- All source material the agent is authorized to read.
- Agents MUST NOT read files outside `inputs/`, `role.md`, `recipe.md`, `00_Constitution/core.md`, and `01_Roadmap/*.md` (only when explicitly listed in `recipe.md > Input Sources`).

---

## 4. State Machine — `status.txt` Tokens

`status.txt` MUST contain exactly one of these tokens, with no trailing whitespace:

| Token | Meaning | Who Sets It |
|-------|---------|-------------|
| `PENDING` | Task awaiting execution | Layer 2 (initial) or Checker (on rejection) |
| `IN_PROGRESS` | Worker agent actively executing | Worker agent (upon starting) |
| `REVIEW` | Worker complete; awaiting Checker | Worker agent (upon submitting) |
| `DONE` | Checker approved; task closed | Checker agent |
| `ESCALATED` | Task halted; human or Layer 2 intervention required. Triggered by: (a) Checker retry limit exceeded, or (b) Worker discovered a prerequisite gap and created a subtask via `create_subtask` (see Section 10a). | Checker agent (scenario a) or Worker agent (scenario b) |

**Transition rules:**
```
PENDING      → IN_PROGRESS  (Worker starts)
IN_PROGRESS  → REVIEW       (Worker submits via submit_for_review)
IN_PROGRESS  → ESCALATED    (Worker finds prerequisite gap; creates subtask then escalates — see Section 10a)
REVIEW       → DONE         (Checker approves)
REVIEW       → PENDING      (Checker rejects; retry count < 3)
REVIEW       → ESCALATED    (Checker rejects; retry count >= 3)
```

---

## 5. Authorized Tool API

Layer 3 agents MUST only use the following tools. No direct shell access or arbitrary file system operations are permitted.

| Tool | Parameters | Permission Boundary |
|------|-----------|-------------------|
| `read_file(filepath)` | `filepath: str` | Allowed: `00_Constitution/core.md`, `01_Roadmap/*.md`, current `Task_<NNN>/` only |
| `list_directory(path)` | `path: str` | Same boundary as `read_file` |
| `write_artifact(filepath, content)` | `filepath: str`, `content: str` | Current `Task_<NNN>/` only. Triggers automatic `git commit`. |
| `change_status(task_id, status)` | `task_id: str`, `status: enum` | `status` MUST be one of the five allowed tokens. |
| `submit_for_review(summary)` | `summary: str` | Sets status to `REVIEW`; notifies Checker role. |
| `escalate_issue(reason)` | `reason: str` | Halts task; writes to `action_log.jsonl`; sets status to `ESCALATED`. |
| `create_subtask(slug, recipe_content, role_content)` | `slug: str`, `recipe_content: str`, `role_content: str` | Orchestrator creates `02_Task_Queue/Task_<next_NNN>_<slug>/` with provided content and `status.txt = PENDING`. Agent MUST NOT write outside its own folder directly — this tool is the only sanctioned path for micro-level Task Queue injection. |

**MUST NOT use:**
- Native shell commands (`rm`, `cp`, `mv`, `mkdir`) directly.
- Any write target inside `00_Constitution/` or `01_Roadmap/`.
- File paths outside the current task folder (except authorized read paths).

---

## 6. Worker Agent Protocol

Upon receiving a task (status = `PENDING`):

1. **Set status** to `IN_PROGRESS` using `change_status`.
2. **Load role**: Read `role.md` and apply as effective system persona.
3. **Read recipe**: Parse all sections of `recipe.md`. If any required section is missing, call `escalate_issue("recipe.md missing required section: <section_name>")`.
4. **Read inputs**: Process only files listed in `recipe.md > Input Sources`.
5. **Execute**: Produce the artifact defined in `recipe.md > Output Specification`.
6. **Write output**: Use `write_artifact("output.md", <content>)`.
7. **Submit**: Call `submit_for_review(<one-sentence summary of what was produced>)`.

**On error or uncertainty:**
- Insufficient inputs where a prerequisite task can be defined → call `create_subtask(...)` first, then `escalate_issue(...)` (see Section 10a). Do NOT skip directly to `escalate_issue`.
- Insufficient inputs due to a recipe specification error (e.g., referenced file does not exist and cannot be produced by a subtask) → `escalate_issue("Insufficient input: <specific gap>")`
- Contradictory instructions → `escalate_issue("Contradictory instructions in recipe.md: <detail>")`
- NEVER hallucinate data or invent file contents to fill gaps.

---

## 7. Checker Agent Protocol

Upon detecting status = `REVIEW`:

1. **Read** `recipe.md > Local Definition of Done` — this is the authoritative checklist.
2. **Read** `output.md` — evaluate against every DoD item.
3. **APPROVE** (all DoD items satisfied):
   - Call `change_status(task_id, "DONE")`.
4. **REJECT** (one or more DoD items not satisfied):
   - Write specific, actionable feedback to `feedback.md` using `write_artifact`.
   - Increment retry counter (tracked in `action_log.jsonl`).
   - Retry count < 3 → `change_status(task_id, "PENDING")`.
   - Retry count >= 3 → `escalate_issue("Max retries reached. Last failure: <reason>")`.

---

## 8. Action Log Format — `action_log.jsonl`

Every tool call MUST be appended to `action_log.jsonl` as one JSON object per line:

```json
{"ts": "2026-05-21T09:30:00+08:00", "role": "worker", "tool": "write_artifact", "args": {"filepath": "output.md"}, "result": "ok"}
{"ts": "2026-05-21T09:31:00+08:00", "role": "checker", "tool": "change_status", "args": {"task_id": "Task_001", "status": "DONE"}, "result": "ok"}
```

Fields: `ts` (ISO 8601 + timezone) | `role` (`worker`/`checker`) | `tool` (tool name) | `args` (parameters) | `result` (`ok` or error string)

---

## 9. Information Isolation Principle

Layer 3 agents MUST NOT:
- Read task folders other than their own assigned `Task_<NNN>/`.
- Retain or reference conversational history from previous tasks.
- Access external networks or URLs not explicitly listed in `recipe.md > Input Sources`.

Each agent operates as a **stateless executor**: its entire world is the current task folder plus the two authorized read paths.

---

## 10. Escalation and Recovery

When `escalate_issue` is called:
1. Status is set to `ESCALATED`. Task is frozen — no further tool calls permitted.
2. A human or Layer 2 agent MUST review `feedback.md` and `action_log.jsonl`.
3. Resolution options:
   - **Re-specify**: Layer 2 rewrites `recipe.md`, resets status to `PENDING`.
   - **Split task**: Layer 2 replaces this task with two smaller sub-tasks. The new sub-task folders MUST be created directly inside `02_Task_Queue/` immediately — do NOT wait for Global Aggregation.
   - **Human intervention**: Human directly resolves the constraint or provides missing input.

## 10a. Micro-Level Feedback — Direct Task Queue Injection

A Worker agent that discovers a prerequisite gap during execution MUST use this path **before** resorting to `escalate_issue`:

1. Worker detects a missing precondition (e.g., required input does not exist yet).
2. Worker calls `create_subtask(slug="<descriptive-slug>", recipe_content="<full recipe.md text>", role_content="<full role.md text>")`. The orchestrator creates the new task folder in `02_Task_Queue/` with `status.txt = PENDING`. Worker MUST NOT use `write_artifact` to write outside its own task folder.
3. Worker logs the `create_subtask` call in its own `action_log.jsonl`.
4. Worker calls `escalate_issue("Prerequisite gap found; sub-task <slug> created in queue.")` to pause itself and signal that the new task must be completed first.

**Key principle:** Micro-level feedback bypasses Global Aggregation entirely. The gap is patched in real time, preventing technical debt accumulation that would otherwise only surface after all tasks complete.

| Feedback Path | Trigger | Route | Timing |
|--------------|---------|-------|--------|
| **Micro (⑤)** | Worker finds gap during execution | Worker → `02_Task_Queue/` directly | Immediate |
| **Macro (⑥)** | Global Aggregation finds Global DoD unmet | AGG → Layer 2 → new task packages | After all tasks complete |

---

## 11. Git Integration Requirements

The orchestrating system MUST:
- Auto-commit after every `write_artifact`: `git commit -m "agent: <role> updated <filepath> in <task_id>"`.
- Support `revert_task(task_id)` to restore last committed state of the task folder.
- Never expose raw git commands to agents.

---

*This protocol is version-controlled. Changes require Layer 1 (human) approval and a new git commit.*

🔗 See also: [for_humans.md](for_humans.md) | [glossary.md](glossary.md) | [Framework README](../README.md)
