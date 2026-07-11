"""键鼠模拟工具。

封装 pywinauto 的键盘 / 鼠标接口，并提供：

    - 组合快捷键（Ctrl+C/V/A、Enter、ESC、Tab、Backspace 等）
    - 模拟真人的慢速输入（逐字符 + 随机延时，降低风控风险）
    - 精准鼠标点击 / 右键 / 双击
    - 鼠标滚轮上下滚动（翻阅聊天记录）

pywinauto 的 ``send_keys`` 中部分字符是特殊字符，需要转义，见 :func:`escape_keys`。
"""

from __future__ import annotations

import random
import time
from typing import Optional, Tuple

try:
    from pywinauto.keyboard import send_keys as _send_keys  # type: ignore
    from pywinauto.mouse import (  # type: ignore
        click as _mouse_click,
        double_click as _mouse_double_click,
        right_click as _mouse_right_click,
        scroll as _mouse_scroll,
    )

    _HAS_PYWINAUTO = True
except Exception:  # pragma: no cover - 非 Windows 环境
    _HAS_PYWINAUTO = False

    def _send_keys(*_a, **_k):  # type: ignore
        raise RuntimeError("send_keys 需要 pywinauto（仅 Windows 支持）")


# send_keys 中需要转义的特殊字符（否则会被解释为控制指令）
_SPECIAL_CHARS = set("^+%~(){}[]")


def escape_keys(text: str) -> str:
    """转义 send_keys 中的特殊字符。

    pywinauto 中 ``^ + % ~ ( ) { } [ ]`` 具有特殊含义，
    需要用花括号包裹才能作为普通字符输入。
    """
    result = []
    for ch in text:
        if ch in _SPECIAL_CHARS:
            result.append("{%s}" % ch)
        else:
            result.append(ch)
    return "".join(result)


def send_keys(keys: str, pause: float = 0.02, with_spaces: bool = True) -> None:
    """发送按键序列（原样，keys 中的控制符会被解释）。

    :param keys: pywinauto 语法的按键串，如 ``"^a"``（Ctrl+A）、``"{ENTER}"``
    :param pause: 每个按键之间的停顿
    :param with_spaces: 是否保留空格
    """
    _send_keys(keys, pause=pause, with_spaces=with_spaces)


def type_text(
    text: str,
    human_like: bool = False,
    min_delay: float = 0.03,
    max_delay: float = 0.12,
) -> None:
    """输入纯文本（自动转义特殊字符）。

    :param text: 要输入的文字，支持换行（``\\n`` 会转换为 ``{ENTER}``，
        在微信中通常配合 Shift+Enter 才是软换行，这里用于普通逐段输入）
    :param human_like: 是否模拟真人逐字符慢速输入（防风控）
    :param min_delay: 慢速输入时单字符最小延时
    :param max_delay: 慢速输入时单字符最大延时
    """
    if not human_like:
        # 将换行转换为 send_keys 语法
        payload = escape_keys(text).replace("\n", "{ENTER}")
        _send_keys(payload, with_spaces=True, pause=0.01)
        return

    for ch in text:
        if ch == "\n":
            _send_keys("{ENTER}", pause=0.0)
        else:
            _send_keys(escape_keys(ch), with_spaces=True, pause=0.0)
        time.sleep(random.uniform(min_delay, max_delay))


# ---- 常用组合快捷键 ----

def select_all() -> None:
    """全选 Ctrl+A。"""
    _send_keys("^a")


def copy() -> None:
    """复制 Ctrl+C。"""
    _send_keys("^c")


def paste() -> None:
    """粘贴 Ctrl+V。"""
    _send_keys("^v")


def cut() -> None:
    """剪切 Ctrl+X。"""
    _send_keys("^x")


def enter() -> None:
    """回车。"""
    _send_keys("{ENTER}")


def newline() -> None:
    """软换行（微信中为 Shift+Enter，不发送消息）。"""
    _send_keys("+{ENTER}")


def esc() -> None:
    """ESC。"""
    _send_keys("{ESC}")


def tab() -> None:
    """Tab。"""
    _send_keys("{TAB}")


def backspace(times: int = 1) -> None:
    """退格删除。"""
    _send_keys("{BACKSPACE %d}" % times)


def at_someone(name: str) -> None:
    """输入 @ 并跟上名字（群聊中触发 @ 提及）。"""
    _send_keys("@")
    time.sleep(0.3)
    type_text(name)


# ---- 鼠标 ----

def click(coords: Tuple[int, int], button: str = "left") -> None:
    """在屏幕坐标处单击。"""
    _mouse_click(button=button, coords=coords)


def right_click(coords: Tuple[int, int]) -> None:
    """右键单击。"""
    _mouse_right_click(coords=coords)


def double_click(coords: Tuple[int, int]) -> None:
    """双击。"""
    _mouse_double_click(coords=coords)


def scroll(coords: Tuple[int, int], wheel_dist: int) -> None:
    """在坐标处滚动滚轮。

    :param wheel_dist: 正数向上滚（看更早的历史消息），负数向下滚
    """
    _mouse_scroll(coords=coords, wheel_dist=wheel_dist)
