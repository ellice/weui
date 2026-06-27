"""键鼠模拟配套功能：慢速输入、组合快捷键、鼠标点击/拖拽滚动。

封装 pywinauto.keyboard / mouse，统一处理特殊字符转义与「模拟真人」节奏。
"""

from __future__ import annotations

import random
import time
from typing import Optional, Tuple

try:
    from pywinauto.keyboard import send_keys as _send_keys
    from pywinauto import mouse as _mouse

    _HAS_PYWINAUTO = True
except Exception:  # pragma: no cover - 非 Windows 环境
    _HAS_PYWINAUTO = False

    def _send_keys(*_args, **_kwargs):  # type: ignore
        raise RuntimeError("pywinauto 未安装，无法模拟键盘（仅 Windows）")

    class _MouseStub:  # type: ignore
        def click(self, *a, **k):
            raise RuntimeError("pywinauto 未安装，无法模拟鼠标（仅 Windows）")

        double_click = click
        right_click = click
        press = click
        release = click
        move = click
        scroll = click

    _mouse = _MouseStub()


# pywinauto send_keys 中需要转义的特殊字符
_ESCAPE_CHARS = set("^+%~(){}[]")


def escape_text(text: str) -> str:
    """转义 send_keys 的特殊字符，并把换行转成 {ENTER}。

    注意：聊天输入框里「换行」用 Shift+Enter，单独 Enter 会直接发送。
    因此这里默认把 \n 转成 +{ENTER}（Shift+Enter）。
    """
    out = []
    for ch in text:
        if ch == "\n":
            out.append("+{ENTER}")
        elif ch == "\t":
            out.append("{TAB}")
        elif ch in _ESCAPE_CHARS:
            out.append("{" + ch + "}")
        else:
            out.append(ch)
    return "".join(out)


def type_text(text: str, with_spaces: bool = True, with_newlines: bool = True) -> None:
    """一次性把文本通过键盘事件输入（已自动转义特殊符号）。

    适合短文本；大段文本/含复杂符号建议走剪贴板粘贴 (clipboard.paste)。
    """
    keys = escape_text(text)
    _send_keys(keys, with_spaces=with_spaces, with_newlines=with_newlines, pause=0)


def type_text_human(
    text: str,
    min_delay: float = 0.03,
    max_delay: float = 0.12,
) -> None:
    """逐字符慢速输入，模拟真人打字，降低风控风险。"""
    for ch in text:
        if ch == "\n":
            _send_keys("+{ENTER}", pause=0)
        elif ch == "\t":
            _send_keys("{TAB}", pause=0)
        elif ch in _ESCAPE_CHARS:
            _send_keys("{" + ch + "}", pause=0)
        elif ch == " ":
            _send_keys("{SPACE}", pause=0)
        else:
            _send_keys(ch, with_spaces=True, pause=0)
        time.sleep(random.uniform(min_delay, max_delay))


def hotkey(keys: str) -> None:
    """发送原始组合键，例如：
    - 全选: hotkey('^a')
    - 复制: hotkey('^c')   粘贴: hotkey('^v')
    - 回车: hotkey('{ENTER}')
    - 退格: hotkey('{BACKSPACE}')
    - 退出/收起: hotkey('{ESC}')
    - 换行: hotkey('+{ENTER}')
    """
    _send_keys(keys, pause=0)


# —— 语义化快捷键封装 ——
def press_enter() -> None:
    _send_keys("{ENTER}", pause=0)


def press_shift_enter() -> None:
    """聊天框内换行。"""
    _send_keys("+{ENTER}", pause=0)


def press_tab() -> None:
    _send_keys("{TAB}", pause=0)


def press_esc() -> None:
    _send_keys("{ESC}", pause=0)


def press_backspace(count: int = 1) -> None:
    _send_keys("{BACKSPACE " + str(count) + "}", pause=0)


def select_all() -> None:
    _send_keys("^a", pause=0)


def copy() -> None:
    _send_keys("^c", pause=0)


def paste() -> None:
    _send_keys("^v", pause=0)


def cut() -> None:
    _send_keys("^x", pause=0)


def mention(name: str = "") -> None:
    """触发 @ 选人面板，可选直接输入名字。"""
    _send_keys("@", pause=0)
    if name:
        time.sleep(0.3)
        type_text(name)


# —— 鼠标模拟 ——
def click(coords: Tuple[int, int]) -> None:
    _mouse.click(button="left", coords=coords)


def right_click(coords: Tuple[int, int]) -> None:
    _mouse.right_click(coords=coords)


def double_click(coords: Tuple[int, int]) -> None:
    _mouse.double_click(button="left", coords=coords)


def move(coords: Tuple[int, int]) -> None:
    _mouse.move(coords=coords)


def scroll(coords: Tuple[int, int], wheel_dist: int = -3) -> None:
    """在指定坐标滚动鼠标滚轮。

    wheel_dist > 0 向上（看更早的消息），< 0 向下。
    """
    _mouse.scroll(coords=coords, wheel_dist=wheel_dist)


def drag(start: Tuple[int, int], end: Tuple[int, int], duration: float = 0.3) -> None:
    """从 start 拖拽到 end，用于拖动滚动条翻页等。"""
    _mouse.press(button="left", coords=start)
    steps = max(1, int(duration / 0.02))
    for i in range(1, steps + 1):
        x = int(start[0] + (end[0] - start[0]) * i / steps)
        y = int(start[1] + (end[1] - start[1]) * i / steps)
        _mouse.move(coords=(x, y))
        time.sleep(0.02)
    _mouse.release(button="left", coords=end)


def random_sleep(min_seconds: float = 0.5, max_seconds: float = 1.5) -> None:
    """随机延时，模拟真人操作间隔，防风控。"""
    time.sleep(random.uniform(min_seconds, max_seconds))
