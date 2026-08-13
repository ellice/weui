"""键鼠模拟工具（第五类能力）。

基于 pywinauto 的 ``keyboard`` / ``mouse`` 子模块封装：
- 全局快捷键、组合键
- 精准点击、右键、双击、拖拽
- 模拟真人慢速输入（随机延时防风控）
"""

from __future__ import annotations

import random
import time
from typing import Iterable, Tuple

from .config import Timing


def _send_keys(keys: str, pause: float = 0.0) -> None:
    """底层发送按键序列（pywinauto 语法）。"""
    from pywinauto.keyboard import send_keys as _sk

    _sk(keys, pause=pause, with_spaces=True, with_tabs=True, with_newlines=False)


# --------------------------------------------------------------------------- #
# 键盘
# --------------------------------------------------------------------------- #
def press_enter() -> None:
    """回车（微信默认发送）。"""
    _send_keys("{ENTER}")


def press_esc() -> None:
    _send_keys("{ESC}")


def press_tab() -> None:
    _send_keys("{TAB}")


def press_backspace(times: int = 1) -> None:
    _send_keys("{BACKSPACE}" * max(1, times))


def new_line() -> None:
    """在输入框内换行（不发送）。微信中为 Shift+Enter。"""
    _send_keys("+{ENTER}")


def select_all() -> None:
    """Ctrl+A 全选。"""
    _send_keys("^a")


def copy() -> None:
    """Ctrl+C 复制。"""
    _send_keys("^c")


def paste() -> None:
    """Ctrl+V 粘贴。"""
    _send_keys("^v")


def cut() -> None:
    """Ctrl+X 剪切。"""
    _send_keys("^x")


def at_someone(name: str = "") -> None:
    """触发 @ 面板，可选紧跟输入昵称。"""
    _send_keys("@")
    if name:
        # @ 之后逐字输入昵称，交由调用方自行选择候选
        for ch in name:
            _send_keys(_escape(ch))


def hotkey(combo: str) -> None:
    """发送任意组合键，直接使用 pywinauto 语法。

    例如：``hotkey("^a")``、``hotkey("+{ENTER}")``、``hotkey("%{F4}")``。
    """
    _send_keys(combo)


def _escape(text: str) -> str:
    """转义 pywinauto send_keys 的特殊字符。"""
    specials = "^+%~(){}[]"
    out = []
    for ch in text:
        if ch in specials:
            out.append("{" + ch + "}")
        else:
            out.append(ch)
    return "".join(out)


def type_text(text: str, timing: Timing | None = None, human: bool = True) -> None:
    """把文本逐字输入到当前焦点控件。

    :param human: 为 True 时按 ``timing`` 配置加入随机延时，模拟真人输入。
    """
    timing = timing or Timing()
    for ch in text:
        if ch == "\n":
            new_line()
        else:
            _send_keys(_escape(ch))
        if human:
            time.sleep(
                random.uniform(timing.typing_min_delay, timing.typing_max_delay)
            )


# --------------------------------------------------------------------------- #
# 鼠标
# --------------------------------------------------------------------------- #
def click(coords: Tuple[int, int]) -> None:
    """在屏幕坐标处单击左键。"""
    from pywinauto import mouse

    mouse.click(button="left", coords=coords)


def right_click(coords: Tuple[int, int]) -> None:
    from pywinauto import mouse

    mouse.click(button="right", coords=coords)


def double_click(coords: Tuple[int, int]) -> None:
    from pywinauto import mouse

    mouse.double_click(button="left", coords=coords)


def move(coords: Tuple[int, int]) -> None:
    from pywinauto import mouse

    mouse.move(coords=coords)


def scroll(coords: Tuple[int, int], wheel_dist: int = -3) -> None:
    """在指定坐标滚动滚轮。``wheel_dist`` 为负向下、为正向上。"""
    from pywinauto import mouse

    mouse.scroll(coords=coords, wheel_dist=wheel_dist)


def drag(start: Tuple[int, int], end: Tuple[int, int]) -> None:
    """按住左键从 start 拖拽到 end（可用于拖动滚动条翻页）。"""
    from pywinauto import mouse

    mouse.press(button="left", coords=start)
    time.sleep(0.1)
    mouse.move(coords=end)
    time.sleep(0.1)
    mouse.release(button="left", coords=end)
