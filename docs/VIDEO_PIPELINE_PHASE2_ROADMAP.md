# Video Pipeline Phase 2 — 高品質模式規劃

## 目標
支援 **Fish Speech**（高品質本地 TTS）與 **AI 圖像生成**（ComfyUI/RunningHub），讓使用者能產出專業級 YouTube 影片。

---

## 系統架構（Phase 2）

```
┌─────────────────────────────────────────────────────────────┐
│                    config.yaml                               │
│  video:                                                      │
│    tts:                                                       │
│      provider: "fish-speech"  ← 可切換                       │
│    image:                                                     │
│      provider: "comfyui"       ← 可切換                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Provider 抽象層                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ EdgeTTS      │  │ FishSpeech   │  │ KokoroTTS    │      │
│  │ (Phase 1)    │  │ (Phase 2)    │  │ (Future)     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ NoneImage    │  │ ComfyUIImage │  │ RunningHub   │      │
│  │ (Phase 1)    │  │ (Phase 2)    │  │ (Phase 2)    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    pipeline.py (不變)
                              │
                              ▼
                    輸出 mp4
```

---

## Phase 2 任務清單

### 前置需求
- [ ] Fish Speech Docker 環境驗證
- [ ] ComfyUI 環境驗證（可選，需 GPU 16GB+）
- [ ] RunningHub API key 測試

### 任務規劃

| 任務 | 說明 | 依賴 | 預估時間 |
|------|------|------|----------|
| T015 | TDD: `tts_fish.py` — Fish Speech HTTP client | T001 | 2h |
| T016 | TDD: `image_comfyui.py` — ComfyUI client | T001 | 3h |
| T017 | TDD: `image_runninghub.py` — RunningHub API | T001 | 2h |
| T018 | 中譯英 prompt 翻譯步驟 | T016, T017 | 1h |
| T019 | Docker Compose: Fish Speech 一鍵啟動 | 無 | 1h |
| T020 | config.yaml 驗證擴展 | T015-T017 | 1h |
| T021 | Phase 2 整合測試 | T015-T020 | 2h |

### 預估總時間：12-15 小時

---

## 技術細節

### Fish Speech API
```python
# 請求格式
POST http://localhost:8080/v1/audio/speech
{
    "model": "fish-speech-1.4",
    "input": "你好世界",
    "voice": "default",  # 或自訂聲線 ID
    "response_format": "wav",
    "speed": 1.0
}
```

### ComfyUI API
```python
# 提交工作流
POST http://localhost:8188/prompt
{
    "prompt": { workflow_id },
    "client_id": "unique_client_id"
}

# 輪詢結果
GET http://localhost:8188/history/{prompt_id}
```

---

## 授權注意事項

| 工具 | 授權 | 商業使用 |
|------|------|----------|
| Fish Speech | Fish Audio Research License | ⚠️ 需自行確認 |
| ComfyUI FLUX | 開源 | ✅ 可商業使用 |
| RunningHub | 按量計費 | ✅ 可商業使用 |

---

## Phase 2 進入條件

Phase 2 開始前需滿足：
1. Phase 1 整合測試通過 ✅
2. 使用者反饋 Phase 1 功能穩定 ✅
3. 有 GPU 環境或 RunningHub API key 可用 ✅
