# -*- coding: utf-8 -*-
"""
按键精灵（Python 版）入口
运行： python main.py
依赖： pip install -r requirements.txt
跨平台支持：Windows / macOS / Linux
"""
from __future__ import annotations

import os
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


def _write_crash_log(content: str) -> str:
    """把崩溃信息写到 crash.log，返回日志路径。"""
    import time
    import traceback
    try:
        from platform_utils import get_app_dir
        log_dir = get_app_dir()
    except Exception:
        # platform_utils 自身导入失败时，回退到家目录
        log_dir = os.path.expanduser("~")
    try:
        os.makedirs(log_dir, exist_ok=True)
    except Exception:
        log_dir = os.path.expanduser("~")
    log_path = os.path.join(log_dir, "crash.log")
    try:
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(f"时间：{time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Python：{sys.version}\n")
            f.write(f"平台：{sys.platform}\n")
            f.write(f"可执行文件：{sys.executable}\n")
            f.write(f"argv：{sys.argv}\n")
            f.write("-" * 60 + "\n")
            f.write(content)
    except Exception:
        # 写日志本身失败，最后兜底
        try:
            alt = os.path.join(os.path.expanduser("~"), "keyboardwizard_crash.log")
            with open(alt, "w", encoding="utf-8") as f:
                f.write(content)
            return alt
        except Exception:
            pass
    return log_path


def main():
    _check_deps()
    import traceback
    try:
        from app import App
        app = App()
        app.mainloop()
    except Exception:
        # 捕获所有异常，写崩溃日志并弹窗提示
        tb = traceback.format_exc()
        log_path = _write_crash_log(tb)
        print(tb)
        print(f"\n崩溃日志已保存到：{log_path}")
        try:
            from tkinter import messagebox, Tk
            root = Tk()
            root.withdraw()
            messagebox.showerror(
                "启动失败",
                f"程序启动时发生错误：\n\n{tb[:800]}\n\n"
                f"完整日志已保存到：\n{log_path}",
            )
        except Exception:
            pass
        raise


if __name__ == "__main__":
    main()
