# MC Server Framework - PowerShell 啟動腳本
# 自動啟用虛擬環境並執行指令

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

if (-not (Test-Path "env\Scripts\Activate.ps1")) {
    Write-Host "錯誤: 找不到虛擬環境" -ForegroundColor Red
    Write-Host "請先執行: python -m venv env"
    Write-Host "然後執行: .\env\Scripts\Activate.ps1"
    Write-Host "最後執行: pip install -r requirements.txt"
    Read-Host "按 Enter 繼續"
    exit 1
}

& .\env\Scripts\Activate.ps1
python -m app.main $args
