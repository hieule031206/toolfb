# -*- mode: python ; coding: utf-8 -*-

import customtkinter
import selenium
import PIL

customtkinter_path = customtkinter.__path__[0]

a = Analysis(
    ['f:\\toolfb\\giaodien.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('backend.py', '.'),
        (customtkinter_path, 'customtkinter'),
    ],
    hiddenimports=[
        'customtkinter',
        'selenium',
        'selenium.webdriver',
        'selenium.webdriver.chrome',
        'selenium.webdriver.chrome.service',
        'selenium.webdriver.chrome.options',
        'selenium.webdriver.chrome.webdriver',
        'selenium.webdriver.common.by',
        'selenium.webdriver.common.keys',
        'selenium.webdriver.common.service',
        'selenium.webdriver.common.options',
        'selenium.webdriver.support.ui',
        'selenium.webdriver.support.expected_conditions',
        'webdriver_manager',
        'webdriver_manager.chrome',
        'webdriver_manager.core',
        'webdriver_manager.core.manager',
        'webdriver_manager.core.download_manager',
        'webdriver_manager.core.os_manager',
        'PIL',
        'PIL.Image',
        'PIL.ImageGrab',
        'win32clipboard',
        'random',
        'json',
        'threading',
        'time',
        'pathlib',
        'datetime',
        'traceback',
        'os',
        'sys',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='FBAutoPost',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    onefile=True,  # Build thành 1 file độc lập
)
