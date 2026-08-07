"""键鼠模拟配套功能（第五类）。

封装 pywinauto 的鼠标、键盘底层能力：
- 精准点击、右键、双击、拖拽滚动
- 全局快捷键（Ctrl+C/V/A、Enter、Backspace 等）
- 逐字输入 + 延时控制，模拟真人慢速输入防风控
"""

from __future__ import annotations

import time
from typing import Optional, Tuple

try:  # pragma: no cover - 仅在 Windows 上可用
    from pywinauto import keyboard, mouse
except Exception:  # noqa: BLE001 - 允许在非 Windows 环境导入以便阅读 / 测试
    keyboard = None
    mouse = None


class InputController:
    """键鼠模拟统一入口。"""

    def __init__(self, type_interval: float = 0.02, action_delay: float = 0.3) -> None:
        #: 逐字输入间隔（秒）
        self.type_interval = type_interval
        #: 每步操作之间的间隔（秒）
        self.action_delay = action_delay

    # ------------------------------------------------------------------ #
    # 鼠标
    # ------------------------------------------------------------------ #
    def click(self, coords: Tuple[int, int], button: str = "left") -> None:
        """在屏幕绝对坐标 ``coords`` 精准单击。"""
        mouse.click(button=button, coords=coords)
        self._pause()

    def right_click(self, coords: Tuple[int, int]) -> None:
        """右键单击。"""
        mouse.right_click(coords=coords)
        self._pause()

    def double_click(self, coords: Tuple[int, int]) -> None:
        """双击。"""
        mouse.double_click(coords=coords)
        self._pause()

    def move(self, coords: Tuple[int, int]) -> None:
        """移动鼠标到指定坐标。"""
        mouse.move(coords=coords)

    def drag(
        self,
        start: Tuple[int, int],
        end: Tuple[int, int],
        button: str = "left",
    ) -> None:
        """从 ``start`` 拖拽到 ``end``（可用于拖动滚动条）。"""
        mouse.press(button=button, coords=start)
        time.sleep(0.1)
        mouse.move(coords=end)
        time.sleep(0.1)
        mouse.release(button=button, coords=end)
        self._pause()

    def scroll(self, coords: Tuple[int, int], wheel_dist: int) -> None:
        """在 ``coords`` 处滚动鼠标滚轮。

        ``wheel_dist`` 为正向上翻页（更早的消息），为负向下翻页。
        """
        mouse.scroll(coords=coords, wheel_dist=wheel_dist)
        self._pause()

    # ------------------------------------------------------------------ #
    # 键盘
    # ------------------------------------------------------------------ #
    def send_keys(self, keys: str, pause: Optional[float] = None) -> None:
        """发送快捷键 / 组合键。

        使用 pywinauto 语法，例如::

            send_keys("^c")          # Ctrl+C
            send_keys("^v")          # Ctrl+V
            send_keys("^a")          # Ctrl+A（全选）
            send_keys("{ENTER}")     # 回车
            send_keys("{BACKSPACE}") # 退格
            send_keys("{ESC}")       # ESC
            send_keys("{TAB}")       # Tab
            send_keys("+{ENTER}")    # Shift+Enter（换行）
        """
        keyboard.send_keys(keys, pause=pause if pause is not None else 0.01)
        self._pause()

    def hotkey_copy(self) -> None:
        self.send_keys("^c")

    def hotkey_paste(self) -> None:
        self.send_keys("^v")

    def hotkey_select_all(self) -> None:
        self.send_keys("^a")

    def press_enter(self) -> None:
        self.send_keys("{ENTER}")

    def press_backspace(self, times: int = 1) -> None:
        self.send_keys("{BACKSPACE " + str(times) + "}")

    def press_esc(self) -> None:
        self.send_keys("{ESC}")

    def press_tab(self) -> None:
        self.send_keys("{TAB}")

    def new_line(self) -> None:
        """在微信输入框中换行（Shift+Enter）。"""
        self.send_keys("+{ENTER}")

    # ------------------------------------------------------------------ #
    # 慢速输入（防风控）
    # ------------------------------------------------------------------ #
    def type_text_slowly(self, text: str, interval: Optional[float] = None) -> None:
        """逐字输入文本，模拟真人打字节奏。

        对包含 pywinauto 特殊字符（``^ % + ~ ( ) { }``）的文本会自动转义，
        换行符转换为 Shift+Enter。
        """
        interval = self.type_interval if interval is None else interval
        for ch in text:
            if ch == "\n":
                self.new_line()
            else:
                keyboard.send_keys(_escape_keys(ch), pause=0)
            if interval:
                time.sleep(interval)

    # ------------------------------------------------------------------ #
    # 内部
    # ------------------------------------------------------------------ #
    def _pause(self) -> None:
        if self.action_delay:
            time.sleep(self.action_delay)


_SPECIAL_KEYS = set("^%+~(){}[]")


def _escape_keys(text: str) -> str:
    """转义 pywinauto ``send_keys`` 的特殊字符。"""
    result = []
    for ch in text:
        if ch in _SPECIAL_KEYS:
            result.append("{" + ch + "}")
        else:
            result.append(ch)
    return "".join(result)
