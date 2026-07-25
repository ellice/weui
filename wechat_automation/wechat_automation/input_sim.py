"""键鼠模拟配套功能。

对 pywinauto 的 ``keyboard`` / ``mouse`` 模块做一层封装，提供：

* 逐字符慢速输入（模拟真人、规避风控）
* 常用组合键与特殊键（Enter、换行、Tab、ESC、@、Ctrl+C/V/A、Backspace）
* 精准鼠标点击 / 右键 / 双击 / 拖拽
* 鼠标滚轮上下翻页（用于滚动聊天记录 / 会话列表）

pywinauto 的 ``send_keys`` 中部分字符具有特殊含义（``+ ^ % ~ ( ) { }``），
本模块提供转义处理，保证任意文本可原样输入。
"""

from __future__ import annotations

import random
import time
from typing import Optional, Tuple

try:
    from pywinauto import keyboard as _kb  # type: ignore
    from pywinauto import mouse as _mouse  # type: ignore

    _HAS_PYWINAUTO = True
except Exception:  # pragma: no cover - 非 Windows / 未安装
    _HAS_PYWINAUTO = False


# send_keys 语法中的特殊字符，需要用 {} 包裹转义。
_SPECIAL_CHARS = set("+^%~(){}[]")


def escape_keys(text: str) -> str:
    """转义 ``send_keys`` 中的特殊字符，使文本按字面量输入。"""
    out = []
    for ch in text:
        if ch in _SPECIAL_CHARS:
            out.append("{" + ch + "}")
        else:
            out.append(ch)
    return "".join(out)


def _ensure_backend() -> None:
    if not _HAS_PYWINAUTO:
        raise RuntimeError(
            "pywinauto 未安装或当前非 Windows 环境，无法进行键鼠模拟。"
        )


def send_keys(keys: str, pause: float = 0.02, with_spaces: bool = True) -> None:
    """发送按键序列（原始 send_keys 语法，调用方自行负责转义）。"""
    _ensure_backend()
    _kb.send_keys(keys, pause=pause, with_spaces=with_spaces)


def type_text(
    text: str,
    interval_min: float = 0.02,
    interval_max: float = 0.08,
) -> None:
    """逐字符慢速输入文本，字符间随机停顿以模拟真人。

    文本中的换行会被转换为 Shift+Enter（软换行），避免逐行触发发送。
    特殊字符会自动转义。
    """
    _ensure_backend()
    for ch in text:
        if ch == "\n":
            _kb.send_keys("+{ENTER}")  # Shift+Enter 软换行
        elif ch == "\t":
            _kb.send_keys("{TAB}")
        else:
            _kb.send_keys(escape_keys(ch), with_spaces=True)
        time.sleep(random.uniform(interval_min, max(interval_min, interval_max)))


def press_enter() -> None:
    """回车（在微信中默认即为发送）。"""
    _ensure_backend()
    _kb.send_keys("{ENTER}")


def press_shift_enter() -> None:
    """Shift+Enter 软换行。"""
    _ensure_backend()
    _kb.send_keys("+{ENTER}")


def press_tab() -> None:
    _ensure_backend()
    _kb.send_keys("{TAB}")


def press_esc() -> None:
    _ensure_backend()
    _kb.send_keys("{ESC}")


def press_backspace(count: int = 1) -> None:
    _ensure_backend()
    _kb.send_keys("{BACKSPACE}" * max(1, count))


def press_at() -> None:
    """输入 @ 符号（用于群聊 @ 成员，随后可继续输入昵称并选择）。"""
    _ensure_backend()
    _kb.send_keys("@")


def select_all() -> None:
    """Ctrl+A 全选。"""
    _ensure_backend()
    _kb.send_keys("^a")


def copy() -> None:
    """Ctrl+C 复制。"""
    _ensure_backend()
    _kb.send_keys("^c")


def paste() -> None:
    """Ctrl+V 粘贴（用于粘贴文本 / 文件 / 图片）。"""
    _ensure_backend()
    _kb.send_keys("^v")


def clear_edit() -> None:
    """清空当前焦点输入框：Ctrl+A 全选后 Backspace 删除。"""
    _ensure_backend()
    _kb.send_keys("^a")
    time.sleep(0.05)
    _kb.send_keys("{BACKSPACE}")


def click(x: int, y: int, button: str = "left", double: bool = False) -> None:
    """在屏幕坐标 (x, y) 进行精准鼠标点击。"""
    _ensure_backend()
    coords = (int(x), int(y))
    if double:
        _mouse.double_click(button=button, coords=coords)
    else:
        _mouse.click(button=button, coords=coords)


def right_click(x: int, y: int) -> None:
    """右键单击。"""
    click(x, y, button="right")


def double_click(x: int, y: int) -> None:
    """双击。"""
    click(x, y, button="left", double=True)


def scroll(coords: Tuple[int, int], wheel_dist: int) -> None:
    """在指定坐标处滚动鼠标滚轮。

    Args:
        coords: 滚动发生的屏幕坐标 (x, y)。
        wheel_dist: 正数向上、负数向下，绝对值为滚动步数。
    """
    _ensure_backend()
    _mouse.scroll(coords=coords, wheel_dist=wheel_dist)


def drag(
    start: Tuple[int, int],
    end: Tuple[int, int],
    button: str = "left",
) -> None:
    """鼠标拖拽：从 start 按下拖到 end 释放。"""
    _ensure_backend()
    _mouse.press(button=button, coords=start)
    time.sleep(0.1)
    _mouse.move(coords=end)
    time.sleep(0.1)
    _mouse.release(button=button, coords=end)
