# -*- coding: utf-8 -*-
"""键鼠模拟配套功能。

封装 pywinauto 的键盘 / 鼠标接口，并补充：
- 真人慢速输入（防风控）
- 常用组合快捷键
- 精准点击 / 右键 / 双击 / 拖拽滚动
"""

from __future__ import annotations

import random
import time
from typing import Iterable, Optional, Tuple

try:
    from pywinauto import keyboard as _kb
    from pywinauto import mouse as _mouse
except Exception:  # pragma: no cover - 非 Windows / 未安装
    _kb = None
    _mouse = None


# --------------------------------------------------------------------------- #
# 特殊字符转义：pywinauto send_keys 中 {}()+^%~ 等是控制符，需转义
# --------------------------------------------------------------------------- #
_SPECIAL = set("^+%~(){}[]")


def escape_keys(text: str) -> str:
    """转义 send_keys 的特殊控制字符，使其按字面量输入。"""
    out = []
    for ch in text:
        if ch in _SPECIAL:
            out.append("{" + ch + "}")
        else:
            out.append(ch)
    return "".join(out)


def _require_kb():
    if _kb is None:
        raise RuntimeError("pywinauto 未安装或当前非 Windows 环境，无法模拟键盘")
    return _kb


def _require_mouse():
    if _mouse is None:
        raise RuntimeError("pywinauto 未安装或当前非 Windows 环境，无法模拟鼠标")
    return _mouse


def send_keys(keys: str, pause: float = 0.02, with_spaces: bool = True,
              with_newlines: bool = True) -> None:
    """发送原始按键序列（不做字面量转义，可包含 send_keys 控制符）。"""
    _require_kb().send_keys(
        keys, pause=pause, with_spaces=with_spaces, with_newlines=with_newlines
    )


def type_text(text: str, *, human: bool = False,
              min_delay: float = 0.02, max_delay: float = 0.08) -> None:
    """以字面量方式输入文本（自动转义特殊符号）。

    :param human: 是否模拟真人逐字慢速输入（防风控）。
    :param min_delay: 真人模式下每个字符的最小间隔。
    :param max_delay: 真人模式下每个字符的最大间隔。
    """
    kb = _require_kb()
    if not human:
        kb.send_keys(escape_keys(text), with_spaces=True, with_newlines=True)
        return

    for ch in text:
        if ch == "\n":
            # 软换行（Shift+Enter），避免触发发送
            kb.send_keys("+{ENTER}")
        else:
            kb.send_keys(escape_keys(ch), with_spaces=True)
        time.sleep(random.uniform(min_delay, max_delay))


def press_enter() -> None:
    """回车（用于发送消息）。"""
    _require_kb().send_keys("{ENTER}")


def press_shift_enter() -> None:
    """软换行（输入框内换行而不发送）。"""
    _require_kb().send_keys("+{ENTER}")


def press_esc() -> None:
    _require_kb().send_keys("{ESC}")


def press_tab() -> None:
    _require_kb().send_keys("{TAB}")


def press_backspace(count: int = 1) -> None:
    _require_kb().send_keys("{BACKSPACE}" * max(1, count))


def select_all() -> None:
    """Ctrl+A 全选。"""
    _require_kb().send_keys("^a")


def copy() -> None:
    """Ctrl+C 复制。"""
    _require_kb().send_keys("^c")


def paste() -> None:
    """Ctrl+V 粘贴。"""
    _require_kb().send_keys("^v")


def cut() -> None:
    """Ctrl+X 剪切。"""
    _require_kb().send_keys("^x")


def hotkey(*keys: str) -> None:
    """发送任意组合键，例如 ``hotkey('^', 'a')`` 或 ``hotkey('%', 's')``。

    约定使用 send_keys 修饰符：``^``=Ctrl，``+``=Shift，``%``=Alt。
    """
    _require_kb().send_keys("".join(keys))


def at_someone(name: str = "", human: bool = False) -> None:
    """在群聊中触发 @ 菜单；若传入 name 则输入名称并回车选中。"""
    kb = _require_kb()
    kb.send_keys("@")
    if name:
        time.sleep(0.3)
        type_text(name, human=human)
        time.sleep(0.4)
        kb.send_keys("{ENTER}")


# --------------------------------------------------------------------------- #
# 鼠标操作
# --------------------------------------------------------------------------- #
def click(coords: Tuple[int, int], button: str = "left") -> None:
    """在屏幕绝对坐标处点击。"""
    _require_mouse().click(button=button, coords=coords)


def right_click(coords: Tuple[int, int]) -> None:
    _require_mouse().right_click(coords=coords)


def double_click(coords: Tuple[int, int]) -> None:
    _require_mouse().double_click(coords=coords)


def move(coords: Tuple[int, int]) -> None:
    _require_mouse().move(coords=coords)


def scroll(coords: Tuple[int, int], wheel_dist: int = -3) -> None:
    """在指定坐标处滚动鼠标滚轮。

    :param wheel_dist: 正值向上、负值向下；数值越大滚动越多。
    """
    _require_mouse().scroll(coords=coords, wheel_dist=wheel_dist)


def drag(start: Tuple[int, int], end: Tuple[int, int],
         button: str = "left") -> None:
    """从 start 拖拽到 end（可用于拖动滚动条翻页）。"""
    m = _require_mouse()
    m.press(button=button, coords=start)
    time.sleep(0.1)
    m.move(coords=end)
    time.sleep(0.1)
    m.release(button=button, coords=end)


def sleep_jitter(base: float = 0.5, jitter: float = 0.3) -> None:
    """带抖动的随机延时，模拟真人节奏、降低风控风险。"""
    time.sleep(base + random.uniform(0, jitter))
