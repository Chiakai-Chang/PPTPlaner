# 🚀 PPTPlaner - 快速開始指南

## 5 分鐘上手

### 步驟 1：安裝

```bash
# 方法 1：使用安裝腳本（推薦）
.\scripts\install.ps1

# 方法 2：手動安裝
pip install edge-tts Pillow httpx
```

### 步驟 2：啟動圖形介面

```bash
# 啟動 UI
python run_ui.py
```

### 步驟 3：生成簡報

1. 選擇「全新生成」模式
2. 選擇要分析的文件
3. 點擊「開始生成」

### 步驟 4：生成影片（可選）

**透過 UI：**
1. 選擇「影片生成」模式
2. 選擇簡報輸出資料夾
3. 點擊「開始生成」

**透過命令列：**
```bash
python scripts/video_pipeline.py --output-dir output/20260521_... --enable-video
```

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
