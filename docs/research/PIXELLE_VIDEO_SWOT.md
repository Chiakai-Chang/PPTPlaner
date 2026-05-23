# Pixelle-Video SWOT 評估報告
> 研究日期：2026-05-23  
> Repo：https://github.com/AIDC-AI/Pixelle-Video  
> 評估人：AI 代理 (claude-sonnet-4-6)  
> 目的：評估是否能讓 PPTPlaner 進一步產出精美的解說影片（含 YT 開結尾客製化）

---

## 背景

PPTPlaner 目前 pipeline：
```
Source MD → Plan → Slides (SVG) → Notes (逐字稿 2~3 min/page) → Guide HTML → ZIP
```

期望新增：
```
Slides (SVG) + Notes (逐字稿) → 解說影片 (mp4)
├── 開頭：YT 頻道 Logo + 開場詞 (客製化)
├── 主體：每張投影片 + 旁白 TTS + AI 視覺效果
└── 結尾：YT 結語 + 訂閱 CTA (客製化)
```

---

## Pixelle-Video 技術概覽

| 面向 | 說明 |
|------|------|
| **核心流程** | Script → Image Planning → Frame TTS → Video Composition |
| **輸入模式** | AI 自動生成劇本 OR 直接輸入固定劇本（Fixed Script）|
| **TTS 引擎** | Edge-TTS、Index-TTS、聲音克隆 (voice cloning) |
| **影像生成** | ComfyUI 本地部署 OR RunningHub 雲端 API |
| **影像模型** | FLUX、WAN 2.1、Qwen Image 等 |
| **Video Compose** | ffmpeg + HTML 模板渲染（HTML → 影格 PNG） |
| **後端架構** | FastAPI RESTful API + Streamlit Web UI |
| **授權** | Apache 2.0 |
| **Config** | YAML (config.yaml) |
| **平台** | Python 3.10+, uv, Docker 支援 |

---

## SWOT 分析

### 優勢 (Strengths) — Pixelle-Video 本身具備的能力

| # | 優勢 | 對 PPTPlaner 的意義 |
|---|------|-------------------|
| S1 | **Fixed Script 模式** | 可直接餵入 PPTPlaner 的 `notes/` 逐字稿，跳過 AI 劇本生成 |
| S2 | **FastAPI REST API** | PPTPlaner 可用 HTTP 呼叫，無需 fork 或嵌入其程式碼 |
| S3 | **HTML 模板系統** | 自訂 YT 開頭/結尾模板，純 HTML/CSS 即可，技術門檻低 |
| S4 | **多種 TTS 支援** | Edge-TTS 免費可用，voice cloning 可匹配特定頻道聲線 |
| S5 | **Custom Media 支援** | 可上傳自訂圖片 — 投影片 SVG 轉 PNG 後可作為每幀背景 |
| S6 | **BGM 支援** | 內建背景音樂，可放置自訂 mp3 到 bgm/ |
| S7 | **Docker + Windows 套件** | 部署選項多元，使用者可按需求選擇 |
| S8 | **Apache 2.0** | 商業友善，可自由整合 |

### 劣勢 (Weaknesses) — 導入 PPTPlaner 的代價

| # | 劣勢 | 嚴重度 |
|---|------|--------|
| W1 | **重量級外部依賴**：ComfyUI 或 RunningHub API Key 為必要條件（影像生成） | 高 |
| W2 | **短影音設計假設**：每幀 1~3 句話，不是「一幀 = 一張投影片」 | 中 |
| W3 | **無原生 PPT/SVG 整合**：投影片需先轉 PNG 才能用作 Custom Media | 中 |
| W4 | **Streamlit UI 非 headless**：API server 需額外啟動，不是零額外程序 | 中 |
| W5 | **長影片效能未驗證**：PPTPlaner 一份文件可能產出 20+ 頁，總影片 30~60 分鐘 | 中 |
| W6 | **ffmpeg 系統依賴**：需要系統層安裝，非純 Python | 低（常見） |

### 機會 (Opportunities) — PPTPlaner 可利用之處

| # | 機會 | 實作方向 |
|---|------|---------|
| O1 | **逐字稿直接用作劇本** | Fixed Script 模式，每頁 notes 對應一段 script segment |
| O2 | **SVG 投影片 → PNG → 影格背景** | cairosvg 或 playwright 轉換，每頁對應一段影格畫面 |
| O3 | **YT 客製化模板** | 新增 `templates/yt_intro.html` 和 `templates/yt_outro.html` 靜態模板 |
| O4 | **config.yaml 擴展** | 新增 `video:` 區塊，控制開關、頻道名稱、開結尾詞、BGM、TTS 聲線 |
| O5 | **模組化後端切換** | Pixelle-Video API 作為 default，也可選用輕量替代方案（只 Edge-TTS + ffmpeg） |
| O6 | **批次生成** | PPTPlaner 每頁生成一個 clip，最後 ffmpeg concat 成完整影片 |

### 威脅 (Threats) — 潛在衝突與風險

| # | 威脅 | 應對 |
|---|------|------|
| T1 | **安裝複雜度打破 PPTPlaner 輕量原則** | 設為 optional，有 Pixelle-Video 才啟用，否則降級到基礎模式 |
| T2 | **上游 Pixelle-Video API 變動** | Pin 到特定版本，用 Docker Compose 固定環境 |
| T3 | **教育長影片 ≠ 短影音設計目標** | 每頁生成獨立 clip，再 concat，而非一次生成全片 |
| T4 | **ComfyUI 需要 GPU** | RunningHub 雲端替代方案，或降級到 static 模板（無 AI 圖） |

---

## TOWS 決策

### 結論：採用 **WO 策略** + 可選 SO 升級

**基礎模式（WO）**  
不依賴 Pixelle-Video，只用 Edge-TTS + ffmpeg + 靜態模板：
- 每頁 notes → Edge-TTS 生成 WAV
- 每頁 SVG → PNG（cairosvg）
- ffmpeg 將 PNG + WAV 合成 clip
- 開頭/結尾為靜態 HTML → PNG 幀
- concat 所有 clips → 最終 mp4

**進階模式（SO，可選）**  
安裝並啟動 Pixelle-Video API 服務：
- 使用 Pixelle-Video 的 AI 圖像生成（FLUX/Wan2.1）豐富每幀視覺
- 使用 voice cloning 保持特定聲線
- 透過 HTTP API 呼叫，PPTPlaner 仍為 orchestrator

### 策略邊界

```yaml
# config.yaml 新增區塊（預覽）
video:
  enabled: false          # 預設關閉，不影響現有使用者
  backend: "basic"        # basic (Edge-TTS+ffmpeg) | pixelle-video (API)
  pixelle_video_url: ""   # 進階模式才填
```

---

## 下一步

→ 詳見 [`VIDEO_PIPELINE_SPEC.md`](VIDEO_PIPELINE_SPEC.md) 規格文件  
→ 決策紀錄見 [`RATIONALE.md`](RATIONALE.md)
