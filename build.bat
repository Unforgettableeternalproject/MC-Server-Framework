@echo off
REM MC Server Framework - 打包腳本 (批次檔)
REM 此腳本會調用 PowerShell 打包腳本

echo ==============================================================
echo     MC Server Framework - 應用程式打包工具
echo ==============================================================
echo.

REM 檢查 PowerShell
where powershell >nul 2>&1
if %errorlevel% neq 0 (
    echo [錯誤] 找不到 PowerShell
    echo 請安裝 PowerShell 或直接使用 build.ps1
    pause
    exit /b 1
)

REM 執行 PowerShell 腳本
powershell -ExecutionPolicy Bypass -File ".\build.ps1"

if %errorlevel% neq 0 (
    echo.
    echo [錯誤] 打包失敗
    pause
    exit /b 1
)

pause
