# PPTPlaner - 快速安裝腳本 (PowerShell)
# 適用於 Windows 10/11

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  PPTPlaner - AI 簡報規劃器 安裝精靈" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 檢查 Python
Write-Host "[1/4] 檢查 Python..." -ForegroundColor Yellow
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    Write-Host "❌ 未找到 Python，請先安裝 Python 3.12+" -ForegroundColor Red
    Write-Host "   下載網址: https://www.python.org/downloads/" -ForegroundColor Gray
    exit 1
}
Write-Host "✅ Python 已安裝: $($python.Source)" -ForegroundColor Green

# 檢查 FFmpeg (可選)
Write-Host ""
Write-Host "[2/4] 檢查 FFmpeg (影片生成需要)..." -ForegroundColor Yellow
$ffmpeg = Get-Command ffmpeg -ErrorAction SilentlyContinue
if (-not $ffmpeg) {
    Write-Host "⚠️  FFmpeg 未安裝 - 影片生成將不可用" -ForegroundColor Yellow
    Write-Host "   如需影片功能，請安裝: https://ffmpeg.org/download.html" -ForegroundColor Gray
} else {
    Write-Host "✅ FFmpeg 已安裝" -ForegroundColor Green
}

# 安裝 Python 套件
Write-Host ""
Write-Host "[3/4] 安裝 Python 套件..." -ForegroundColor Yellow
pip install edge-tts Pillow httpx --quiet

Write-Host "✅ 套件安裝完成" -ForegroundColor Green

# 建立 config.yaml (如果不存在)
Write-Host ""
Write-Host "[4/4] 檢查 config.yaml..." -ForegroundColor Yellow
if (-not (Test-Path "config.yaml")) {
    Write-Host "⚠️  未找到 config.yaml，複製範本..." -ForegroundColor Yellow
    if (Test-Path "config.yaml.example") {
        Copy-Item "config.yaml.example" "config.yaml"
        Write-Host "✅ 已建立 config.yaml 從範本" -ForegroundColor Green
    } else {
        Write-Host "❌ 未找到 config.yaml.example，請手動建立" -ForegroundColor Red
    }
} else {
    Write-Host "✅ config.yaml 已存在" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  安裝完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "快速開始:" -ForegroundColor Cyan
Write-Host "  python scripts/orchestrate.py --source 你的文件.md" -ForegroundColor White
Write-Host ""
Write-Host "如需更多幫助:" -ForegroundColor Cyan
Write-Host "  查看 docs/VIDEO_PIPELINE_INDEX.md" -ForegroundColor White
Write-Host ""
