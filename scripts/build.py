"""
打包腳本 - 使用 PyInstaller 將專案打包成可執行檔
"""

import os
import shutil
import subprocess
from pathlib import Path

def clean_build():
    """清理舊的建置檔案"""
    print("清理舊檔案...")
    dirs_to_remove = ['build', 'dist']
    for dir_name in dirs_to_remove:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"  已刪除 {dir_name}/")

def build_exe():
    """使用 PyInstaller 建置執行檔"""
    print("\n開始建置執行檔...")
    
    # 基本參數
    cmd = [
        'pyinstaller',
        '--name=mc-host',
        '--onefile',  # 單一執行檔
        '--console',  # 命令列應用
        '--clean',
        
        # 指定主程式入口
        'app/main.py',
        
        # 包含必要的模組
        '--hidden-import=yaml',
        '--hidden-import=requests',
        '--hidden-import=typer',
        '--hidden-import=rich',
        '--hidden-import=psutil',
        
        # 包含資料檔案
        '--add-data=config;config',
        '--add-data=templates;templates',
        '--add-data=docs;docs',
        
        # 排除不必要的模組
        '--exclude-module=tkinter',
        '--exclude-module=matplotlib',
        '--exclude-module=PIL',
        
        # 圖示（如果有的話）
        # '--icon=assets/icon.ico',
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print("\n✅ 建置成功！")
        print(f"執行檔位置: dist/mc-host.exe")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ 建置失敗: {e}")
        return False

def create_dist_package():
    """建立分發套件"""
    print("\n建立分發套件...")
    
    dist_dir = Path('dist')
    package_dir = dist_dir / 'mc-host-package'
    
    # 建立資料夾結構
    package_dir.mkdir(exist_ok=True)
    (package_dir / 'config').mkdir(exist_ok=True)
    (package_dir / 'templates').mkdir(exist_ok=True)
    (package_dir / 'docs').mkdir(exist_ok=True)
    (package_dir / 'servers').mkdir(exist_ok=True)
    
    # 複製執行檔
    shutil.copy(dist_dir / 'mc-host.exe', package_dir / 'mc-host.exe')
    
    # 複製設定範本
    if Path('config/java_registry.yml').exists():
        shutil.copy('config/java_registry.yml', package_dir / 'config/')
    if Path('config/app.yml').exists():
        shutil.copy('config/app.yml', package_dir / 'config/')
    
    # 複製範本
    if Path('templates/default_server.yml').exists():
        shutil.copy('templates/default_server.yml', package_dir / 'templates/')
    
    # 複製文檔
    docs_to_copy = ['README.md', 'docs/DNS-SETUP.md', 'docs/PACKAGING.md']
    for doc in docs_to_copy:
        if Path(doc).exists():
            shutil.copy(doc, package_dir / 'docs/')
    
    # 建立啟動腳本
    create_startup_scripts(package_dir)
    
    print(f"✅ 分發套件已建立: {package_dir}")
    print("\n包含檔案：")
    for item in package_dir.rglob('*'):
        if item.is_file():
            print(f"  {item.relative_to(package_dir)}")

def create_startup_scripts(package_dir):
    """建立便利的啟動腳本"""
    
    # Windows 批次檔
    bat_content = """@echo off
echo MC Server Framework
echo.
mc-host.exe %*
"""
    with open(package_dir / 'mc-host.bat', 'w') as f:
        f.write(bat_content)
    
    # PowerShell 腳本
    ps1_content = """# MC Server Framework
Write-Host "MC Server Framework" -ForegroundColor Green
Write-Host ""
& "$PSScriptRoot\\mc-host.exe" @args
"""
    with open(package_dir / 'mc-host.ps1', 'w') as f:
        f.write(ps1_content)
    
    print("  已建立啟動腳本")

def main():
    """主函式"""
    print("=" * 50)
    print("MC Server Framework - 打包腳本")
    print("=" * 50)
    
    # 確認在正確的目錄
    if not Path('app/main.py').exists():
        print("❌ 錯誤: 請在專案根目錄執行此腳本")
        return
    
    # 清理
    clean_build()
    
    # 建置
    if not build_exe():
        return
    
    # 建立分發套件
    create_dist_package()
    
    print("\n" + "=" * 50)
    print("✅ 完成！")
    print("=" * 50)
    print("\n使用方式：")
    print("  1. 進入 dist/mc-host-package/")
    print("  2. 編輯 config/java_registry.yml 設定 Java 路徑")
    print("  3. 執行 mc-host.exe --help 查看指令")
    print("\n或直接執行:")
    print("  mc-host.bat scan")
    print("  mc-host.exe init my-server")

if __name__ == '__main__':
    main()
