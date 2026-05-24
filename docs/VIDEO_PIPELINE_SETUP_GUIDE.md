# Video Pipeline Phase 2 — 環境設定指南

## 快速檢查

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

---

## 情境一：你有 GPU + Docker ✅ (最佳設定)

### 1. 安裝 Python 套件
```bash
pip install httpx
```

### 2. 啟動服務
```bash
# 啟動 Fish Speech + ComfyUI
docker compose -f docker-compose.video.yml up -d

# 等待服務就緒 (約 1-2 分鐘)
docker compose -f docker-compose.video.yml ps
```

### 3. 設定 config.yaml
```yaml
video:
  enabled: true
  tts:
    provider: "fish-speech"
    fish_speech_url: "http://localhost:8080"
  image:
    provider: "comfyui"
    comfyui_url: "http://localhost:8188"
```

### 4. 驗證
```bash
# 測試 TTS
curl http://localhost:8080/health

# 測試 ComfyUI
curl http://localhost:8188
```

---

## 情境二：有 GPU 但無 Docker

### 方案 A：安裝 Docker（推薦）
1. 下載 Docker Desktop：https://www.docker.com/products/docker-desktop/
2. 安裝後重開機
3. 回到「情境一」

### 方案 B：本地安裝 Fish Speech
```bash
# 1. 克隆 Fish Speech
git clone https://github.com/fishaudio/fish-speech.git
cd fish-speech

# 2. 安裝依賴
pip install -e .

# 3. 下載模型
python scripts/download_models.py

# 4. 啟動 API
python api.py --host 0.0.0.0 --port 8080
```

### 方案 C：只用 Edge-TTS（不需 GPU）
```yaml
video:
  enabled: true
  tts:
    provider: "edge-tts"
  image:
    provider: "none"  # 文字 overlay
```

---

## 情境三：無 GPU

### 方案 A：使用 RunningHub 雲端 API
```bash
# 1. 申請 API Key: https://www.runninghub.cn/

# 2. 安裝 httpx
pip install httpx

# 3. 設定 config.yaml
video:
  enabled: true
  tts:
    provider: "edge-tts"
  image:
    provider: "runninghub"
    runninghub_api_key: "你的 API Key"
    runninghub_workflow: "image_flux.json"
```

### 方案 B：純文字 overlay（最簡單）
```yaml
video:
  enabled: true
  tts:
    provider: "edge-tts"
  image:
    provider: "none"
```

---

## 常見問題

### Q: Docker 無法啟動 GPU
```
error: could not select device driver "nvidia"
```
**解法**：
```bash
# 檢查 NVIDIA Container Toolkit
docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi

# 如果失敗，安裝 NVIDIA Container Toolkit
# Windows: Docker Desktop → Settings → General → Use WSL 2
# Linux: sudo apt install nvidia-container-toolkit
```

### Q: Fish Speech 啟動後立即關閉
```bash
# 查看日誌
docker compose -f docker-compose.video.yml logs fish-speech

# 常見原因：
# 1. VRAM 不足（需要至少 8GB）
# 2. 模型下載中（需要等待）
```

### Q: ComfyUI 記憶體不足
```bash
# 限制模型數量
docker compose -f docker-compose.video.yml config
# 修改 volumes，定期清理不用的模型
```

---

## 資源需求

| 服務 | 最低 VRAM | 推薦 VRAM | 硬碟空間 |
|------|-----------|-----------|----------|
| Fish Speech | 4GB | 8GB | 10GB |
| ComfyUI + FLUX | 8GB | 16GB | 20GB |
| 兩者同時 | 12GB | 16GB+ | 30GB |

---

## 自動啟動腳本（Windows）

```batch
@echo off
REM start_video_services.bat
echo Starting PPTPlaner video services...

docker compose -f docker-compose.video.yml up -d

echo Waiting for services to start...
timeout /t 60

docker compose -f docker-compose.video.yml ps

echo Services ready!
pause
```

---

## 故障排除流程

```
服務無法啟動
    │
    ├── Docker 沒開？ → 啟動 Docker Desktop
    │
    ├── GPU 不可用？ → 檢查 nvidia-smi
    │
    ├── 記憶體不足？ → 關閉其他 GPU 應用
    │
    └── 端口衝突？ → 更換 port 設定
```
