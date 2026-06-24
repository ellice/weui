"""键鼠模拟 Mixin：快捷键、组合键、慢速输入、鼠标点击/拖拽滚动。

依赖宿主类提供 ``self.window`` 与 ``self.config``。
"""

import time
from typing import Optional, Tuple

from .utils import human_sleep, logger

try:
    from pywinauto.keyboard import send_keys as _send_keys
except ImportError:  # pragma: no cover - 非 Windows
    _send_keys = None


# pywinauto.keyboard 中需要转义的特殊符号
_SPECIAL_CHARS = set("^+%~(){}[]")


def escape_keys(text: str) -> str:
    """转义 ``send_keys`` 的特殊字符，保证文本（含特殊符号/空格）原样输入。"""
    out = []
    for ch in text:
        if ch in _SPECIAL_CHARS:
            out.append("{" + ch + "}")
        elif ch == "\n":
            out.append("{ENTER}")
        elif ch == "\t":
            out.append("{TAB}")
        else:
            out.append(ch)
    return "".join(out)


class InputMixin:
    """封装键盘与鼠标的底层模拟。"""

    window = None
    config = None

    # ------------------------------------------------------------------ 键盘
    def send_keys(self, keys: str, with_spaces: bool = True, pause: Optional[float] = None):
        """直接发送 pywinauto 按键序列（不做转义，调用方自行控制）。

        例如 ``send_keys("^a")`` 表示 Ctrl+A，``"{ENTER}"`` 表示回车。
        """
        if _send_keys is None:
            raise RuntimeError("pywinauto 不可用（仅支持 Windows）")
        if pause is not None:
            _send_keys(keys, with_spaces=with_spaces, pause=pause)
        else:
            _send_keys(keys, with_spaces=with_spaces)

    def type_text(self, text: str, slow: bool = False, interval: Optional[float] = None):
        """输入一段文本，自动转义特殊符号、空格、换行。

        :param slow: 是否逐字符慢速输入（模拟真人，防风控）。
        :param interval: 慢速模式下字符间隔，默认取配置 ``type_interval``。
        """
        if slow:
            interval = self.config.type_interval if interval is None else interval
            for ch in text:
                self.send_keys(escape_keys(ch), with_spaces=True)
                time.sleep(interval)
        else:
            self.send_keys(escape_keys(text), with_spaces=True)

    # ------------------------------- 常用快捷键 / 组合键
    def press_enter(self):
        """回车（一键发送 / 确认）。"""
        self.send_keys("{ENTER}")

    def press_esc(self):
        """ESC 键。"""
        self.send_keys("{ESC}")

    def press_tab(self):
        """Tab 键。"""
        self.send_keys("{TAB}")

    def press_backspace(self, count: int = 1):
        """退格删除若干字符。"""
        self.send_keys("{BACKSPACE " + str(count) + "}")

    def select_all(self):
        """Ctrl+A 全选。"""
        self.send_keys("^a")

    def copy(self):
        """Ctrl+C 复制。"""
        self.send_keys("^c")

    def paste(self):
        """Ctrl+V 粘贴。"""
        self.send_keys("^v")

    def new_line(self):
        """在输入框内换行（微信中为 Shift+Enter，发送为 Enter）。"""
        self.send_keys("+{ENTER}")

    def at_someone(self, name: str = ""):
        """输入 ``@`` 触发群成员选择，并可附带名字。"""
        self.send_keys("@")
        if name:
            human_sleep(0.3)
            self.type_text(name)

    def hotkey(self, keys: str):
        """发送任意组合键，等价于 :meth:`send_keys` 的语义化别名。

        例如 ``hotkey("^+a")`` 表示 Ctrl+Shift+A。
        """
        self.send_keys(keys)

    # ------------------------------------------------------------------ 鼠标
    def click_at(self, x: int, y: int, double: bool = False, right: bool = False):
        """在窗口相对坐标处精准点击 / 双击 / 右键单击。"""
        from pywinauto import mouse

        rect = self.window.rectangle()
        abs_x, abs_y = rect.left + x, rect.top + y
        button = "right" if right else "left"
        if double:
            mouse.double_click(button=button, coords=(abs_x, abs_y))
        else:
            mouse.click(button=button, coords=(abs_x, abs_y))
        logger.debug("鼠标点击 (%d,%d) double=%s right=%s", abs_x, abs_y, double, right)

    def scroll(self, control=None, direction: str = "down", amount: int = 3):
        """在指定控件（默认整窗）上滚动鼠标滚轮，翻阅聊天记录 / 会话列表。

        :param direction: ``"up"`` 向上翻历史，``"down"`` 向下。
        :param amount: 滚动「格」数，每格约一屏的一部分。
        """
        target = control if control is not None else self.window
        wheel = amount if direction == "up" else -amount
        try:
            target.scroll(  # pywinauto BaseWrapper.scroll
                "up" if direction == "up" else "down",
                "page",
                amount,
            )
        except Exception:  # noqa: BLE001 - 退化为滚轮模拟
            from pywinauto import mouse

            rect = target.rectangle()
            mouse.scroll(coords=(rect.mid_point().x, rect.mid_point().y), wheel_dist=wheel)
        logger.debug("滚动 %s x%d", direction, amount)

    def drag(self, start: Tuple[int, int], end: Tuple[int, int]):
        """鼠标拖拽（窗口相对坐标），可用于拖动滚动条翻页。"""
        from pywinauto import mouse

        rect = self.window.rectangle()
        s = (rect.left + start[0], rect.top + start[1])
        e = (rect.left + end[0], rect.top + end[1])
        mouse.press(coords=s)
        time.sleep(0.1)
        mouse.move(coords=e)
        time.sleep(0.1)
        mouse.release(coords=e)
        logger.debug("鼠标拖拽 %s -> %s", s, e)
