# 🧠 PPTPlaner (AI 簡報學習規劃器)

一個由 AI 驅動，專為「深度學習」而設計的簡報與講稿自動生成工具。

---

## 🎯 這是什麼？ (What It Does)

本專案的核心構想源於「費曼學習法」(The Feynman Technique) — **如果你不能向其他人簡單解釋一件事，你就還沒有真正弄懂它。**

您是否曾為了準備一場簡報，而需要啃讀大量原文資料（如教科書、研究論文、商業報告），並為此耗費大量心力？

**PPTPlaner** 就是為了解決這個問題而生。它是一個以「教」為「學」的 AI 工具，能將任何長篇的原文文字，自動轉換成一套完整的簡報學習方案，包含：

1.  **重點投影片 (Slides)**：AI 會為您提煉原文精華，生成一頁頁重點清晰的 Markdown 格式投影片。
2.  **深度學習備忘稿 (Speaker Notes)**：這不只是一份講稿！AI 會扮演「老師」的角色，針對每一頁投影片的內容，從原文中找出更深入的細節、案例、上下文，並加上原文出處索引。這份備忘稿旨在幫助您在準備簡報的同時，真正地學懂、學透原文的核心知識。

### 核心使用情境

*   **從零到有**：提供一份原文書籍章節，AI 自動生成「投影片」與「深度學習備忘稿」。
*   **為簡報加值**：提供一份原文書籍章節，和一份您**已經做好**的簡報檔案，AI 會專注於為您現有的簡報，量身打造最匹配的深度學習備忘稿。

---

## ✨ 專案亮點 (Key Features)

*   🎓 **費曼學習法驅動 (Feynman-Powered Learning)**：本專案的核心是「以教為學」。AI 產出的備忘稿不只是講稿，更是實踐「費曼學習法」的工具。它將您置於老師的角色，引導您深入原文的精髓與案例，在準備「教」的過程中，達成真正的「懂」。
*   🤖 **AI 智慧分頁 (AI-Powered Planning)**：當給予一份現成的簡報檔案時，AI 會運用它的智慧去分析檔案的結構並規劃頁面，而非依賴固定的程式規則。
*   🎨 **客製化輸出 (Customizable Output)**：UI 介面中提供一個「客製化需求」欄位，讓您可以直接用自然語言微調備忘稿的語氣、風格、語言或內容重點。
*   💻 **極簡易用 UI (User-Friendly UI)**：一個簡潔的圖形介面，讓您只需點幾下滑鼠，就能完成所有操作，完全無需撰寫任何程式碼。
*   📂 **自動化成果整理 (Organized Output)**：每一次執行，都會在 `output` 資料夾中，建立一個以「時間戳 + AI總結標題」命名的專屬資料夾，讓您的專案保持整潔、有條理。
*   🚀 **自動開啟成果 (Auto-Open Results)**：執行完畢後，程式會自動為您打開包含所有結果的資料夾，以及 `guide.html` 總覽頁面。
*   🔍 **雙重 AI 品管循環 (Dual AI Quality Loops)**：為確保簡報與備忘稿的雙重品質，系統為兩者分別設計了「生成-品管-修正」的循環機制：
    1.  **簡報 (Slides)**：AI 會先**一次性生成整份簡報**，再由「設計總監 AI」從整體視角審核風格、語氣和邏輯流暢度。若不通過，整份簡報將被打回重做，確保了最終成品的高度一致性。
    2.  **備忘稿 (Memos)**：在簡報定稿後，針對每一頁投影片，系統採用「寫手-品管」兩階段流程，確保備忘稿的內容深度與準確性。

---

## 💻 系統預覽 (Demo)

<!-- 兩張圖並排，各佔一半（GitHub 允許的純 HTML，無 style 屬性） -->
<table width="100%">
  <tr>
    <td align="center"><b>程式運行畫面</b></td>
    <td align="center"><b>程式介面（含品管AI回饋）</b></td>
  </tr>
  <tr>
    <td width="50%" align="center">
      <img src="/demo/CMD.png" width="100%" alt="程式運行畫面">
    </td>
    <td width="50%" align="center">
      <img src="/demo/UI_Validate.png" width="100%" alt="程式介面（含品管AI回饋）">
    </td>
  </tr>
</table>

<!-- 跨欄：產出結果預覽 -->
<p align="center" style="margin-top: 12px;"><b>產出結果預覽</b></p>
<p align="center">
  <img src="/demo/Result.png" width="98%" alt="產出結果預覽">
</p>

---

## ⚙️ 系統需求 (System Requirements)

為了讓程式順利運行，您的電腦需要先安裝兩項基礎軟體。別擔心，整個過程非常簡單！

### 步驟 1：安裝 Python

*   **用途**：這是執行本專案所有核心腳本的程式語言。
*   **如何安裝**：
    1.  前往 [Python 官方網站](https://www.python.org/downloads/) 下載最新版本。
    2.  執行安裝程式。在安裝的第一個畫面，**請務必勾選 `Add Python to PATH`** 這個選項，這非常重要！

### 步驟 2：安裝 Node.js (包含 npm)

*   **用途**：我們需要它來安裝 AI 的核心命令列工具 (CLI)。
*   **如何安裝**：
    1.  前往 [Node.js 官方網站](https://nodejs.org/) 下載 `LTS` (長期支援) 版本。
    2.  執行安裝程式，一路點擊「下一步 (Next)」即可完成安裝。`npm` 會跟著一起被裝好。

### 步驟 3：安裝 AI Agent (以 Gemini 為例)

*   **用途**：這是我們專案的「大腦」。
*   **如何安裝**：
    1.  打開您的「命令提示字元 (cmd.exe)」或「Windows Terminal」。
    2.  輸入並執行以下指令：
        ```bash
        npm install -g @google/gemini-cli@latest
        ```

完成以上三個步驟後，您的電腦就具備執行本專案所需的一切環境了！

---

## 🚀 如何執行 (Quick Start)

我們提供了一個「一鍵啟動」的體驗，讓任何人都能輕鬆使用。

1.  **找到 `START_HERE.bat`**
    *   在專案資料夾中，找到一個名為 `START_HERE.bat` 的檔案。

2.  **雙擊它**
    *   直接用滑鼠雙擊執行它。

就是這麼簡單！這個腳本會自動處理所有事情，並為您啟動圖形操作介面。

---

## 🧭 運作原理 (How It Works)

本系統的核心設計是將「指揮官」、「大腦」、「指令書」三個角色分離，實現自動化且高品質的內容生成。

*   **指揮官 (The Commander) - `scripts/orchestrate.py`**
    *   這個 Python 腳本是整個流程的自動化指揮官。它負責讀取設定、依序呼叫 AI、並將結果存檔。它**不負責**任何內容的理解與創作。

*   **大腦 (The Brain) - AI Agent (e.g., Gemini CLI)**
    *   您所選擇的 AI Agent 是真正的核心大腦。它負責讀取您的原始文本，並根據指令書的規則，進行規劃、摘要、創作簡報與備忘稿。

*   **指令書 (The Instruction Manual) - `AGENTS.md`**
    *   這份規格文件是您給予 AI 的劇本與指令。AI 的所有產出品質、風格、格式，都取決於這份指令書的定義。

> 下圖展示了「指揮官」如何驅動「大腦」依據「指令書」完成任務的流程：

```mermaid
flowchart TD
    A["使用者輸入<br>(原文書 + 選填的簡報檔)"] --> B["run_ui.py<br>(圖形介面)"]
    B --> C["scripts/orchestrate.py<br>(指揮官)"]
    
    C -- "命令 AI" --> D["AI Agent<br>(大腦)"]
    D -- "讀取指令" --> E["AGENTS.md<br>(指令書)"]

    subgraph "1. 整體簡報生成與品管"
        D -- "生成整份簡報初稿" --> S1["簡報初稿"]
        S1 --> V1{"整體品管檢查"}
        V1 -- "合格" --> S2["最終簡報"]
        V1 -- "不合格<br>(帶意見重寫)" --> D
    end

    subgraph "2. 逐頁備忘稿生成與品管"
        S2 --> C2{指揮官讀取最終簡報}
        C2 -- "命令 AI (逐頁)" --> D
        D -- "生成備忘稿初稿" --> M1["備忘稿初稿"]
        M1 --> V2{逐頁品管檢查}
        V2 -- "合格" --> M2["最終備忘稿"]
        V2 -- "不合格<br>(帶意見重寫)" --> D
    end

    S2 --> G
    M2 --> G
    
    G["scripts/build_guide.py"] --> H["最終產出<br>(guide.html 等檔案)"]
```

### 雙重「品管-修正」循環 (The Dual Quality-Rework Loops)

本專案最特殊之處，在於其雙重的「自我修正」機制，以確保簡報與備忘稿的雙重高品質：

1.  **整體簡報品管 (Holistic Deck Validation)**
    *   **生成初稿 (Drafting)**：指揮官 (`orchestrate.py`) 命令 AI (`DECK` agent) 一次性生成**整份**簡報的初稿。
    *   **整體檢驗 (Holistic Validation)**：接著，指揮官將整份簡報交給「設計總監 AI」 (`VALIDATE_DECK` agent)。這位品管員會從宏觀角度檢查簡報的**風格一致性、邏輯流暢度、及前後連貫性**。
    *   **迭代修正 (Reworking)**：若不合格，總監會提出全面修改建議。指揮官會帶著這些建議，命令 AI **重做整份簡報**。這個循環確保了簡報的整體設計品質。

2.  **逐頁備忘稿品管 (Per-Page Memo Validation)**
    *   **生成初稿 (Drafting)**：在簡報定稿後，指揮官針對**每一頁**投影片，命令「寫手 AI」 (`MEMO` agent) 生成備忘稿。
    *   **品質檢驗 (Validation)**：指揮官接著將稿件交給「品管 AI」 (`VALIDATE_MEMO` agent)，檢查內容是否緊扣該頁投影片、是否提供足夠深度。
    *   **迭代修正 (Reworking)**：若不合格，品管員會提供具體修改建議，指揮官會命令寫手 AI 重寫。

這個「生成 -> 品管 -> 修正」的雙重循環，大幅提升了最終產出的專業度與實用性。

---

## 📂 核心檔案清單 (Core Project Files)

若您想分享此專案，以下是確保程式運作所需的最精簡檔案列表：

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
*   您自己的原文書或簡報檔案，通常會放在 `source/` 資料夾中。

---

## 📜 授權與作者 (License & Credits)

*   **License**: MIT License. 可自由使用於非商業的教學與研究用途。
*   **Original Creator**: Chiakai Chang
*   **Contact**:
    *   **Email**: [lotifv@gmail.com](mailto:lotifv@gmail.com)
    *   **LinkedIn**: [chiakai-chang-htciu](https://www.linkedin.com/in/chiakai-chang-htciu)
    *   **GitHub**: [Chiakai-Chang](https://github.com/Chiakai-Chang)
*   **Inspiration**: Inspired by the need to prepare for the *Eyewitness Memory* chapter in a Forensic Psychology course at Central Police University.
