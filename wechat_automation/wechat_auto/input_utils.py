"""键鼠模拟工具：慢速输入、快捷键、鼠标点击 / 拖拽滚动。

统一在这里封装 ``pywinauto.keyboard`` / ``pywinauto.mouse``，并提供
"模拟真人"的延时输入，降低触发风控的概率。
"""

from __future__ import annotations

import logging
import random
import time
from typing import Optional, Sequence, Tuple

logger = logging.getLogger("wechat_auto")


def _keyboard():
    from pywinauto import keyboard  # type: ignore

    return keyboard


def _mouse():
    from pywinauto import mouse  # type: ignore

    return mouse


def _escape_keys(text: str) -> str:
    """转义 pywinauto send_keys 的特殊字符 ``{}()+^%~[]``。"""

    special = set("{}()+^%~[]")
    out = []
    for ch in text:
        if ch in special:
            out.append("{" + ch + "}")
        else:
            out.append(ch)
    return "".join(out)


def send_keys(keys: str, pause: float = 0.02, with_spaces: bool = True) -> None:
    """发送原始快捷键序列（不转义），例如 ``^a``、``{ENTER}``、``%{F4}``。

    这是对 ``pywinauto.keyboard.send_keys`` 的直通封装，调用者需自行了解
    其语法：``^``=Ctrl，``%``=Alt，``+``=Shift，``{ENTER}``/``{TAB}``/``{ESC}`` 等。
    """

    _keyboard().send_keys(keys, pause=pause, with_spaces=with_spaces)


def type_text(
    text: str,
    slow: bool = True,
    min_delay: float = 0.03,
    max_delay: float = 0.12,
) -> None:
    """逐字符输入文本，自动转义特殊字符，兼容空格与换行。

    Parameters
    ----------
    slow:
        为 ``True`` 时在字符间加入随机延时，模拟真人打字防风控；
        为 ``False`` 时一次性发送（更快）。
    min_delay / max_delay:
        慢速模式下每个字符之间的随机延时范围（秒）。
    """

    kb = _keyboard()
    if not slow:
        # 换行用 {ENTER}，其余字符转义后一次发送
        kb.send_keys(_prepare_multiline(text), with_spaces=True, pause=0.01)
        return

    for ch in text:
        if ch == "\n":
            # 聊天框中换行 = Shift+Enter，避免直接发送
            kb.send_keys("+{ENTER}")
        elif ch == "\t":
            kb.send_keys("{TAB}")
        else:
            kb.send_keys(_escape_keys(ch), with_spaces=True)
        time.sleep(random.uniform(min_delay, max_delay))


def _prepare_multiline(text: str) -> str:
    """把普通文本转换为 send_keys 语法：换行->Shift+Enter，制表->{TAB}。"""

    parts = []
    for ch in text:
        if ch == "\n":
            parts.append("+{ENTER}")
        elif ch == "\t":
            parts.append("{TAB}")
        else:
            parts.append(_escape_keys(ch))
    return "".join(parts)


# ---------------------------------------------------------------------------
# 常用组合键快捷方法
# ---------------------------------------------------------------------------
def press_enter() -> None:
    _keyboard().send_keys("{ENTER}")


def press_shift_enter() -> None:
    """聊天框内换行（不发送）。"""

    _keyboard().send_keys("+{ENTER}")


def press_esc() -> None:
    _keyboard().send_keys("{ESC}")


def press_tab() -> None:
    _keyboard().send_keys("{TAB}")


def press_backspace(count: int = 1) -> None:
    _keyboard().send_keys("{BACKSPACE}" * count)


def select_all() -> None:
    _keyboard().send_keys("^a")


def copy() -> None:
    _keyboard().send_keys("^c")


def paste() -> None:
    _keyboard().send_keys("^v")


def cut() -> None:
    _keyboard().send_keys("^x")


def mention(name: str, delay: float = 0.4) -> None:
    """在群聊输入框中 @ 某人：输入 ``@`` + 名称，等待候选后回车确认。"""

    kb = _keyboard()
    kb.send_keys("@")
    time.sleep(delay)
    type_text(name, slow=False)
    time.sleep(delay)
    kb.send_keys("{ENTER}")


# ---------------------------------------------------------------------------
# 鼠标操作
# ---------------------------------------------------------------------------
def click(coords: Tuple[int, int], button: str = "left") -> None:
    """在屏幕绝对坐标处点击。"""

    _mouse().click(button=button, coords=coords)


def right_click(coords: Tuple[int, int]) -> None:
    _mouse().right_click(coords=coords)


def double_click(coords: Tuple[int, int]) -> None:
    _mouse().double_click(coords=coords)


def scroll(coords: Tuple[int, int], wheel_dist: int = -3) -> None:
    """在指定坐标滚动鼠标滚轮。

    ``wheel_dist`` 为正向上滚（看更早消息），为负向下滚。
    """

    _mouse().scroll(coords=coords, wheel_dist=wheel_dist)


def drag(
    start: Tuple[int, int],
    end: Tuple[int, int],
    button: str = "left",
    duration: float = 0.3,
) -> None:
    """从 ``start`` 拖拽到 ``end``（可用于滚动条拖动翻页）。"""

    m = _mouse()
    m.press(button=button, coords=start)
    steps = 20
    dx = (end[0] - start[0]) / steps
    dy = (end[1] - start[1]) / steps
    for i in range(1, steps + 1):
        m.move(coords=(int(start[0] + dx * i), int(start[1] + dy * i)))
        time.sleep(duration / steps)
    m.release(button=button, coords=end)


def human_pause(min_seconds: float = 0.3, max_seconds: float = 1.0) -> None:
    """随机停顿，模拟真人操作节奏。"""

    time.sleep(random.uniform(min_seconds, max_seconds))
