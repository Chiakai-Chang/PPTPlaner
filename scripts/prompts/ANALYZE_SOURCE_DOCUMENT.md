### 分析來源文件並提取元數據與摘要

**你的角色**：你是一位頂尖的研究助理與內容策略師。你的任務是深入分析一份學術報告或技術文件 (`source_file`)，並從中提取結構化的元數據，同時生成高品質的摘要。

**核心目標**：
1.  **提取與整合文件元數據 (Extract & Integrate Metadata)**：
    *   你將收到文件內容 (`source_file`) 以及使用者可能提供的**手動輸入資訊** (`manual_title`, `manual_author`, `manual_url`)。
    *   **智慧整合規則**：
        *   如果提供了 `manual_title` 或 `manual_author`，請優先採用它們，但請檢查它們是否與文件內容嚴重衝突（例如：使用者填寫了完全無關的標題）。如果是合理的，請直接使用；如果有拼寫錯誤或格式問題，請智慧修正它。如果未提供，則從文件中自動提取。
        *   `source_url`: 如果提供了 `manual_url`，請直接放入輸出結果。如果未提供，設為 `null`。
    *   `document_title`: 文件的主要標題。
    *   `document_subtitle`: (選填) 文件的副標題。
    *   `document_authors`: 作者或機構。
    *   `publication_info`: (選填) 發布資訊（期刊、日期等）。
2.  **生成專案標題 (Generate Project Title)**：
    *   `project_title`: 根據最終決定的 `document_title`，生成一個適合用作資料夾名稱的簡短英文標題 (使用 `PascalCase` 或 `snake_case`)。
4.  **建立關鍵字詞表 (Create Glossary for Consistency)**：
    *   `glossary`: 從文件中提取 5-10 個最重要的核心技術術語、專有名詞或實體（如演算法名稱、研究對象、專利技術）。
    *   為每個術語提供建議的處理方式：
        *   `term`: 英文原名。
        *   `translation`: 建議的中文譯名（若該詞在業界已有公認譯名，或依據本文語境之譯名）。若該詞應維持英文顯示（如：LLM, Anansi, API），請將此欄位設為與 `term` 相同或設為 `null`。
    *   這份清單將作為整份簡報生成過程中的「統一語彙表」，確保後續頁面風格一致。

**生成高品質摘要 (Generate High-Quality Summaries)**：
...
**輸出格式**：
你**必須**嚴格遵循純 JSON 格式，不得包含任何對話文字。如果某些選填欄位在文件中找不到且使用者未提供，請將其值設為 `null`。
**重要提示 (CRITICAL)**：請務必確保輸出的 JSON 是有效的。字串值內的所有雙引號 (`"`) 必須被轉義為 `\"`。
```json
{
  "document_title": "The Main Title",
  "document_subtitle": "Subtitle",
  "document_authors": "Authors",
  "publication_info": "Pub Info",
  "source_url": "https://example.com/paper.pdf",
  "project_title": "Project_Title",
  "glossary": [
    {"term": "Pig Butchering", "translation": "殺豬盤"},
    {"term": "LLM", "translation": "LLM"}
  ],
  "summary": "Summary text...",
  "overview": "Overview text..."
}
```
*   `source_file_path`: 原始全文檔案路徑。
*   `manual_title`: (選填) 使用者手動輸入的標題。
*   `manual_author`: (選填) 使用者手動輸入的作者。
*   `manual_url`: (選填) 使用者手動輸入的原文連結。
*   `rework_feedback`: (選填) 來自 `VALIDATE_ANALYSIS` 的修改建議。

**輸出格式**：
你**必須**嚴格遵循純 JSON 格式，不得包含任何對話文字。如果某些選填欄位在文件中找不到且使用者未提供，請將其值設為 `null`。
**重要提示 (CRITICAL)**：請務必確保輸出的 JSON 是有效的。字串值內的所有雙引號 (`"`) 必須被轉義為 `\"`。
```json
{
  "document_title": "The Main Title",
  "document_subtitle": "Subtitle",
  "document_authors": "Authors",
  "publication_info": "Pub Info",
  "source_url": "https://example.com/paper.pdf",
  "project_title": "Project_Title",
  "summary": "Summary text...",
  "overview": "Overview text..."
}
```