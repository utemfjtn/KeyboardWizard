# -*- coding: utf-8 -*-
"""
脚本录制模块
监听全局鼠标和键盘事件，将操作录制为指令列表。

生成的指令结构与 commands.py 中定义的一致：
    {"type": ..., "params": {...}, "enabled": True, "comment": ""}

后端选择：
    - 优先 pynput（可同时录制鼠标和键盘）
    - pynput 不可用时回退到 keyboard 库（仅键盘）
    - macOS 需要「辅助功能」与「输入监控」权限，否则监听可能无效
"""
from __future__ import annotations

import threading
import time


class Recorder:
    """录制鼠标键盘操作，生成指令列表。"""

    def __init__(self, on_log=None, on_state=None, on_command=None):
        """
        :param on_log: 日志回调 (msg, level)
        :param on_state: 状态回调 (state) -> None, state in {recording, stopped}
        :param on_command: 每录制到一条指令时的回调 (cmd: dict) -> None
        """
        self.on_log = on_log or (lambda m, l="info": None)
        self.on_state = on_state or (lambda s: None)
        self.on_command = on_command or (lambda c: None)

        self._stop_flag = threading.Event()
        self._thread = None
        self._listener = None
        self.commands = []
        self._last_click_time = 0
        self._last_key_time = 0
        # 最小间隔（秒），小于此间隔的连续操作合并
        self.min_interval = 0.05

        # ---- 以下为扩展字段 ----
        self._kb_listener = None          # pynput keyboard.Listener
        self._kb_lib = None               # keyboard 库（回退后端）
        self._kb_hook = None              # keyboard 库 hook 句柄
        self._lock = threading.Lock()     # 保护 commands 跨线程读写
        self._last_event_time = 0.0       # 上一次任意操作时间，用于插入 delay
        self._modifiers = set()           # 当前按下的修饰键名称集合
        self._backend = None              # "pynput" / "keyboard" / None
        # 停止录制快捷键，录制时按下不录入指令
        self.stop_hotkey = "f8"
        # 两次操作间隔超过该阈值（秒）则自动插入 delay 指令
        self.delay_threshold = 0.3

        # 特殊键映射表（惰性构建）
        self._special_map = None

    # ------------------------------------------------------------------ public
    def start(self):
        """启动录制。"""
        if self.is_recording():
            return
        self._stop_flag.clear()
        self.commands = []
        self._modifiers.clear()
        self._last_click_time = 0.0
        self._last_key_time = 0.0
        self._last_event_time = time.time()

        ok = self._start_pynput()
        if not ok:
            ok = self._start_keyboard_lib()
        if not ok:
            self.on_log("无法启动录制：pynput 与 keyboard 库均不可用", "error")
            return

        self.on_state("recording")
        self.on_log("开始录制", "info")

    def stop(self):
        """停止录制。"""
        if not self.is_recording() and self._backend is None:
            return
        self._stop_flag.set()
        self._stop_listeners()
        self._modifiers.clear()
        self.on_state("stopped")
        with self._lock:
            n = len(self.commands)
        self.on_log(f"已停止录制，共 {n} 条指令", "info")

    def is_recording(self) -> bool:
        """返回是否正在录制。"""
        if self._stop_flag.is_set():
            return False
        return (self._listener is not None
                or self._kb_listener is not None
                or self._kb_hook is not None)

    def get_commands(self) -> list:
        """返回录制到的指令列表（副本）。"""
        with self._lock:
            return list(self.commands)

    # ------------------------------------------------------------------ backends
    def _start_pynput(self) -> bool:
        """尝试用 pynput 启动监听（鼠标 + 键盘）。成功返回 True。"""
        try:
            from pynput import mouse, keyboard
        except Exception as e:
            self.on_log(f"pynput 不可用：{e}", "warn")
            return False

        # macOS 权限提示
        try:
            from platform_utils import IS_MACOS, has_accessibility_permission
            if IS_MACOS:
                if not has_accessibility_permission():
                    self.on_log(
                        "macOS 辅助功能权限未授予，pynput 可能无法监听全局事件",
                        "warn")
                self.on_log(
                    "macOS 上 pynput 监听键盘需「输入监控」权限，可能不稳定",
                    "warn")
        except Exception:
            pass

        try:
            self._listener = mouse.Listener(on_click=self._on_click)
            self._kb_listener = keyboard.Listener(
                on_press=self._on_press, on_release=self._on_release)
            self._listener.daemon = True
            self._kb_listener.daemon = True
            self._listener.start()
            self._kb_listener.start()
            self._backend = "pynput"
            return True
        except Exception as e:
            self.on_log(f"pynput 启动失败：{e}", "error")
            self._listener = None
            self._kb_listener = None
            return False

    def _start_keyboard_lib(self) -> bool:
        """pynput 不可用时回退到 keyboard 库（仅键盘，无法录制鼠标）。"""
        try:
            import keyboard as kb_lib
        except Exception as e:
            self.on_log(f"keyboard 库不可用：{e}", "warn")
            return False
        try:
            self._kb_lib = kb_lib
            self._kb_hook = kb_lib.hook(
                self._on_keyboard_lib_event, suppress=False)
            self._backend = "keyboard"
            self.on_log("已回退到 keyboard 库（仅录制键盘，无法录制鼠标）", "warn")
            return True
        except Exception as e:
            self.on_log(f"keyboard 库启动失败：{e}", "error")
            self._kb_lib = None
            return False

    def _stop_listeners(self):
        """停止所有监听器。"""
        if self._listener is not None:
            try:
                self._listener.stop()
            except Exception:
                pass
            self._listener = None
        if self._kb_listener is not None:
            try:
                self._kb_listener.stop()
            except Exception:
                pass
            self._kb_listener = None
        if self._kb_lib is not None and self._kb_hook is not None:
            try:
                self._kb_lib.unhook(self._kb_hook)
            except Exception:
                pass
            self._kb_hook = None
        self._backend = None

    # ------------------------------------------------------------------ mouse (pynput)
    def _on_click(self, x, y, button, pressed):
        """鼠标点击回调：只记录按下事件。"""
        if self._stop_flag.is_set():
            return
        if not pressed:
            return
        now = time.time()
        # 合并过快连续点击
        if now - self._last_click_time < self.min_interval:
            return
        self._last_click_time = now

        cmd = {
            "type": "click",
            "params": {
                "x": int(x), "y": int(y),
                "button": self._button_name(button),
                "clicks": 1, "interval": 0.0,
            },
            "enabled": True,
            "comment": "",
        }
        self._append_command(cmd, now)

    @staticmethod
    def _button_name(button) -> str:
        """pynput Button -> "left"/"right"/"middle"。"""
        try:
            name = getattr(button, "name", "") or str(button)
        except Exception:
            name = str(button)
        name = name.lower()
        if "right" in name:
            return "right"
        if "middle" in name:
            return "middle"
        return "left"

    # ------------------------------------------------------------------ keyboard (pynput)
    def _on_press(self, key):
        """键盘按下回调。"""
        if self._stop_flag.is_set():
            return
        now = time.time()

        # 修饰键：仅记录状态，不单独生成指令
        mod = self._modifier_name(key)
        if mod is not None:
            self._modifiers.add(mod)
            return

        name = self._key_name(key)
        if name is None:
            return

        # 不录制停止快捷键
        if name.lower() == self.stop_hotkey.lower():
            return

        # 合并过快连续按键
        if now - self._last_key_time < self.min_interval:
            return
        self._last_key_time = now

        # 组合键：修饰键 + 普通键
        if self._modifiers:
            combo = "+".join(sorted(self._modifiers)) + "+" + name
        else:
            combo = name

        cmd = {
            "type": "key",
            "params": {"key": combo, "hold": 0.0},
            "enabled": True,
            "comment": "",
        }
        self._append_command(cmd, now)

    def _on_release(self, key):
        """键盘释放回调：清理修饰键状态。"""
        mod = self._modifier_name(key)
        if mod is not None:
            self._modifiers.discard(mod)

    @staticmethod
    def _modifier_name(key):
        """pynput key -> 修饰键名称（ctrl/shift/alt/cmd），非修饰键返回 None。"""
        try:
            from pynput.keyboard import Key
        except Exception:
            return None
        if key in (Key.ctrl, Key.ctrl_l, Key.ctrl_r):
            return "ctrl"
        if key in (Key.shift, Key.shift_l, Key.shift_r):
            return "shift"
        if key in (Key.alt, Key.alt_l, Key.alt_r, Key.alt_gr):
            return "alt"
        if key in (Key.cmd, Key.cmd_l, Key.cmd_r):
            return "cmd"
        return None

    def _build_special_map(self):
        """惰性构建 pynput 特殊键映射表。"""
        if self._special_map is not None:
            return self._special_map
        try:
            from pynput.keyboard import Key
        except Exception:
            self._special_map = {}
            return self._special_map
        m = {
            Key.enter: "enter",
            Key.space: "space",
            Key.tab: "tab",
            Key.esc: "esc",
            Key.backspace: "backspace",
            Key.delete: "delete",
            Key.left: "left",
            Key.right: "right",
            Key.up: "up",
            Key.down: "down",
            Key.home: "home",
            Key.end: "end",
            Key.page_up: "pageup",
            Key.page_down: "pagedown",
            Key.insert: "insert",
            Key.caps_lock: "capslock",
            Key.print_screen: "printscreen",
            Key.scroll_lock: "scrolllock",
            Key.num_lock: "numlock",
            Key.pause: "pause",
            Key.menu: "menu",
        }
        # 功能键 f1~f20
        for attr in dir(Key):
            if attr.startswith("f") and attr[1:].isdigit():
                try:
                    m[getattr(Key, attr)] = attr
                except Exception:
                    pass
        self._special_map = m
        return m

    def _key_name(self, key):
        """pynput key -> 字符串名称。"""
        special = self._build_special_map()
        # 特殊键
        if key in special:
            return special[key]

        # 普通字符
        char = None
        try:
            char = key.char
        except Exception:
            char = None
        if char and len(char) == 1:
            o = ord(char)
            # ctrl+letter 会产生控制字符：ctrl+a=\x01 ... ctrl+z=\x1a
            if 1 <= o <= 26:
                return chr(o + ord('a') - 1)
            if 0 <= o < 32 or o == 127:
                # 其他控制字符，忽略
                pass
            elif char.isprintable():
                return char.lower()
            else:
                return char.lower()

        # 兜底：虚拟键码 / name 属性
        try:
            vk = key.vk
            if vk:
                return str(vk)
        except Exception:
            pass
        try:
            name = getattr(key, "name", None)
            if name:
                return str(name).lower()
        except Exception:
            pass
        return None

    # ------------------------------------------------------------------ keyboard (keyboard lib fallback)
    def _on_keyboard_lib_event(self, event):
        """keyboard 库回调。event.event_type in {'down', 'up'}。"""
        if self._stop_flag.is_set():
            return
        name = (getattr(event, "name", "") or "").lower()

        if event.event_type != "down":
            # 修饰键释放时清理状态
            mod = self._normalize_mod(name)
            if mod is not None:
                self._modifiers.discard(mod)
            return

        # 修饰键按下：仅记录状态
        mod = self._normalize_mod(name)
        if mod is not None:
            self._modifiers.add(mod)
            return

        if not name:
            return
        # 不录制停止快捷键
        if name == self.stop_hotkey.lower():
            return

        now = time.time()
        if now - self._last_key_time < self.min_interval:
            return
        self._last_key_time = now

        if self._modifiers:
            combo = "+".join(sorted(self._modifiers)) + "+" + name
        else:
            combo = name
        cmd = {
            "type": "key",
            "params": {"key": combo, "hold": 0.0},
            "enabled": True,
            "comment": "",
        }
        self._append_command(cmd, now)

    @staticmethod
    def _normalize_mod(name):
        """将 keyboard 库的修饰键名称标准化。"""
        name = (name or "").lower()
        if name in ("ctrl", "control"):
            return "ctrl"
        if name == "shift":
            return "shift"
        if name == "alt":
            return "alt"
        if name in ("cmd", "command", "windows", "win", "super"):
            return "cmd"
        return None

    # ------------------------------------------------------------------ command utils
    def _append_command(self, cmd: dict, now: float):
        """加锁追加指令，自动在前面插入 delay；回调在锁外触发以免死锁。"""
        to_fire = []
        with self._lock:
            to_fire.extend(self._maybe_add_delay(now))
            self.commands.append(cmd)
            to_fire.append(cmd)
        for c in to_fire:
            try:
                self.on_command(c)
            except Exception:
                pass

    def _maybe_add_delay(self, now: float) -> list:
        """距上次操作超过阈值时插入 delay 指令。需在锁内调用，返回新建指令列表。"""
        created = []
        if self._last_event_time <= 0:
            self._last_event_time = now
            return created
        delta = now - self._last_event_time
        if delta > self.delay_threshold:
            ms = int(delta * 1000)
            delay_cmd = {
                "type": "delay",
                "params": {"ms": ms},
                "enabled": True,
                "comment": "",
            }
            self.commands.append(delay_cmd)
            created.append(delay_cmd)
        self._last_event_time = now
        return created
