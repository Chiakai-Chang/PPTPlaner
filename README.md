# 🧠 PPTPlaner (AI 簡報學習規劃器)

> 將任何長篇原文自動轉換為完整的簡報學習方案，包含投影片、深度學習備忘稿與影片

---

## 🚀 快速開始

```bash
# 1. 安裝
.\scripts\install.ps1

# 2. 配置
copy config.yaml.example config.yaml

# 3. 生成簡報
python scripts/orchestrate.py --source 你的文件.md

# 4. 生成影片（可選）
python scripts/video_pipeline.py
```

詳細說明請查看 [QUICKSTART.md](QUICKSTART.md)

---

## ✨ 核心功能

| 功能 | 說明 | 狀態 |
|------|------|------|
| 📊 **AI 簡報生成** | 自動生成 Markdown 格式投影片 | ✅ |
| 📝 **深度學習備忘稿** | 費曼學習法驅動的講稿生成 | ✅ |
| 🎬 **影片生成** | 將簡報轉換為 YouTube 影片 | ✅ |
| 🎤 **高品質 TTS** | 支援 Edge-TTS、Fish Speech | ✅ |
| 🖼️ **AI 圖像** | 支援 ComfyUI、RunningHub | ✅ |

---

## 📚 文件導航

| 需求 | 文件 | 連結 |
|------|------|------|
| 🚀 快速上手 | 快速開始 | [QUICKSTART.md](QUICKSTART.md) |
| 📖 完整說明 | 使用說明 | [README.md](README.md) |
| 🎬 影片功能 | 影片文件索引 | [VIDEO_PIPELINE_INDEX.md](docs/VIDEO_PIPELINE_INDEX.md) |
| 🛠️ 環境設定 | 設定指南 | [VIDEO_PIPELINE_SETUP_GUIDE.md](docs/VIDEO_PIPELINE_SETUP_GUIDE.md) |
| 🔄 工作流程 | 工作流程 | [VIDEO_PIPELINE_WORKFLOW.md](docs/VIDEO_PIPELINE_WORKFLOW.md) |

---

## 🎯 系統架構

```
┌─────────────────────────────────────────────────────────────────┐
│                        PPTPlaner 系統                            │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│   orchestrate.py    │    │  video_pipeline.py  │    │ check_video_env.py  │
│   (簡報生成)         │    │   (影片生成)         │    │   (環境檢查)         │
└─────────────────────┘    └─────────────────────┘    └─────────────────────┘
         │                         │                         │
         ▼                         ▼                         ▼
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│  output/slides/*.md │    │  output/            │    │  video_env.json     │
│  output/notes/*.md  │    │    video_final.mp4  │    │                     │
└─────────────────────┘    └─────────────────────┘    └─────────────────────┘
```

---

## 🛠️ 技術棧

| 技術 | 用途 |
|------|------|
| Python 3.12+ | 核心程式語言 |
| FFmpeg | 影片處理 |
| Edge-TTS / Fish Speech | 語音生成 |
| ComfyUI / RunningHub | AI 圖像生成 |
| Docker | 服務容器化 |

---

## 📊 測試覆蓋

```bash
# 執行測試
pytest tests/video/

# 結果
================== 105 passed, 1 skipped, 1 warning ==================
```

---

## ❓ 常見問題

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
    edge_tts_voice: "zh-TW-YunJheNeural"
```

更多問題請查看 [設定指南](docs/VIDEO_PIPELINE_SETUP_GUIDE.md)

---

## 📜 授權

本專案使用 [MIT License](LICENSE)

---

## 🙏 致謝

感謝以下開源專案的貢獻：
- [Edge-TTS](https://github.com/rany2/edge-tts)
- [Fish Speech](https://github.com/fishaudio/fish-speech)
- [ComfyUI](https://github.com/comfyanonymous/ComfyUI)
