# PPTPlaner 影片產出管道 — 技術規格文件
> 版本：v0.2  
> 日期：2026-05-23  
> 狀態：決策已確認，可開始 Phase 1 實作

---

## 已確認決策（D1~D5）

| # | 問題 | 決策 |
|---|------|------|
| D1 | SVG 轉 PNG 工具 | **playwright**（cairosvg 放棄，SVG 輸出格式一併放棄） |
| D2 | Phase 順序 | **先 basic MVP**，Pixelle-Video 整合為 Phase 2 |
| D3 | 模板設計 | **AI 設計草稿，使用者點擊確認** |
| D4 | 多語言 | **繁中優先**，多語言為 Phase 3 |
| D5 | TTS 分段 | **整頁 notes 為一段 TTS**，未來可加智慧拆幀 |

**SVG 輸出放棄**：影片視覺由 AI 生成圖像或文字 overlay 取代，不再以投影片截圖為影格背景。

---

## 1. 目標

讓 PPTPlaner 在現有「slides + notes」輸出後，可選性地自動產出 `.mp4` 解說影片，含：
- YT 頻道開場（Logo + 開場詞，可客製化）
- 主體：AI 生成視覺背景 + 關鍵字 overlay + 旁白 TTS（逐字稿）
- YT 結尾（訂閱 CTA + 頻道 slogan，可客製化）
- BGM 全程播放（可選）

**設計原則**：
- 整夜跑不怕：斷點續傳，失敗跳過繼續，早上看日誌
- 依序不並行：一張投影片完整跑完再跑下一張
- 完全 optional：`video.enabled: false` 預設，不影響現有使用者

---

## 2. Pipeline 全圖

```
PPTPlaner 現有輸出（不變）
├── slides/01_intro.md      ← 內容結構（標題 + bullet points）
├── slides/02_memory.md
│   ...
└── notes/note-01_intro-zh.md      ← TTS 腳本來源
    notes/note-02_memory-zh.md
    ...

          ↓ [VIDEO phase，依序執行每個 slide]

per-slide 處理（有 checkpoint，可中斷續傳）：
  slide 01:
    ├── step1: notes → WAV（TTS）
    ├── step2: slide 內容 → AI image（optional）
    ├── step3: image/text-overlay + WAV → clip_01.mp4
    └── checkpoint 記錄 ✓

  slide 02 ... 03 ... N（同上）

bookend:
  ├── intro_clip.mp4（HTML 模板 → playwright → ffmpeg）
  └── outro_clip.mp4（HTML 模板 → playwright → ffmpeg）

concat:
  [intro] + [clip_01] + [clip_02] + ... + [outro]
          ↓
  output/<source_name>_video.mp4
  output/video_progress.json（執行紀錄）
```

---

## 3. 執行模式

### Mode A：基礎模式（無 GPU 可用）

| 子系統 | 工具 | 說明 |
|--------|------|------|
| TTS | Edge-TTS（呼叫 Microsoft） | 繁中品質優，需網路 |
| 影像 | `none`（文字 overlay） | 深色漸層背景 + 標題 + bullet points |
| Intro/Outro | HTML → playwright → ffmpeg | 靜態設計幀 |
| 影片合成 | ffmpeg | per-clip + concat |

### Mode B：本地高品質模式（有 GPU 16GB+）

| 子系統 | 工具 | 說明 |
|--------|------|------|
| TTS | Fish Speech（本地 HTTP server） | 4B 模型，繁中最高品質，支援聲音克隆 |
| 影像 | ComfyUI FLUX.1-schnell（本地） | 8~16GB VRAM，每幀 AI 生成配圖 |
| Intro/Outro | 同 Mode A | |
| 影片合成 | ffmpeg | |

> **⚠ Fish Speech 授權警告**：使用 Fish Audio Research License（非開源授權）。研究與個人使用可行，商業化 YT 頻道使用前請自行確認授權範圍。

### Mode C：雲端圖像模式（無 GPU，但有 RunningHub key）

| 子系統 | 工具 |
|--------|------|
| TTS | Edge-TTS |
| 影像 | RunningHub API（FLUX 雲端） |
| 影片合成 | ffmpeg |

---

## 4. Checkpoint 機制（可靠性核心）

### checkpoint 狀態檔

```json
// output/<run_id>/video_progress.json
{
  "session_id": "Chapter5_20260523_2300",
  "source_file": "source/Chapter5.md",
  "total_slides": 12,
  "slides": {
    "slide_01": {"tts": "ok", "image": "ok", "clip": "ok"},
    "slide_02": {"tts": "ok", "image": "failed", "clip": "ok"},
    "slide_03": {"tts": "pending", "image": "pending", "clip": "pending"}
  },
  "intro": "ok",
  "outro": "pending",
  "final_concat": "pending",
  "started_at": "2026-05-23T23:00:00",
  "last_updated": "2026-05-23T23:47:12",
  "errors": [
    {"slide": "slide_02", "step": "image", "error": "RunningHub timeout", "skipped": true}
  ]
}
```

### Pipeline 核心邏輯

```python
for slide in slides:
    # 已完成則跳過
    if checkpoint.is_done(slide.id, "clip"):
        print(f"⏭  {slide.id} — clip 已存在，跳過")
        continue

    try:
        # Step 1: TTS（失敗則整張跳過）
        if not checkpoint.is_done(slide.id, "tts"):
            tts_provider.generate(slide.notes_path, slide.wav_path)
            checkpoint.mark(slide.id, "tts", "ok")

        # Step 2: 圖像（失敗則降級為文字 overlay，不中止）
        if not checkpoint.is_done(slide.id, "image"):
            try:
                image_provider.generate(slide.content, slide.image_path)
                checkpoint.mark(slide.id, "image", "ok")
            except Exception as e:
                checkpoint.mark(slide.id, "image", "failed", str(e))
                slide.image_path = None  # fallback to text overlay

        # Step 3: 合成 clip
        if not checkpoint.is_done(slide.id, "clip"):
            compose_clip(slide)
            checkpoint.mark(slide.id, "clip", "ok")

    except Exception as e:
        checkpoint.mark_failed(slide.id, str(e))
        print(f"✗  {slide.id} 失敗，跳過繼續：{e}")
        continue
```

---

## 5. config.yaml 擴展規格

```yaml
# ============================================================
#  影片輸出設定 (Video Output Settings)
#  預設全部關閉，不影響現有使用者
# ============================================================
video:
  enabled: false                      # 是否啟用影片產出

  # --- TTS 設定 ---
  tts:
    provider: "edge-tts"              # edge-tts | fish-speech | kokoro
    language: "zh-TW"

    # Edge-TTS 設定（provider=edge-tts 時有效）
    edge_tts_voice: "zh-TW-HsiaoChenNeural"
    edge_tts_speed: "+0%"

    # Fish Speech 設定（provider=fish-speech 時有效）
    fish_speech_url: "http://localhost:8080"
    fish_speech_reference_audio: null  # 聲音克隆參考音檔（null = 使用預設聲線）

  # --- 圖像生成設定 ---
  image:
    provider: "none"                  # none | comfyui | runninghub
    # none = 純文字 overlay（無 GPU 需求，速度最快）

    # ComfyUI 設定（provider=comfyui 時有效）
    comfyui_url: "http://localhost:8188"
    comfyui_workflow: "image_flux.json"

    # RunningHub 設定（provider=runninghub 時有效）
    runninghub_api_key: ""
    runninghub_workflow: "image_flux.json"

    # 通用圖像設定
    prompt_prefix: ""                 # 圖像生成風格前綴（需英文）
    width: 1920
    height: 1080

  # --- 影片規格 ---
  resolution: "1920x1080"
  fps: 30
  bgm_file: null                      # BGM 檔案路徑（null = 無 BGM）
  bgm_volume: 0.15

  # --- YT 開頭（Intro）---
  intro:
    enabled: true
    duration_sec: 8
    channel_name: "我的頻道"
    channel_logo: null                # Logo 圖片路徑（null = 純文字）
    tagline: "每週更新 | 歡迎訂閱"
    video_title: ""                   # 空白 = 自動取自 source 文件名
    template: "yt_intro_default"

  # --- YT 結尾（Outro）---
  outro:
    enabled: true
    duration_sec: 12
    cta_text: "如果這個影片有幫助，請按讚並訂閱！"
    subscribe_hint: true
    next_video_text: ""               # 下支影片預告（空白 = 不顯示）
    template: "yt_outro_default"
```

---

## 6. 目錄結構（實作後）

```
PPTPlaner/
├── config.yaml
├── scripts/
│   └── orchestrate.py               # 主流程末尾呼叫 video/pipeline.py
│
├── video/
│   ├── __init__.py
│   ├── pipeline.py                  # 主控：依序 slide loop + bookend + concat
│   ├── checkpoint.py                # 斷點狀態管理（讀寫 video_progress.json）
│   ├── progress.py                  # 人可讀的 CLI 進度輸出
│   │
│   ├── steps/
│   │   ├── step1_tts.py             # notes → WAV（呼叫 provider）
│   │   ├── step2_image.py           # slide 內容 → 圖像（呼叫 provider）
│   │   ├── step3_clip.py            # image/overlay + WAV → per-slide mp4
│   │   ├── step4_bookend.py         # HTML → playwright → intro/outro clip
│   │   └── step5_concat.py          # clips → final.mp4，可選 BGM 混音
│   │
│   ├── providers/
│   │   ├── tts_edge.py              # Edge-TTS wrapper
│   │   ├── tts_fish.py              # Fish Speech HTTP client
│   │   ├── tts_kokoro.py            # Kokoro local wrapper（英文備用）
│   │   ├── image_none.py            # text overlay 生成（純 PIL/ffmpeg）
│   │   ├── image_comfyui.py         # ComfyUI HTTP client
│   │   └── image_runninghub.py      # RunningHub API client
│   │
│   └── templates/
│       ├── yt_intro_default.html    # 開場模板（Jinja2）
│       └── yt_outro_default.html    # 結尾模板（Jinja2）
│
└── output/
    ├── PPTPlaner_Package.zip
    ├── <run_id>/
    │   ├── clips/                   # per-slide mp4 clips（中間產物）
    │   ├── wav/                     # per-slide TTS 音檔
    │   ├── images/                  # per-slide 圖像
    │   └── video_progress.json      # checkpoint 狀態
    └── <source_name>_video.mp4      # 最終輸出
```

---

## 7. 開頭/結尾模板規格

模板為 HTML，由 playwright 截圖後生成 PNG 序列，ffmpeg 合成為定長 clip。

### `yt_intro_default.html` Jinja2 變數

| 變數 | 說明 | 範例 |
|------|------|------|
| `{{ channel_name }}` | 頻道名稱 | "認知科學解說" |
| `{{ tagline }}` | 副標語 | "每週更新" |
| `{{ logo_path }}` | Logo 路徑或空字串 | "" |
| `{{ video_title }}` | 本支影片標題 | "Chapter 5: 目擊者記憶" |
| `{{ duration_sec }}` | 開場時長（供 JS 動畫參考） | 8 |

### `yt_outro_default.html` Jinja2 變數

| 變數 | 說明 | 範例 |
|------|------|------|
| `{{ channel_name }}` | 頻道名稱 | "認知科學解說" |
| `{{ cta_text }}` | 行動呼籲 | "請按讚並訂閱！" |
| `{{ next_video_text }}` | 下支預告（可空） | "" |
| `{{ subscribe_hint }}` | 是否顯示訂閱動畫 | true |
| `{{ duration_sec }}` | 結尾時長 | 12 |

---

## 8. 實作階段規劃

### Phase 1：基礎管道 MVP（目標：端到端跑通）

核心：`edge-tts` + `image: none`（文字 overlay）+ `ffmpeg` + checkpoint

- [ ] `video/checkpoint.py`：checkpoint 讀寫、is_done/mark/mark_failed
- [ ] `video/progress.py`：CLI 進度輸出（含 ETA 估算）
- [ ] `video/providers/tts_edge.py`：Edge-TTS 生成 WAV
- [ ] `video/providers/image_none.py`：PIL 生成文字 overlay PNG
- [ ] `video/steps/step1_tts.py`：呼叫 tts provider
- [ ] `video/steps/step2_image.py`：呼叫 image provider
- [ ] `video/steps/step3_clip.py`：ffmpeg 合成 per-slide clip
- [ ] `video/steps/step4_bookend.py`：playwright 渲染 HTML → intro/outro clip
- [ ] `video/steps/step5_concat.py`：ffmpeg concat + BGM 混音
- [ ] `video/templates/yt_intro_default.html`：AI 設計草稿（使用者確認後）
- [ ] `video/templates/yt_outro_default.html`：AI 設計草稿
- [ ] `video/pipeline.py`：主控 loop，整合所有 steps
- [ ] `config.yaml`：新增 `video:` 區塊（預設 `enabled: false`）
- [ ] `scripts/orchestrate.py`：在 ZIP 步驟後呼叫 video pipeline

**Phase 1 最小依賴**（requirements-video.txt）：
```
edge-tts
Pillow
Jinja2
playwright
httpx
```
系統層：`ffmpeg`（需另行安裝）、`playwright install chromium`

### Phase 2：Fish Speech + AI 圖像整合

目標：本地高品質模式可用

- [ ] `video/providers/tts_fish.py`：Fish Speech HTTP client
- [ ] `video/providers/image_comfyui.py`：ComfyUI client
- [ ] `video/providers/image_runninghub.py`：RunningHub client
- [ ] 中文 image prompt 翻譯步驟（LLM 呼叫，zh-TW → EN prompt）
- [ ] Docker Compose 範例：Fish Speech server 一鍵啟動
- [ ] `config.yaml`：fish_speech / comfyui / runninghub 子區塊完整驗證

### Phase 3：YT 完整化

- [ ] 多種開結尾模板（極簡 / 科技感 / 暖色系）
- [ ] 字幕檔自動生成（`.srt`，與 WAV 時間軸同步）
- [ ] YT chapters 格式輸出（依 slides 章節自動生成）
- [ ] 影片縮圖自動生成（第一幀 + 頻道 Logo 疊合）
- [ ] AI 自動推薦 video config（分析 source 後預填，使用者點擊確認）

---

## 9. 依賴總覽

| 依賴 | 類型 | 安裝方式 | 必要性 |
|------|------|---------|--------|
| `edge-tts` | pip | `pip install edge-tts` | Phase 1 |
| `Pillow` | pip | `pip install Pillow` | Phase 1 |
| `Jinja2` | pip | `pip install Jinja2` | Phase 1（可能已有）|
| `playwright` | pip + chromium | `pip install playwright && playwright install chromium` | Phase 1 |
| `httpx` | pip | `pip install httpx` | Phase 2 |
| `ffmpeg` | 系統層 | 官網下載，加入 PATH | Phase 1 |
| Fish Speech | 外部 server | Docker 或本地安裝 | Phase 2，需 GPU |
| ComfyUI | 外部 server | 獨立安裝 | Phase 2，需 GPU |

**原則：core pipeline（slides + notes）不增加任何依賴。影片功能完全 optional。**

---

## 10. 風險與緩解

| 風險 | 嚴重度 | 緩解方式 |
|------|--------|---------|
| Fish Speech 授權限制商業使用 | 高 | 確認授權後再商業化；備案用 Edge-TTS |
| ffmpeg PATH 設定在 Windows 易出錯 | 中 | 啟動時 shutil.which("ffmpeg") 檢查，給友善錯誤訊息 |
| playwright chromium 下載慢 | 低 | 一次性安裝，後續快取 |
| Edge-TTS 網路請求被限速 | 低 | 加重試機制（已有 PPTPlaner retry 框架） |
| 長影片 concat 記憶體不足 | 低 | ffmpeg concat list file 方式（不 in-memory 合併） |
