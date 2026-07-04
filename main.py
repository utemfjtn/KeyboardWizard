# -*- coding: utf-8 -*-
"""
按键精灵（Python 版）入口
运行： python main.py
依赖： pip install -r requirements.txt
注意：本程序面向 Windows，pyautogui/keyboard/pygetwindow 在 Windows 上效果最佳。
"""
from __future__ import annotations

import sys


def _check_deps():
    """启动前做一次依赖检查，给出友好提示。"""
    missing = []
    for mod in ("customtkinter", "pyautogui", "PIL", "keyboard", "pygetwindow"):
        try:
            __import__(mod)
        except Exception:
            missing.append(mod)
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
