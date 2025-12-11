# PPTPlaner - AI Presentation Generator (Project Context)

## 專案簡介 (Project Overview)
PPTPlaner 是一個自動化的簡報生成系統。它讀取原始文本 (`source_file`)，透過多個 AI Agent 協作，生成結構化的投影片 (`slides`)、講者逐字稿 (`memos`) 以及 SVG 動畫素材，最終組合成一份完整的教學/演講資源。

## 核心架構 (Core Architecture)

### 1. 指揮中心 (Orchestrator)
*   **入口點**: `scripts/orchestrate.py`
*   **職責**: 負責讀取設定、管理流程狀態、呼叫 AI Agent、處理錯誤重試 (Retry) 與人機協作 (Pause/Resume)。
*   **關鍵邏輯**: 
    *   它**不包含** Prompt 內容。
    *   它動態讀取 `scripts/prompts/` 下的 `.md` 檔案來組裝 Prompt。

### 2. AI Agents (Prompts)
所有的 Agent 人格與指令設定都已模組化，存放於 `scripts/prompts/` 目錄中。
*   **`PLAN.md`**: 負責將長文拆解為分頁大綱。
*   **`DECK.md`**: 負責生成投影片 Markdown 內容。
*   **`MEMO.md`**: 負責撰寫詳細的講者逐字稿。
*   **`CREATE_SLIDE_SVG.md`**: 負責將文字轉為動畫 SVG。
*   **`CREATE_CONCEPTUAL_SVG.md`**: 負責將概念轉為視覺化圖表。
*   **`VALIDATE_*.md`**: 各個階段的品質檢驗 (QA) Agent。

### 3. 資料流 (Data Flow)
1.  **Source** (`config.yaml` 指定) -> **Analyze** (分析元數據) -> `overview.md`
2.  **Plan** (生成分頁結構) -> `.plan.json`
3.  **Deck** (生成每頁 Markdown) -> `output/.../slides/*.md`
4.  **Memo** (生成每頁逐字稿) -> `output/.../notes/*.md`
5.  **SVG** (生成視覺素材) -> `output/.../slides/*.svg`

## 開發指南 (Developer Guidelines)

*   **修改 Prompt**: 不要修改 Python 程式碼。請直接編輯 `scripts/prompts/` 下對應的 `.md` 檔案。
*   **新增 Agent**: 
    1. 在 `scripts/prompts/` 新增 `NEW_AGENT_NAME.md`。
    2. 在 `orchestrate.py` 中使用 `run_agent(cfg["agent"], "NEW_AGENT_NAME", ...)` 呼叫即可。
*   **設定檔**: `config.yaml` 控制全域參數（如 retry 次數、使用的模型）。

## 目錄結構說明
*   `output/`: 所有的生成結果都存放在此，依日期與專案名分資料夾。
*   `logs/`: 紀錄詳細的執行 Log，包含 AI 的原始回應。
*   `scripts/`: 包含 Python 核心邏輯。
*   `demo/`: 存放範例圖片。

---
*此文件供 AI 助手 (Gemini CLI) 快速理解專案上下文使用。*
