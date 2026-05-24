# PPTPlaner Video Pipeline 架構文檔

## 系統概覽

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            PPTPlaner 完整架構                                 │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│   簡報生成流程        │    │   影片生成流程        │    │   環境檢查流程        │
│   (orchestrate.py)   │    │   (video_pipeline)   │    │   (check_video_env)  │
└─────────────────────┘    └─────────────────────┘    └─────────────────────┘
         │                         │                         │
         ▼                         ▼                         ▼
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│  1. 分析文件         │    │  1. TTS 語音生成     │    │  1. GPU 偵測         │
│  2. 生成投影片       │    │  2. 圖像生成         │    │  2. Docker 檢查      │
│  3. 生成備忘稿       │    │  3. 影片合成         │    │  3. FFmpeg 檢查      │
│  4. 打包輸出         │    │  4. 輸出 MP4         │    │  4. Python 套件檢查   │
└─────────────────────┘    └─────────────────────┘    └─────────────────────┘
         │                         │                         │
         ▼                         ▼                         ▼
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│  輸出目錄:           │    │  輸出目錄:           │    │  輸出報告:            │
│  output/<run>/       │    │  output/<run>/      │    │  video_env.json      │
│  ├── slides/         │    │  ├── clips/          │    │                     │
│  ├── notes/          │    │  ├── video_final.mp4 │    │                     │
│  └── diagrams/       │    │  └── video_progress.json │                     │
└─────────────────────┘    └─────────────────────┘    └─────────────────────┘
```

---

## 核心設計原則

### 1. 分離關注點 (Separation of Concerns)
- **簡報生成**：專注於內容分析與結構化
- **影片生成**：專注於多媒體處理
- **環境檢查**：專注於依賴驗證

### 2. 資源隔離 (Resource Isolation)
- GPU 資源不再競爭
- 可以依需求獨立執行
- 失敗不會影響其他流程

### 3. 可組合性 (Composability)
- 每個流程可獨立執行
- 支援定時任務
- 支援 CI/CD 整合

---

## 工作流程

### 標準流程

```bash
# 步驟 1：環境檢查
python scripts/check_video_env.py

# 步驟 2：生成簡報
python scripts/orchestrate.py --source Chapter1.md

# 步驟 3：生成影片
python scripts/video_pipeline.py
```

### 快速流程（只生成簡報）

```bash
# 只需簡報，不需影片
python scripts/orchestrate.py --source Chapter1.md
```

### 快速流程（只生成影片）

```bash
# 簡報已存在，只需影片
python scripts/video_pipeline.py --force
```

---

## 模組結構

### 簡報生成模組 (scripts/orchestrate.py)

| 功能 | 說明 |
|------|------|
| 文件分析 | AI 分析源文件 |
| 投影片生成 | 生成 Markdown 投影片 |
| 備忘稿生成 | 生成逐頁講稿 |
| 打包輸出 | 輸出完整簡報包 |

### 影片生成模組 (scripts/video_pipeline.py)

| 功能 | 說明 |
|------|------|
| TTS 語音 | 文字轉語音 |
| 圖像生成 | AI 圖像或文字 overlay |
| 影片合成 | FFmpeg 組合所有片段 |
| 斷點續傳 | Checkpoint 機制支援恢復 |

### 環境檢查模組 (scripts/check_video_env.py)

| 功能 | 說明 |
|------|------|
| GPU 偵測 | NVIDIA GPU 狀態 |
| Docker 檢查 | Docker Desktop 狀態 |
| FFmpeg 檢查 | 影片處理工具 |
| Python 套件 | 所有依賴套件 |

---

## 配置檔結構 (config.yaml)

```yaml
video:
  enabled: true
  
  # TTS 設定
  tts:
    provider: "edge-tts"  # 或 "fish-speech"
    edge_tts_voice: "zh-TW-HsiaoChenNeural"
    
  # 圖像設定
  image:
    provider: "none"  # 或 "comfyui", "runninghub"
    width: 1920
    height: 1080
    
  # 影片規格
  fps: 30
  bgm_file: null
  bgm_volume: 0.15
  
  # 開場設定
  intro:
    enabled: true
    text: "大家好，歡迎收看！"
    channel_name: "我的頻道"
    duration_sec: 8
    
  # 結尾設定
  outro:
    enabled: true
    text: "感謝收看！"
    channel_name: "我的頻道"
    duration_sec: 12
```

---

## 錯誤處理

### 簡報生成失敗
- 不影響影片生成
- 可以重新運行簡報生成
- 已有內容保留在 output/

### 影片生成失敗
- 不影響簡報生成
- 可以重新運行影片生成
- Checkpoint 機制支援恢復

### 環境檢查失敗
- 提供明確的解決建議
- 輸出 JSON 報告供自動化使用

---

## 未來擴展

### 已規劃
- [x] Edge-TTS 支援
- [x] 文字 overlay 圖像
- [ ] Fish Speech 高品質 TTS
- [ ] ComfyUI AI 圖像
- [ ] RunningHub 雲端圖像

### 待規劃
- [ ] 多種開結尾模板
- [ ] 自動字幕生成
- [ ] YT chapters 輸出
- [ ] AI 推薦 config

---

## 效能考量

### GPU 使用
| 流程 | GPU 需求 | 預估時間 |
|------|----------|----------|
| 簡報生成 | 中 | 30-60 分鐘 |
| 影片生成 | 高 | 1-2 小時 |
| 環境檢查 | 無 | < 5 秒 |

### 記憶體使用
| 流程 | 預估使用 |
|------|----------|
| 簡報生成 | 2-4 GB |
| 影片生成 | 4-8 GB |

---

## 安全性

- **API Key 保護**：config.yaml 不被提交到 Git
- **本地服務**：Fish Speech 和 ComfyUI 僅本地運行
- **網路請求**：Edge-TTS 僅呼叫 Microsoft API
