# 打包快速開始

## 🚀 一鍵打包

### Windows

```powershell
# 方法 1: PowerShell (推薦)
.\build.ps1

# 方法 2: 批次檔
build.bat
```

執行後會在 `dist\mc-server-framework\` 生成執行檔。

## 📦 創建發佈包

打包完成後，執行：

```powershell
.\package.ps1
```

會在 `release\` 目錄生成完整的發佈 ZIP 檔案。

## 📝 詳細文檔

查看 [BUILD.md](BUILD.md) 了解完整的打包選項和常見問題。

## ✅ 測試執行檔

```powershell
cd dist\mc-server-framework
.\mc-server-framework.exe --help
```

## 📚 系統需求

- Windows 10/11 (64-bit)
- Python 3.8+ (僅開發時需要)
- PyInstaller 6.0+ (已在 requirements.txt 中)

最終用戶**不需要**安裝 Python！
