# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller 打包配置：按键精灵 · Python 版
生成单个 exe：pyinstaller build.spec
"""
import os
import sys
import customtkinter

block_cipher = None

# customtkinter 的资源目录（主题 JSON、图标等）
ctk_path = os.path.dirname(customtkinter.__file__)

datas = [
    (os.path.join(ctk_path, "assets"), "customtkinter/assets"),
]

# 如果有 assets/app.ico 也打包进去
local_assets = os.path.join(os.path.dirname(SPEC), "assets")
if os.path.exists(local_assets):
    datas.append((local_assets, "assets"))

hiddenimports = [
    "customtkinter",
    "PIL._tkinter_finder",
    "pyautogui",
    "pyperclip",
    "pygetwindow",
    "keyboard",
    "cv2",
    "numpy",
    "pyscreeze",
    "pymsgbox",
    "pytweening",
    "mouseinfo",
]

a = Analysis(
    ["main.py"],
    pathex=[os.path.dirname(SPEC)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# 图标路径（可选）
icon_path = os.path.join(os.path.dirname(SPEC), "assets", "app.ico")
if not os.path.exists(icon_path):
    icon_path = None

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="按键精灵",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,          # 无控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_path,
)
