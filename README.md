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
-> 將 **簡報** 連同**原文書的 Markdown.md** 一併提供給 LLM (例如: ChatGPT、Gemini、Claude等)，請 LLM 根據原文以及簡報每一頁的內容，目的不是對齊簡報，而是完整學習該章節內容為目的，逐頁規劃生成該頁的完整備忘稿內容
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
6. **逐頁生成備忘稿**：請參考以下「**生成高品質備忘稿參考作法**」

### **生成備忘稿可參考**
* **初始系統提示詞**
   * 將 **簡報**、**原文書的 Markdown.md**檔案，以及以下提示詞，一併提供給 LLM (例如: ChatGPT、Gemini、Claude等)
```text
# **系統提示**
你是一位熟悉心理學、刑事偵查與教育呈現設計的講稿編輯助理。
你的任務是根據使用者提供的原文書章節，以及使用者提供的簡報逐頁內容，
撰寫適合博士生、研究生研討課使用的高品質 **逐頁備忘稿**。

# **撰寫原則**：
1. 使用**臺灣繁體中文**，語氣學術但自然、具教學節奏。
2. 每頁輸出分為兩段：
   * **【摘要重點】**：整理該頁的概念、理論、研究或章節位置，讓講者能快速掌握要點。
   * **【講述稿】**：撰寫成可直接貼進 PowerPoint 備忘欄（Notes）的逐字口語稿，
     應自然流暢、適合口頭發表，避免條列式、要能「說得出來」。
3. 若有**專有名詞、人名、理論或實驗**，請保留英文原文並加上中文解釋，例如：
   > *Tulving & Thomson (1971)* 的「**編碼特異性原則（Encoding Specificity Principle）**」。
4. 撰寫目的不是僅對齊簡報文字，而是**完整學習章節內容**，
   需融合該章原文（如 Chapter5.md）中的核心概念、例子、理論、與實務應用。
5. 文字長度：每頁講述稿約 2–3 分鐘可講完，約 250–350 字，
   適度引用研究或案例，但不需過度細節化。
6. 若章節有延續性（如上頁概念的延伸），可在開頭簡短銜接說明。
7. 結尾若合適，可加入一句總結或反思，幫助過渡到下一頁。

# **參考輸出範例格式**（助理回答時應遵循此架構，但不必遵循此格式，以最佳呈現為主）：
## 🧠 第 X 頁：<簡報頁標題>
（說明此頁是對應章節理論位置，重點是什麼，簡要說明承先啟後的部分）

### 【摘要重點】
（簡要說明此頁簡報內容，用講者熟悉語言快速對齊進度與這頁內容）

### 【講述稿】
（完整逐字講稿，學術但自然、有趣且引人入勝，真正讓人了解原文的內容，可直接貼入 PowerPoint 備忘欄）
```

* 然後每一頁可參考使用以下提示詞來生成: 
```markdown
請幫我撰寫簡報第 X 頁備忘稿，內容如下(請記得這簡報是從原文出來的，我們的目的不是對齊這份簡報，而是要完整學習該章節內容，所以備忘稿很重要)：
<貼上該頁簡報文字內容>
```

* **(逐頁)使用範例**：
```text
請幫我撰寫簡報第11頁備忘稿，內容如下(記得這簡報是從 Chapter5.md 出來的，我們的目的不是對齊這份簡報，而是要完整學習該章節內容，所以備忘稿很重要):
'''
Memory As Construction

The Public Misconception
Most people view memory as video playback—a perfect recording that can be rewound and replayed with complete accuracy. This metaphor is deeply misleading.

The Reality of Retrieval
Actual retrieval mixes the original memory trace with current retrieval cues, general knowledge, expectations, and schemas. Each recall is a reconstruction, not a replay.

Pattern Completion
The same event recalled with different cues produces different versions. Our brains fill in gaps using whatever information is available at retrieval time.
'''
```

```markdown
(以下是 ChatGPT 的回答)
非常好 👏
第 11 頁「**Memory As Construction**」是 Chapter 5 的核心概念之一。
這頁要讓學生理解：

> 「記憶不是攝影機（not a recording device），而是建構性的心理重組過程（constructive reconstruction process）。」

這個觀念是整章理論的支點，也奠定後續「犯罪腳本（crime scripts）」與「刻板印象干擾」的理論背景。

以下是可直接放入 PowerPoint 備忘欄的完整逐字講稿👇

---

### 🧩 第 11 頁：Memory As Construction

#### 【摘要重點】

* **大眾誤解（Public Misconception）**：記憶常被誤以為是精準的「影片回放」。
* **真實情況（Reality of Retrieval）**：每一次回想都混合了原始記憶痕跡、當下線索、一般知識與期待。
* **模式補全（Pattern Completion）**：在回想過程中，大腦會主動填補空白，使同一事件在不同情境下呈現出不同版本。

---

#### 【講述稿】

在上一頁我們提到，記憶是個動態系統。
這一頁要更進一步說明——
**記憶的本質，是「建構（Construction）」，不是「重播（Replay）」**。

---

**首先是大眾的誤解（Public Misconception）**。
多數人以為記憶就像影片，
可以「倒帶」、「重播」，甚至「放慢看清楚細節」。
但心理學告訴我們：

> 這個比喻是錯誤的，甚至是危險的。

因為記憶不是一個封存的檔案，
而是一個會在提取當下被重新組合的活資料。

---

**第二，我們來看真實的回想過程（Reality of Retrieval）**。
每一次提取記憶時，大腦都會把：

* 原始的記憶痕跡（Memory Trace），
* 當下的提取線索（Retrieval Cues），
* 自己的知識背景（General Knowledge），
* 以及既有的認知框架（Schemas），
  整合成一個「看似完整」的敘述。

換句話說，我們記得的不只是「事件」，
還包括我們「如何理解那個事件」。
因此，**回想永遠是重新建構（Reconstruction），而不是回放（Playback）**。

---

**第三個重點是「模式補全（Pattern Completion）」**。
這是一個神經心理學概念，指的是：

> 當記憶中有缺口時，大腦會自動用可得資訊去「補齊」它。

例如：同一個事件，若在不同的提問情境下回想，
人可能會產生不同版本的敘述。
這並非說謊，而是大腦在進行「合理化填補」。

舉例來說，一名證人第一次被問「那時你看到誰？」時，
他可能說「我不太確定，應該是一個高個子男子」。
但如果第二次被問「那個男的有戴帽子嗎？」——
即使他當初沒注意，大腦也可能在第二次回想時自動「補上帽子」這個細節。

---

因此，我們在面對證人時，要記得：
**他所敘述的，往往是一次「重組後的真實」**。
這不代表他不誠實，而是人類記憶本來就帶有建構性。

對法律與偵查而言，這有兩個啟示：
1️⃣ 不能把證詞當成「錄影重播」；
2️⃣ 要理解每一次訪談，都是一次「再建構」。

換句話說，我們聽到的，不只是他記得什麼，
還包括「他今天是怎麼被引導去記得那些東西」。

---

是否要我繼續撰寫 **第 12 頁（Schemas Fill The Gaps）** 的備忘稿？
那一頁會延伸本章「建構性記憶」的主題，
討論「圖式（Schema）」如何幫我們理解世界、同時也導致錯誤與偏誤（如刻板印象與文化預期）。
```

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


