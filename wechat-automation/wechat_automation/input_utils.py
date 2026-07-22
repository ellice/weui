"""键鼠模拟工具。

封装 pywinauto 的键盘 / 鼠标接口，提供：

* 组合快捷键：Ctrl+C/V/A、Enter、Backspace、Tab、Esc、@ 等
* 慢速真人输入（带随机抖动）防风控
* 精准点击、右键、双击
* 滚轮 / 拖拽滚动聊天记录
"""

from __future__ import annotations

import random
import time
from typing import Optional, Tuple

from pywinauto import keyboard, mouse

# ---- 常用按键别名（pywinauto send_keys 语法）----
ENTER = "{ENTER}"
TAB = "{TAB}"
ESC = "{ESC}"
BACKSPACE = "{BACKSPACE}"
SELECT_ALL = "^a"
COPY = "^c"
PASTE = "^v"
CUT = "^x"
NEWLINE = "{ENTER}"  # 在纯文本编辑区中的换行；发送场景下换行使用 Shift+Enter


def _escape_for_send_keys(text: str) -> str:
    """转义 send_keys 的特殊字符，使文本按字面量输入。

    pywinauto 的 send_keys 会把 ``{} () + ^ % ~`` 等当作控制符，
    需要用大括号包裹或转义，避免「特殊符号」被错误解析。
    """
    special = set("{}()+^%~[]")
    out = []
    for ch in text:
        if ch in special:
            out.append("{" + ch + "}")
        elif ch == "\n":
            out.append("{ENTER}")
        elif ch == "\t":
            out.append("{TAB}")
        else:
            out.append(ch)
    return "".join(out)


def send_keys(keys: str, pause: float = 0.02) -> None:
    """发送一段 send_keys 语法的按键序列（不做转义）。

    适合发送快捷键组合，例如 ``send_keys("^a")``。
    """
    keyboard.send_keys(keys, pause=pause)


def type_text_fast(text: str) -> None:
    """快速输入一段文本（按字面量），自动转义特殊符号并兼容换行。"""
    keyboard.send_keys(_escape_for_send_keys(text), pause=0.0, with_spaces=True)


def type_text_human(
    text: str,
    base_interval: float = 0.03,
    jitter: float = 0.04,
) -> None:
    """模拟真人慢速逐字输入，带随机抖动，降低被风控概率。

    :param text: 待输入文本，支持换行 / 空格 / 特殊符号
    :param base_interval: 每个字符之间的基础延时（秒）
    :param jitter: 随机抖动上限（秒），实际延时 = base + rand(0, jitter)
    """
    for ch in text:
        keyboard.send_keys(_escape_for_send_keys(ch), pause=0.0, with_spaces=True)
        time.sleep(base_interval + random.uniform(0, jitter))


def press_shift_enter() -> None:
    """Shift+Enter：在微信输入框内换行而不触发发送。"""
    keyboard.send_keys("+{ENTER}")


def press_enter() -> None:
    """回车：一键发送当前输入框内容。"""
    keyboard.send_keys("{ENTER}")


def press_at() -> None:
    """输入 @ 符号（群聊内触发 @ 成员菜单）。"""
    keyboard.send_keys("@")


def select_all() -> None:
    """Ctrl+A 全选。"""
    keyboard.send_keys("^a")


def clear_edit() -> None:
    """清空当前焦点编辑框：全选 + 删除。"""
    keyboard.send_keys("^a{BACKSPACE}")


def paste() -> None:
    """Ctrl+V 粘贴剪贴板内容。"""
    keyboard.send_keys("^v")


# ---------------------------------------------------------------- 鼠标 ----
def click(x: int, y: int, button: str = "left") -> None:
    """在屏幕绝对坐标处单击。"""
    mouse.click(button=button, coords=(x, y))


def right_click(x: int, y: int) -> None:
    """右键单击。"""
    mouse.click(button="right", coords=(x, y))


def double_click(x: int, y: int) -> None:
    """双击。"""
    mouse.double_click(button="left", coords=(x, y))


def scroll(x: int, y: int, wheel_dist: int) -> None:
    """在指定坐标滚动滚轮。

    :param wheel_dist: 正数向上（查看更早的聊天记录），负数向下
    """
    mouse.scroll(coords=(x, y), wheel_dist=wheel_dist)


def drag(start: Tuple[int, int], end: Tuple[int, int], button: str = "left") -> None:
    """从 start 拖拽到 end，可用于拖动滚动条翻页聊天记录。"""
    mouse.press(button=button, coords=start)
    time.sleep(0.1)
    mouse.move(coords=end)
    time.sleep(0.1)
    mouse.release(button=button, coords=end)


def sleep(seconds: float) -> None:
    """封装延时，便于统一控制节奏。"""
    time.sleep(seconds)
