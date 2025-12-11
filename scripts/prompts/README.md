# AI Agent Prompts

本目錄存放 PPTPlaner 系統中所有 AI Agent 的指令與人格設定。

## 檔案結構
每個 `.md` 檔案代表一個 Agent 或是任務模式 (Mode)。檔名（不含副檔名）即為程式呼叫時的 Agent ID。

*   **`_SAFETY_PREAMBLE.md`**: 全域通用的安全前導文，會自動附加在所有 Prompt 的最開頭。
*   **`PLAN.md`**: 生成簡報架構。
*   **`DECK.md`**: 生成投影片內容。
*   **`MEMO.md`**: 生成演講者備忘稿。
*   **`VALIDATE_*.md`**: 各階段的品質檢驗 Agent。

## 如何新增/修改 Agent
1.  **修改**: 直接編輯對應的 `.md` 檔案即可，無需修改 Python 程式碼。
2.  **新增**: 建立一個新的 `MY_NEW_AGENT.md`，然後在 `orchestrate.py` 中使用 `run_agent(..., "MY_NEW_AGENT", ...)` 呼叫它。

## Prompt 撰寫原則
*   清楚定義 **角色 (Role)**。
*   列出 **核心目標 (Core Objectives)**。
*   明確定義 **輸入變數 (Input Variables)** 與 **輸出格式 (Output Format)**。
*   對於 JSON 輸出，務必強調轉義規則。
