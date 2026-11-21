"""键鼠模拟配套功能（第五类能力）。

- 精准鼠标点击、右键、双击；
- 鼠标拖拽 / 滚轮翻页聊天记录；
- 全局键盘快捷键（Ctrl+C/V/A、Enter、Backspace 等）；
- 逐字慢速输入，模拟真人、降低风控风险。
"""

import time
from typing import Optional, Tuple

from ..config import WeChatConfig
from ..utils.humanize import human_typing_delays


class InputDevice:
    """键鼠动作封装，可绑定具体控件或在屏幕坐标上操作。"""

    def __init__(self, config: Optional[WeChatConfig] = None):
        self.config = config or WeChatConfig()

    # ------------------------------------------------------------------
    # 鼠标
    # ------------------------------------------------------------------
    def click(self, ctrl=None, coords: Optional[Tuple[int, int]] = None) -> None:
        """左键单击控件或绝对坐标。"""
        self._mouse_action("left", "click", ctrl, coords)

    def double_click(self, ctrl=None, coords: Optional[Tuple[int, int]] = None) -> None:
        self._mouse_action("left", "double", ctrl, coords)

    def right_click(self, ctrl=None, coords: Optional[Tuple[int, int]] = None) -> None:
        self._mouse_action("right", "click", ctrl, coords)

    def _mouse_action(self, button, kind, ctrl, coords) -> None:
        from pywinauto import mouse

        if ctrl is not None:
            if kind == "double":
                ctrl.double_click_input(button=button)
            else:
                ctrl.click_input(button=button)
        elif coords is not None:
            if kind == "double":
                mouse.double_click(button=button, coords=coords)
            else:
                mouse.click(button=button, coords=coords)
        else:
            raise ValueError("必须提供 ctrl 或 coords 之一。")
        time.sleep(self.config.action_pause)

    def scroll(self, ctrl, direction: str = "up", amount: int = 3) -> None:
        """在控件上滚动滚轮翻页（``direction`` 为 up/down）。

        常用于上翻聊天记录或下拉加载更多会话。
        """
        wheel = amount if direction == "up" else -amount
        ctrl.set_focus()
        ctrl.wheel_mouse_input(wheel_dist=wheel)
        time.sleep(self.config.action_pause)

    def drag(
        self,
        start: Tuple[int, int],
        end: Tuple[int, int],
        button: str = "left",
    ) -> None:
        """从 ``start`` 拖拽到 ``end``，可用于拖动滚动条翻页。"""
        from pywinauto import mouse

        mouse.press(button=button, coords=start)
        time.sleep(0.1)
        mouse.move(coords=end)
        time.sleep(0.1)
        mouse.release(button=button, coords=end)
        time.sleep(self.config.action_pause)

    # ------------------------------------------------------------------
    # 键盘
    # ------------------------------------------------------------------
    def send_keys(self, keys: str, pause: float = 0.05) -> None:
        """发送按键序列（pywinauto keys 语法），用于组合键 / 功能键。

        例如 ``^a``（Ctrl+A）、``^c``、``^v``、``{ENTER}``、``{BACKSPACE}``、
        ``{ESC}``、``{TAB}``、``+{ENTER}``（Shift+Enter 换行）等。
        """
        from pywinauto.keyboard import send_keys

        send_keys(keys, pause=pause, with_spaces=True)
        time.sleep(self.config.action_pause)

    def hotkey(self, name: str) -> None:
        """常用全局快捷键的语义化封装。"""
        mapping = {
            "copy": "^c",
            "paste": "^v",
            "cut": "^x",
            "select_all": "^a",
            "enter": "{ENTER}",
            "backspace": "{BACKSPACE}",
            "esc": "{ESC}",
            "tab": "{TAB}",
            "newline": "+{ENTER}",
            "at": "@",
        }
        if name not in mapping:
            raise ValueError(f"未知快捷键: {name}")
        self.send_keys(mapping[name])

    def type_text(self, text: str, humanize: bool = True) -> None:
        """逐字输入文本。

        ``humanize=True`` 时在字符间加入随机延时，模拟真人慢速输入；
        文本中的 pywinauto 特殊字符（``{}()+^%~``）会被转义，空格保留。
        """
        from pywinauto.keyboard import send_keys

        escaped_chars = list(self._escape_for_send_keys(text))
        if not humanize:
            send_keys("".join(escaped_chars), with_spaces=True)
            time.sleep(self.config.action_pause)
            return

        delays = human_typing_delays(
            len(escaped_chars),
            self.config.typing_interval_min,
            self.config.typing_interval_max,
        )
        for ch, delay in zip(escaped_chars, delays):
            send_keys(ch, with_spaces=True, pause=0)
            time.sleep(delay)
        time.sleep(self.config.action_pause)

    @staticmethod
    def _escape_for_send_keys(text: str):
        """转义 pywinauto keys 语法中的特殊字符，逐字符产出。"""
        special = set("{}()+^%~[]")
        for ch in text:
            if ch == "\n":
                # 输入框内换行使用 Shift+Enter，避免触发发送。
                yield "+{ENTER}"
            elif ch == "\t":
                yield "{TAB}"
            elif ch in special:
                yield "{" + ch + "}"
            else:
                yield ch
