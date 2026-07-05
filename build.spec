# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller 打包配置：按键精灵 · Python 版
跨平台：Windows (exe) / macOS (app) / Linux (binary)
生成：pyinstaller build.spec
注意：PyInstaller 不支持交叉编译，需在对应平台上打包
"""
import os
import sys
import platform
import customtkinter

block_cipher = None

IS_WINDOWS = sys.platform.startswith("win")
IS_MACOS = sys.platform == "darwin"
IS_LINUX = sys.platform.startswith("linux")

ctk_path = os.path.dirname(customtkinter.__file__)

datas = [
    (os.path.join(ctk_path, "assets"), "customtkinter/assets"),
]

local_assets = os.path.join(os.path.dirname(SPEC), "assets")
if os.path.exists(local_assets):
    datas.append((local_assets, "assets"))

hiddenimports = [
    "customtkinter",
    "customtkinter.windows.widgets",
    "customtkinter.windows.widgets.ctk_button",
    "customtkinter.windows.widgets.ctk_frame",
    "customtkinter.windows.widgets.ctk_label",
    "customtkinter.windows.widgets.ctk_entry",
    "customtkinter.windows.widgets.ctk_checkbox",
    "customtkinter.windows.widgets.ctk_optionmenu",
    "customtkinter.windows.widgets.ctk_scrollable_frame",
    "customtkinter.windows.widgets.ctk_scrollbar",
    "PIL._tkinter_finder",
    "PIL.Image",
    "PIL.ImageTk",
    "pyautogui",
    "pyautogui._pyautogui_osx",
    "pyperclip",
    "pygetwindow",
    "pywinctl",
    "pynput",
    "pynput.keyboard",
    "pynput.keyboard._darwin",
    "pynput.keyboard._win32",
    "pynput.keyboard._xorg",
    "pynput.mouse",
    "pynput.mouse._darwin",
    "pynput.mouse._win32",
    "pynput.mouse._xorg",
    "pynput._util",
    "pynput._util.darwin",
    "pynput._util.win32",
    "pynput._util.xorg",
    "cv2",
    "numpy",
    "pyscreeze",
    "pyscreeze._pyscreeze_osx",
    "pymsgbox",
    "pytweening",
    "mouseinfo",
    "mouseinfo._mouseinfo_osx",
    "pyobjc",
    "pyobjc.core",
    "pyobjc.frameworks.ApplicationServices",
    "pyobjc.frameworks.AppKit",
    "pyobjc.frameworks.Foundation",
    "pyobjc.frameworks.SystemConfiguration",
    "pyobjc.frameworks.CoreGraphics",
    "pyobjc.frameworks.CoreFoundation",
    "pyobjc.frameworks.Quartz",
    "pyobjc.frameworks.Cocoa",
    "AppKit",
    "Foundation",
    "ApplicationServices",
    "CoreGraphics",
    "Quartz",
    "Cocoa",
    "CoreFoundation",
]

# macOS 需要显式收集 pynput 的 darwin 后端、pyobjc 框架等动态模块
if IS_MACOS:
    extra_hidden = [
        "pynput.keyboard._darwin",
        "pynput.mouse._darwin",
        "pynput._util.darwin",
        "pyautogui._pyautogui_osx",
        "pyscreeze._pyscreeze_osx",
        "mouseinfo._mouseinfo_osx",
    ]
    for m in extra_hidden:
        if m not in hiddenimports:
            hiddenimports.append(m)

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

icon_path = None
if IS_WINDOWS:
    icon_path = os.path.join(os.path.dirname(SPEC), "assets", "app.ico")
elif IS_MACOS:
    icon_path = os.path.join(os.path.dirname(SPEC), "assets", "app.icns")
elif IS_LINUX:
    icon_path = os.path.join(os.path.dirname(SPEC), "assets", "app.png")

if icon_path and not os.path.exists(icon_path):
    icon_path = None

app_name = "按键精灵"
if IS_WINDOWS:
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        [],
        name=app_name,
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
        icon=icon_path,
    )
elif IS_MACOS:
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name=app_name,
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon=icon_path,
    )
    coll = COLLECT(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name=app_name,
    )
    app = BUNDLE(
        coll,
        name=f"{app_name}.app",
        icon=icon_path,
        bundle_identifier="com.example.keyboardwizard",
        info_plist={
            "NSHighResolutionCapable": True,
            "LSUIElement": False,
            "CFBundleShortVersionString": "1.0.0",
            "NSMicrophoneUsageDescription": "本应用不使用麦克风",
            "NSCameraUsageDescription": "本应用不使用摄像头",
            "NSAppleEventsUsageDescription": "用于控制其他应用窗口",
            "NSAccessibilityUsageDescription": "用于全局快捷键和界面自动化",
        },
    )
elif IS_LINUX:
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        [],
        name=app_name,
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
        icon=icon_path,
    )
