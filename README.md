# PPTPlaner

PPTPlaner 是一個結合「原文書共讀 + AI 簡報製作」的實作範本。透過 Codex CLI 讀取章節 Markdown（例如 Chapter01.md、Chapter07.md），即可自動產出簡報、講稿、Mermaid 圖表與操作指引，協助學員在有限時間內掌握重點，同時維持原作的學習深度。

## 功能亮點
- **AI 產出簡報**：依章節內容拆分 slides/*.md，遵循「Less is More」原則並保留理論、實驗與故事脈絡。
- **雙語講稿支援**：
otes/ 提供台灣繁體中文備忘稿，保留英文專有名詞，方便導讀與 Presenter Notes 使用。
- **圖表視覺化**：diagrams/*.mmd 為 Mermaid 原始碼，可貼到 [mermaid.live](https://mermaid.live/edit) 轉換為 SVG/PNG。
- **互動式操作指引**：指引.html 集中列出每段 Slide 與講稿，可一鍵複製或開啟檔案。
- **統一工作守則**：AGENTS.md 定義檔案命名、產出格式、Gamma 匯入與檢查要點，方便多人協作。

## 專案結構
`
PPTPlaner/
├─ Chapter*.md          # 由 PDF 轉出的章節 Markdown
├─ slides/              # AI 產出的簡報段落 (01_intro.md ...)
├─ notes/               # 對應講稿 (note-*-zh.md)
├─ diagrams/            # Mermaid 圖表原始碼 (.mmd)
├─ 指引.html            # 操作指南（含連結與複製按鈕）
├─ AGENTS.md            # Codex 工作規範與交付清單
└─ README.md            # 本檔案
`

## 文件轉換教學（PDF → Markdown）
1. **MinerU（建議優先使用這個，效果不錯且方便）** 
   - 下載：<https://mineru.net/OpenSourceTools/Extractor>  
   - 支援輸出 .html、.md、LaTeX 等格式，適合需要保留版面或公式的文件。
   - 這個方法的優點就是全自動化，雖然也花時間，但不太需要太多人工操作，實測效果也很準確。
3. **自建 GPT（AnyIMG_to_Markdown）**  
   - <https://chatgpt.com/g/g-68e122adb2508191ad323ad85385d7f3-anyimg-to-markdown>  
   - 先將 PDF 轉成影像（jpg/png），再將陸續分批將圖片(大概每次1~5張圖片)交給 GPT 自動辨識並整理成 Markdown 格式，再由我們手動將結果複製、貼上到 Notepad 中去彙整成 .md 檔。
     - 可以使用這個線上工具來將 PDF 轉換成 JPG: [iLovePDF](https://www.ilovepdf.com/zh-tw/pdf_to_jpg) 。
   - 這個方法好處在於使用當前最新且強大的視覺語言模型，精準度等效果會比較好；缺點是操作麻煩、需要花費一些時間去做。
3. **Docling（建議: 需有點程式能力）**  
   - 專案：<https://github.com/docling-project/docling>  
   - 安裝並依文件操作，可直接將 PDF 解析為 .md（保留段落與標題架構）。
   - 這個方法其實有不少視覺語言模型可以選擇，效果也不錯，但缺點是實測起來有些原本有的文字沒有辨識出來，且整體速度相對也是要花不少時間。

> 建議：確認產出的 .md 檔名遵循 ChapterXX.md 格式，方便 Codex 讀取與迭代。 若檔名不同，要特別跟 Codex 敘明。

## 前置環境

### 安裝 Node.js（Windows 建議使用 nvm-windows）
1. 下載 [nvm-windows](https://github.com/coreybutler/nvm-windows/releases) 的最新 
vm-setup.exe。
2. 安裝後重新開啟 PowerShell 或命令提示字元。
3. 在終端機輸入：
   `powershell
   nvm install 18.20.3
   nvm use 18.20.3
   node -v   # 應顯示 v18.x.x
   npm -v
   `
4. macOS / Linux 可使用 [nvm](https://github.com/nvm-sh/nvm) 或直接安裝官方 Node.js 套件。

### 安裝與登入 Codex CLI
1. 建立專案資料夾並進入：mkdir PPTPlaner && cd PPTPlaner（或使用既有資料夾）。
2. 將 AGENTS.md 與章節 Markdown (Chapter*.md) 放入該資料夾。  
   （可先 fork/clone 本專案，再替換章節內容。）
3. 安裝 CLI：
   `ash
   npm install -g @openai/codex-cli
   `
4. 登入 Codex：
   `ash
   codex login
   `
   - 會開啟瀏覽器，使用擁有 ChatGPT Plus 權限的 OpenAI 帳號登入即可。  
   - 若偏好使用 API key，可改用 codex login --api-key YOUR_KEY。
5. 在專案根目錄執行一次 codex init，讓 CLI 設定好專案並記住 AGENTS.md。

## 手把手流程
1. **放入章節 Markdown**：將最新章節（如 Chapter07.md）存放於專案根目錄。
2. **啟動 Codex**：執行 codex work 或 codex chat，開場即提醒「請先閱讀 AGENTS.md」。
3. **委派產出**：請 Codex 依章節內容生成以下檔案：
   - slides/NN_section.md：每段 ≤10 頁、含 --- 分頁與風格建議。
   - 
otes/note-section-zh.md：台灣繁中講稿，保留英文專有名詞。
   - diagrams/*.mmd：Mermaid 原始碼，可貼到 mermaid.live 轉圖。
   - 指引.html：段落清單、開啟連結與複製按鈕。
4. **檢查成果**：打開 指引.html，確認內容、複製按鈕與開啟連結皆正常。
5. **匯入簡報工具**：依 指引.html 提示將 Markdown 貼入 Gamma，並在 mermaid.live 轉換圖表後嵌入簡報。
6. **排練與記錄**：練習講稿並視情況更新 AGENTS.md 或 指引.html 的注意事項、日期與下一步建議。

## 建議工作習慣
- 章節更新時，優先維護 Chapter*.md；其他檔案可重新透過 Codex 依 AGENTS.md 產出。
- 每次改動後，記錄 指引.html 與 AGENTS.md 的變更重點，方便下一位協作者接手。
- 保留所有 Mermaid 原始碼於 diagrams/，轉出的 SVG/PNG 依需求存放於 ssets/ 或 slides/img/。

## 參與方式
1. Fork / Clone 專案，新增章節 Markdown 或補充講稿、圖表。
2. 按 AGENTS.md 的規範執行 Codex CLI 工作並提交產出。
3. 發 Pull Request 時附上更新後的 指引.html、slides/、
otes/、diagrams/，並說明主要改動與測試方式。

## 延伸工具
- [Docling](https://github.com/docling-project/docling) — PDF 轉 Markdown。  
- [MinerU Extractor](https://mineru.net/OpenSourceTools/Extractor) — 多格式匯出（.html/.md/LaTeX）。  
- [AnyIMG_to_Markdown](https://chatgpt.com/g/g-68e122adb2508191ad323ad85385d7f3-anyimg-to-markdown) — 將自 PDF 轉出的圖片轉 Markdown。

若對流程或 Codex CLI 有任何建議，歡迎於 Issue 區回報；期待透過 AI 協助，讓原文書共讀更有效率，也更容易上台分享。
