<# 
PPTPlaner Windows 一鍵安裝與啟動腳本
- 需求：Windows 10/11、網路可連線、已啟用 winget（Windows Package Manager）
- 作用：
  1) 檢查/安裝 Python 3.11+
  2) 檢查/安裝 uv
  3) （可選）檢查/安裝 Git
  4) 使用 uv 建立虛擬環境並安裝必要套件
  5) 執行 orchestrate.py 產生 slides/ notes/ 指引.html
#>

param(
  [switch]$SkipGit,          # 加上 -SkipGit 可略過 Git 安裝
  [switch]$NoRun,            # 加上 -NoRun 只安裝環境，不執行 orchestrate
  [string]$PythonId = "Python.Python.3.11",   # winget Python 套件 ID（可改 3.x）
  [string]$GitId    = "Git.Git"               # winget Git 套件 ID
)

$ErrorActionPreference = "Stop"

function Write-Title($t) { Write-Host "`n== $t ==" -ForegroundColor Cyan }
function Write-Step($t)  { Write-Host " - $t" -ForegroundColor Yellow }
function Ok($t)          { Write-Host " ✓ $t" -ForegroundColor Green }
function Warn($t)        { Write-Host " ! $t" -ForegroundColor DarkYellow }
function Fail($t)        { Write-Host " ✗ $t" -ForegroundColor Red }

# 0) 檢查 winget
Write-Title "檢查 winget"
if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
  Fail "找不到 winget。請先安裝 Windows Package Manager 後重試（Microsoft Store 版 App Installer）。"
  Write-Host "文件： https://learn.microsoft.com/windows/package-manager/winget/" -ForegroundColor DarkGray
  exit 1
}
Ok "winget 可用"

# 1) 檢查 / 安裝 Python
Write-Title "檢查 / 安裝 Python 3.11+"
$pyOk = $false
try {
  $pyv = (& python --version) 2>$null
  if ($LASTEXITCODE -eq 0 -and $pyv) {
    Ok "已安裝 $pyv"
    $pyOk = $true
  }
} catch {}

if (-not $pyOk) {
  Write-Step "透過 winget 安裝 $PythonId（需數分鐘）"
  winget install -e --id $PythonId --source winget --accept-package-agreements --accept-source-agreements
  Start-Sleep -Seconds 3
  # 重新載入環境變數（新開殼層最保險）
  $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
  try {
    $pyv = (& python --version)
    Ok "Python 安裝完成：$pyv"
  } catch {
    Warn "Python 可能剛安裝，請關閉並重新開啟 PowerShell 後再執行本腳本。"
    exit 1
  }
}

# 2) 檢查 / 安裝 uv（優先 winget，失敗則官方安裝指令）
Write-Title "檢查 / 安裝 uv"
$uvOk = $false
try {
  $uvv = (& uv --version) 2>$null
  if ($LASTEXITCODE -eq 0) { Ok "已安裝 uv：$uvv"; $uvOk = $true }
} catch {}

if (-not $uvOk) {
  Write-Step "嘗試透過 winget 安裝 uv"
  try {
    # 一些發行版是 astral-sh.uv；若此 ID 失敗，可自動嘗試 astral.uv
    $uvIds = @("astral-sh.uv","astral.uv")
    $installed = $false
    foreach ($id in $uvIds) {
      try {
        winget install -e --id $id --source winget --accept-package-agreements --accept-source-agreements
        $installed = $true; break
      } catch {}
    }
    if (-not $installed) { throw "winget 安裝 uv 失敗" }
    $uvv = (& uv --version)
    Ok "uv 安裝完成：$uvv"
    $uvOk = $true
  } catch {
    Warn "winget 安裝 uv 失敗，改用官方安裝指令"
    try {
      # 官方文件建議指令（PowerShell）：
      # PS> powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
      powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
      $uvv = (& uv --version)
      Ok "uv 安裝完成：$uvv"
      $uvOk = $true
    } catch {
      Fail "安裝 uv 失敗。請參考官方文件後重試。"
      Write-Host "文件： https://docs.astral.sh/uv/" -ForegroundColor DarkGray
      exit 1
    }
  }
}

# 3) 檢查 / 安裝 Git（可略過）
if (-not $SkipGit) {
  Write-Title "檢查 / 安裝 Git（可跳過：-SkipGit）"
  $gitOk = $false
  try {
    $gitv = (& git --version) 2>$null
    if ($LASTEXITCODE -eq 0) { Ok "已安裝 $gitv"; $gitOk = $true }
  } catch {}
  if (-not $gitOk) {
    Write-Step "透過 winget 安裝 $GitId"
    winget install -e --id $GitId --source winget --accept-package-agreements --accept-source-agreements
    Start-Sleep -Seconds 2
    try {
      $gitv = (& git --version)
      Ok "Git 安裝完成：$gitv"
    } catch {
      Warn "Git 可能剛安裝，若無法使用請重新開啟終端機。"
    }
  }
}

# 4) 以 uv 建立虛擬環境並安裝必要套件
Write-Title "建立虛擬環境（.venv）並安裝套件"
if (-not (Test-Path ".venv")) {
  Write-Step "建立 .venv"
  uv venv .venv
  Ok "虛擬環境建立完成"
} else {
  Ok ".venv 已存在"
}

Write-Step "安裝必要套件：pyyaml、jinja2"
# 使用 uv 的 pip 介面安裝
uv pip install pyyaml jinja2
Ok "套件安裝完成"

# 5) 執行 orchestrate.py（可用 -NoRun 略過）
if (-not $NoRun) {
  Write-Title "執行 orchestrate.py（自動生成 slides/、notes/ 與 指引.html）"
  if (-not (Test-Path "scripts/orchestrate.py")) {
    Fail "找不到 scripts/orchestrate.py，請確認你在 repo 根目錄執行。"
    exit 1
  }
  # 以虛擬環境 Python 執行
  $py = Join-Path ".venv\Scripts" "python.exe"
  & $py "scripts/orchestrate.py"
  if ($LASTEXITCODE -eq 0) {
    Ok "已完成！請查看 指引.html、slides/、notes/"
  } else {
    Warn "主流程執行非 0 結束碼，請檢查終端輸出訊息。"
  }
} else {
  Warn "你使用了 -NoRun，已完成環境設定但未執行 orchestrate。"
}

Write-Host "`n完成。若剛安裝過 Python/uv/Git，開新視窗可確保路徑生效。" -ForegroundColor Cyan
