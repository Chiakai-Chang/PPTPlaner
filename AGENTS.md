# AGENTS.md — Source Text → Slides + Page-by-Page Memos (SPEC)

> 本規格（SPEC）用於驅動 AI Agents，將任意「原始文檔」自動轉換為簡報與備忘稿。

---

## [PLAN]
### 切頁規劃（輸出 JSON）
**目的**：將整份 source text 規劃成若干「頁」（page），每頁一個簡短主題 `topic`。  
**輸出**：純 JSON，格式：`{"pages": [{"page": "01", "topic": "Intro"}]}`

---

## [SLIDE]
### 生成單頁投影片（Markdown）
**目的**：依 `PLAN` 的 `page` 與 `topic`，輸出**單頁**投影片內容（Markdown）。
**輸出**：單頁 Markdown。

---

## [MEMO]
### 生成以學習為核心的逐頁備忘稿

**目的**：以傳入的 `slide_content` 為綱要，扮演「老師」的角色，深度挖掘 `source_file` 的精髓，生成一份以引導使用者「完整學習」原文為核心目標的逐頁備忘稿。

**寫作哲學 (Writing Philosophy)**
*   **你是老師，不是摘要機**：你的目標是「教會」講者，而不只是總結。
*   **備忘稿是學習的主體，簡報是輔助**：講稿內容必須遠比簡報豐富。
*   **創造連貫的敘事**：在頁面之間建立清晰的邏輯聯繫。
*   **確保可溯源性 (Traceability)**：備忘稿中闡述的核心概念，必須讓學習者能對應回原文。

**輸入變數**：
*   `source_file`: 原始全文，用於查找細節。
*   `slide_content`: 單頁簡報的 Markdown 內容，作為生成講稿的核心依據。
*   `page`, `topic`: 頁碼與主題（供參考）。
*   `custom_instruction`: 使用者客製化指令 (選填)。
*   `notes_locale`, `preserve_english_terms`, `tone`, `memo_time_min`, `memo_time_max`

**必要段落（順序固定）**
1.  **本頁摘要（Slide Recap）**：總結 `slide_content` 的核心要點。
2.  **核心概念與深度學習 (含溯源)**：針對 `slide_content` 的要點，從 `source_file` 找出詳細解釋。在闡述完關鍵概念後，**必須**加上來源標註，例如 `(Source: Page 42)`。
3.  **延伸議題與觀點 (Extended Topics & Viewpoints)**：根據原文核心概念，提出延伸議題、案例或應用場景。若使用者有提供 `custom_instruction`，則優先依其指示生成此段落。
4.  **承先啟後與轉場（Bridge）**：將本頁核心概念與下一頁的主題聯繫起來。

---

## [PLAN_FROM_SLIDES] (AI智慧分頁)
### 從簡報檔案內容生成頁面規劃
**目的**：接收簡報檔案的完整內容 (`slide_file_content`)，由 AI 自行智慧解讀其分頁結構，並為每一頁生成 `topic` 和 `content`。
**輸出**：純 JSON，格式**必須**包含 `content` 鍵：
```json
{"pages": [{"page": "01", "topic": "Topic1", "content": "..."}]}
```

---

## [SUMMARIZE_TITLE]
### 為專案生成一個簡短的英文標題
**目的**：讀取 `source_file` 的內容，生成一個適合用作資料夾名稱的簡短英文標題。
**輸出**：一個包含 `title` 鍵的 JSON 物件。例如：`{"title": "Boston_Bombing_Analysis"}`

---

**End of SPEC**
