# PPTPlaner

PPTPlaner 是一個「原文書共讀 + AI 簡報製作」的工作範本。透過 Codex CLI 讀取章節 Markdown（例如 `Chapter01.md`、`Chapter07.md`），就能自動產出簡報檔、講稿、Mermaid 圖表與操作指引，協助學員在有限時間內掌握重點，同時保留原作的學習深度。

## 功能亮點
- **AI 驅動的簡報**：依章節內容拆分成 `slides/*.md`，每段遵循「Less is More」原則，保留理論、實驗與故事脈絡。
- **雙語講稿支援**：`notes/` 提供台灣繁體中文備忘稿，保留英文專有名詞，方便導讀與 Presenter Notes 使用。
- **圖表視覺化**：`diagrams/*.mmd` 為 Mermaid 原始碼，可貼到 [mermaid.live](https://mermaid.live/edit) 轉出 SVG/PNG。
- **互動式操作指引**：`指引.html` 列出每段 Slide 與講稿，提供一鍵複製與開啟連結；`指引.md` 則提醒使用者前往 HTML 版本。
- **統一工作守則**：`AGENTS.md` 說明輸出檔案結構、命名規則、Gamma 匯入與檢查要點，供 Codex 與協作者遵循。

## 目錄結構
```
PPTPlaner/
├─ Chapter*.md          # 由 PDF 轉出的原文章節 Markdown
├─ slides/              # AI 產出的簡報段落 (01_intro.md ...)
├─ notes/               # 對應講稿 (note-*-zh.md)
├─ diagrams/            # Mermaid 圖表原始碼 (.mmd)
├─ 指引.html / 指引.md      # 操作指南（HTML 版含複製按鈕與連結）
├─ AGENTS.md            # Codex 工作規範與交付清單
└─ README.md            # 專案說明（本檔）
```

## 前置環境

### 安裝 Node.js（Windows 建議使用 nvm-windows）
1. 前往 [nvm-windows 發佈頁](https://github.com/coreybutler/nvm-windows/releases)，下載最新的 `nvm-setup.exe`。
2. 依照安裝程式指示完成安裝，安裝完成後重新開啟 PowerShell 或命令提示字元。
3. 在終端機輸入：
   ```powershell
   nvm install 18.20.3
   nvm use 18.20.3
   node -v   # 應顯示 v18.x.x
   npm -v
   ```
4. macOS / Linux 使用者可改用 [nvm](https://github.com/nvm-sh/nvm) 或直接安裝 Node.js 官方套件。

### 安裝與登入 Codex CLI
1. `mkdir PPTPlaner && cd PPTPlaner`（或使用既有資料夾）。
2. 下載/複製 `AGENTS.md` 及章節 Markdown (`Chapter*.md`) 到此資料夾。
3. 安裝 CLI：
   ```bash
   npm install -g @openai/codex-cli
   ```
4. 登入：
   ```bash
   codex login
   ```
   - 會開啟瀏覽器，使用擁有 ChatGPT Plus 權限的 OpenAI 帳號登入即可。
   - 如需 API key，可改用 `codex login --api-key YOUR_KEY`。
5. 在專案根目錄執行 `codex init`，讓 CLI 設定好專案並記住 `AGENTS.md`。

## 在 PPTPlaner 的手把手流程
1. **準備章節 Markdown**：將新章節（例如 `Chapter07.md`）放在專案根目錄。
2. **啟動 Codex CLI**：執行 `codex work` 或 `codex chat`，開場即提醒「請先閱讀 AGENTS.md」。
3. **委派生成任務**：要求 Codex 依章節內容產出：
   - `slides/NN_section.md`（每段 ≤10 頁、含 `---` 分頁與風格建議）。
   - `notes/note-section-zh.md`（台灣繁中講稿，保留英文專有名詞）。
   - `diagrams/*.mmd`（Mermaid 原始碼，可貼到 mermaid.live 轉圖）。
   - `指引.html` / `指引.md`（互動複製工具與操作提醒）。
4. **檢視成果**：打開 `指引.html`，確認每段內容、複製按鈕與開啟連結皆正常。
5. **匯入簡報工具**：依 `指引.html` 提示將 Markdown 貼入 Gamma，並在 mermaid.live 轉換圖表，完成後排練講稿。
6. **收尾與記錄**：視情況更新 `AGENTS.md` 或 `指引.html` 的注意事項與日期，留下下一步建議。

## 推薦工作方式
- **內容更新**：新增章節或修訂內容時，先維護對應的 `Chapter*.md`；其餘檔案可重新透過 Codex 依 `AGENTS.md` 產出。
- **版本管理**：變更完成後更新 `指引.html` 與 `AGENTS.md` 的迭代紀錄，方便下一次合作。
- **圖表維護**：Mermaid 原始碼放在 `diagrams/`，轉換後的 SVG/PNG 可視簡報工具需求存於 `assets/` 或 `slides/img/`。

## 參與與貢獻
歡迎同學或協作者：
1. Fork / Clone 專案，新增章節 Markdown 或補充講稿與圖表。
2. 依 `AGENTS.md` 規範執行 Codex CLI 工作，將產出整理回專案結構。
3. 提交 PR 時附上更新後的 `指引.html`、`slides/`、`notes/`、`diagrams/` 並說明主要改動與測試方式。

若對流程或 Codex CLI 有建議，歡迎於 Issue 區回報；期待透過 AI 協助，讓原文書共讀更有效率，也更容易上台分享。
