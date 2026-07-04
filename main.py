# -*- coding: utf-8 -*-
"""
KeyboardWizard · 按键精灵 入口
运行： python main.py
依赖： pip install -r requirements.txt
跨平台支持：Windows / macOS / Linux
"""
from __future__ import annotations

import sys


def _check_deps():
    """启动前做一次依赖检查，给出友好提示。"""
    missing = []
    for mod in ("customtkinter", "pyautogui", "PIL", "pyperclip"):
        try:
            __import__(mod)
        except Exception:
            missing.append(mod)
    has_hotkey = False
    try:
        __import__("pynput")
        has_hotkey = True
    except Exception:
        try:
            __import__("keyboard")
            has_hotkey = True
        except Exception:
            pass
    if not has_hotkey:
        missing.append("pynput (或 keyboard)")
    has_window = False
    try:
        __import__("pygetwindow")
        has_window = True
    except Exception:
        try:
            __import__("pywinctl")
            has_window = True
        except Exception:
            pass
    if not has_window:
        missing.append("pygetwindow (或 pywinctl)")
    if missing:
        print("缺少依赖：" + ", ".join(missing))
        print("请先执行： pip install -r requirements.txt")
        try:
            from tkinter import messagebox, Tk
            root = Tk()
            root.withdraw()
            messagebox.showerror("缺少依赖",
                                 "缺少：" + ", ".join(missing) +
                                 "\n请先执行： pip install -r requirements.txt")
        except Exception:
            pass
        sys.exit(1)


def main():
    _check_deps()
    from app import App
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
