"""键鼠模拟配套功能（对应需求第五类）。

在 pywinauto 的 ``keyboard`` / ``mouse`` 之上做一层封装，提供：

* 精准鼠标点击、右键、双击、拖拽滚动
* 常用全局快捷键：Ctrl+C/V/A、Enter、Backspace、Esc、Tab、@、表情、换行
* 输入延时控制，逐字符"慢速"输入以模拟真人、降低风控风险

这些函数不依赖具体控件，作用于当前焦点窗口 / 屏幕坐标，
因此既可以单独使用，也会被上层业务模块复用。
"""

from __future__ import annotations

import random
import time
from typing import Iterable, Tuple

from .config import Config
from .logger import get_logger

log = get_logger("inputs")

try:
    from pywinauto import keyboard as _kbd  # type: ignore
    from pywinauto import mouse as _mouse  # type: ignore

    _HAS_PYWINAUTO = True
except Exception:  # pragma: no cover - 非 Windows / 未安装
    _HAS_PYWINAUTO = False


def _ensure_pywinauto() -> None:
    if not _HAS_PYWINAUTO:
        raise RuntimeError("键鼠模拟依赖 pywinauto，且仅支持 Windows 平台。")


# pywinauto send_keys 中需要转义的特殊字符
_SPECIAL_CHARS = set("{}()+^%~[]")


def escape_keys(text: str) -> str:
    """把普通文本转义为 ``send_keys`` 可安全发送的字符串。

    ``send_keys`` 会把 ``+ ^ % ~ ( ) { } [ ]`` 当作控制符，
    这里用 ``{X}`` 形式转义，保证特殊符号、空格原样输入。
    """
    out = []
    for ch in text:
        if ch in _SPECIAL_CHARS:
            out.append("{%s}" % ch)
        else:
            out.append(ch)
    return "".join(out)


class InputSimulator:
    """键鼠模拟器。

    :param config: 全局配置，用于读取输入延时区间等参数。
    """

    def __init__(self, config: Config | None = None) -> None:
        self.config = config or Config()

    # ------------------------------------------------------------------ #
    # 键盘
    # ------------------------------------------------------------------ #
    def send_keys(self, keys: str, pause: float = 0.02, with_spaces: bool = True) -> None:
        """直接发送 ``send_keys`` 语法的按键序列（不做转义）。

        适合发送组合键，如 ``"^a"``（Ctrl+A）、``"{ENTER}"`` 等。
        """
        _ensure_pywinauto()
        _kbd.send_keys(keys, pause=pause, with_spaces=with_spaces)

    def type_text(self, text: str, human_like: bool = True) -> None:
        """输入一段纯文本（自动转义特殊字符）。

        :param human_like: 为 True 时逐字符输入并加入随机延时，模拟真人打字；
            为 False 时一次性快速输入。
        """
        _ensure_pywinauto()
        if not human_like:
            _kbd.send_keys(escape_keys(text), with_spaces=True)
            return

        cfg = self.config
        for ch in text:
            _kbd.send_keys(escape_keys(ch), with_spaces=True)
            time.sleep(random.uniform(cfg.type_delay_min, cfg.type_delay_max))

    # --- 常用单键 / 组合键 ---
    def enter(self) -> None:
        """回车。"""
        self.send_keys("{ENTER}")

    def new_line(self) -> None:
        """换行（微信中为 Shift+Enter，不触发发送）。"""
        self.send_keys("+{ENTER}")

    def backspace(self, count: int = 1) -> None:
        """退格删除 count 个字符。"""
        self.send_keys("{BACKSPACE %d}" % count)

    def esc(self) -> None:
        """Esc。"""
        self.send_keys("{ESC}")

    def tab(self) -> None:
        """Tab。"""
        self.send_keys("{TAB}")

    def at(self) -> None:
        """输入 @ 符号（群聊中触发 @ 成员列表）。"""
        # send_keys 中 @ 无需转义，但为稳妥使用花括号
        _ensure_pywinauto()
        _kbd.send_keys("@", with_spaces=True)

    def select_all(self) -> None:
        """全选：Ctrl+A。"""
        self.send_keys("^a")

    def copy(self) -> None:
        """复制：Ctrl+C。"""
        self.send_keys("^c")

    def paste(self) -> None:
        """粘贴：Ctrl+V。"""
        self.send_keys("^v")

    def cut(self) -> None:
        """剪切：Ctrl+X。"""
        self.send_keys("^x")

    def hotkey(self, *keys: str) -> None:
        """发送任意组合键，例如 ``hotkey("ctrl", "shift", "s")`` 触发截图。

        内部转换为 send_keys 语法。
        """
        mapping = {"ctrl": "^", "alt": "%", "shift": "+"}
        prefix = ""
        normal_keys = []
        for k in keys:
            kl = k.lower()
            if kl in mapping:
                prefix += mapping[kl]
            else:
                normal_keys.append(k)
        seq = prefix + "".join(normal_keys)
        self.send_keys(seq)

    # ------------------------------------------------------------------ #
    # 鼠标
    # ------------------------------------------------------------------ #
    def click(self, coords: Tuple[int, int]) -> None:
        """在屏幕坐标处单击左键。"""
        _ensure_pywinauto()
        _mouse.click(button="left", coords=coords)
        time.sleep(self.config.after_click_delay)

    def right_click(self, coords: Tuple[int, int]) -> None:
        """在屏幕坐标处单击右键。"""
        _ensure_pywinauto()
        _mouse.click(button="right", coords=coords)
        time.sleep(self.config.after_click_delay)

    def double_click(self, coords: Tuple[int, int]) -> None:
        """在屏幕坐标处双击左键。"""
        _ensure_pywinauto()
        _mouse.double_click(button="left", coords=coords)
        time.sleep(self.config.after_click_delay)

    def move(self, coords: Tuple[int, int]) -> None:
        """移动鼠标到指定坐标。"""
        _ensure_pywinauto()
        _mouse.move(coords=coords)

    def scroll(self, coords: Tuple[int, int], wheel_dist: int) -> None:
        """在指定坐标滚动滚轮。

        :param wheel_dist: 正数向上滚（看更早的历史），负数向下滚。
        """
        _ensure_pywinauto()
        _mouse.scroll(coords=coords, wheel_dist=wheel_dist)
        time.sleep(0.2)

    def drag(self, start: Tuple[int, int], end: Tuple[int, int]) -> None:
        """按住左键从 start 拖拽到 end（可用于拖动滚动条翻页）。"""
        _ensure_pywinauto()
        _mouse.press(button="left", coords=start)
        _mouse.move(coords=end)
        _mouse.release(button="left", coords=end)
        time.sleep(self.config.after_click_delay)
