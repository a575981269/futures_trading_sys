# -*- mode: python ; coding: utf-8 -*-
import os

block_cipher = None

a = Analysis(
    ['gui/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('gui/resources', 'resources') if os.path.exists('gui/resources') else None,
    ],
    hiddenimports=[
        'vnpy_ctp',
        'vnpy.event',
        'vnpy.trader.event',
        'vnpy.trader.object',
        'vnpy.trader.constant',
        'PyQt6',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'pyqtgraph',
        'sqlalchemy',
        'pandas',
        'numpy',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# 过滤掉None值
a.datas = [d for d in a.datas if d is not None]

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='FuturesTradingSystem',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 不显示控制台窗口
    icon=None,  # 可以添加图标文件路径，例如: 'gui/resources/icons/app.ico'
)

