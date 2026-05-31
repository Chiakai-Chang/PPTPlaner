# 🧠 PPTPlaner (AI 簡報學習規劃器)

> **「程式碼是我們對抗時間焦慮的武器。」**  
> 將任何長篇文獻、研究報告自動轉化為結構化的簡報學習方案，包含投影片 (Slides)、深度學習備忘稿 (Notes) 與展示影片。

本專案內建全新的 **零摩擦自動啟動器**。**無論您是第一次用電腦執行程式的新手，還是進階開發者，均不需要手動下載配置任何 Python 依賴套件或虛擬環境！**
首次啟動時，啟動器會自動偵測您的系統，並建立乾淨隔離的 `.venv` 虛擬環境；同時支援最新的 Astral `uv` 超高速安裝引擎，享受秒級的極速啟動體驗！

---

## 🚀 快速開始 (新手友善 / 零摩擦一鍵啟動)

### Step 1: 取得專案檔案
您可以選擇使用 Git，也可以完全不依賴 Git：
* **💡 方法 A：不使用 Git (適合全新新手)**
  直接點擊下載連結：[**下載專案 ZIP 壓縮檔**](https://github.com/Chiakai-Chang/PPTPlaner/archive/refs/heads/main.zip)  
  下載完成後，將 ZIP 檔案**解壓縮**到您的電腦中（如桌面或文件資料夾）。
* **🛠️ 方法 B：使用 Git (適合開發者)**
  在終端機中執行以下指令複製專案：
  ```bash
  git clone https://github.com/Chiakai-Chang/PPTPlaner.git
  cd PPTPlaner
  ```

---

### Step 2: 依您的作業系統一鍵啟動
啟動後，PPTPlaner 會**自動完成所有環境偵測、下載安裝缺失套件、完成配置遷移，並自動開啟 premium 的 GUI 圖形化操作介面**！

> [!TIP]
> **🚀 Astral `uv` 支援**：
> 啟動時會自動偵測是否已安裝 Astral `uv` 工具。若未安裝，啟動器會貼心地提供**一鍵自動下載並啟用 uv** 的選項。使用 `uv` 能將專案初始化與套件安裝速度**提升 10 倍以上**！您也可以選擇不安裝並直接改用標準 Python 工具，完全不受影響。

#### 💻 Windows 系統 (Windows 10/11)
在您解壓或 clone 出來的資料夾中，直接 **按兩下 (Double Click) 執行** 以下檔案：
```bash
PPTPlaner.bat
```
*(提示：首次執行時若出現 Windows Defender 防護警告，請點擊「其他資訊」並選擇「仍要執行」即可)*

#### 🍏 macOS 或 🐧 Linux 系統
開啟終端機 (Terminal)，切換到專案目錄後執行以下指令：
```bash
# 1. 賦予啟動腳本執行權限（僅需在首次執行一次）
chmod +x PPTPlaner.sh

# 2. 啟動 PPTPlaner 智慧助手
./PPTPlaner.sh
```

---

### Step 3: 在 GUI 圖形化介面中操作
一鍵啟動成功後，會自動彈出精美且具科技感的 Tkinter 視窗：
1. **全新生成簡報**：選擇「全新生成」模式 -> 點擊瀏覽選取您的 Markdown 原始文獻 (例如 `source/Chapter5.md`) -> 點擊「開始生成」即可。
2. **影片合成 (選用)**：簡報生成完畢後，切換到「影片生成」模式 -> 選擇簡報的輸出資料夾 -> 點擊「開始生成」即可自動合成帶有高品質 AI 配音的 MP4 教學影片。

---

## 🛠️ 開發者進階命令 (CLI 模式)

如果您習慣使用 Command Line 進行開發，可以直接呼叫核心腳本：

```bash
# 1. 啟用簡報與備忘稿生成管線 (Phase 1-5)
python scripts/orchestrate.py --source source/Chapter5.md

# 2. 獨立調用影片合成管線 (Phase 6 - 需要 ffmpeg)
python scripts/video_pipeline.py --project-root . --enable-video

# 3. 獨立調用投影片按數字順序合併工具
python scripts/combine_slides.py output/你的簡報資料夾
```

---

## ✨ 核心功能與品質保證

| 功能 | 說明 | 狀態 |
|------|------|------|
| 📊 **AI 簡報生成** | 自動生成結構化、排版優雅的 Markdown 格式投影片 (Gamma 相容) | ✅ |
| 📝 **深度學習備忘稿** | 基於費曼學習法驅動的逐字講稿生成，保留關鍵學術名詞 | ✅ |
| 🎬 **影片生成** | 一鍵將投影片與備忘稿轉換為精美、動態的 YouTube 教學影片 | ✅ |
| 🎤 **跨平台 TTY Agent** | 支援 Antigravity CLI (agy) 與 PTY 降級，無縫支援 Windows/macOS/Linux | ✅ |
| 🧰 **智慧品管引擎** | 雙代理人 Generator-Validator 品管機制，自動自我糾錯與重試 | ✅ |

---

## 📚 文件導航

| 需求 | 文件 | 連結 |
|------|------|------|
| 🚀 系統架構與適配 | 跨平台與 TTY 技術指南 | [CROSS_PLATFORM_SUPPORT.md](docs/CROSS_PLATFORM_SUPPORT.md) |
| 🎬 影片生成技術 | 影片管線總索引 | [VIDEO_PIPELINE_INDEX.md](docs/VIDEO_PIPELINE_INDEX.md) |
| ⚙️ 環境安裝細節 | 影片管線設定指南 | [VIDEO_PIPELINE_SETUP_GUIDE.md](docs/VIDEO_PIPELINE_SETUP_GUIDE.md) |
| 📚 哲學與開發指南 | PPTPlaner 核心哲學 | [GEMINI.md](GEMINI.md) |

---

## 🎯 系統架構

```
                     ┌─────────────────────┐
                     │   PPTPlaner 啟動器   │
                     │  (bat / sh 智慧偵測) │
                     └──────────┬──────────┘
                                │
           ┌────────────────────┼────────────────────┐
           │                    │                    │
           ▼                    ▼                    ▼
 ┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
 │     run_ui.py       │    │   orchestrate.py    │    │  video_pipeline.py  │
 │   (圖形操作介面)     │    │   (簡報/講稿生成)    │    │   (影片合成管線)     │
 └─────────────────────┘    └─────────────────────┘    └─────────────────────┘
           │                         │                         │
           ▼                         ▼                         ▼
 ┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
 │   output/slides/    │    │   output/notes/     │    │  output/video/      │
 │   (投影片 Markdown)  │    │   (備忘/講稿Markdown)│    │  (video_final.mp4)  │
 └─────────────────────┘    └─────────────────────┘    └─────────────────────┘
```

---

## 📊 測試覆蓋 (TDD 驅動)

專案採用嚴格的測試驅動開發 (TDD) 模式，在乾淨的非 Windows 環境下亦能流暢收集並執行所有測試：

```bash
# 執行完整測試套件
pytest

# 結果
======================= 153 passed, 3 skipped in 56.54s =======================
```

---

## ❓ 常見問題

### Q: 出現「找不到 Python」錯誤？
**A:** 請前往 [Python 官網](https://www.python.org/downloads/) 下載並安裝 Python 3.12+，安裝時請務必勾選 **"Add Python to PATH"**。

### Q: 影片生成失敗，提示缺少 FFmpeg？
**A:** 影片渲染需要 FFmpeg：
- **Windows**: 圖形介面會引導您下載，或透過 `winget install Gyan.FFmpeg` 安裝。
- **macOS**: 在終端機執行 `brew install ffmpeg`。
- **Linux**: 在終端機執行 `sudo apt install ffmpeg`。

---

## 📜 授權

本專案使用 [MIT License](LICENSE) 授權。

---

## 🙏 致謝

感謝以下開源專案的貢獻：
- [Edge-TTS](https://github.com/rany2/edge-tts) — 高品質語音合成
- [Pillow](https://github.com/python-pillow/Pillow) — 圖形介面與圖像生成
- [Jinja2](https://github.com/pallets/jinja) — 範本化引擎
- [pytest](https://github.com/pytest-dev/pytest) — 測試框架
