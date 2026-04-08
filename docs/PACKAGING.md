# MC Server Framework - 打包與分發指南

本文檔說明如何將框架打包成獨立的 CLI 工具，方便在其他電腦上使用。

## 📦 打包方式

### 方式一：PyInstaller 打包成 .exe（推薦）

將整個框架打包成單一可執行檔，不需要 Python 環境即可使用。

#### 1. 安裝 PyInstaller

```powershell
.\env\Scripts\Activate.ps1
pip install pyinstaller
```

#### 2. 建立打包腳本

已提供 `build.py` 和 `mc-host.spec` 配置檔。

#### 3. 執行打包

```powershell
.\env\Scripts\Activate.ps1
python build.py
```

#### 4. 輸出位置

打包完成後，可執行檔位於：
```
dist/mc-host.exe
```

#### 5. 使用方式

```powershell
# 不需要 Python 環境！
mc-host.exe scan
mc-host.exe start my-server
mc-host.exe dns update my-server
```

### 方式二：Python 套件安裝

將框架安裝成系統級 Python 套件，使用 `mc-host` 命令。

#### 1. 安裝

```powershell
# 在專案根目錄
.\env\Scripts\Activate.ps1
pip install -e .
```

#### 2. 使用

```powershell
mc-host scan
mc-host start my-server
mc-host dns update my-server
```

### 方式三：便攜版（ZIP 打包）

打包整個專案資料夾，包含虛擬環境。

#### 1. 建立便攜版

```powershell
# 執行打包腳本
.\create-portable.ps1
```

#### 2. 輸出

會產生 `mc-host-portable.zip`，包含：
- 所有程式碼
- 虛擬環境
- 啟動腳本

#### 3. 在其他電腦使用

1. 解壓縮
2. 執行 `mc-host.bat` 或 `mc-host.ps1`

## 🚀 快速開始（使用者視角）

### 使用 .exe 版本

```powershell
# 1. 下載並解壓縮
# 2. 初始化配置
mc-host.exe init-config

# 3. 設定 Java
# 編輯 config/java_registry.yml

# 4. 建立伺服器
mc-host.exe init my-server

# 5. 啟動
mc-host.exe start my-server
```

## 📋 分發清單

打包時應包含的檔案：

### 最小版本（僅 .exe）
```
mc-host.exe          # 主程式
README.md            # 使用說明
LICENSE              # 授權
```

### 完整版本
```
mc-host.exe
config/
  java_registry.yml  # Java 設定範本
  app.yml            # 全域設定範本
templates/
  default_server.yml # 伺服器範本
docs/
  DNS-SETUP.md       # DNS 設定指南
  SPEC.md            # 完整規格
README.md
LICENSE
```

## 🔧 設定檔管理

### 打包後的設定檔位置

使用 .exe 版本時，設定檔會放在：
```
C:\Users\<USER>\AppData\Local\MC-Server-Framework\
  config/
  servers/
  logs/
```

或在可執行檔同目錄（便攜模式）。

### 便攜模式 vs 安裝模式

**便攜模式**（預設）：
- 設定和伺服器資料在程式目錄
- 適合 USB 隨身碟使用
- 換電腦時整個資料夾複製即可

**安裝模式**：
- 設定在使用者目錄
- 符合 Windows 規範
- 多使用者各自獨立

## 🎯 打包最佳實踐

### 1. 版本號管理

在 `app/__init__.py` 設定版本號：
```python
__version__ = "0.1.0"
```

### 2. 圖示設定

準備圖示檔案：
```
assets/icon.ico
```

### 3. 排除不必要的檔案

`.spec` 檔案中已設定排除：
- `__pycache__`
- `.git`
- `env/`
- `.vscode/`
- 測試檔案

### 4. 包含資料檔案

確保包含：
- 設定檔範本
- 文檔
- 授權

## 🔐 授權與發布

### 建議授權

專案目前使用 MIT License，適合開源分發。

### GitHub Release

1. 建立 Tag：`git tag v0.1.0`
2. 推送：`git push origin v0.1.0`
3. 在 GitHub 建立 Release
4. 上傳 `mc-host.exe` 和文檔

### 版本命名

```
v0.1.0-alpha    # 早期測試版
v0.1.0-beta     # 功能測試版
v1.0.0          # 正式版
```

## 📊 效能優化

### 減少執行檔大小

```powershell
# 使用 UPX 壓縮
pyinstaller --onefile --upx-dir=C:\upx mc-host.spec
```

### 加速啟動

```python
# 在 main.py 延遲載入大型模組
import importlib
```

## 🐛 除錯打包問題

### 問題：找不到模組

檢查 `.spec` 檔案的 `hiddenimports`：
```python
hiddenimports=['yaml', 'requests', 'typer']
```

### 問題：執行檔過大

排除不必要的套件：
```python
excludes=['tkinter', 'matplotlib']
```

### 問題：殺毒軟體誤報

使用程式碼簽章或提交到 VirusTotal。

## 📝 更新日誌

打包時應包含 `CHANGELOG.md`：
```markdown
# Changelog

## [0.1.0] - 2026-04-08
### Added
- 初始版本
- 支援 Forge 1.17+ 伺服器
- Cloudflare DNS 整合
- 自動備份功能
```

## 🌐 多語言支援（未來）

準備 i18n 結構：
```
locales/
  zh-TW/
    messages.json
  en-US/
    messages.json
```

## 🔄 自動更新（未來）

實作自動更新檢查：
```python
# 檢查 GitHub Releases
check_for_updates()
```

---

**重要提醒**：
- 打包前先在本機測試所有功能
- 確保 Java registry 範本路徑正確
- 測試 DNS 功能是否正常
- 檢查設定檔是否正確複製
