"""键鼠模拟配套功能。

对应需求「五、键鼠模拟配套功能」：

* 精准鼠标点击、右键单击、双击
* 鼠标拖拽滚动聊天记录上下翻页
* 全局键盘快捷键：Ctrl+C/V/A、Enter、Backspace
* 输入延时控制，模拟真人慢速输入防风控

这些是与具体业务无关的底层键鼠封装，直接基于 pywinauto 的
mouse / keyboard 模块，可在任意窗口坐标上使用。
"""

from __future__ import annotations

import logging
import time
from typing import Tuple

from .utils import type_slowly as _type_slowly, human_delay

logger = logging.getLogger("wechat_auto")

Coords = Tuple[int, int]


class InputSimulator:
    """底层键鼠模拟。可独立使用，也可配合 :class:`WeChatWindow`。"""

    def __init__(self, win=None):
        self.win = win

    # ------------------------------------------------------------------ #
    # 鼠标
    # ------------------------------------------------------------------ #
    def click(self, coords: Coords, button: str = "left") -> None:
        """在屏幕绝对坐标处单击。"""
        from pywinauto.mouse import click

        click(button=button, coords=coords)

    def right_click(self, coords: Coords) -> None:
        """右键单击。"""
        from pywinauto.mouse import right_click

        right_click(coords=coords)

    def double_click(self, coords: Coords, button: str = "left") -> None:
        """双击。"""
        from pywinauto.mouse import double_click

        double_click(button=button, coords=coords)

    def move(self, coords: Coords) -> None:
        from pywinauto.mouse import move

        move(coords=coords)

    def drag(self, start: Coords, end: Coords, button: str = "left",
             steps: int = 20, duration: float = 0.4) -> None:
        """从 start 拖拽到 end（可用于拖动滚动条 / 拖拽内容）。"""
        from pywinauto.mouse import press, release, move

        press(button=button, coords=start)
        dx = (end[0] - start[0]) / steps
        dy = (end[1] - start[1]) / steps
        for i in range(1, steps + 1):
            move(coords=(int(start[0] + dx * i), int(start[1] + dy * i)))
            time.sleep(duration / steps)
        release(button=button, coords=end)

    def scroll(self, coords: Coords, wheel_dist: int = -3) -> None:
        """在指定坐标处滚动鼠标滚轮（负值向下、正值向上）。"""
        from pywinauto.mouse import scroll

        scroll(coords=coords, wheel_dist=wheel_dist)

    def scroll_chat(self, up: bool = True, amount: int = 3) -> None:
        """在当前微信聊天记录区域上下翻页（拖拽滚动）。

        需要在构造时传入 WeChatWindow。
        """
        if self.win is None:
            raise RuntimeError("scroll_chat 需要在构造 InputSimulator 时传入 WeChatWindow。")
        rect = self.win.window.rectangle()
        cx = (rect.left + rect.right) // 2
        # 聊天区域大致在窗口中部
        cy = rect.top + int((rect.bottom - rect.top) * 0.45)
        self.scroll((cx, cy), wheel_dist=amount if up else -amount)

    # ------------------------------------------------------------------ #
    # 键盘
    # ------------------------------------------------------------------ #
    def hotkey(self, keys: str, pause: float = 0.05) -> None:
        """发送任意 pywinauto 组合键字符串，如 ``'^c'`` / ``'^v'`` / ``'^a'``。"""
        from pywinauto.keyboard import send_keys

        send_keys(keys, pause=pause)

    def copy(self) -> None:
        self.hotkey("^c")

    def paste(self) -> None:
        self.hotkey("^v")

    def select_all(self) -> None:
        self.hotkey("^a")

    def enter(self) -> None:
        self.hotkey("{ENTER}")

    def backspace(self, times: int = 1) -> None:
        self.hotkey("{BACKSPACE " + str(times) + "}")

    def type_text(self, text: str, slow: bool = False,
                  per_char: float = 0.05, jitter: float = 0.06) -> None:
        """输入文本；slow=True 时逐字符慢速输入模拟真人防风控。"""
        from pywinauto.keyboard import send_keys

        if slow:
            _type_slowly(lambda ch: send_keys(_escape(ch), pause=0),
                         text, per_char=per_char, jitter=jitter)
        else:
            send_keys(_escape(text), pause=0.01)

    # ------------------------------------------------------------------ #
    # 延时
    # ------------------------------------------------------------------ #
    @staticmethod
    def delay(base: float = 0.05, jitter: float = 0.05) -> None:
        """拟人随机延时。"""
        human_delay(base, jitter)


def _escape(text: str) -> str:
    specials = "^%+~(){}[]"
    return "".join("{" + c + "}" if c in specials else c for c in text)
