"""键鼠模拟配套功能。

封装 pywinauto 的 ``keyboard`` / ``mouse`` 模块，提供：
- 精准点击 / 右键 / 双击；
- 滚轮上下翻页（用于聊天记录翻页）；
- 全局快捷键（Ctrl+C/V/A、Enter、Backspace、Tab、Esc 等）；
- 模拟真人慢速逐字输入，带可配置延时，降低风控风险。
"""

from __future__ import annotations

import random
import time
from typing import Tuple

from ._compat import load_keyboard, load_mouse


class InputSimulator:
    """键鼠模拟器。"""

    def __init__(self, human_like: bool = True,
                 min_char_delay: float = 0.02,
                 max_char_delay: float = 0.12) -> None:
        """
        :param human_like: 是否启用拟人慢速输入。
        :param min_char_delay: 逐字输入最小间隔（秒）。
        :param max_char_delay: 逐字输入最大间隔（秒）。
        """
        self.human_like = human_like
        self.min_char_delay = min_char_delay
        self.max_char_delay = max_char_delay
        self._keyboard = load_keyboard()
        self._mouse = load_mouse()

    # ----- 键盘 -----
    def send_keys(self, keys: str, pause: float = 0.05,
                  with_spaces: bool = True) -> None:
        """发送 pywinauto 风格的按键序列。

        例如 ``"^a"``=Ctrl+A，``"^c"``=Ctrl+C，``"{ENTER}"``、``"{TAB}"``、
        ``"{ESC}"``、``"{BACKSPACE}"`` 等。
        """
        self._keyboard.send_keys(keys, pause=pause, with_spaces=with_spaces)

    def type_text(self, text: str) -> None:
        """逐字输入普通文本。

        ``human_like=True`` 时每个字符间随机延时，模拟真人打字。
        会把 pywinauto 的特殊字符 ``{}()+^%~`` 自动转义为字面量。
        """
        if not self.human_like:
            self._keyboard.send_keys(self._escape(text), with_spaces=True,
                                     pause=0.0)
            return
        for ch in text:
            self._keyboard.send_keys(self._escape(ch), with_spaces=True, pause=0.0)
            time.sleep(random.uniform(self.min_char_delay, self.max_char_delay))

    @staticmethod
    def _escape(text: str) -> str:
        """转义 pywinauto send_keys 的特殊字符为字面量。"""
        specials = set("{}()+^%~[]")
        out = []
        for ch in text:
            if ch in specials:
                out.append("{" + ch + "}")
            else:
                out.append(ch)
        return "".join(out)

    # ----- 常用快捷键封装 -----
    def press_enter(self) -> None:
        self._keyboard.send_keys("{ENTER}")

    def press_tab(self) -> None:
        self._keyboard.send_keys("{TAB}")

    def press_esc(self) -> None:
        self._keyboard.send_keys("{ESC}")

    def press_backspace(self, times: int = 1) -> None:
        self._keyboard.send_keys("{BACKSPACE}" * max(1, times))

    def newline(self) -> None:
        """输入框内换行（Shift+Enter，不触发发送）。"""
        self._keyboard.send_keys("+{ENTER}")

    def select_all(self) -> None:
        self._keyboard.send_keys("^a")

    def copy(self) -> None:
        self._keyboard.send_keys("^c")

    def paste(self) -> None:
        self._keyboard.send_keys("^v")

    def cut(self) -> None:
        self._keyboard.send_keys("^x")

    def mention(self) -> None:
        """输入 @ 触发群成员选择浮层。"""
        self._keyboard.send_keys("@")

    # ----- 鼠标 -----
    def click(self, coords: Tuple[int, int]) -> None:
        """左键单击屏幕坐标。"""
        self._mouse.click(button="left", coords=coords)

    def right_click(self, coords: Tuple[int, int]) -> None:
        """右键单击。"""
        self._mouse.click(button="right", coords=coords)

    def double_click(self, coords: Tuple[int, int]) -> None:
        """左键双击。"""
        self._mouse.double_click(button="left", coords=coords)

    def scroll(self, coords: Tuple[int, int], amount: int) -> None:
        """在指定坐标处滚动滚轮。

        :param amount: 正数向上翻（看更早消息），负数向下翻。
        """
        self._mouse.scroll(coords=coords, wheel_dist=amount)

    def scroll_up(self, coords: Tuple[int, int], steps: int = 3) -> None:
        self.scroll(coords, abs(steps))

    def scroll_down(self, coords: Tuple[int, int], steps: int = 3) -> None:
        self.scroll(coords, -abs(steps))
