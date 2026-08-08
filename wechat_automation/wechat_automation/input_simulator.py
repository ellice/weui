"""模块五：键鼠模拟配套功能。

封装 ``pywinauto.keyboard`` / ``pywinauto.mouse``，提供：

- 拟人化慢速输入（随机字符间隔，防风控）；
- 组合键（``Ctrl+C/V/A``、``Enter``、``Backspace``、``@``、``Tab``、``ESC``）；
- 精准鼠标点击、右键、双击、拖拽滚动。

其中 :func:`escape_send_keys` 会把普通文本里的 ``+ ^ % ~ ( ) { } [ ]`` 等
在 ``send_keys`` 语法里有特殊含义的字符转义，保证换行、特殊符号、空格都能
按字面原样输入。
"""

from __future__ import annotations

import random
import time
from typing import Iterable, Optional

from ._compat import load_keyboard, load_mouse

# send_keys 语法里具有特殊含义、需要用 {x} 包裹才能字面输入的字符。
_SPECIAL_CHARS = set("^+%~(){}[]")


def escape_send_keys(text: str) -> str:
    """把普通文本转义为 ``send_keys`` 可安全字面输入的字符串。

    - 特殊字符 ``^ + % ~ ( ) { } [ ]`` 使用 ``{char}`` 包裹；
    - 换行 ``\\n`` 转成 ``{ENTER}``；
    - 制表符 ``\\t`` 转成 ``{TAB}``。

    :param text: 原始文本。
    :return: 可直接交给 ``send_keys`` 的字符串。
    """
    out = []
    for ch in text:
        if ch == "\n":
            out.append("{ENTER}")
        elif ch == "\r":
            continue
        elif ch == "\t":
            out.append("{TAB}")
        elif ch in _SPECIAL_CHARS:
            out.append("{" + ch + "}")
        else:
            out.append(ch)
    return "".join(out)


class InputSimulator:
    """键鼠模拟器。

    :param human_like: 是否启用拟人慢速逐字输入。
    :param min_char_delay: 拟人输入时单字符最小间隔（秒）。
    :param max_char_delay: 拟人输入时单字符最大间隔（秒）。
    """

    def __init__(self, human_like: bool = True,
                 min_char_delay: float = 0.02,
                 max_char_delay: float = 0.12) -> None:
        self.human_like = human_like
        self.min_char_delay = min_char_delay
        self.max_char_delay = max_char_delay

    # ---------------------------------------------------------------- 键盘
    def send_keys(self, keys: str, pause: float = 0.0,
                  with_spaces: bool = True) -> None:
        """直接发送 ``send_keys`` 语法串（不做转义）。

        用于发送组合键，例如 ``"^a"``（Ctrl+A）、``"{ENTER}"``、``"%{F4}"``。
        """
        keyboard = load_keyboard()
        keyboard.send_keys(keys, pause=pause, with_spaces=with_spaces)

    def type_text(self, text: str, human_like: Optional[bool] = None) -> None:
        """输入一段**字面文本**（自动转义特殊字符、换行、Tab）。

        当启用拟人输入时逐字符发送并加入随机延时，模拟真人打字，降低风控风险。
        """
        use_human = self.human_like if human_like is None else human_like
        keyboard = load_keyboard()
        if not use_human:
            keyboard.send_keys(escape_send_keys(text), with_spaces=True)
            return
        for ch in text:
            keyboard.send_keys(escape_send_keys(ch), with_spaces=True)
            time.sleep(random.uniform(self.min_char_delay, self.max_char_delay))

    # 常用单键 / 组合键快捷方法 -------------------------------------------
    def enter(self) -> None:
        """回车。"""
        self.send_keys("{ENTER}")

    def tab(self) -> None:
        """Tab 键。"""
        self.send_keys("{TAB}")

    def esc(self) -> None:
        """ESC 键。"""
        self.send_keys("{ESC}")

    def backspace(self, count: int = 1) -> None:
        """退格删除 ``count`` 个字符。"""
        self.send_keys("{BACKSPACE " + str(int(count)) + "}")

    def at(self) -> None:
        """输入 ``@`` 唤起群成员选择。"""
        self.send_keys("@")

    def select_all(self) -> None:
        """Ctrl+A 全选。"""
        self.send_keys("^a")

    def copy(self) -> None:
        """Ctrl+C 复制。"""
        self.send_keys("^c")

    def paste(self) -> None:
        """Ctrl+V 粘贴。"""
        self.send_keys("^v")

    def cut(self) -> None:
        """Ctrl+X 剪切。"""
        self.send_keys("^x")

    def hotkey(self, *keys: str) -> None:
        """按下一组组合键，如 ``hotkey("ctrl", "enter")``。

        支持的修饰键名：``ctrl/control``、``alt``、``shift``、``win``。
        其余作为普通键名（单字符或如 ``enter``、``f4``）。
        """
        mod_map = {
            "ctrl": "^", "control": "^",
            "alt": "%", "shift": "+",
            "win": "{VK_LWIN down}", "cmd": "{VK_LWIN down}",
        }
        prefix = ""
        body = ""
        for key in keys:
            low = key.lower()
            if low in mod_map and mod_map[low] in ("^", "%", "+"):
                prefix += mod_map[low]
            elif len(key) == 1:
                body += key
            else:
                body += "{" + key.upper() + "}"
        self.send_keys(prefix + body)

    # ---------------------------------------------------------------- 鼠标
    def click(self, coords: tuple[int, int], button: str = "left") -> None:
        """在屏幕绝对坐标处点击。"""
        mouse = load_mouse()
        mouse.click(button=button, coords=coords)

    def right_click(self, coords: tuple[int, int]) -> None:
        """右键单击。"""
        mouse = load_mouse()
        mouse.right_click(coords=coords)

    def double_click(self, coords: tuple[int, int]) -> None:
        """左键双击。"""
        mouse = load_mouse()
        mouse.double_click(coords=coords)

    def scroll(self, coords: tuple[int, int], wheel_dist: int = -3) -> None:
        """在指定坐标滚动鼠标滚轮。

        :param wheel_dist: 正数向上、负数向下（每格约一“行”）。
        """
        mouse = load_mouse()
        mouse.scroll(coords=coords, wheel_dist=wheel_dist)

    def drag(self, src: tuple[int, int], dst: tuple[int, int],
             button: str = "left") -> None:
        """按住鼠标从 ``src`` 拖拽到 ``dst``（可用于拖动滚动条翻页）。"""
        mouse = load_mouse()
        mouse.press(button=button, coords=src)
        mouse.move(coords=dst)
        mouse.release(button=button, coords=dst)

    @staticmethod
    def sleep(seconds: float) -> None:
        """统一的延时封装，便于测试替换。"""
        time.sleep(seconds)
