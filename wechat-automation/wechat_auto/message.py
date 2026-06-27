"""基础消息发送：纯文本、分段长文本、剪贴板粘贴、批量群发。"""

from __future__ import annotations

import time
from typing import Dict, Iterable, List, Optional, Sequence

from . import clipboard
from . import controls as C
from . import input_utils as K
from .core import WeChatAuto


class MessageSender:
    """文本类消息发送能力封装。"""

    def __init__(self, wechat: WeChatAuto):
        self.wx = wechat

    # ------------------------------------------------------------------ #
    # 单条文本
    # ------------------------------------------------------------------ #
    def send_text(
        self,
        text: str,
        use_clipboard: bool = True,
        human_typing: bool = False,
        clear_first: bool = True,
    ) -> None:
        """向当前聊天窗口发送一条文本消息。

        参数：
            use_clipboard : True 用剪贴板粘贴（推荐，兼容换行/特殊符号/空格/链接）
            human_typing  : True 时逐字符慢速输入，模拟真人，防风控
            clear_first   : 发送前先清空输入框
        """
        edit = self.wx.input_edit()
        C.wait_visible(edit, timeout=self.wx.default_timeout)
        edit.set_focus()

        if clear_first:
            C.clear_edit(edit)

        if use_clipboard:
            clipboard.copy_text(text)
            K.paste()
        elif human_typing:
            K.type_text_human(text)
        else:
            K.type_text(text)

        time.sleep(0.2)
        K.press_enter()

    # ------------------------------------------------------------------ #
    # 分段长文本
    # ------------------------------------------------------------------ #
    def send_long_text(
        self,
        text: str,
        max_chars: int = 2000,
        interval: float = 0.6,
    ) -> int:
        """把超长文本按 max_chars 分段，逐段发送。返回发送的段数。"""
        segments = [text[i : i + max_chars] for i in range(0, len(text), max_chars)]
        for seg in segments:
            self.send_text(seg)
            time.sleep(interval)
        return len(segments)

    def send_lines(self, lines: Sequence[str], interval: float = 0.5) -> None:
        """把多行分别作为独立消息逐条发送。"""
        for line in lines:
            self.send_text(line)
            time.sleep(interval)

    def send_multiline_message(self, lines: Sequence[str]) -> None:
        """把多行合并成一条带换行的消息发送（Shift+Enter 换行）。"""
        self.send_text("\n".join(lines))

    # ------------------------------------------------------------------ #
    # 批量群发
    # ------------------------------------------------------------------ #
    def broadcast(
        self,
        contacts: Iterable[str],
        text: str,
        interval: float = 1.5,
        human_like: bool = True,
    ) -> Dict[str, bool]:
        """循环给多个联系人/群聊群发同一段文本。

        返回 {联系人: 是否成功} 的结果字典。单个失败不影响其余。
        """
        results: Dict[str, bool] = {}
        for name in contacts:
            try:
                self.wx.search_and_open(name)
                self.send_text(text)
                results[name] = True
            except Exception:  # noqa: BLE001
                results[name] = False
            if human_like:
                K.random_sleep(interval, interval + 1.0)
            else:
                time.sleep(interval)
        return results

    def broadcast_personalized(
        self,
        messages: Dict[str, str],
        interval: float = 1.5,
    ) -> Dict[str, bool]:
        """给不同联系人发送不同内容。messages = {联系人: 文本}。"""
        results: Dict[str, bool] = {}
        for name, text in messages.items():
            try:
                self.wx.search_and_open(name)
                self.send_text(text)
                results[name] = True
            except Exception:  # noqa: BLE001
                results[name] = False
            K.random_sleep(interval, interval + 1.0)
        return results

    # ------------------------------------------------------------------ #
    # @ 群成员
    # ------------------------------------------------------------------ #
    def send_with_mention(self, member_name: str, text: str) -> None:
        """在群聊中 @某人 并附带文本后发送。"""
        edit = self.wx.input_edit()
        edit.set_focus()
        C.clear_edit(edit)
        K.mention(member_name)
        time.sleep(0.5)
        K.press_enter()  # 选中 @ 候选
        time.sleep(0.2)
        clipboard.copy_text(" " + text)
        K.paste()
        time.sleep(0.2)
        K.press_enter()
