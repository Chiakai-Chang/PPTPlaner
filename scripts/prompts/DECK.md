### 生成完整投影片組 (Holistic Deck Generation)
**目的**: 根據 `PLAN` 提供的頁面規劃 (`pages_json`)，一次性生成所有投影片的內容，確保整份簡報風格、語氣和結構的一致性。
**輸入變數**:
*   `source_file_path`: 原始全文檔案路徑。
*   `pages_json`: 包含所有頁面規劃的 JSON 字串 (e.g., `[{"page": "01", "topic": "Intro"}, ...]`)。
*   `rework_feedback`: (選填) 來自 `VALIDATE_DECK` 的整體修改建議。若收到此指令，你的首要任務是根據該建議全面修正所有投影片。
**輸出**: 純 JSON，格式: `{"slides": [{"page": "01", "topic": "Intro", "content": "# Intro..."}, ...]}`
**重要提示 (CRITICAL)**：你生成的 JSON **必須**是語法正確的。這意味著所有的字串值（特別是 `content` 裡的 Markdown 內容）若包含雙引號 (`"`)，**必須**被正確地轉義為 `\"`。
*   **錯誤範例 (WRONG)**: `"content": "This is a "quoted" word."` (這會導致解析失敗)
*   **正確範例 (CORRECT)**: `"content": "This is a \"quoted\" word."` (務必這樣做)
如果沒有正確轉義，JSON 解析將會失敗。請在生成後仔細檢查。