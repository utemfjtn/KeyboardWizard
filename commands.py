# -*- coding: utf-8 -*-
"""
命令定义模块
定义所有可用的指令类型、参数结构、默认值以及序列化/反序列化逻辑。
每条命令在列表中的结构为：
    {
        "type":   指令类型字符串,
        "params": dict,        # 该类型所需的参数
        "enabled": bool,       # 是否启用
        "comment": str,        # 备注
    }
"""
from __future__ import annotations

# ----------------------------------------------------------------------------
# 指令类型常量
# ----------------------------------------------------------------------------
KEY = "key"                        # 按键（支持组合键，如 "ctrl+s"）
CLICK = "click"                    # 鼠标点击指定坐标
IMAGE_CLICK = "image_click"        # 在屏幕中查找图片并点击
IMAGE_WAIT = "image_wait"          # 等待图片出现
DELAY = "delay"                    # 延时（毫秒）
REPEAT = "repeat"                  # 重复开始
END_REPEAT = "end_repeat"          # 重复结束
IF_IMAGE = "if_image"              # 如果图片存在
IF_NOT_IMAGE = "if_not_image"      # 如果图片不存在
IF_WINDOW = "if_window"            # 如果窗口存在
END_IF = "end_if"                  # 条件结束
LABEL = "label"                    # 标签（跳转目标）
GOTO = "goto"                      # 跳转到标签
LOOP = "loop"                      # 无限/有限循环（基于 label+goto 的高层封装）
INPUT_TEXT = "input_text"          # 输入文本
SET_VAR = "set_var"                # 设置变量

# 所有指令类型
ALL_TYPES = [
    KEY, CLICK, IMAGE_CLICK, IMAGE_WAIT, INPUT_TEXT, SET_VAR,
    DELAY,
    REPEAT, END_REPEAT,
    IF_IMAGE, IF_NOT_IMAGE, IF_WINDOW, END_IF,
    LABEL, GOTO,
]

# 指令中文显示名
TYPE_NAMES = {
    KEY:          "按键",
    CLICK:        "鼠标点击",
    IMAGE_CLICK:  "点击图片",
    IMAGE_WAIT:   "等待图片",
    INPUT_TEXT:   "输入文本",
    SET_VAR:      "设置变量",
    DELAY:        "延时",
    REPEAT:       "重复开始",
    END_REPEAT:   "重复结束",
    IF_IMAGE:     "如果图片存在",
    IF_NOT_IMAGE: "如果图片不存在",
    IF_WINDOW:    "如果窗口存在",
    END_IF:       "条件结束",
    LABEL:        "标签",
    GOTO:         "跳转",
}

# 每种指令需要的参数键及默认值
PARAM_SCHEMA = {
    KEY:          {"key": "enter", "hold": 0.0},
    CLICK:        {"x": 0, "y": 0, "button": "left", "clicks": 1, "interval": 0.0},
    IMAGE_CLICK:  {"image": "", "confidence": 0.8, "button": "left",
                   "clicks": 1, "region": None, "offset_x": 0, "offset_y": 0},
    IMAGE_WAIT:   {"image": "", "confidence": 0.8, "timeout": 10.0, "region": None},
    INPUT_TEXT:   {"text": "", "interval": 0.0},
    SET_VAR:      {"name": "var1", "value": ""},
    DELAY:        {"ms": 1000},
    REPEAT:       {"count": 3},
    END_REPEAT:   {},
    IF_IMAGE:     {"image": "", "confidence": 0.8, "region": None},
    IF_NOT_IMAGE: {"image": "", "confidence": 0.8, "region": None},
    IF_WINDOW:    {"title": ""},
    END_IF:       {},
    LABEL:        {"name": "label1"},
    GOTO:         {"name": "label1"},
}

# 鼠标按键选项
MOUSE_BUTTONS = ["left", "right", "middle"]


def make_command(cmd_type: str) -> dict:
    """创建一条默认命令。"""
    schema = PARAM_SCHEMA.get(cmd_type, {})
    # 深拷贝默认值，避免可变对象共享
    import copy
    params = copy.deepcopy(schema)
    return {
        "type": cmd_type,
        "params": params,
        "enabled": True,
        "comment": "",
    }


def describe(cmd: dict) -> str:
    """生成命令的人类可读摘要，用于列表显示。"""
    t = cmd.get("type", "")
    p = cmd.get("params", {})
    name = TYPE_NAMES.get(t, t)
    if t == KEY:
        hold = f"，按住{p.get('hold',0)}s" if p.get("hold") else ""
        return f"{name}：{p.get('key','')}{hold}"
    if t == CLICK:
        return f"{name}：({p.get('x',0)},{p.get('y',0)}) {p.get('button','left')}×{p.get('clicks',1)}"
    if t == IMAGE_CLICK:
        img = p.get("image", "")
        img = img.split("/")[-1].split("\\")[-1] if img else "(未设置)"
        return f"{name}：{img} 置信度{p.get('confidence',0.8)}"
    if t == IMAGE_WAIT:
        img = p.get("image", "")
        img = img.split("/")[-1].split("\\")[-1] if img else "(未设置)"
        return f"{name}：{img} 超时{p.get('timeout',10)}s"
    if t == INPUT_TEXT:
        txt = p.get("text", "")
        txt = (txt[:12] + "…") if len(txt) > 12 else txt
        return f"{name}：\"{txt}\""
    if t == DELAY:
        return f"{name}：{p.get('ms',1000)}ms"
    if t == REPEAT:
        return f"{name}：{p.get('count',3)}次"
    if t in (IF_IMAGE, IF_NOT_IMAGE):
        img = p.get("image", "")
        img = img.split("/")[-1].split("\\")[-1] if img else "(未设置)"
        return f"{name}：{img}"
    if t == IF_WINDOW:
        return f"{name}：\"{p.get('title','')}\""
    if t == LABEL:
        return f"{name}：{p.get('name','')}"
    if t == GOTO:
        return f"{name}：{p.get('name','')}"
    if t == SET_VAR:
        var_name = p.get("name", "")
        value = p.get("value", "")
        return f"{name}：{var_name}={value}"
    return name


def to_dict(cmd: dict) -> dict:
    """序列化为可 JSON 保存的字典。"""
    return {
        "type": cmd["type"],
        "params": cmd["params"],
        "enabled": cmd.get("enabled", True),
        "comment": cmd.get("comment", ""),
    }


def from_dict(data: dict) -> dict:
    """从字典恢复命令，补全缺失字段。"""
    t = data.get("type", KEY)
    schema = PARAM_SCHEMA.get(t, {})
    import copy
    params = copy.deepcopy(schema)
    params.update(data.get("params", {}))
    return {
        "type": t,
        "params": params,
        "enabled": data.get("enabled", True),
        "comment": data.get("comment", ""),
    }
