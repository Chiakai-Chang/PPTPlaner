# Video Pipeline 工作流程

## 系統架構

```
┌─────────────────────────────────────────────────────────────────┐
│                    PPTPlaner 完整工作流程                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Phase 1: 簡報生成 (orchestrate.py)                              │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │  分析文件    │───▶│  生成投影片  │───▶│  生成備忘稿  │         │
│  │  (AI)       │    │  (AI)       │    │  (AI)       │         │
│  └─────────────┘    └─────────────┘    └─────────────┘         │
│                              │                                   │
│                              ▼                                   │
│                    輸出到 output/                                │
│                    ├── slides/*.md                              │
│                    └── notes/*.md                               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Phase 2: 影片生成 (video_pipeline.py) ← 獨立執行！               │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │  TTS 語音   │───▶│  圖片生成   │───▶│  影片合成   │         │
│  │  (本地/雲端)│    │  (AI/文字)  │    │  (FFmpeg)   │         │
│  └─────────────┘    └─────────────┘    └─────────────┘         │
│                              │                                   │
│                              ▼                                   │
│                    輸出到 output/<run>/                          │
│                    └── video_final.mp4                          │
└─────────────────────────────────────────────────────────────────┘
```

---

## 為什麼要分開執行？

### 問題：同時執行
```
orchestrate.py (同時做簡報 + 影片)
    ├── AI 生成投影片 (使用 GPU)
    ├── AI 生成備忘稿 (使用 GPU)
    └── AI 生成影片 (使用 GPU)
```

### 解決方案：分開執行
```
步驟 1: python scripts/orchestrate.py --source <file.md>
        └── 只生成簡報，不佔用 GPU

步驟 2: python scripts/video_pipeline.py
        └── 只生成影片，獨佔 GPU
```

---

## 使用指南

### 情境 A：標準流程（有 GPU）

```bash
# 步驟 1：生成簡報
python scripts/orchestrate.py --source Chapter1.md

# 步驟 2：等待簡報生成完成
# （此時 GPU 閒置）

# 步驟 3：生成影片
python scripts/video_pipeline.py
```

### 情境 B：只更新簡報

```bash
# 簡報有修改，但影片可以沿用
python scripts/orchestrate.py --source Chapter1.md

# 影片保持不變（利用 checkpoint）
```

### 情境 C：只更新影片

```bash
# 簡報已存在，只重新生成影片
python scripts/video_pipeline.py --force

# 或者指定不同的輸出目錄
python scripts/video_pipeline.py --output-dir ./new_video_output
```

### 情境 D：無 GPU 環境

```bash
# 步驟 1：生成簡報（無 GPU 需求）
python scripts/orchestrate.py --source Chapter1.md

# 步驟 2：生成影片（使用 Edge-TTS + 文字 overlay）
# config.yaml:
#   video:
#     tts:
#       provider: "edge-tts"
#     image:
#       provider: "none"

python scripts/video_pipeline.py
```

---

## 進階使用

### 檢查環境

```bash
python scripts/check_video_env.py
```

輸出範例：
```
🖥️  GPU: ✓ NVIDIA RTX A4500
🐳 Docker: ✓ 29.4.0 (Running)
🎬 FFmpeg: ✓ 7.0.2
🐍 Python: Phase 1 ✓
```

### 使用 Fish Speech（高品質 TTS）

```bash
# 步驟 1：啟動 Fish Speech
python -m scripts.start_docker_services

# 步驟 2：修改 config.yaml
video:
  tts:
    provider: "fish-speech"

# 步驟 3：生成影片
python scripts/video_pipeline.py
```

### 使用 AI 圖像生成

```bash
# 步驟 1：啟動 ComfyUI
python -m scripts.start_docker_services

# 步驟 2：修改 config.yaml
video:
  image:
    provider: "comfyui"

# 步驟 3：生成影片
python scripts/video_pipeline.py
```

---

## CLI 命令參考

### pptplaner (簡報生成)

```bash
# 基本使用
pptplaner --source Chapter1.md

# 完整參數
pptplaner --source Chapter1.md --agent antigravity --gemini-model gemini-1.5-pro
```

### pptplaner-video (影片生成)

```bash
# 基本使用
pptplaner-video

# 指定專案根目錄
pptplaner-video --project-root /path/to/PPTPlaner

# 指定輸出目錄
pptplaner-video --output-dir ./my_output

# 指定設定檔
pptplaner-video --config ./my_config.yaml

# 強制重新生成
pptplaner-video --force

# 預覽模式（不實際生成）
pptplaner-video --dry-run
```

### pptplaner-video-check (環境檢查)

```bash
# 檢查環境
pptplaner-video-check
```

---

## 故障排除

### 問題：影片生成失敗

```bash
# 1. 檢查環境
python scripts/check_video_env.py

# 2. 檢查設定
# 確認 config.yaml 中的 video 設定正確

# 3. 查看錯誤日誌
# 錯誤會記錄在 output/<run>/video_progress.json
```

### 問題：GPU 記憶體不足

```bash
# 方案 1：使用 Edge-TTS（不需 GPU）
video:
  tts:
    provider: "edge-tts"

# 方案 2：使用 RunningHub（雲端）
video:
  image:
    provider: "runninghub"
    runninghub_api_key: "your_key"
```

---

## 最佳實踐

### 1. 資源管理
- **優先級**：簡報生成 > 影片生成
- **時間**：建議在簡報完成後再執行影片生成

### 2. 版本控制
- **簡報**：使用 Git 追蹤
- **影片**：可以存放在單獨的目錄

### 3. 自動化
- **CI/CD**：可以設定在簡報生成後自動觸發影片生成
- **定時任務**：適合定期更新內容的頻道

---

## 總結

| 流程 | 命令 | GPU 需求 |
|------|------|----------|
| 簡報生成 | `pptplaner --source <file>` | 可選 |
| 影片生成 | `pptplaner-video` | 可選（Edge-TTS 不需要） |
| 環境檢查 | `pptplaner-video-check` | 否 |

**關鍵原則**：先簡報，後影片。獨立執行，資源不衝突。
