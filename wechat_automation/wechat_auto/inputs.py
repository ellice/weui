"""键鼠模拟配套功能。

依赖 pywinauto 的 ``keyboard`` / ``mouse`` 模块，封装：

* 精准鼠标点击、右键、双击、拖拽滚动
* 常用全局快捷键（Ctrl+C/V/A、Enter、Backspace、ESC、Tab、@、表情面板等）
* 拟人化慢速逐字输入，降低风控风险

pywinauto 的按键转义约定：``^`` = Ctrl，``+`` = Shift，``%`` = Alt，
``{ENTER}`` / ``{BACKSPACE}`` / ``{ESC}`` / ``{TAB}`` 等为特殊键。
"""

from __future__ import annotations

import random
from typing import Optional

from .utils import human_sleep, logger


class InputController:
    """键鼠模拟控制器。

    :param default_delay: 每个动作后的默认停顿秒数。
    """

    def __init__(self, default_delay: float = 0.15) -> None:
        self.default_delay = default_delay

    # ------------------------------------------------------------------ #
    # 键盘
    # ------------------------------------------------------------------ #
    def send_keys(self, keys: str, pause: Optional[float] = None) -> None:
        """向当前焦点窗口发送按键序列（pywinauto 转义语法）。"""
        from pywinauto.keyboard import send_keys as _send_keys

        _send_keys(keys, pause=pause if pause is not None else 0.02, with_spaces=True)
        human_sleep(self.default_delay)

    def type_text(
        self,
        text: str,
        min_interval: float = 0.03,
        max_interval: float = 0.12,
    ) -> None:
        """逐字“拟人”输入文本，字符间隔随机，降低风控风险。

        注意：本方法用于模拟真人打字；发送大段文本 / 含特殊符号时，
        更推荐用剪贴板粘贴（见 :mod:`wechat_auto.messaging`）。
        """
        from pywinauto.keyboard import send_keys as _send_keys

        for ch in text:
            if ch == "\n":
                _send_keys("{ENTER}")
            else:
                # 转义 pywinauto 的特殊字符
                _send_keys(_escape(ch), with_spaces=True)
            human_sleep(random.uniform(min_interval, max_interval))

    # -- 常用快捷键封装 -------------------------------------------------- #
    def press_enter(self) -> None:
        """回车（发送消息）。"""
        self.send_keys("{ENTER}")

    def press_shift_enter(self) -> None:
        """Shift+Enter（输入框内换行，不发送）。"""
        self.send_keys("+{ENTER}")

    def press_esc(self) -> None:
        """ESC（关闭弹窗 / 取消）。"""
        self.send_keys("{ESC}")

    def press_tab(self) -> None:
        """Tab（切换焦点）。"""
        self.send_keys("{TAB}")

    def press_backspace(self, times: int = 1) -> None:
        """退格删除。"""
        self.send_keys("{BACKSPACE " + str(times) + "}")

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

    def clear_input(self) -> None:
        """清空当前输入框：全选 + 退格。"""
        self.select_all()
        self.press_backspace()

    def open_emoji_panel(self) -> None:
        """在聊天窗口按下 @ 之外，微信表情面板通常靠点击按钮唤起；
        此处提供组合键占位，实际以点击“表情”按钮为准。"""
        # 微信没有统一表情快捷键，保留接口一致性
        logger.info("表情面板一般通过点击“表情”按钮唤起，见 click_button('表情')")

    def mention(self) -> None:
        """输入 @ 触发群聊成员选择。"""
        self.send_keys("@")

    # ------------------------------------------------------------------ #
    # 鼠标
    # ------------------------------------------------------------------ #
    def click(self, x: int, y: int, button: str = "left") -> None:
        """在屏幕绝对坐标处点击。"""
        from pywinauto import mouse

        mouse.click(button=button, coords=(x, y))
        human_sleep(self.default_delay)

    def right_click(self, x: int, y: int) -> None:
        """右键单击。"""
        from pywinauto import mouse

        mouse.right_click(coords=(x, y))
        human_sleep(self.default_delay)

    def double_click(self, x: int, y: int) -> None:
        """双击。"""
        from pywinauto import mouse

        mouse.double_click(coords=(x, y))
        human_sleep(self.default_delay)

    def scroll(self, x: int, y: int, wheel_dist: int = -3) -> None:
        """在指定坐标滚动鼠标滚轮。

        :param wheel_dist: 正数向上、负数向下，绝对值越大滚动越多。
        """
        from pywinauto import mouse

        mouse.scroll(coords=(x, y), wheel_dist=wheel_dist)
        human_sleep(self.default_delay)

    def drag(
        self,
        start: tuple,
        end: tuple,
        button: str = "left",
    ) -> None:
        """按住鼠标从 start 拖拽到 end（可用于拖动滚动条翻页）。"""
        from pywinauto import mouse

        mouse.press(button=button, coords=start)
        human_sleep(0.1)
        mouse.move(coords=end)
        human_sleep(0.1)
        mouse.release(button=button, coords=end)
        human_sleep(self.default_delay)


_SPECIAL_CHARS = set("^+%~(){}[]")


def _escape(ch: str) -> str:
    """转义 pywinauto send_keys 的特殊字符。"""
    if ch in _SPECIAL_CHARS:
        return "{" + ch + "}"
    return ch
