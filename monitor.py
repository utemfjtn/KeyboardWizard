# -*- coding: utf-8 -*-
"""
全局监控模块
独立线程持续监控屏幕，识别"系统提示/杀毒弹窗/保存对话框"等全局事件。
即使主脚本列表中没有这些判断，一旦弹出匹配的窗口或图片，立即触发预设动作。

规则结构：
    {
        "type":   "window" | "image",   # 按窗口标题 或 按图片识别
        "title":  str,                   # window 模式：窗口标题关键词（模糊匹配）
        "image":  str,                   # image 模式：图片路径
        "confidence": float,
        "action": "enter" | "esc" | "click_image" | "close_window" | "custom_key",
        "action_key": str,               # custom_key 模式：按键
        "action_image": str,             # click_image 模式：要点击的按钮图片
        "enabled": bool,
        "name": str,
    }
"""
from __future__ import annotations

import threading
import time
import traceback


class GlobalMonitor:
    def __init__(self, rules, on_log=None, interval=0.8):
        """
        :param rules: 规则列表
        :param on_log: 日志回调 (msg, level)
        :param interval: 检查间隔（秒）
        """
        self.rules = rules
        self.on_log = on_log or (lambda m, l="info": None)
        self.interval = interval
        self._stop_flag = threading.Event()
        self._thread = None
        self._cooldown = {}  # name -> 上次触发时间，避免狂触发

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop_flag.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        self.on_log("全局监控已启动", "info")

    def stop(self):
        self._stop_flag.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)
        self.on_log("全局监控已停止", "info")

    def is_running(self):
        return self._thread is not None and self._thread.is_alive()

    def update_rules(self, rules):
        self.rules = rules

    def _loop(self):
        while not self._stop_flag.is_set():
            try:
                for rule in list(self.rules):
                    if self._stop_flag.is_set():
                        break
                    if not rule.get("enabled", True):
                        continue
                    name = rule.get("name", "?")
                    now = time.time()
                    # 冷却 2 秒，避免同一弹窗被反复处理
                    if now - self._cooldown.get(name, 0) < 2:
                        continue
                    if self._match(rule):
                        self._cooldown[name] = now
                        self.on_log(f"全局监控触发：{name}", "warn")
                        self._perform_action(rule)
            except Exception as e:
                self.on_log(f"全局监控异常：{e}\n{traceback.format_exc()}", "error")
            self._stop_flag.wait(self.interval)

    # ------------------------------------------------------------------ 匹配
    def _match(self, rule):
        t = rule.get("type", "window")
        if t == "window":
            return self._window_match(rule.get("title", ""))
        elif t == "image":
            return self._image_match(rule.get("image", ""),
                                     float(rule.get("confidence", 0.8)))
        return False

    def _window_match(self, title):
        if not title:
            return False
        from platform_utils import window_exists
        return window_exists(title)

    def _image_match(self, image, confidence):
        if not image:
            return False
        try:
            import pyautogui
            pos = pyautogui.locateCenterOnScreen(image, confidence=confidence)
            return pos is not None
        except Exception:
            return False

    # ------------------------------------------------------------------ 动作
    def _perform_action(self, rule):
        action = rule.get("action", "enter")
        try:
            import pyautogui
            if action == "enter":
                pyautogui.press("enter")
            elif action == "esc":
                pyautogui.press("escape")
            elif action == "custom_key":
                key = rule.get("action_key", "enter")
                if "+" in key:
                    pyautogui.hotkey(*[k.strip() for k in key.split("+")])
                else:
                    pyautogui.press(key)
            elif action == "click_image":
                img = rule.get("action_image", "")
                if img:
                    pos = pyautogui.locateCenterOnScreen(img, confidence=0.8)
                    if pos:
                        pyautogui.click(pos.x, pos.y)
                    else:
                        self.on_log(f"未找到动作图片 {img}", "warn")
            elif action == "close_window":
                self._close_window(rule.get("title", ""))
            self.on_log(f"已执行动作：{action}", "info")
        except Exception as e:
            self.on_log(f"执行动作出错：{e}", "error")

    def _close_window(self, title):
        from platform_utils import close_windows_by_title
        if close_windows_by_title(title):
            return
        try:
            import pyautogui
            from platform_utils import IS_MACOS
            if IS_MACOS:
                pyautogui.hotkey("command", "q")
            else:
                pyautogui.hotkey("alt", "f4")
        except Exception:
            pass
