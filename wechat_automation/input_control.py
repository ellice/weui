"""第五部分：键鼠模拟配套功能。

- 精准鼠标点击 / 右键 / 双击
- 鼠标拖拽滚动聊天记录上下翻页
- 全局键盘快捷键：Ctrl+C/V/A、Enter、Backspace 等
- 输入延时控制，模拟真人慢速输入防风控
"""

import random
import time
from typing import Optional, Tuple

from .config import DEFAULT_CONFIG, WeChatConfig

try:
    from pywinauto import mouse as _mouse  # type: ignore
    from pywinauto import keyboard as _keyboard  # type: ignore

    _HAS_PYWINAUTO = True
except ImportError:  # pragma: no cover - 非 Windows 环境
    _mouse = None  # type: ignore
    _keyboard = None  # type: ignore
    _HAS_PYWINAUTO = False


class InputController:
    """封装 pywinauto 的 mouse / keyboard，统一延时与人性化输入。"""

    def __init__(self, config: Optional[WeChatConfig] = None):
        self.config = config or DEFAULT_CONFIG

    # ------------------------------------------------------------------ 鼠标
    def click(self, coords: Tuple[int, int], button: str = "left") -> None:
        """在屏幕绝对坐标处单击。"""
        _mouse.click(button=button, coords=coords)
        time.sleep(self.config.poll_interval)

    def right_click(self, coords: Tuple[int, int]) -> None:
        """右键单击。"""
        _mouse.right_click(coords=coords)
        time.sleep(self.config.poll_interval)

    def double_click(self, coords: Tuple[int, int]) -> None:
        """双击。"""
        _mouse.double_click(coords=coords)
        time.sleep(self.config.poll_interval)

    def move(self, coords: Tuple[int, int]) -> None:
        """移动鼠标到指定坐标。"""
        _mouse.move(coords=coords)

    def scroll(self, coords: Tuple[int, int], wheel_dist: int = -3) -> None:
        """在指定位置滚轮滚动，负数向下、正数向上。"""
        _mouse.scroll(coords=coords, wheel_dist=wheel_dist)
        time.sleep(self.config.poll_interval)

    def drag_scroll(
        self,
        start: Tuple[int, int],
        end: Tuple[int, int],
        steps: int = 20,
    ) -> None:
        """模拟按住鼠标拖拽，用于聊天记录上下翻页。"""
        _mouse.press(button="left", coords=start)
        sx, sy = start
        ex, ey = end
        for i in range(1, steps + 1):
            x = int(sx + (ex - sx) * i / steps)
            y = int(sy + (ey - sy) * i / steps)
            _mouse.move(coords=(x, y))
            time.sleep(0.01)
        _mouse.release(button="left", coords=end)
        time.sleep(self.config.poll_interval)

    # ------------------------------------------------------------------ 键盘
    def send_keys(self, keys: str, pause: Optional[float] = None) -> None:
        """发送按键序列（pywinauto 语法）。

        例：``^a``(Ctrl+A)、``^c``、``^v``、``{ENTER}``、``{BACKSPACE}``、
        ``{TAB}``、``{ESC}``、``@`` 等。
        """
        _keyboard.send_keys(
            keys,
            pause=self.config.poll_interval if pause is None else pause,
            with_spaces=True,
            with_newlines=True,
        )

    def type_like_human(self, text: str) -> None:
        """逐字慢速输入，字符间加入随机抖动，模拟真人、规避风控。"""
        base = self.config.type_interval
        for ch in text:
            self._type_char(ch)
            time.sleep(base + random.uniform(0, base))

    def _type_char(self, ch: str) -> None:
        if ch == "\n":
            # 输入框内换行用 Shift+Enter，避免误触发发送
            _keyboard.send_keys("+{ENTER}")
            return
        # 转义 pywinauto 的特殊字符
        special = set("^+%~(){}[]")
        if ch in special:
            _keyboard.send_keys("{" + ch + "}", with_spaces=True)
        elif ch == " ":
            _keyboard.send_keys("{SPACE}")
        else:
            _keyboard.send_keys(ch, with_spaces=True)

    # ------------------------------------------- 常用快捷键封装（全局 / 焦点）
    def select_all(self) -> None:
        self.send_keys("^a")

    def copy(self) -> None:
        self.send_keys("^c")

    def paste(self) -> None:
        self.send_keys("^v")

    def enter(self) -> None:
        self.send_keys("{ENTER}")

    def backspace(self, times: int = 1) -> None:
        self.send_keys("{BACKSPACE " + str(times) + "}")

    def tab(self) -> None:
        self.send_keys("{TAB}")

    def esc(self) -> None:
        self.send_keys("{ESC}")

    def newline(self) -> None:
        """输入框内换行（Shift+Enter）。"""
        self.send_keys("+{ENTER}")

    def at(self) -> None:
        """输入 @ 符号（群聊 @ 成员）。"""
        self.send_keys("@")
