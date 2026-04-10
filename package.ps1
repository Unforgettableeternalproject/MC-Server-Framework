# MC Server Framework - 發佈打包腳本
# 此腳本會將編譯好的執行檔打包成發佈用的 ZIP 檔案

param(
    [string]$Version = "v0.2.0",
    [switch]$IncludeSource = $false
)

Write-Host "==============================================================" -ForegroundColor Cyan
Write-Host "    MC Server Framework - 發佈打包工具" -ForegroundColor Cyan
Write-Host "==============================================================" -ForegroundColor Cyan
Write-Host ""

# 檢查 dist 目錄
if (-not (Test-Path ".\dist\mc-server-framework")) {
    Write-Host "❌ 找不到編譯輸出" -ForegroundColor Red
    Write-Host "請先執行 build.ps1 打包應用程式" -ForegroundColor Yellow
    exit 1
}

# 創建發佈目錄
$releaseDir = ".\release"
if (-not (Test-Path $releaseDir)) {
    New-Item -ItemType Directory -Path $releaseDir | Out-Null
    Write-Host "✓ 創建發佈目錄: $releaseDir" -ForegroundColor Green
}

# 創建暫存目錄
$tempDir = ".\release\temp"
if (Test-Path $tempDir) {
    Remove-Item -Recurse -Force $tempDir
}
New-Item -ItemType Directory -Path $tempDir | Out-Null

Write-Host "準備發佈檔案..." -ForegroundColor Cyan

# 複製執行檔
Write-Host "  複製執行檔..." -ForegroundColor White
Copy-Item -Recurse ".\dist\mc-server-framework\*" "$tempDir\"

# 創建必要的目錄結構
Write-Host "  創建目錄結構..." -ForegroundColor White
@("config", "servers", "logs", "templates") | ForEach-Object {
    $dir = "$tempDir\$_"
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir | Out-Null
    }
}

# 複製文檔
Write-Host "  複製文檔..." -ForegroundColor White
if (Test-Path ".\README.md") {
    Copy-Item ".\README.md" "$tempDir\"
}
if (Test-Path ".\LICENSE") {
    Copy-Item ".\LICENSE" "$tempDir\"
}

# 創建使用說明
Write-Host "  創建使用說明..." -ForegroundColor White
$readmeContent = @"
================================================================================
          MC Server Framework - Minecraft 伺服器管理框架
================================================================================

版本: $Version
發佈日期: $(Get-Date -Format "yyyy-MM-dd")

--------------------------------------------------------------------------------
📦 安裝說明
--------------------------------------------------------------------------------

1. 解壓縮此 ZIP 檔案到任意目錄
2. 執行 mc-server-framework.exe
3. 框架會自動初始化並創建必要的配置文件

首次執行後會生成：
  - config/app.yml           全域配置
  - config/java_registry.yml Java 版本註冊表
  - templates/               配置模板
  - GETTING_STARTED.txt      詳細入門指南

--------------------------------------------------------------------------------
🚀 快速開始
--------------------------------------------------------------------------------

1. 註冊 Java 版本（編輯 config/java_registry.yml）
2. 在 servers/ 目錄下放置您的伺服器
3. 執行以下命令：

   # 查看所有伺服器
   mc-server-framework.exe scan

   # 啟動伺服器
   mc-server-framework.exe start <伺服器名稱>

   # 互動式選單
   mc-server-framework.exe

--------------------------------------------------------------------------------
📚 常用命令
--------------------------------------------------------------------------------

伺服器管理:
  mc-server-framework.exe scan              掃描所有伺服器
  mc-server-framework.exe start <name>      啟動伺服器
  mc-server-framework.exe stop <name>       停止伺服器
  mc-server-framework.exe status <name>     查看狀態

系統工具:
  mc-server-framework.exe info              查看完整說明
  mc-server-framework.exe check             系統診斷
  mc-server-framework.exe setup             重新初始化

詳細文檔:
  mc-server-framework.exe --help            查看所有命令

--------------------------------------------------------------------------------
⚙️  系統需求
--------------------------------------------------------------------------------

- Windows 10/11 (64-bit)
- 至少 4GB RAM
- Java 8/17/21（根據 Minecraft 版本）

--------------------------------------------------------------------------------
🔧 配置文件位置
--------------------------------------------------------------------------------

配置目錄: .\config\
  - app.yml                 全域配置（API tokens、路徑等）
  - java_registry.yml       Java 安裝路徑註冊表

伺服器目錄: .\servers\
  每個伺服器需要一個 server.yml 配置文件

--------------------------------------------------------------------------------
❓ 常見問題
--------------------------------------------------------------------------------

Q: 執行時出現「找不到 VCRUNTIME140.dll」
A: 下載並安裝 Visual C++ Redistributable:
   https://aka.ms/vs/17/release/vc_redist.x64.exe

Q: 如何配置 PlayIt.gg 隧道？
A: 1. 下載 PlayIt agent: https://playit.gg/download
   2. 在 config/app.yml 設定執行檔路徑
   3. 在伺服器的 server.yml 啟用隧道功能

Q: 如何配置 Cloudflare DNS？
A: 在 config/app.yml 設定 API token 和 zone ID
   詳見 GETTING_STARTED.txt

--------------------------------------------------------------------------------
📞 支援
--------------------------------------------------------------------------------

GitHub: https://github.com/Unforgettableeternalproject/MC-Server-Framework
文檔: 執行 mc-server-framework.exe info

--------------------------------------------------------------------------------

祝您使用愉快！🎮

================================================================================
"@

$readmeContent | Out-File -FilePath "$tempDir\使用說明.txt" -Encoding UTF8

# 創建發佈 ZIP
$zipName = "MC-Server-Framework-$Version-Windows-x64.zip"
$zipPath = "$releaseDir\$zipName"

Write-Host ""
Write-Host "打包發佈檔案..." -ForegroundColor Cyan

if (Test-Path $zipPath) {
    Remove-Item $zipPath
}

# 使用 PowerShell 5.1+ 的壓縮功能
Compress-Archive -Path "$tempDir\*" -DestinationPath $zipPath -CompressionLevel Optimal

# 清理暫存目錄
Remove-Item -Recurse -Force $tempDir

# 顯示結果
Write-Host ""
Write-Host "==============================================================" -ForegroundColor Green
Write-Host "    ✓ 發佈打包完成！" -ForegroundColor Green
Write-Host "==============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "發佈檔案: " -NoNewline
Write-Host "$zipPath" -ForegroundColor Yellow
Write-Host ""

# 顯示檔案大小
if (Test-Path $zipPath) {
    $size = (Get-Item $zipPath).Length / 1MB
    Write-Host "檔案大小: " -NoNewline
    Write-Host "$([math]::Round($size, 2)) MB" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "此發佈包包含:" -ForegroundColor Cyan
Write-Host "  ✓ 獨立執行檔（無需安裝 Python）" -ForegroundColor White
Write-Host "  ✓ 預建立的目錄結構" -ForegroundColor White
Write-Host "  ✓ 使用說明文件" -ForegroundColor White
Write-Host "  ✓ 配置模板" -ForegroundColor White
Write-Host ""
Write-Host "可直接分發給最終用戶使用！" -ForegroundColor Green
Write-Host ""
