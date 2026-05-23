# Video Pipeline Phase 1 — 完成報告

## 概述
Phase 1 完成了 PPTPlaner 的影片生成管道，支援從投影片 + 備忘稿自動產生 YouTube 格式影片。

## 系統架構

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  config.yaml │────▶│ orchestrate │────▶│  pipeline   │
└─────────────┘     │   .py       │     │   .py       │
                    └─────────────┘     └─────────────┘
                                              │
                    ┌─────────────────────────┼─────────────────────────┐
                    ▼                         ▼                         ▼
              ┌──────────┐              ┌──────────┐              ┌──────────┐
              │ Step 1:  │              │ Step 2:  │              │ Step 3:  │
              │    TTS    │────────────▶│   Image  │────────────▶│  Clip    │
              │  (edge)   │              │   (PIL)  │              │ (FFmpeg) │
              └──────────┘              └──────────┘              └──────────┘
                    │                         │                         │
                    └─────────────────────────┼─────────────────────────┘
                                              ▼
                                    ┌──────────────┐
                                    │  Intro/Outro │
                                    │  (TTS+PIL)   │
                                    └──────────────┘
                                              │
                                              ▼
                                    ┌──────────────┐
                                    │   Concat     │
                                    │   + BGM      │
                                    └──────────────┘
                                              │
                                              ▼
                                    ┌──────────────┐
                                    │  Final .mp4  │
                                    └──────────────┘
```

## 新增檔案清單

| 路徑 | 用途 | 測試 |
|------|------|------|
| `video/__init__.py` | Package marker | N/A |
| `video/constants.py` | 共用常數（1920x1080, 30fps） | N/A |
| `video/checkpoint.py` | 進度持久化（支援中斷恢復） | 11 tests |
| `video/progress.py` | CLI 進度輸出 | 6 tests |
| `video/pipeline.py` | 主流程管線 | 9 tests |
| `video/providers/__init__.py` | Package marker | N/A |
| `video/providers/base.py` | Provider ABC | N/A |
| `video/providers/tts_edge.py` | Edge TTS 實作 | 7 tests |
| `video/providers/image_none.py` | PIL 文字圖片實作 | 7 tests |
| `video/steps/__init__.py` | Package marker | N/A |
| `video/steps/step3_clip.py` | 單張投影片剪輯 | 5 tests |
| `video/steps/step4_bookend.py` | Intro/Outro 產生 | 4 tests |
| `video/steps/step5_concat.py` | 最終合併 + BGM | 6 tests |
| `video/templates/yt_intro_default.html` | Intro HTML 模板 | N/A |
| `video/templates/yt_outro_default.html` | Outro HTML 模板 | N/A |
| `tests/video/test_*.py` | 測試檔案 | 55 tests |

## 修改檔案清單

| 路徑 | 修改內容 |
|------|---------|
| `config.yaml` | 新增 `video:` 區段 |
| `scripts/orchestrate.py` | 新增 video pipeline hook |

## 設定檔範例

```yaml
video:
  enabled: true
  tts:
    provider: "edge-tts"
    edge_tts_voice: "zh-TW-HsiaoChenNeural"
    edge_tts_speed: "+0%"
  image:
    provider: "none"
    width: 1920
    height: 1080
  fps: 30
  bgm_file: null
  bgm_volume: 0.15
  intro:
    enabled: true
    text: "大家好，歡迎收看本期影片！"
    channel_name: "我的頻道"
    duration_sec: 8
  outro:
    enabled: true
    text: "感謝收看，歡迎訂閱！"
    channel_name: "我的頻道"
    duration_sec: 12
```

## 安裝需求

| 項目 | 安裝方式 | 說明 |
|------|---------|------|
| Python | 系統已安裝 | 3.14+ |
| edge-tts | `pip install edge-tts` | TTS 語音 |
| Pillow | `pip install Pillow` | 圖片生成 |
| ffmpeg | 系統安裝 | 影片處理 |

**不需要 Playwright** — Intro/Outro 使用 TTS + PIL，不依賴瀏覽器。

## 測試結果

- **55 通過** | **1 跳過**（整合測試需 ffmpeg）
- 覆蓋率：87-91%

## Phase 2 建議

1. 支援更多 TTS provider（Fish Speech）
2. 支援 AI 圖片生成（ComfyUI、Running Hub）
3. 動態字幕疊加
4. 進度條動畫
5. 影片預覽網頁
