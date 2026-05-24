# 📚 PPTPlaner 影片功能文件索引

## 🎯 快速導覽

| 我想知道... | 請查看... |
|-------------|-----------|
| 如何快速開始 | [QUICKSTART.md](../QUICKSTART.md) |
| 如何設定環境 | [設定指南](VIDEO_PIPELINE_SETUP_GUIDE.md) |
| 工作流程說明 | [工作流程](VIDEO_PIPELINE_WORKFLOW.md) |
| 系統架構 | [架構文件](ARCHITECTURE_VIDEO.md) |
| Phase 1 完成報告 | [Phase 1 摘要](VIDEO_PIPELINE_PHASE1_SUMMARY.md) |
| Phase 2 任務規劃 | [Phase 2 路線圖](VIDEO_PIPELINE_PHASE2_ROADMAP.md) |
| 最終完成報告 | [最終摘要](VIDEO_PIPELINE_FINAL_SUMMARY.md) |

---

## 📋 功能清單

### Phase 1 ✅ 已完成
- [x] Edge-TTS 語音生成
- [x] 文字 overlay 圖像
- [x] 影片剪輯合成
- [x] Intro/Outro 生成
- [x] 最終影片合併
- [x] 斷點續傳
- [x] 進度顯示

### Phase 2 ✅ 已完成
- [x] Fish Speech TTS Provider
- [x] ComfyUI Image Provider
- [x] RunningHub Image Provider
- [x] 中譯英 Prompt 翻譯
- [x] Config 驗證
- [x] Phase 2 整合測試

---

## 🎬 使用流程

```
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│   環境檢查           │───▶│   簡報生成          │───▶│   影片生成          │
│                     │    │                     │    │                     │
│  python scripts/    │    │  python scripts/    │    │  python scripts/    │
│  check_video_env.py │    │  orchestrate.py     │    │  video_pipeline.py  │
└─────────────────────┘    └─────────────────────┘    └─────────────────────┘
```

---

## 🛠️ 技術文件

| 類別 | 文件 | 位置 |
|------|------|------|
| API 參考 | Provider 介面 | `video/providers/base.py` |
| 配置參考 | 配置範本 | `config.yaml.example` |
| 測試套件 | 單元測試 | `tests/video/` |
| 整合測試 | Pipeline 測試 | `tests/video/test_phase2_integration.py` |

---

## ❓ 常見問題

### 安裝與配置
- **FFmpeg 安裝**：[設定指南](VIDEO_PIPELINE_SETUP_GUIDE.md#情境二有-gpu-但無-docker)
- **Docker 配置**：[設定指南](VIDEO_PIPELINE_SETUP_GUIDE.md#情境一你有-gpu--docker-)

### 使用問題
- **影片生成失敗**：[工作流程](VIDEO_PIPELINE_WORKFLOW.md#故障排除)
- **GPU 記憶體不足**：[設定指南](VIDEO_PIPELINE_SETUP_GUIDE.md#常見問題)

---

## 📞 支援

- **GitHub Issues**：https://github.com/Chiakai-Chang/PPTPlaner/issues
- **文件問題**：請提交 PR 或直接開啟 Issue
