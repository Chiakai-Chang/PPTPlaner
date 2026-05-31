# Audit Progress Tracker

**Created**: 2026-05-31  
**Last Updated**: 2026-06-01  
**Auditor**: Antigravity Agent (Chiakai-Chang/PPTPlaner)

## Status Legend
- 🔴 Not Started
- 🟡 In Progress
- ✅ Completed

## High Severity Issues

| ID | Issue | Status | Assigned To |
|----|-------|--------|-------------|
| H01 | `os.startfile()` Windows-only in orchestrate.py:846 | ✅ Completed | Antigravity Agent |
| H02 | pywinpty hard dependency breaking Mac/Linux | ✅ Completed | Antigravity Agent |
| H03 | Agy agent TypeError at line 395/629 | ✅ Completed | Antigravity Agent |
| H04 | `creationflags` TypeError in run_combiner_ui.py:130 | ✅ Completed | Antigravity Agent |
| H05 | Duplicate except block in build_guide.py:204-210 | ✅ Completed | Antigravity Agent |
| H06 | VENV Python path Windows-only in run_combiner_ui.py:18 | ✅ Completed | Antigravity Agent |
| H07 | Test collection error — edge-tts missing | ✅ Completed | Antigravity Agent |
| H08 | Python version requirement inconsistency (3.8 vs 3.12) | ✅ Completed | Antigravity Agent |

## Medium Severity Issues

| ID | Issue | Status | Assigned To |
|----|-------|--------|-------------|
| M01 | Antigravity is_available() missing Mac/Linux agy search | ✅ Completed | Antigravity Agent |
| M02 | subprocess shell=True TTY fallback for antigravity | ✅ Completed | Antigravity Agent |
| M03 | Python version check in launcher.py too lenient (3.8) | ✅ Completed | Antigravity Agent |
| M04 | orchestrator_old.py has os.startfile() too | ✅ Completed | Antigravity Agent (Archived) |
| M05 | PyYAML missing from pyproject.toml dependencies | ✅ Completed | Antigravity Agent |

## Low Severity Issues

| ID | Issue | Status | Assigned To |
|----|-------|--------|-------------|
| L01 | sys.stdout.reconfigure() only on Windows | ✅ Completed | Antigravity Agent |
| L02 | launcher.py version check too lenient | ✅ Completed | Antigravity Agent |
| L03 | orchestrator_old.py Windows-only path handling | ✅ Completed | Antigravity Agent (Archived) |

## OmniHeal Alignment Check

| 原則 | 狀態 | 說明 |
|------|------|------|
| **零安裝 (Zero Install)** | ✅ Aligned | pywinpty has been made a platform-specific optional dependency. Clean installs work out of the box on macOS/Linux. |
| **永不中斷 (Never Interrupt)** | ✅ Aligned | Agy CLI features automatic exception recovery and safe type checks. |
| **高精度優先 (Precision First)** | ✅ Aligned | Dead except blocks, legacy orchestrator files have been removed or archived. |
| **可中斷恢復 (Interrupt & Recover)** | ⚠️ Partial | Retained robust recovery in video pipeline. |
