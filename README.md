# 🧠 PPTPlaner  
AI 自動化章節講稿與簡報生成系統  
> 為教學、研究與司法實務而設計的全自動章節簡報與逐頁備忘稿生成流程。

---

## 📘 導覽（Navigation）
- [👉 使用教學（docs/USAGE_zh-TW.md）](./docs/USAGE_zh-TW.md)  
- [⚙️ 規格文件（AGENTS.md）](./AGENTS.md)  
- [🧭 系統架構圖（Architecture Overview）](#系統架構architecture-overview)  
- [📂 專案檔案架構與說明（Project Structure & Roles）](#專案檔案架構與說明project-structure--roles)

---

## 🌟 專案簡介（Overview）
**PPTPlaner** 是一個針對長篇章節、學術論文或調查報告，  
自動生成投影片（Slides）與逐頁備忘稿（Notes）的系統。

本專案特別針對：
- **法心理學、刑事學、教育訓練** 場域的教學／簡報需求  
- **警察、研究人員、公務員** 常用的 Windows 環境  
- **Codex CLI / Gemini CLI / Claude Code** 等 AI Agent 命令列整合  

使用者只需提供原始章節 Markdown（例：`Chapter5.md`），  
系統即可自動生成：
- `slides/`：逐頁 Markdown 簡報  
- `notes/`：繁中逐頁講稿  
- `指引.html`：可搜尋、可複製的對照頁  

---

## 💡 系統特色（Features）
- 🎓 **為學習而生的備忘稿 (Memos for Learning)**：AI 不僅是總結簡報，更是扮演「老師」的角色，產出的備忘稿旨在引導講者深入學習原文書的精髓、案例與脈絡，真正實現「以教為學」。
- 🧩 **Spec-Driven**：以 `AGENTS.md` 為核心規格，定義多種 CLI 模式（PLAN / SLIDE / MEMO）。  
- ⚙️ **全自動流程**：由 `orchestrate.py` 一鍵完成切頁、生成、驗證與導出。  
- 🪄 **高品質講稿**：逐頁生成繁體中文備忘稿，保留英文術語與研究名稱。  
- 📚 **支援多 Agent**：可自由切換 Codex / Gemini / Claude CLI。  
- 🖥️ **Windows 友善**：所有腳本為純 Python，免 bash、免 Makefile。  
- 🔍 **品質驗證**：自動檢查中英對齊、口述時間與關鍵詞保留。  
- 📦 **完整打包**：輸出 ZIP 成果包，含 `slides/`、`notes/`、`指引.html`。  

---

## 🧭 系統架構（Architecture Overview）
> 本系統的核心設計是將「指揮官」、「大腦」、「指令書」三個角色分離，實現自動化且高品質的內容生成。

- **指揮官 (Commander) - `scripts/orchestrate.py`**
  - 這個 Python 腳本是整個流程的自動化指揮官。它負責讀取設定、依序呼叫 AI、並將結果存檔。它**不負責**任何內容的理解與創作。

- **大腦 (The Brain) - AI Agent (e.g., Gemini CLI)**
  - 您所選擇的 AI Agent 是真正的核心大腦。它負責讀取您的原始文本，並根據指令書的規則，進行規劃、摘要、創作簡報與備忘稿。

- **指令書 (The Instruction Manual) - `AGENTS.md`**
  - 這份規格文件是您給予 AI 的劇本與指令。AI 的所有產出品質、風格、格式，都取決於這份指令書的定義。

> 下圖展示了「指揮官」如何驅動「大腦」依據「指令書」完成任務的流程：

```mermaid
flowchart TD
    A["原始文本 Source File<br>(Chapter5.md / Report.txt)"] --> B["scripts/orchestrate.py<br>主控腳本"]
    B --> C["PLAN 模式<br>切頁規劃 (JSON)"]
    B --> D["SLIDE 模式<br>逐頁簡報 Markdown"]
    B --> E["MEMO 模式<br>逐頁備忘稿 (繁中＋英文)"]
    D & E --> F["scripts/validate.py<br>品質檢查"]
    F --> G["scripts/build_guide.py<br>生成 guide.html"]
    G --> H["最終產出<br>(在 output/資料夾中)"]
    B -.-> I["多 Agent 支援<br>(Codex / Gemini / Claude)"]
````

---

## 📂 專案檔案架構與說明（Project Structure & Roles）

> 本專案將「規格 / 腳本 / 輸出」**分層**管理；生成物與原始規格分離，便於審閱與版控。

```text
PPTPlaner/
├─ AGENTS.md                  # 規格：定義 PLAN/SLIDE/MEMO 等模式，所有 CLI 依此輸出
├─ README.md                  # 專案首頁（你現在看的這份）
├─ docs/
│  └─ USAGE_zh-TW.md          # 使用教學（臺灣繁中）— 詳細操作步驟與 FAQ
├─ config.yaml                # 任務設定（只要改這一檔，就能一鍵重跑）
├─ scripts/
│  ├─ orchestrate.py          # 🪄 主控腳本（Windows 友善；驅動 PLAN→SLIDE→MEMO→驗證→指引）
│  ├─ validate.py             # 產出檢查：slides/notes 對齊、英文術語、口述時間
│  └─ build_guide.py          # 生成「指引.html」（搜尋、深色、一鍵複製講稿）
├─ templates/
│  └─ guide.html.j2           # Jinja2 模板；若沒安裝 Jinja2 會自動改用內建備援模板
├─ slides/                    # （生成物）逐頁投影片（Markdown）
├─ notes/                     # （生成物）逐頁備忘稿（繁中＋保留英文術語）
├─ diagrams/                  # （選用生成物）Mermaid .mmd 原始碼（可自行轉成 PNG/SVG）
├─ 指引.html                   # （生成物）對照指引頁（搜尋 + Copy 備忘稿）
└─ PPTPlaner_Package.zip      # （生成物）打包交付（可在 config.yaml 改名）
```

### 🔑 關鍵檔案職責一覽

| 檔案                                                   | 功能說明                                                                      |
| ---------------------------------------------------- | ------------------------------------------------------------------------- |
| [`AGENTS.md`](./AGENTS.md)                           | **唯一真相（Single Source of Truth）** 的規格檔。定義 PLAN / SLIDE / MEMO / REVIEW 模式。 |
| [`config.yaml`](./config.yaml)                       | 任務設定：來源檔、Agent 選擇、命名規則、是否打包等。                                             |
| [`scripts/orchestrate.py`](./scripts/orchestrate.py) | 主控流程。自動依序呼叫 Agent、產生 slides / notes、驗證品質並輸出指引。                            |
| [`scripts/validate.py`](./scripts/validate.py)       | 對齊檢查、英文保留檢查、講稿時間評估。                                                       |
| [`scripts/build_guide.py`](./scripts/build_guide.py) | 將投影片與備忘稿合併生成「指引.html」。                                                    |

### 🗂️ 生成物與版控策略

| 類別        | 資料夾                                    | 是否納入 Git | 備註               |
| --------- | -------------------------------------- | -------- | ---------------- |
| 核心規格 / 腳本 | `AGENTS.md`, `scripts/`, `config.yaml` | ✅ 建議     | 永久維護版本           |
| 來源檔       | `Chapter5.md` 等                        | ✅ 建議     | 可重現依據            |
| 生成物       | `slides/`, `notes/`, `指引.html`         | ⚠️ 視需求   | 審稿可保留、重跑可忽略      |
| 壓縮包       | `.zip`                                 | ⛔ 不建議    | 可加入 `.gitignore` |

### 🧱 建議 `.gitignore`

```gitignore
# Python / venv
.venv/
__pycache__/
*.pyc

# Generated
指引.html
slides/
notes/
diagrams/
*.zip
.plan.json

# OS
.DS_Store
Thumbs.db
```

---

## ⚙️ 系統需求（System Requirements）

* **作業系統**：Windows 10 / 11
* **Python**：3.10 以上
* **AI Agent CLI**：`gemini`, `codex`, 或 `claude` 等 CLI 工具需已安裝且在系統 PATH 中。
* **相依套件**：請見 `requirements.txt` 檔案。

--- 

## 🚀 如何執行 (How to Run)

我們提供了一個「一鍵啟動」的體驗，讓任何人都能輕鬆使用。

1.  **找到 `START_HERE.bat`**
    -   在專案資料夾中，找到一個名為 `START_HERE.bat` 的檔案。

2.  **雙擊它**
    -   直接用滑鼠雙擊執行它。

就是這麼簡單！

這個腳本會自動為您：
- 檢查您的電腦環境是否符合需求。
- 如果缺少套件，會自動為您安裝。
- 完成後，會自動開啟圖形操作介面，之後您就可以在介面中完成所有操作。

> 對於進階使用者，您依然可以透過 `scripts/orchestrate.py` 進行更複雜的命令列操作。

---
## 🧩 工作流摘要（Workflow Summary）

| 階段    | 輸出            | 工具 / 模式     |
| ----- | ------------- | ----------- |
| 章節分析  | page 切割規劃     | PLAN 模式     |
| 投影片生成 | slides/*.md   | SLIDE 模式    |
| 備忘稿生成 | notes/*.md    | MEMO 模式     |
| 品質檢查  | log + console | VALIDATE    |
| 對照指引頁 | 指引.html       | BUILD_GUIDE |
| 打包成果  | ZIP           | AUTO        |

---

## 🧠 延伸閱讀與進階應用

* [docs/USAGE_zh-TW.md](./docs/USAGE_zh-TW.md)：完整使用教學與錯誤排除
* [AGENTS.md](./AGENTS.md)：Agent 模式定義與規格說明
* 支援多來源專案：可建立子資料夾，如 `projects/eyewitness/`、`projects/deception/`

---

## 📜 授權與鳴謝

* 授權：MIT License（非商業教學與研究可自由使用）
* 原創者：Chang, Chia-Kai（[lotifv@gmail.com](mailto:lotifv@gmail.com)）
* 靈感源自中央警察大學法心理學課程《Eyewitness Memory》章節
* 貢獻：感謝所有協作者與學生測試回饋

## 📦 核心檔案清單 (Core Project Files)

如果您想將此專案分享給他人，或在一個乾淨的環境中執行，以下是確保程式運作所需的最精簡檔案列表：

```
PPTPlaner/
├─ START_HERE.bat         # ⭐ 使用者唯一的啟動入口
├─ AGENTS.md              # AI 指令書 (不可或缺)
├─ config.yaml            # 專案基礎設定
├─ requirements.txt       # Python 套件依賴列表
├─ run_ui.py              # 圖形介面主程式
├─ templates/
│  └─ guide.html.j2     # HTML 產生模板
└─ scripts/
   ├─ orchestrate.py      # 核心主控腳本
   └─ build_guide.py      # HTML 產生腳本
```

**您需要提供的：**
- 一個 `source/` 資料夾，裡面放您的原文書檔案。

---

> 📘 [詳細操作說明 → docs/USAGE_zh-TW.md](./docs/USAGE_zh-TW.md)
> ⚙️ [完整 Agent 規格 → AGENTS.md](./AGENTS.md)

---
