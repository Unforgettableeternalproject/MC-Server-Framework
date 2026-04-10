# -*- mode: python ; coding: utf-8 -*-
"""
MC Server Framework - PyInstaller 打包配置文件

此文件定義了如何將 Python 專案打包成獨立的 .exe 執行檔
"""

import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# 收集所有需要的資料檔案
datas = [
    ('templates', 'templates'),  # 配置模板
]

# 收集所有子模組
hiddenimports = [
    'rich.console',
    'rich.table',
    'rich.panel',
    'rich.markdown',
    'rich.tree',
    'rich.prompt',
    'rich.progress',
    'typer',
    'yaml',
    'requests',
    'psutil',
    'dateutil',
]

a = Analysis(
    ['app/main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'PIL',
        'tkinter',
        'pytest',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='mc-server-framework',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # 可以添加 .ico 圖標文件
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='mc-server-framework',
)
