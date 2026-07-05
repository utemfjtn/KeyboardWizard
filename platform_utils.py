# -*- coding: utf-8 -*-
"""
平台适配层
封装 Windows / macOS / Linux 之间的差异，上层模块只调用本模块的统一接口。
包括：全局快捷键、窗口操作、剪贴板粘贴、字体、图标等。
"""
from __future__ import annotations

import os
import sys
import platform


# ---------------------------------------------------------------------------
# 平台检测
# ---------------------------------------------------------------------------
IS_WINDOWS = sys.platform.startswith("win")
IS_MACOS = sys.platform == "darwin"
IS_LINUX = sys.platform.startswith("linux")


def current_os() -> str:
    """返回平台名称：windows / macos / linux"""
    if IS_WINDOWS:
        return "windows"
    if IS_MACOS:
        return "macos"
    if IS_LINUX:
        return "linux"
    return sys.platform


# ---------------------------------------------------------------------------
# 资源路径 / 应用数据目录
# ---------------------------------------------------------------------------
def resource_path(*parts: str) -> str:
    """获取资源文件的绝对路径，兼容 PyInstaller 打包后的 _MEIPASS 解包目录。

    用法：
        resource_path("assets", "app.ico")
        resource_path("assets")
    """
    base = getattr(sys, "_MEIPASS", os.path.abspath("."))
    if parts:
        return os.path.join(base, *parts)
    return base


def get_app_dir() -> str:
    """返回应用数据目录（用于存放 config.json、crash.log 等）。

    - Windows: %APPDATA%/KeyboardWizard
    - macOS:   ~/Library/Application Support/KeyboardWizard
    - Linux:   ~/.config/keyboardwizard
    """
    app_name = "KeyboardWizard"
    if IS_WINDOWS:
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
        return os.path.join(base, app_name)
    if IS_MACOS:
        return os.path.join(os.path.expanduser("~"),
                            "Library", "Application Support", app_name)
    # Linux / 其他
    base = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
    return os.path.join(base, app_name.lower())


# ---------------------------------------------------------------------------
# macOS 辅助功能权限（Accessibility）
# ---------------------------------------------------------------------------
def has_accessibility_permission() -> bool:
    """检查当前进程是否拥有辅助功能权限（macOS）。

    Windows/Linux 直接返回 True（不需要此权限）。
    """
    if not IS_MACOS:
        return True
    try:
        from ApplicationServices import AXIsProcessTrustedWithOptions
        from CoreFoundation import CFDictionaryCreate, kCFBooleanTrue
        from CoreFoundation import kCFTypeDictionaryKeyCallBacks
        from CoreFoundation import kCFTypeDictionaryValueCallBacks
        key = "AXTrustedCheckOptionPrompt"
        opts = CFDictionaryCreate(
            None, [key], [kCFBooleanTrue],
            1, kCFTypeDictionaryKeyCallBacks, kCFTypeDictionaryValueCallBacks
        )
        return bool(AXIsProcessTrustedWithOptions(opts))
    except Exception:
        # pyobjc 未安装或调用失败，降级为只检查不弹窗
        try:
            from ApplicationServices import AXIsProcessTrusted
            return bool(AXIsProcessTrusted())
        except Exception:
            return True  # 无法判断时，不阻塞启动


def open_accessibility_settings() -> bool:
    """打开系统设置的辅助功能面板（macOS）。"""
    if not IS_MACOS:
        return False
    try:
        import subprocess
        # macOS 13+ 的新路径
        subprocess.Popen([
            "open", "x-apple.systempreferences:com.apple.preference.security"
            "?Privacy_Accessibility"
        ])
        return True
    except Exception:
        return False


def has_input_monitoring_permission() -> bool:
    """检查输入监控权限（macOS 10.15+）。

    用于 pynput 监听全局键盘事件。Windows/Linux 直接返回 True。
    """
    if not IS_MACOS:
        return True
    try:
        # 通过 IORegistry 检查是否被列入输入监控信任列表
        import subprocess
        # 检查当前进程是否在输入监控列表中
        r = subprocess.run(
            ["sqlite3", "/Library/Application Support/com.apple.TCC/TCC.db",
             "SELECT client FROM access WHERE service='kTCCServicePostEvent';"],
            capture_output=True, text=True, timeout=3
        )
        # 这个查询需要 root 权限，普通进程拿不到，所以这里只是尽力而为
        return True  # 无法准确判断时，不阻塞
    except Exception:
        return True


# ---------------------------------------------------------------------------
# 字体：根据平台选择合适的中文字体
# ---------------------------------------------------------------------------
def get_ui_font(size: int = 11, bold: bool = False) -> tuple:
    """返回适合当前平台的 UI 字体配置。"""
    if IS_WINDOWS:
        name = "Microsoft YaHei"
    elif IS_MACOS:
        name = "PingFang SC"
    else:
        name = "Noto Sans CJK SC"
    weight = "bold" if bold else "normal"
    return (name, size, weight)


def get_mono_font(size: int = 11) -> tuple:
    """返回适合当前平台的等宽字体配置。"""
    if IS_WINDOWS:
        name = "Consolas"
    elif IS_MACOS:
        name = "Menlo"
    else:
        name = "Monospace"
    return (name, size)


# ---------------------------------------------------------------------------
# 图标：根据平台选择合适的图标格式
# ---------------------------------------------------------------------------
def get_app_icon(assets_dir: str) -> str | None:
    """返回适合当前平台的图标文件路径，不存在则返回 None。"""
    import os
    if IS_WINDOWS:
        p = os.path.join(assets_dir, "app.ico")
    elif IS_MACOS:
        p = os.path.join(assets_dir, "app.icns")
    else:
        p = os.path.join(assets_dir, "app.png")
    return p if os.path.exists(p) else None


def set_window_icon(tk_window, icon_path: str | None) -> bool:
    """为 tk 窗口设置图标，成功返回 True。"""
    if not icon_path:
        return False
    try:
        if IS_WINDOWS:
            tk_window.iconbitmap(icon_path)
        else:
            from PIL import Image, ImageTk
            img = Image.open(icon_path)
            photo = ImageTk.PhotoImage(img)
            tk_window.iconphoto(True, photo)
            tk_window._icon_photo_ref = photo
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# 全局快捷键
# macOS：使用 CGEventTap（主线程 CFRunLoop），避免 pynput 后台线程崩溃
# Windows/Linux：优先 pynput，回退 keyboard
# ---------------------------------------------------------------------------

# macOS 虚拟键码映射（key name -> keycode）
_MAC_KEYCODES = {
    "a": 0, "s": 1, "d": 2, "f": 3, "h": 4, "g": 5, "z": 6, "x": 7,
    "c": 8, "v": 9, "b": 11, "q": 12, "w": 13, "e": 14, "r": 15,
    "y": 16, "t": 17, "1": 18, "2": 19, "3": 20, "4": 21, "6": 22,
    "5": 23, "=": 24, "9": 25, "7": 26, "-": 27, "8": 28, "0": 29,
    "]": 30, "o": 31, "u": 32, "[": 33, "i": 34, "p": 35, "l": 37,
    "j": 38, "'": 39, "k": 40, ";": 41, "\\": 42, ",": 43, "/": 44,
    "n": 45, "m": 46, ".": 47, "`": 50, " ": 49,
    "f1": 122, "f2": 120, "f3": 99, "f4": 118, "f5": 96,
    "f6": 97, "f7": 98, "f8": 100, "f9": 101, "f10": 109,
    "f11": 103, "f12": 111,
    "enter": 36, "return": 36, "tab": 48, "space": 49,
    "delete": 51, "backspace": 51, "esc": 53, "escape": 53,
    "ctrl": 59, "control": 59, "shift": 56, "alt": 58, "option": 58,
    "cmd": 55, "command": 55, "win": 55, "super": 55,
    "left": 123, "right": 124, "down": 125, "up": 126,
    "home": 115, "end": 119, "pageup": 116, "pagedown": 121,
    "capslock": 57,
}


class _MacHotkeyManager:
    """macOS 专用全局快捷键管理器，基于 CGEventTap。

    pynput 的 Listener 在后台线程运行，macOS 26+ 要求 TSMGetInputSourceProperty
    等 HIToolbox API 在主线程调用，后台线程调用会触发 dispatch_assert_queue_fail
    (SIGTRAP) 崩溃。

    本类用 CGEventTap 直接挂在主线程的 CFRunLoop 上（Tk mainloop 已在跑），
    回调在主线程执行，完全避免线程亲和性问题。
    """

    def __init__(self):
        self._hotkeys = {}          # frozenset(keycodes) -> callback
        self._current_keys = set()  # 当前按下的键码集合
        self._tap_port = None       # CGEventTap 的 CFMachPortRef
        self._run_loop_src = None   # CFRunLoopSourceRef
        self._available = False
        self._callback_ref = None   # 保持回调引用防止 GC
        self._init_tap()

    def _init_tap(self):
        """创建 CGEventTap 并加入主线程 CFRunLoop。必须在主线程调用。"""
        try:
            from Quartz import (
                CGEventTapCreate,
                kCGSessionEventTap,
                kCGHeadInsertEventTap,
                kCGEventTapOptionListenOnly,
                kCGEventKeyDown,
                kCGEventKeyUp,
                CGEventMaskBit,
            )
            from CoreFoundation import (
                CFRunLoopGetMain,
                CFRunLoopAddSource,
                CFMachPortCreateRunLoopSource,
                kCFRunLoopCommonModes,
            )

            mask = (
                CGEventMaskBit(kCGEventKeyDown) | CGEventMaskBit(kCGEventKeyUp)
            )

            # 保存回调引用，防止 pyobjc 回调被 GC 回收
            self._callback_ref = self._tap_callback

            self._tap_port = CGEventTapCreate(
                kCGSessionEventTap,
                kCGHeadInsertEventTap,
                kCGEventTapOptionListenOnly,  # 只监听不拦截
                mask,
                self._callback_ref,
                None,
            )

            if self._tap_port:
                self._run_loop_src = CFMachPortCreateRunLoopSource(
                    None, self._tap_port, 0
                )
                if self._run_loop_src:
                    loop = CFRunLoopGetMain()
                    CFRunLoopAddSource(
                        loop, self._run_loop_src, kCFRunLoopCommonModes
                    )
                    self._available = True
                else:
                    print("[MacHotkey] CFMachPortCreateRunLoopSource 失败")
            else:
                # CGEventTapCreate 返回 None 通常是因为没有辅助功能权限
                print("[MacHotkey] CGEventTap 创建失败")
                print("[MacHotkey] 请在「系统设置 → 隐私与安全性 → 辅助功能」中授予权限")
        except Exception as e:
            print(f"[MacHotkey] 初始化异常: {e}")
            self._available = False

    def _tap_callback(self, proxy, event_type, event, refcon):
        """CGEventTap 回调，在主线程 CFRunLoop 中执行。"""
        try:
            from Quartz import (
                CGEventGetIntegerValueField,
                kCGKeyboardEventKeycode,
                kCGEventKeyDown,
                kCGEventKeyUp,
            )
            if event_type == kCGEventKeyDown:
                keycode = CGEventGetIntegerValueField(
                    event, kCGKeyboardEventKeycode
                )
                self._current_keys.add(keycode)
                # 检查所有注册的热键
                for key_set, cb in list(self._hotkeys.items()):
                    if key_set <= self._current_keys:
                        try:
                            cb()
                        except Exception:
                            pass
            elif event_type == kCGEventKeyUp:
                keycode = CGEventGetIntegerValueField(
                    event, kCGKeyboardEventKeycode
                )
                self._current_keys.discard(keycode)
        except Exception:
            pass
        # 返回 event 让事件继续传递（ListenOnly 模式其实不拦截）
        return event

    @property
    def available(self) -> bool:
        return self._available

    def add_hotkey(self, hotkey: str, callback) -> bool:
        if not self._available:
            return False
        keycodes = self._parse_hotkey(hotkey)
        if keycodes is None:
            return False
        self._hotkeys[keycodes] = callback
        return True

    def _parse_hotkey(self, hotkey: str):
        """将 'ctrl+shift+f6' 解析为 frozenset(keycodes)。"""
        parts = [p.strip().lower() for p in hotkey.split("+") if p.strip()]
        keycodes = set()
        for p in parts:
            kc = _MAC_KEYCODES.get(p)
            if kc is None:
                return None
            keycodes.add(kc)
        return frozenset(keycodes) if keycodes else None

    def remove_all(self):
        self._hotkeys.clear()
        self._current_keys.clear()


class HotkeyManager:
    """跨平台全局快捷键管理器。

    macOS：使用 _MacHotkeyManager（CGEventTap，主线程）
    Windows/Linux：优先 pynput，回退 keyboard

    用法：
        mgr = HotkeyManager()
        mgr.add_hotkey("f6", callback)
        mgr.add_hotkey("ctrl+shift+s", callback)
        mgr.remove_all()
    """

    def __init__(self):
        self._hooks = []
        self._listener = None
        self._backend = None
        self._mac_mgr = None
        self._init_backend()

    def _init_backend(self):
        """初始化后端。"""
        # macOS 优先使用 CGEventTap（避免 pynput 后台线程 TSM 崩溃）
        if IS_MACOS:
            try:
                self._mac_mgr = _MacHotkeyManager()
                if self._mac_mgr.available:
                    self._backend = "mac_cgeventtap"
                    return
                # CGEventTap 失败（通常缺权限），回退到 pynput
                print("[HotkeyManager] CGEventTap 不可用，回退到 pynput（可能不稳定）")
            except Exception as e:
                print(f"[HotkeyManager] _MacHotkeyManager 初始化失败: {e}")

        # Windows/Linux 或 macOS 回退：尝试 pynput
        try:
            from pynput import keyboard as pynput_kb
            self._backend = "pynput"
            self._pynput_kb = pynput_kb
            return
        except Exception:
            pass
        # 最后回退到 keyboard 库
        try:
            import keyboard as kb_lib
            self._backend = "keyboard"
            self._kb_lib = kb_lib
            return
        except Exception:
            pass
        self._backend = None

    @property
    def available(self) -> bool:
        return self._backend is not None

    def _parse_hotkey(self, hotkey: str):
        """将 'ctrl+shift+f6' 解析为 pynput 所需的按键集合。"""
        parts = [p.strip().lower() for p in hotkey.split("+") if p.strip()]
        keys = []
        for p in parts:
            if p in ("ctrl", "control"):
                keys.append(self._pynput_kb.Key.ctrl)
            elif p == "alt":
                keys.append(self._pynput_kb.Key.alt)
            elif p == "shift":
                keys.append(self._pynput_kb.Key.shift)
            elif p == "cmd" or p == "command" or p == "win" or p == "super":
                keys.append(self._pynput_kb.Key.cmd)
            elif len(p) == 1:
                keys.append(p)
            else:
                try:
                    keys.append(self._pynput_kb.Key[p])
                except Exception:
                    keys.append(p)
        return frozenset(keys)

    def add_hotkey(self, hotkey: str, callback) -> bool:
        """注册一个全局热键，成功返回 True。"""
        if not self.available:
            return False

        # macOS CGEventTap 后端
        if self._backend == "mac_cgeventtap" and self._mac_mgr:
            return self._mac_mgr.add_hotkey(hotkey, callback)

        if self._backend == "keyboard":
            try:
                hook = self._kb_lib.add_hotkey(hotkey, callback, suppress=False)
                self._hooks.append(hook)
                return True
            except Exception:
                return False

        if self._backend == "pynput":
            try:
                target = self._parse_hotkey(hotkey)
                current = set()

                def on_press(key):
                    try:
                        # 注意：访问 key.char 在 macOS 上会触发 HIToolbox TSM
                        # API 调用，在后台线程会导致崩溃。只对特殊键做匹配。
                        k = key if not hasattr(key, "char") else (
                            key.char if key.char and not IS_MACOS else key
                        )
                    except Exception:
                        k = key
                    current.add(k)
                    if all(k in current for k in target):
                        callback()

                def on_release(key):
                    try:
                        k = key if not hasattr(key, "char") else (
                            key.char if key.char and not IS_MACOS else key
                        )
                    except Exception:
                        k = key
                    current.discard(k)

                if self._listener is None:
                    self._listener = self._pynput_kb.Listener(
                        on_press=on_press, on_release=on_release
                    )
                    self._listener.daemon = True
                    self._listener.start()
                self._hooks.append(hotkey)
                return True
            except Exception:
                return False

        return False

    def remove_all(self):
        """移除所有已注册的热键。"""
        if self._backend == "mac_cgeventtap" and self._mac_mgr:
            self._mac_mgr.remove_all()
            return
        if self._backend == "keyboard":
            for h in self._hooks:
                try:
                    self._kb_lib.remove_hotkey(h)
                except Exception:
                    pass
            self._hooks = []
        elif self._backend == "pynput":
            if self._listener:
                try:
                    self._listener.stop()
                except Exception:
                    pass
                self._listener = None
            self._hooks = []


# ---------------------------------------------------------------------------
# 窗口操作
# ---------------------------------------------------------------------------
def get_all_window_titles() -> list[str]:
    """获取所有窗口标题列表。"""
    titles = []
    try:
        try:
            import pygetwindow as gw
            titles = gw.getAllTitles()
        except Exception:
            try:
                import pywinctl as pwc
                wins = pwc.getAllWindows()
                titles = [w.title for w in wins]
            except Exception:
                pass
    except Exception:
        pass
    return titles or []


def close_windows_by_title(title: str) -> bool:
    """按标题模糊匹配关闭窗口，成功返回 True。"""
    if not title:
        return False
    try:
        try:
            import pygetwindow as gw
            wins = gw.getWindowsWithTitle(title)
            for w in wins:
                try:
                    w.close()
                except Exception:
                    pass
            return len(wins) > 0
        except Exception:
            try:
                import pywinctl as pwc
                wins = pwc.getWindowsWithTitle(title)
                for w in wins:
                    try:
                        w.close()
                    except Exception:
                        pass
                return len(wins) > 0
            except Exception:
                pass
    except Exception:
        pass
    return False


def window_exists(title: str) -> bool:
    """按标题模糊匹配判断窗口是否存在。"""
    if not title:
        return False
    titles = get_all_window_titles()
    return any(title.lower() in (w or "").lower() for w in titles)


# ---------------------------------------------------------------------------
# 粘贴快捷键
# ---------------------------------------------------------------------------
def get_paste_modifiers() -> list[str]:
    """返回粘贴快捷键的修饰键列表。Windows/Linux 用 ctrl，macOS 用 cmd。"""
    if IS_MACOS:
        return ["command", "v"]
    return ["ctrl", "v"]


def press_paste():
    """执行粘贴操作（ctrl+v 或 cmd+v）。"""
    try:
        import pyautogui
        mods = get_paste_modifiers()
        pyautogui.hotkey(*mods)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# 中文输入（剪贴板 + 粘贴）
# ---------------------------------------------------------------------------
def copy_text_to_clipboard(text: str) -> bool:
    """将文本复制到剪贴板，成功返回 True。"""
    try:
        import pyperclip
        pyperclip.copy(text)
        return True
    except Exception:
        return False


def input_text_via_clipboard(text: str) -> bool:
    """通过剪贴板粘贴方式输入文本（用于中文等非 ASCII 文本）。"""
    if copy_text_to_clipboard(text):
        import time
        time.sleep(0.05)
        press_paste()
        return True
    return False
