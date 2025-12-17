# PPTPlaner - AI Presentation Generator (System Context)

"Code is our weapon against the anxiety of time."
This document serves as the primary context for the Gemini CLI agent to understand the philosophy, architecture, and operational rules of the PPTPlaner project.

---

## 1. 專案哲學與願景 (Project Philosophy)

### 核心初衷 (The "Why")
身處 2025 年的科技前線（Cyber Investigation, Data Analysis, AI, OSINT），時間是最稀缺的資源。本專案旨在解決「讀與不讀」的兩難，透過自動化工具將艱澀文獻轉化為易於吸收的結構化簡報，作為原著與讀者之間的橋樑。

### AI 角色定位 (AI Persona)
*   **知識導讀者 (Knowledge Interpreter)**：AI 不應以原作者自居，而是扮演「導讀者」。
*   **中立視角 (Neutral Perspective)**：使用「作者指出」、「研究顯示」等第三人稱，避免使用「我認為」。
*   **引用倫理 (Citation Ethics)**：尊重智慧財產權，保留關鍵原文術語，不進行過度創作或冒名。

---

## 2. 技術架構 (Technical Architecture)

本專案採用 **階層式多代理人系統 (Hierarchical Multi-Agent System)**，具備自我修正與容錯能力。

### 核心組件 (Core Components)
1.  **指揮官 (Orchestrator - `scripts/orchestrate.py`)**：
    *   負責狀態管理、流程控制、錯誤處理。
    *   **Stateless Execution**: 每個 Agent 呼叫都是獨立的，但由指揮官串接上下文。
    *   **Resilient Loop**: 實作了無限重試與暫停機制 (`[PAUSE_REQUIRED]`)，允許使用者在 API 錯誤時介入（如切換模型）並繼續。

2.  **AI 代理人 (Agents - `scripts/prompts/*.md`)**：
    *   **Generator**: `PLAN`, `DECK`, `MEMO`, `CREATE_*_SVG` (負責生成)。
    *   **Validator**: `VALIDATE_*` (負責品管)。
    *   **Analyzer**: `ANALYZE_SOURCE_DOCUMENT` (負責元數據提取)。

### 品質控制引擎 (The Quality Engine)
系統採用 **「追求完美 (Strive for Perfection)」** 的迴圈邏輯：
1.  **Generate**: 生成初稿。
2.  **Validate**: 進行 AI 審查。
    *   `is_valid: true` (Perfect) -> 立即採用，結束迴圈。
    *   `is_acceptable: true` (Acceptable) -> 存為備案，但**繼續重試**以追求完美。
    *   `is_valid: false` (Fail) -> 累積錯誤反饋 (`feedback_history`)，繼續重試。
3.  **Retry**: 附上累積的歷史反饋，要求 Agent 修正。
4.  **Fallback**: 若達最大重試次數仍無完美結果，則退回使用「可接受」的備案。

---

## 3. 資料處理管線 (Data Pipeline)

流程分為 5 個階段 (Phases)，由 `orchestrate.py` 依序執行：

*   **Phase 1: Analysis & Setup**
    *   Input: `source_file` (+ optional manual metadata).
    *   Agent: `ANALYZE_SOURCE_DOCUMENT` -> `VALIDATE_ANALYSIS`.
    *   Output: `overview.md` (含 Title, Author, Summary, Overview).
*   **Phase 2: Planning**
    *   Agent: `PLAN` (or `PLAN_FROM_SLIDES`).
    *   Output: `.plan.json` (結構化大綱).
*   **Phase 3: Deck Generation**
    *   Agent: `DECK` -> `VALIDATE_DECK`.
    *   Output: `slides/*.md`.
*   **Phase 4: Memo Generation**
    *   Agent: `MEMO` -> `VALIDATE_MEMO`.
    *   Output: `notes/*.md` (逐字講稿).
*   **Phase 5: SVG Generation**
    *   Agent: `CREATE_*_SVG` -> `VALIDATE_*_SVG`.
    *   Output: `slides/*.svg` (視覺素材).
*   **Finalize**:
    *   Script: `build_guide.py`.
    *   Output: `guide.html` (整合閱覽介面).

---

## 4. 可解釋性與審計 (Explainability & Audit)

*   **透明化品管 (Transparent QA)**：
    *   CLI 介面會即時顯示驗證結果 (`[QA Feedback]: ...`)。
    *   使用者能看到 AI 為什麼決定重試（例如：「內容遺漏」、「格式錯誤」）。
*   **完整審計日誌 (Full Audit Logs)**：
    *   所有 AI 的原始輸入 (Prompt) 與輸出 (Raw Response) 都會被 `ResearchLogger` 記錄在 `logs/` 目錄下。
    *   日誌檔開頭會記錄當次執行的所有參數 (`args`) 與設定 (`config`)。

## 5. 開發者指南 (Developer Guidelines)

*   **新增 Agent**: 在 `scripts/prompts/` 新增 `.md`，並在 `orchestrate.py` 中加入呼叫邏輯。
*   **修改 Prompt**: 請遵循「知識導讀者」的角色設定，並保留「修正與優化 (Handling Rework)」章節以支援重試機制。
*   **版本控制**: 專案版本號統一於 `config.yaml` 中管理。

---
*Generated for Gemini CLI Context Awareness.*