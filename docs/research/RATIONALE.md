# 研究決策紀錄 (Research Rationale Log)
> 此檔案記錄每次外部 repo 研究的決策，包含導入、放棄、或部分採用的理由。

---

## [2026-05-23] Pixelle-Video 評估

**Repo**：https://github.com/AIDC-AI/Pixelle-Video  
**評估文件**：[PIXELLE_VIDEO_SWOT.md](PIXELLE_VIDEO_SWOT.md)  
**規格文件**：[VIDEO_PIPELINE_SPEC.md](VIDEO_PIPELINE_SPEC.md)

### 研究問題

PPTPlaner 已能穩定產出高品質投影片 (SVG) + 逐字稿 (md)。  
評估 Pixelle-Video 是否能作為下游工具，將以上輸出轉化為精美的 YT 解說影片，含客製化開場/結尾。

### 決策：部分採用（WO 策略）

**採用什麼**：
- Pixelle-Video 的**流程概念**（Script → Frame → TTS → Video → Concat）
- 其**HTML 模板系統**設計思路（YT intro/outro 用靜態 HTML 模板渲染）
- 其**Fixed Script 模式**確認逐字稿可直接作為 TTS 輸入
- 其**FastAPI API 架構**作為進階模式後端呼叫介面

**不採用什麼（及原因）**：
- 不嵌入 Pixelle-Video 原始碼（避免耦合與維護負擔）
- 不強制要求 ComfyUI/RunningHub（違反 PPTPlaner 輕量原則）
- 不用 Pixelle-Video 的 Streamlit UI（PPTPlaner 是 CLI/orchestrator 驅動，不需 Web UI）

**做了哪些調整**：
- 設計兩層後端架構：`basic`（Edge-TTS + ffmpeg，無需額外服務）vs `pixelle-video`（API 整合，可選）
- 所有影片功能預設 `video.enabled: false`，不影響現有使用者
- YT 開結尾模板作為 PPTPlaner 自己的 `video/templates/` 資源，不依賴 Pixelle-Video 模板

### 風險備注

- Pixelle-Video 設計目標為短影音（1~5 分鐘），PPTPlaner 教育影片可能 30~60 分鐘 — 已透過「per-clip 生成再 concat」策略規避
- cairosvg 在 Windows 上需要 GTK/Cairo 系統庫安裝，可能有門檻 — Phase 1 驗證後決定是否改用 playwright
- Pixelle-Video API 與 PPTPlaner 整合的 Phase 2 實作時，需 pin 版本防止上游 breaking changes

### 下一步

~~1. 使用者確認 VIDEO_PIPELINE_SPEC.md 的待決策事項（D1~D5）~~ → **已確認，見下方**  
2. 開始 Phase 1 實作（basic 模式 MVP）  
3. Phase 1 驗收通過後，評估是否推進 Phase 2（Fish Speech + ComfyUI 整合）

---

## [2026-05-23] D1~D5 決策確認 + SVG 放棄

**觸發**：使用者確認所有分析建議

### 決策清單

| 決策 | 內容 |
|------|------|
| SVG 輸出放棄 | SVG 品質差，影片視覺改由 AI 圖像或文字 overlay 取代 |
| D1：SVG→PNG 工具 | playwright（cairosvg 因 Windows GTK 門檻放棄） |
| D2：Phase 順序 | basic MVP 先行，Pixelle-Video 整合為 Phase 2 |
| D3：模板設計 | AI 設計草稿 → 使用者點擊確認，不手動撰寫 |
| D4：多語言 | 繁中優先；英文 TTS 為 Phase 3 |
| D5：TTS 分段 | 整頁 notes 為一段，未來可加 LLM 智慧拆幀 |
| 執行模式 | 依序（sequential），不並行；整夜跑可接受 |
| 可靠性核心 | checkpoint 機制（video_progress.json），斷點可續傳 |

---

## [2026-05-23] Fish Speech TTS 評估

**Repo**：https://github.com/fishaudio/fish-speech

### 研究問題

繁中本地 TTS 缺口：Kokoro 英文限定，XTTS-v2 繁中品質差。Fish Speech 是否能填補？

### 決策：Phase 2 採用（需 GPU），Phase 1 用 Edge-TTS

**採用什麼**：
- Fish Speech HTTP Server 模式作為 `tts_fish` provider（Phase 2）
- 聲音克隆能力（10~30 秒參考音）對 YT 頻道一致聲線有高價值
- 80+ 語言（含繁中 Tier 1）解決多語言 Phase 3 需求

**不採用什麼（及原因）**：
- Phase 1 不用：需要 16GB+ VRAM，不符合 MVP 零 GPU 需求
- 不嵌入其程式碼：透過 HTTP server 呼叫，保持解耦

**風險**：
- **授權為 Fish Audio Research License（非開源）**，商業化 YT 頻道使用前須自行確認
- 4B 模型需要 16GB VRAM 舒適執行
- 備案：Edge-TTS（繁中品質亦佳，依賴 Microsoft 網路服務）
