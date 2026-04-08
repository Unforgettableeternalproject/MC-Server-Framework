@echo off
REM MC Server Framework - 便利啟動腳本
REM 自動啟用虛擬環境並執行指令

cd /d "%~dp0"

if not exist "env\Scripts\activate.bat" (
    echo 錯誤: 找不到虛擬環境
    echo 請先執行: python -m venv env
    echo 然後執行: env\Scripts\activate.bat
    echo 最後執行: pip install -r requirements.txt
    pause
    exit /b 1
)

call env\Scripts\activate.bat
python -m app.main %*
