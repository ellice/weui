"""键鼠模拟配套功能（需求类别五）。

基于 pywinauto.keyboard / pywinauto.mouse 封装：
- 精准鼠标点击、右键、双击
- 鼠标滚轮上下翻页（聊天记录）
- 全局快捷键：Ctrl+C/V/A、Enter、Backspace、Tab、ESC、@、表情、换行
- 输入延时控制，逐字「慢速」输入，模拟真人防风控
"""

from __future__ import annotations

import random
import time
from typing import Iterable, Optional, Tuple

from .utils import human_sleep, logger

try:
    from pywinauto import keyboard as _kb  # type: ignore
    from pywinauto import mouse as _mouse  # type: ignore
    _HAS_PWA = True
except Exception:  # pragma: no cover - 非 Windows / 未安装
    _kb = None  # type: ignore
    _mouse = None  # type: ignore
    _HAS_PWA = False


def _require_pwa() -> None:
    if not _HAS_PWA:
        raise RuntimeError("未安装 pywinauto，键鼠模拟不可用：pip install pywinauto")


# pywinauto.keyboard 转义字符（这些符号在 send_keys 中有特殊含义，需要 {} 包裹）
_SPECIAL_CHARS = set("^+%~(){}[]")


def escape_keys(text: str) -> str:
    """转义 send_keys 的特殊字符，确保纯文本按字面输入。"""
    out = []
    for ch in text:
        if ch in _SPECIAL_CHARS:
            out.append("{" + ch + "}")
        else:
            out.append(ch)
    return "".join(out)


class InputSimulator:
    """键鼠模拟器。所有方法都尽量做成「无状态工具」，可独立调用。"""

    def __init__(self, key_interval: float = 0.0, human_like: bool = True) -> None:
        # key_interval: send_keys 的 pause（每个按键间隔）
        self.key_interval = key_interval
        self.human_like = human_like

    # ---------------- 键盘 ----------------
    def send_keys(self, keys: str, pause: Optional[float] = None) -> None:
        """直接发送 pywinauto 风格按键串（调用方需自行转义）。"""
        _require_pwa()
        _kb.send_keys(keys, pause=self.key_interval if pause is None else pause)

    def type_text(self, text: str, with_spaces: bool = True) -> None:
        """一次性输入纯文本（自动转义），保留空格与换行兼容。"""
        _require_pwa()
        escaped = escape_keys(text).replace("\n", "{ENTER}")
        _kb.send_keys(escaped, with_spaces=with_spaces, pause=self.key_interval)

    def type_text_slowly(
        self, text: str, char_delay: float = 0.08, jitter: float = 0.06
    ) -> None:
        """逐字慢速输入，模拟真人节奏（防风控）。

        换行用 Shift+Enter（聊天框内换行，不发送）。
        """
        _require_pwa()
        for ch in text:
            if ch == "\n":
                _kb.send_keys("+{ENTER}")  # Shift+Enter 换行
            else:
                _kb.send_keys(escape_keys(ch), with_spaces=True, pause=0)
            time.sleep(max(0.0, char_delay + random.uniform(0, jitter)))

    # 常用组合键封装
    def press_enter(self) -> None:
        _require_pwa()
        _kb.send_keys("{ENTER}")

    def newline(self) -> None:
        """聊天框内换行（Shift+Enter），不触发发送。"""
        _require_pwa()
        _kb.send_keys("+{ENTER}")

    def press_tab(self) -> None:
        _require_pwa()
        _kb.send_keys("{TAB}")

    def press_esc(self) -> None:
        _require_pwa()
        _kb.send_keys("{ESC}")

    def press_backspace(self, count: int = 1) -> None:
        _require_pwa()
        _kb.send_keys("{BACKSPACE}" * max(1, count))

    def select_all(self) -> None:
        _require_pwa()
        _kb.send_keys("^a")

    def copy(self) -> None:
        _require_pwa()
        _kb.send_keys("^c")

    def paste(self) -> None:
        _require_pwa()
        _kb.send_keys("^v")
        if self.human_like:
            human_sleep(0.2, 0.2)

    def clear_field(self) -> None:
        """清空当前焦点输入框：全选 + 删除。"""
        _require_pwa()
        _kb.send_keys("^a{BACKSPACE}")

    def at_someone(self, name: str = "", confirm: bool = True) -> None:
        """群聊 @ 某人：输入 @，再输入名字，回车确认候选。

        name 为空时只打出 @，弹出成员列表。
        """
        _require_pwa()
        _kb.send_keys("@")
        human_sleep(0.3, 0.2)
        if name:
            _kb.send_keys(escape_keys(name), with_spaces=True)
            human_sleep(0.4, 0.2)
            if confirm:
                _kb.send_keys("{ENTER}")

    def hotkey(self, *keys: str) -> None:
        """组合键，例如 hotkey('ctrl', 'a')。"""
        _require_pwa()
        mods = {"ctrl": "^", "shift": "+", "alt": "%"}
        prefix = ""
        normal = []
        for k in keys:
            kl = k.lower()
            if kl in mods:
                prefix += mods[kl]
            else:
                normal.append(k)
        seq = prefix + "".join(f"{{{k}}}" if len(k) > 1 else k for k in normal)
        _kb.send_keys(seq)

    # ---------------- 鼠标 ----------------
    def click(self, coords: Tuple[int, int], button: str = "left") -> None:
        """在屏幕绝对坐标处单击。"""
        _require_pwa()
        _mouse.click(button=button, coords=coords)
        if self.human_like:
            human_sleep(0.1, 0.1)

    def right_click(self, coords: Tuple[int, int]) -> None:
        _require_pwa()
        _mouse.right_click(coords=coords)
        if self.human_like:
            human_sleep(0.1, 0.1)

    def double_click(self, coords: Tuple[int, int]) -> None:
        _require_pwa()
        _mouse.double_click(coords=coords)
        if self.human_like:
            human_sleep(0.1, 0.1)

    def scroll(self, coords: Tuple[int, int], wheel_dist: int) -> None:
        """在指定坐标滚动鼠标滚轮。wheel_dist>0 向上，<0 向下。"""
        _require_pwa()
        _mouse.scroll(coords=coords, wheel_dist=wheel_dist)
        if self.human_like:
            human_sleep(0.2, 0.2)

    def scroll_up(self, coords: Tuple[int, int], steps: int = 3) -> None:
        self.scroll(coords, abs(steps))

    def scroll_down(self, coords: Tuple[int, int], steps: int = 3) -> None:
        self.scroll(coords, -abs(steps))
