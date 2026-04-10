# MC Server Framework - 應用程式打包指南

本文檔說明如何將 MC Server Framework 打包成獨立的 Windows 應用程式。

## 目錄

- [環境準備](#環境準備)
- [快速打包](#快速打包)
- [進階配置](#進階配置)
- [發佈流程](#發佈流程)
- [常見問題](#常見問題)

---

## 環境準備

### 1. Python 環境

確保已安裝 Python 3.8 或更高版本：

```powershell
python --version
```

### 2. 安裝依賴

```powershell
# 啟動虛擬環境
.\env\Scripts\Activate

# 安裝所有依賴（包括 PyInstaller）
pip install -r requirements.txt
pip install pyinstaller
```

### 3. 驗證環境

```powershell
# 測試程式能正常運行
python -m app.main --help
```

---

## 快速打包

### 方法 1: 使用 PowerShell 腳本（推薦）

```powershell
# 執行打包腳本
.\build.ps1
```

腳本會自動：
- ✅ 檢查並啟動虛擬環境
- ✅ 安裝 PyInstaller（如果未安裝）
- ✅ 清理舊的建置檔案
- ✅ 執行打包
- ✅ 顯示結果訊息

### 方法 2: 使用批次檔

```cmd
build.bat
```

### 方法 3: 手動執行

```powershell
# 清理舊檔案
Remove-Item -Recurse -Force build, dist -ErrorAction SilentlyContinue

# 執行打包
pyinstaller mc-server-framework.spec --clean
```

---

## 打包輸出

打包完成後，檔案結構如下：

```
MC-Server-Framework/
├── dist/
│   └── mc-server-framework/          ← 打包輸出目錄
│       ├── mc-server-framework.exe   ← 主執行檔
│       ├── _internal/                ← 依賴檔案
│       └── templates/                ← 配置模板
├── build/                            ← 臨時建置檔案（可刪除）
└── ...
```

### 測試執行檔

```powershell
cd dist\mc-server-framework
.\mc-server-framework.exe --help
```

---

## 發佈流程

### 創建發佈包

執行發佈打包腳本：

```powershell
# 預設版本
.\package.ps1

# 指定版本
.\package.ps1 -Version "v1.0.0"
```

這會在 `release/` 目錄生成：
```
MC-Server-Framework-v0.2.0-Windows-x64.zip
```

發佈包包含：
- ✅ 獨立執行檔（無需安裝 Python）
- ✅ 預建立的目錄結構（config, servers, logs, templates）
- ✅ 使用說明文件
- ✅ README 和 LICENSE

### 發佈檢查清單

打包前確認：

- [ ] 更新版本號（`app/main.py` 中的版本資訊）
- [ ] 測試所有主要功能
- [ ] 執行系統診斷：`python -m app.main check`
- [ ] 清理測試資料（servers/ 目錄中的測試伺服器）
- [ ] 更新 README.md 和 CHANGELOG.md

打包後測試：

- [ ] 在乾淨的環境測試執行檔
- [ ] 測試首次運行初始化
- [ ] 測試基本指令（scan, start, stop, status）
- [ ] 測試互動式選單
- [ ] 驗證配置文件生成

---

## 進階配置

### 修改打包選項

編輯 `mc-server-framework.spec` 文件：

#### 添加圖標

```python
exe = EXE(
    ...
    icon='assets/icon.ico',  # 添加 .ico 圖標
    ...
)
```

#### 單檔案打包

如果想打包成單一 .exe（較大但更便攜）：

```python
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,      # ← 添加
    a.zipfiles,      # ← 添加
    a.datas,         # ← 添加
    [],
    name='mc-server-framework',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
```

然後移除 `COLLECT` 區塊。

#### 隱藏控制台視窗

如果要建立 GUI 應用程式（隱藏命令列視窗）：

```python
exe = EXE(
    ...
    console=False,  # ← 改為 False
    ...
)
```

⚠️ 注意：這會隱藏所有輸出，不適合命令列工具。

#### 優化檔案大小

在 `excludes` 中添加不需要的模組：

```python
excludes=[
    'matplotlib',
    'numpy',
    'pandas',
    'scipy',
    'PIL',
    'tkinter',
    'pytest',
    'unittest',
    'email',
    'xml',
],
```

### UPX 壓縮

UPX 可以進一步壓縮執行檔：

```powershell
# 下載 UPX: https://github.com/upx/upx/releases
# 解壓到 PATH 或專案目錄

# 在 .spec 中啟用
upx=True,
upx_exclude=[],
```

---

## 常見問題

### Q: 打包失敗，提示找不到模組

**原因**: PyInstaller 未能自動檢測到某些依賴

**解決方法**: 在 `mc-server-framework.spec` 的 `hiddenimports` 中添加：

```python
hiddenimports = [
    'missing_module',  # 添加缺失的模組
    ...
]
```

### Q: 執行檔啟動慢

**原因**: PyInstaller 需要在臨時目錄解壓縮依賴

**解決方法**: 
1. 使用 `--onedir` 模式（預設，已在使用）
2. 首次啟動後會加快

### Q: 執行檔體積太大

**原因**: 包含了所有依賴

**優化方法**:
1. 在 `excludes` 中排除不需要的模組
2. 啟用 UPX 壓縮
3. 檢查是否有不必要的依賴

目前打包大小約 30-50 MB（包含所有依賴）。

### Q: 防毒軟體誤報

**原因**: PyInstaller 打包的執行檔可能被誤判

**解決方法**:
1. 向防毒軟體廠商提交誤報
2. 為執行檔簽署數位簽章
3. 建議用戶添加到白名單

### Q: 如何添加數位簽章

需要購買程式碼簽章憑證（Code Signing Certificate）：

```powershell
# 使用 signtool.exe（Windows SDK）
signtool sign /f certificate.pfx /p password /t http://timestamp.digicert.com dist\mc-server-framework\mc-server-framework.exe
```

### Q: 打包後某些功能不正常

**除錯方法**:

1. 啟用除錯模式：

```python
exe = EXE(
    ...
    debug=True,  # ← 啟用除錯
    ...
)
```

2. 檢查打包日誌：

```powershell
pyinstaller mc-server-framework.spec --clean --log-level DEBUG
```

3. 確認資料檔案已正確包含：

```python
datas = [
    ('templates', 'templates'),
    ('config', 'config'),  # 如果需要預設配置
]
```

---

## 建置環境設定

### 在乾淨的環境中測試

建議在虛擬機或乾淨的 Windows 安裝中測試：

```powershell
# 1. 複製 dist\mc-server-framework 到測試機器
# 2. 不安裝 Python
# 3. 直接執行 mc-server-framework.exe
# 4. 測試所有功能
```

### 系統需求

最終用戶需要：
- Windows 10/11 (64-bit)
- Visual C++ Redistributable（通常已預裝）
  - 如果缺少，下載：https://aka.ms/vs/17/release/vc_redist.x64.exe

---

## 自動化建置

### GitHub Actions（未來擴展）

可以設定 CI/CD 自動打包：

```yaml
# .github/workflows/build.yml
name: Build Release

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pip install pyinstaller
      - run: pyinstaller mc-server-framework.spec --clean
      - run: .\package.ps1 -Version ${{ github.ref_name }}
      - uses: actions/upload-artifact@v2
        with:
          name: release
          path: release/*.zip
```

---

## 參考資源

- [PyInstaller 官方文檔](https://pyinstaller.org/en/stable/)
- [PyInstaller Spec 文件格式](https://pyinstaller.org/en/stable/spec-files.html)
- [UPX 壓縮工具](https://github.com/upx/upx)

---

## 版本歷史

- **v0.2.0** (2026-04-11): 初始打包配置
  - 支援 Windows x64 打包
  - 包含所有依賴
  - 自動初始化功能

---

如有問題，請在 GitHub Issues 回報。
