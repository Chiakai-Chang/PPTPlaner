# AGENTS.md — Source Text → Slides + Page-by-Page Memos (SPEC)

> 本規格（SPEC）用於驅動 CLI Agents（**Codex CLI / Gemini CLI / Claude Code**）
> 將任意「原始文檔」（*source text*：論文、章節、報告、逐字稿…）自動轉換為：
>
> - `slides/`：**每檔 ≤10 頁** 的 Markdown 投影片段  
> - `notes/`：**逐頁備忘稿**（繁體中文，**保留英文術語原文**）  
> - `diagrams/`：可選的 Mermaid 流程圖（`.mmd`）

[← 使用教學（docs/USAGE_zh-TW.md）](./docs/USAGE_zh-TW.md)  
[← 返回主頁（README.md）](./README.md)

---

## [PLAN]
### 切頁規劃（輸出 JSON）

**目的**：將整份 source text 規劃成若干「頁」（page），每頁一個簡短主題 `topic`。  
**輸出**：純 JSON（不得混雜其他文字），格式：
```json
{
  "pages": [
    { "page": "01", "topic": "Intro" },
    { "page": "02", "topic": "Encoding" }
  ]
}
```

---

## [SLIDE]
### 生成單頁投影片（Markdown）

**目的**：依 `PLAN` 的 `page` 與 `topic`，輸出**單頁**投影片內容（Markdown）。
**輸出**：單頁 Markdown（僅此頁；勿含前後頁）

---

## [MEMO]
### 生成以學習為核心的逐頁備忘稿（繁體中文，保留英文術語）

**目的**：以傳入的 `slide_content` 為綱要，扮演「老師」與「教練」的角色，深度挖掘 `source_file` 的精髓，生成一份**以引導使用者「完整學習」原文為核心目標**的逐頁備忘稿。

**寫作哲學 (Writing Philosophy)**

*   **你是老師，不是摘要機**：你的目標是「教會」講者，而不只是總結。
*   **備忘稿是學習的主體，簡報是輔助**：講稿內容必須遠比簡報豐富。
*   **創造連貫的敘事**：在頁面之間建立清晰的邏輯聯繫。
*   **確保可溯源性 (Traceability)**：備忘稿中闡述的核心概念，必須讓學習者能對應回原文。

**必要段落（順序固定）**

1.  **本頁摘要（Slide Recap）**：用 1-2 句話總結 `slide_content` 的核心要點。
2.  **核心概念與深度學習 (含溯源)**：針對 `slide_content` 上的每個要點，從 `source_file` 中找出其背後的「為何如此」、經典實驗、理論細節或故事脈絡。在闡述完一個關鍵概念後，**必須**加上來源標註，例如 `(Source: Page 42)` 或 `(Source: Eyewitness Memory, Chapter 5)`，以利學習者對照原文。
3.  **法律／實務應用（Taiwan Context）**：補充與 `slide_content` 要點相關的在地化脈絡或應用。
4.  **承先啟後與轉場（Bridge）**：明確地將本頁核心概念與「下一頁」的主題聯繫起來。

---

## [PLAN_FROM_SLIDES] (AI智慧分頁)
### 從簡報檔案內容生成頁面規劃

**目的**：接收一份純文字的簡報檔案內容 (`slide_file_content`)，由 AI 自行「智慧解讀」其中的分頁結構，並為每一頁生成一個簡潔的 `topic`。

**CRITICAL REQUIREMENT**: 您的輸出是一個 JSON 物件。在 `pages` 陣列中的**每一個**物件，都**必須**包含三個鍵：`page` (字串)、`topic` (字串)、和 `content` (字串)。`content` 鍵是**絕對必要**的，其值為該頁投影片的完整 Markdown 內容。

**輸出**：純 JSON（不得混雜其他文字）。格式**必須**如下，每個頁面物件都**必須**包含 `content` 鍵：
```json
{
  "pages": [
    { 
      "page": "01", 
      "topic": "AI_Generated_Topic_1", 
      "content": "Content of slide 1..."
    },
    { 
      "page": "02", 
      "topic": "AI_Generated_Topic_2", 
      "content": "Content of slide 2..."
    }
  ]
}
```

---

## [SUMMARIZE_TITLE]
### 為專案生成一個簡短的英文標題

**目的**：讀取 `source_file` 的內容，為其生成一個非常簡短的、適合用作資料夾名稱的英文標題。

**寫作哲學**：

*   **極度簡潔**：長度嚴格限制在 3 到 5 個單詞之間。
*   **英文輸出**：必須使用英文。
*   **移除特殊字元**：標題中只能包含字母、數字、底線或連字號。
*   **高鑑別度**：標題需能反映文章核心主題。

**輸出**：一個包含 `title` 鍵的 JSON 物件。例如：
```json
{
  "title": "Boston_Bombing_Analysis"
}
```

---

**End of SPEC**