# 🚀 PPTPlaner - 快速開始指南

## 1 分鐘極速上手 (零配置圖形化啟動)

### 步驟 1：一鍵啟動
您不需要手動下載套件或設定環境。首次啟動時，啟動器會自動檢測、自動建立虛擬環境並安裝所有套件！

* **💻 Windows**: 
  直接按兩下 (Double Click) 執行資料夾中的 **`PPTPlaner.bat`** 即可。
* **🍏 macOS / 🐧 Linux**: 
  開啟終端機 (Terminal) 切換到專案資料夾，執行：
  ```bash
  chmod +x PPTPlaner.sh && ./PPTPlaner.sh
  ```

---

### 步驟 2：生成簡報與備忘稿
啟動後會出現精美的 GUI 圖形介面：
1. 點擊進入「全新生成」分頁。
2. 點擊瀏覽選取您的 Markdown 原始文獻 (例如 `source/Chapter5.md`，可參考專案內附範本)。
3. 點擊下方的「開始生成」按鈕，AI 將自動跑完所有 Generator-Validator 循環，並產出完美的投影片與逐字講稿！

---

### 步驟 3：生成教學影片 (選用)
簡報與講稿生成完成後：
1. 切換至「影片生成」分頁。
2. 點擊瀏覽選取生成好的簡報資料夾 (位於 `output/簡報目錄`)。
3. 點擊「開始生成」，AI 將自動呼叫 `edge-tts` 與 `ffmpeg` 合成帶有動態投影片與優質配音的 MP4 影片！
   *(提示：可透過命令列進行進階合成：`python scripts/video_pipeline.py --output-dir output/您的簡報目錄 --enable-video`)*

---

## 命令列方式（進階用戶）

```bash
# 1. 生成簡報
python scripts/orchestrate.py --source 你的文件.md

# 2. 生成影片
python scripts/video_pipeline.py
```

---

## 常用命令

| 命令 | 用途 |
|------|------|
| `python scripts/orchestrate.py --source 文件.md` | 生成簡報 |
| `python scripts/video_pipeline.py` | 生成影片 |
| `python scripts/check_video_env.py` | 檢查環境 |
| `pytest tests/video/` | 執行測試 |

---

## 文件導航

| 文件 | 用途 |
|------|------|
| `README.md` | 完整說明文件 |
| `QUICKSTART.md` | 本文件（快速開始） |
| `docs/VIDEO_PIPELINE_INDEX.md` | 影片功能完整指南 |
| `docs/VIDEO_PIPELINE_SETUP_GUIDE.md` | 環境設定指南 |
| `docs/VIDEO_PIPELINE_WORKFLOW.md` | 工作流程說明 |

---

## 常見問題

### Q: 影片生成失敗
**A:** 檢查 FFmpeg 是否安裝：
```bash
ffmpeg -version
```

### Q: Docker 相關錯誤
**A:** 確保 Docker Desktop 已啟動

### Q: 如何更改語音
**A:** 編輯 config.yaml：
```yaml
video:
  tts:
    edge_tts_voice: "zh-TW-YunJheNeural"  # 更換語音
```
