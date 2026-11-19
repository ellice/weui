"""搜索好友 / 群聊并切入聊天窗口。

通过顶部搜索框输入关键字（备注 / 昵称），回车进入对应会话。
"""

from __future__ import annotations

import time
from typing import Any

from .clipboard import set_text, wait_clipboard_ready
from .controls import ControlHelper
from .exceptions import ContactNotFoundError
from .input_simulator import InputSimulator


class Navigator:
    """负责搜索与切换会话。"""

    def __init__(self, window: Any, controls: ControlHelper,
                 simulator: InputSimulator) -> None:
        self.window = window
        self.controls = controls
        self.sim = simulator

    def _search_box(self) -> Any:
        """获取顶部搜索框控件。"""
        # 微信搜索框是一个 Edit 控件，标题通常为「搜索」。
        return self.controls.wait_control(
            title="搜索", control_type="Edit", timeout=8.0,
        )

    def clear_search(self) -> None:
        """清空搜索框内容。"""
        box = self.controls.find_optional(title="搜索", control_type="Edit")
        if box is None:
            return
        box.click_input()
        self.sim.select_all()
        self.sim.press_backspace()

    def search_and_open(self, keyword: str, wait: float = 1.2,
                        use_clipboard: bool = True) -> None:
        """搜索关键字并进入第一个匹配的会话。

        :param keyword: 好友备注 / 昵称 / 群聊名。
        :param wait: 输入后等待搜索结果出现的时间。
        :param use_clipboard: 是否用剪贴板粘贴关键字（更稳，支持特殊字符）。
        :raises ContactNotFoundError: 找不到匹配项。
        """
        box = self._search_box()
        box.click_input()
        self.sim.select_all()
        self.sim.press_backspace()

        if use_clipboard:
            set_text(keyword)
            wait_clipboard_ready()
            self.sim.paste()
        else:
            self.sim.type_text(keyword)

        time.sleep(wait)
        # 回车进入高亮的第一个搜索结果。
        self.sim.press_enter()
        time.sleep(0.6)

        if not self._chat_opened():
            raise ContactNotFoundError(f"未能进入会话: {keyword!r}")

    def _chat_opened(self) -> bool:
        """粗略判断是否已进入某个聊天窗口（存在消息输入框）。"""
        return self.controls.exists(control_type="Edit", title="输入") or \
            self.controls.exists(control_type="Edit", found_index=0)
