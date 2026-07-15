"""键鼠模拟配套功能。

对应需求"五、键鼠模拟配套功能"：

- 精准鼠标点击 / 右键 / 双击
- 鼠标拖拽滚动聊天记录上下翻页
- 全局快捷键 Ctrl+C/V/A、Enter、Backspace、Tab、ESC、@、表情
- 输入延时控制，模拟真人慢速输入防风控

底层封装 :mod:`pywinauto.keyboard` 与 :mod:`pywinauto.mouse`，同时提供纯延时
辅助函数，便于在不引入 pywinauto 的环境下做单元测试。
"""

from __future__ import annotations

import random
import time
from typing import Optional, Tuple

from .config import WeChatConfig, default_config


def _kbd():
    from pywinauto.keyboard import send_keys  # type: ignore

    return send_keys


def _mouse():
    from pywinauto import mouse  # type: ignore

    return mouse


# —— pywinauto send_keys 需要转义的特殊字符 ——
_SPECIAL_CHARS = set("^+%~(){}[]")


def escape_keys(text: str) -> str:
    """转义 ``send_keys`` 的特殊字符，保证按字面量输入。

    ``send_keys`` 中 ``^ + % ~ ( ) { } [ ]`` 有特殊含义，需用 ``{}`` 包裹。
    """
    out = []
    for ch in text:
        if ch in _SPECIAL_CHARS:
            out.append("{" + ch + "}")
        else:
            out.append(ch)
    return "".join(out)


class InputController:
    """键鼠模拟控制器。

    可传入 :class:`WeChatConfig` 以复用统一的延时与慢速输入间隔。
    """

    def __init__(self, config: Optional[WeChatConfig] = None):
        self.config = config or default_config

    # —————————————————————— 延时 ——————————————————————
    def sleep_short(self) -> None:
        time.sleep(self.config.short_delay)

    def sleep_medium(self) -> None:
        time.sleep(self.config.medium_delay)

    def sleep_long(self) -> None:
        time.sleep(self.config.long_delay)

    @staticmethod
    def sleep(seconds: float) -> None:
        time.sleep(seconds)

    # —————————————————————— 键盘 ——————————————————————
    def send_keys(self, keys: str, pause: Optional[float] = None) -> None:
        """透传给 pywinauto 的 ``send_keys``（支持组合键语法）。"""
        send_keys = _kbd()
        send_keys(keys, pause=pause if pause is not None else 0.02)

    def type_text_fast(self, text: str) -> None:
        """快速整段输入（对特殊字符自动转义）。"""
        self.send_keys(escape_keys(text))

    def type_text_slow(
        self,
        text: str,
        interval: Optional[float] = None,
        jitter: float = 0.4,
    ) -> None:
        """慢速逐字符输入，模拟真人节奏以降低风控风险。

        Args:
            text: 待输入文本。
            interval: 基础字符间隔（秒），默认取配置 ``type_interval``。
            jitter: 抖动比例，实际间隔在 ``interval*(1±jitter)`` 间随机。
        """
        send_keys = _kbd()
        base = interval if interval is not None else self.config.type_interval
        for ch in text:
            if ch == "\n":
                # 换行使用 Shift+Enter，避免直接触发发送
                send_keys("+{ENTER}")
            else:
                send_keys(escape_keys(ch))
            delay = base * (1 + random.uniform(-jitter, jitter))
            time.sleep(max(0.0, delay))

    # —— 常用快捷键封装 ——
    def press_enter(self) -> None:
        self.send_keys("{ENTER}")

    def press_shift_enter(self) -> None:
        """换行（不发送）。"""
        self.send_keys("+{ENTER}")

    def press_backspace(self, times: int = 1) -> None:
        self.send_keys("{BACKSPACE}" * max(1, times))

    def press_tab(self) -> None:
        self.send_keys("{TAB}")

    def press_esc(self) -> None:
        self.send_keys("{ESC}")

    def press_at(self) -> None:
        """输入 ``@``，用于群聊中触发 @ 成员列表。"""
        self.send_keys("@")

    def select_all(self) -> None:
        self.send_keys("^a")

    def copy(self) -> None:
        self.send_keys("^c")

    def paste(self) -> None:
        self.send_keys("^v")

    def cut(self) -> None:
        self.send_keys("^x")

    def clear_edit(self) -> None:
        """清空输入框：全选 + 删除。"""
        self.select_all()
        self.sleep_short()
        self.press_backspace()

    # —————————————————————— 鼠标 ——————————————————————
    def click(self, coords: Tuple[int, int]) -> None:
        """左键单击屏幕绝对坐标。"""
        _mouse().click(button="left", coords=coords)

    def double_click(self, coords: Tuple[int, int]) -> None:
        _mouse().double_click(button="left", coords=coords)

    def right_click(self, coords: Tuple[int, int]) -> None:
        _mouse().click(button="right", coords=coords)

    def move(self, coords: Tuple[int, int]) -> None:
        _mouse().move(coords=coords)

    def scroll(self, coords: Tuple[int, int], wheel_dist: int) -> None:
        """在指定坐标滚动滚轮。

        Args:
            coords: 滚动发生的屏幕坐标（一般为聊天记录区域中心）。
            wheel_dist: 正数向上（查看更早消息），负数向下。
        """
        _mouse().scroll(coords=coords, wheel_dist=wheel_dist)

    def drag(
        self,
        start: Tuple[int, int],
        end: Tuple[int, int],
        button: str = "left",
    ) -> None:
        """从 ``start`` 拖拽到 ``end``，可用于拖动滚动条翻页。"""
        _mouse().press(button=button, coords=start)
        time.sleep(self.config.short_delay)
        _mouse().move(coords=end)
        time.sleep(self.config.short_delay)
        _mouse().release(button=button, coords=end)
