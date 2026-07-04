# -*- coding: utf-8 -*-
"""
屏幕区域截图工具
提供一个全屏覆盖窗口，用户拖动鼠标选择矩形区域，将该区域保存为 PNG 文件。
用于"点击图片/等待图片/全局监控"等需要图片模板的场景。
"""
from __future__ import annotations

import os
import tempfile
import time


class RegionCapture:
    """使用 tkinter 实现的简单区域截图选择器。

    用法：
        path = RegionCapture().capture()   # 返回保存的图片路径，取消则返回 None
    """

    def __init__(self):
        self.result_path = None

    def capture(self):
        # 先截图，再弹出选择窗口
        try:
            import pyautogui
        except Exception as e:
            raise RuntimeError(f"无法导入 pyautogui：{e}")

        shot = pyautogui.screenshot()
        tmp_shot = os.path.join(tempfile.gettempdir(), "_region_full.png")
        shot.save(tmp_shot)

        # 使用 tkinter 显示并选择
        import tkinter as tk
        from PIL import Image, ImageTk
        from platform_utils import get_ui_font

        root = tk.Tk()
        root.attributes("-fullscreen", True)
        root.attributes("-topmost", True)
        # 提示条
        ui_font = get_ui_font(14)
        info = tk.Label(root, text="拖动鼠标选择区域，按 Esc 取消",
                        fg="white", bg="black", font=ui_font)
        info.pack(side="top", fill="x")

        canvas = tk.Canvas(root, cursor="cross", highlightthickness=0)
        canvas.pack(fill="both", expand=True)

        img = ImageTk.PhotoImage(Image.open(tmp_shot))
        canvas.create_image(0, 0, anchor="nw", image=img)

        self._start = None
        self._rect = None

        def on_down(e):
            self._start = (e.x, e.y)
            if self._rect:
                canvas.delete(self._rect)
            self._rect = canvas.create_rectangle(e.x, e.y, e.x, e.y,
                                                 outline="red", width=2)

        def on_move(e):
            if self._start:
                canvas.coords(self._rect, self._start[0], self._start[1], e.x, e.y)

        def on_up(e):
            if not self._start:
                return
            x1, y1 = self._start
            x2, y2 = e.x, e.y
            if x1 > x2:
                x1, x2 = x2, x1
            if y1 > y2:
                y1, y2 = y2, y1
            self._crop = (x1, y1, x2, y2)
            root.quit()

        def on_esc(e):
            self._crop = None
            root.quit()

        canvas.bind("<ButtonPress-1>", on_down)
        canvas.bind("<B1-Motion>", on_move)
        canvas.bind("<ButtonRelease-1>", on_up)
        root.bind("<Escape>", on_esc)

        root.mainloop()
        root.destroy()

        crop = getattr(self, "_crop", None)
        if not crop:
            return None
        # 裁剪并保存
        x1, y1, x2, y2 = crop
        if (x2 - x1) < 3 or (y2 - y1) < 3:
            return None
        cropped = shot.crop((x1, y1, x2, y2))
        out = os.path.join(tempfile.gettempdir(),
                           f"region_{int(time.time())}.png")
        cropped.save(out)
        return out


def pick_position():
    """让用户点击鼠标获取屏幕坐标，返回 (x, y) 或 None。"""
    try:
        import pyautogui
        import tkinter as tk
        from platform_utils import get_ui_font
    except Exception as e:
        raise RuntimeError(f"无法导入所需模块：{e}")

    root = tk.Tk()
    root.attributes("-fullscreen", True)
    root.attributes("-topmost", True)
    ui_font = get_ui_font(14)
    ui_font_small = get_ui_font(12)
    info = tk.Label(root, text="移动并点击鼠标以获取坐标，按 Esc 取消",
                    fg="white", bg="black", font=ui_font)
    info.pack(side="top", fill="x")
    lbl = tk.Label(root, text="", fg="yellow", bg="black",
                   font=ui_font_small)
    lbl.place(x=20, y=40)

    result = {"pos": None}

    def on_move(e):
        lbl.config(text=f"当前坐标：{e.x_root}, {e.y_root}")

    def on_click(e):
        result["pos"] = (e.x_root, e.y_root)
        root.quit()

    def on_esc(e):
        result["pos"] = None
        root.quit()

    root.bind("<Motion>", on_move)
    root.bind("<Button-1>", on_click)
    root.bind("<Escape>", on_esc)
    root.mainloop()
    root.destroy()
    return result["pos"]
