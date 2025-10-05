# PPTPlaner

PPTPlaner 是一個結合「原文書共讀 + AI 簡報製作」的工作範本。透過 Codex CLI 讀取章節 Markdown（例如 Chapter01.md、Chapter07.md），即可自動產出簡報的設計稿、備忘稿、搭配簡報用的圖表草稿(Mermaid格式)與這些草稿如何使用的指引，協助學員在有限時間內掌握重點，同時維持原作的學習深度。

```text
# 本專案大概流程
-> 原文書轉換成 Markdown.md
-> 交給 PPTPlaner 專案生成"簡報設計稿"
-> 丟到 AI 簡報生成網站(如: Gamma)
-> 產出簡報
-> 手動將 PPTPlaner 專案生成的簡報圖表 Mermaid 檔轉換成圖表加入簡報
-> 手動將 PPTPlaner 專案生成的備忘稿加入簡報，並檢查整個簡報
-> 完成一份有深度、有內容的完整簡報
```

## 專案目錄
```text
PPTPlaner/
├─ Chapter*.md          # 由 PDF 轉出的章節 Markdown（請維持 ChapterXX.md 命名）
├─ slides/              # AI 產出的簡報段落 (01_intro.md ...)
├─ notes/               # 對應講稿 (note-*-zh.md)
├─ diagrams/            # Mermaid 原始碼 (.mmd)
├─ 指引.html            # 操作指南（含開啟連結與複製按鈕）
├─ AGENTS.md            # Codex 工作規範與交付清單
└─ README.md            # 專案說明
```

## PDF → Markdown 實務筆記
1. **先拆檔再轉檔**  
   - 大型 PDF 建議先在 [iLovePDF](https://www.ilovepdf.com/zh-tw/split_pdf) 分割出你這次要簡報內容所需頁數小檔（例如從中取出第５章，從 118-143 頁就好，才不會太多）。  
   - 經驗值：PDF 越多頁，後續的工作時間越長，相對也越容易超過免費工具提供的免費額度範圍。
2. **常用轉檔工具比較**  
   | 工具 | 適用情境 | 使用心得 |
   | --- | --- | --- |
   | [MinerU Extractor](https://mineru.net/OpenSourceTools/Extractor) | 想要圖形化介面、操作簡單、自動匯出 .html/.md/LaTeX | （建議優先使用這個，效果不錯且方便）登入即可上傳 PDF 線上轉檔，操作最直覺。 優點就是全自動化，雖然也花時間，但不太需要太多人工操作，實測效果也很準確。 |
   | [AnyIMG_to_Markdown](https://chatgpt.com/g/g-68e122adb2508191ad323ad85385d7f3-anyimg-to-markdown) | 透過最新、強大的 ChatGPT 幫忙看圖片辨識出最精準結果(含文字內容與版型)，但※要使用可能需要有訂閱 ChatGPT Plus。 | 先用 [iLovePDF PDF → JPG](https://www.ilovepdf.com/zh-tw/pdf_to_jpg) 將 PDF 轉換成圖片，再將陸續分批將圖片(大概每次1~5張圖片)交給 GPT 自動辨識並整理成 Markdown 格式，然後每次由我們手動將結果複製、貼上到 Notepad(記事本) 中去彙整成 .md 檔。 優點是精準度等效果會比較好；缺點是操作麻煩、需要花費一些時間去做。 |
   | [Docling](https://github.com/docling-project/docling) | 既有自動化、也會使用有視覺的 AI 來辨識保留段落結構 | ※若不熟悉 GitHub 或自己架設軟體環境不建議使用這個。 安裝使用方法請參考該工具 GitHub 專案內容，雖然沒有 GPU 也可以用，但耗時會更久一些（有 GPU 其實也要耗費不少時間）。優點是這個方法其實有不少視覺語言模型可以選擇，效果也不錯，但缺點是實測起來有些原本有的文字沒有辨識出來，且整體速度相對也是要花不少時間。 |
3. **後製整理**  
   - Markdown 語法其實很簡單，就跟一般在寫文章一樣，只是用它的排版方式，寫出來的文章會按照你的語法來排版，用來在 [HackMD](https://hackmd.io/) 做筆記也非常好用，可以參考: [Markdown 語法說明](https://markdown.tw/) 或 [Markdown 語法大全](https://hackmd.io/@eMP9zQQ0Qt6I8Uqp2Vqy6w/SyiOheL5N/%2FBVqowKshRH246Q7UDyodFA)。
   - 轉出後檢查標題層級 (#, ##, ###) 與列表縮排。  
   - 建議將檔名統一為 ChapterXX.md，以利 Codex 讀取。  
   - 詳細圖文教學可參考 [docs/markdown-conversion.md](docs/markdown-conversion.md)。

## 本專案環境建置

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
1. 建立資料夾並進入：mkdir PPTPlaner && cd PPTPlaner（或使用既有資料夾）。
2. 將 AGENTS.md 與章節 Markdown (Chapter*.md) 放入該資料夾。可先 fork/clone 本專案再替換章節內容。
3. 安裝 CLI：
   `bash
   npm install -g @openai/codex-cli
   `
4. 登入 Codex：
   `bash
   codex login
   `
   - 會開啟瀏覽器，使用擁有 ChatGPT Plus 權限的 OpenAI 帳號登入即可。  
   - 若偏好使用 API key，可改用 codex login --api-key YOUR_KEY。
5. 在專案根目錄執行 codex init，讓 CLI 記住專案設定並自動讀取 AGENTS.md。

## 本專案使用步驟教學
1. **放入章節 Markdown**：將最新章節（如 Chapter07.md）放於專案根目錄。
2. **啟動 Codex**：執行 codex work 或 codex chat，開場即提醒「請先閱讀 AGENTS.md」。
3. **委派產出**：請 Codex 依章節內容生成：
   - slides/NN_section.md（每段 ≤10 頁，含 --- 分頁與風格建議）。
   - notes/note-section-zh.md（台灣繁中講稿，保留英文專有名詞）。
   - diagrams/*.mmd（Mermaid 原始碼，可貼到 mermaid.live 轉圖）。
   - 指引.html（段落清單 + 開啟連結 + 複製按鈕）。
4. **檢查成果**：打開 指引.html，確認內容、複製按鈕與開啟連結皆正常。
5. **匯入簡報工具**：依 指引.html 提示將 Markdown 貼入 AI 簡報製作工具(例如: [Gamma](https://gamma.app/) )，而圖表則可以透過線上工具: [Mermaid Live Editer](https://mermaid.live/) 轉換成圖片後嵌入簡報中。
6. **排練與記錄**：練習講稿並視需要更新 AGENTS.md 或 指引.html 的注意事項、日期與下一步建議。

## 建議工作習慣
- 章節更新時，優先維護 Chapter*.md；其他檔案可重新透過 Codex 依 AGENTS.md 產出。
- 每次改動後記錄 指引.html 與 AGENTS.md 的變更重點，方便下一位協作者接手。
- 保留所有 Mermaid 原始碼於 diagrams/，轉出的 SVG/PNG 依簡報工具需求存放於 ssets/ 或 slides/img/。

## 參與方式
1. Fork / Clone 專案，新增章節 Markdown 或補充講稿、圖表。
2. 依 AGENTS.md 規範執行 Codex CLI 工作，整理產出回專案結構。
3. 發 Pull Request 時附上更新後的 指引.html、slides/、
otes/、diagrams/，並說明主要改動與測試方式。

若對流程或 Codex CLI 有任何建議，歡迎於 Issue 區回報；期待透過 AI 協助，讓原文書共讀更有效率，也更容易上台分享。
