"""文本消息发送能力。

包含：
- 纯文本发送，兼容换行 / 特殊符号 / 空格；
- 回车一键发送 + 分段长文本；
- 循环批量群发；
- @ 提及、表情、Tab、Esc 等快捷键输入；
- 剪贴板粘贴大段文字 / 链接后发送。
"""

from __future__ import annotations

import time
from typing import Any, Dict, Iterable, List, Optional

from .clipboard import set_text, wait_clipboard_ready
from .controls import ControlHelper
from .exceptions import ControlNotFoundError
from .input_simulator import InputSimulator
from .navigation import Navigator


class MessageSender:
    """聊天文本消息发送器。"""

    def __init__(self, window: Any, controls: ControlHelper,
                 simulator: InputSimulator, navigator: Navigator) -> None:
        self.window = window
        self.controls = controls
        self.sim = simulator
        self.nav = navigator

    # ----- 输入框 -----
    def _input_box(self) -> Any:
        """获取当前会话的消息输入框。

        微信不同版本输入框定位不一致，这里做多重回退。
        """
        for criteria in (
            dict(title="输入", control_type="Edit"),
            dict(control_type="Edit", found_index=0),
        ):
            ctrl = self.controls.find_optional(**criteria)
            if ctrl is not None:
                return ctrl
        raise ControlNotFoundError("未找到消息输入框，请确认已进入聊天窗口。")

    def focus_input(self) -> Any:
        box = self._input_box()
        box.click_input()
        return box

    def clear_input(self) -> None:
        """清空输入框。"""
        self.focus_input()
        self.sim.select_all()
        self.sim.press_backspace()

    # ----- 发送 -----
    def send_text(self, text: str, paste: bool = True,
                  send: bool = True) -> None:
        """向当前会话发送一段文本。

        :param text: 文本内容，``\\n`` 视为软换行（Shift+Enter，不触发发送）。
        :param paste: True 用剪贴板粘贴（推荐：兼容空格 / 特殊符号 / emoji /
                      链接，速度快）；False 用拟人逐字输入。
        :param send: 是否输入完毕后回车发送。
        """
        self.focus_input()
        if paste:
            self._paste_with_newlines(text)
        else:
            self._type_with_newlines(text)
        if send:
            time.sleep(0.15)
            self.sim.press_enter()

    def _paste_with_newlines(self, text: str) -> None:
        """按行粘贴，行间用 Shift+Enter 软换行。"""
        lines = text.split("\n")
        for i, line in enumerate(lines):
            if line:
                set_text(line)
                wait_clipboard_ready()
                self.sim.paste()
            if i < len(lines) - 1:
                self.sim.newline()

    def _type_with_newlines(self, text: str) -> None:
        lines = text.split("\n")
        for i, line in enumerate(lines):
            if line:
                self.sim.type_text(line)
            if i < len(lines) - 1:
                self.sim.newline()

    def send_paragraphs(self, paragraphs: Iterable[str],
                        interval: float = 0.8, paste: bool = True) -> None:
        """分段发送长文本：每段作为独立的一条消息逐条发出。"""
        for para in paragraphs:
            self.send_text(para, paste=paste, send=True)
            time.sleep(interval)

    def send_long_text(self, text: str, chunk_size: int = 1500,
                       interval: float = 0.8) -> None:
        """把超长文本按 ``chunk_size`` 切块后分多条发送。"""
        chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]
        self.send_paragraphs(chunks, interval=interval)

    # ----- 批量群发 -----
    def broadcast(self, contacts: Iterable[str], text: str,
                  interval: float = 1.0, paste: bool = True,
                  per_contact_texts: Optional[Dict[str, str]] = None
                  ) -> Dict[str, bool]:
        """循环批量给多个联系人 / 群聊群发文本。

        :param contacts: 联系人备注 / 昵称 / 群名列表。
        :param text: 默认群发内容。
        :param per_contact_texts: 可选，针对特定联系人覆盖默认内容。
        :param interval: 每个联系人之间的等待时间（防风控）。
        :return: {联系人: 是否发送成功}
        """
        results: Dict[str, bool] = {}
        per_contact_texts = per_contact_texts or {}
        for contact in contacts:
            try:
                self.nav.search_and_open(contact)
                content = per_contact_texts.get(contact, text)
                self.send_text(content, paste=paste, send=True)
                results[contact] = True
            except Exception:  # noqa: BLE001
                results[contact] = False
            time.sleep(interval)
        return results

    # ----- 快捷键输入 -----
    def mention(self, name: str = "", wait: float = 0.6) -> None:
        """在群聊中 @ 某人。

        输入 ``@`` 触发成员浮层，键入名字后回车选择；``name`` 为空则仅触发浮层。
        """
        self.focus_input()
        self.sim.mention()
        if name:
            time.sleep(0.2)
            self.sim.type_text(name)
            time.sleep(wait)
            self.sim.press_enter()

    def insert_emoji_text(self, emoji_codes: List[str]) -> None:
        """通过表情代码（如 ``[微笑]``）插入微信内置表情。"""
        for code in emoji_codes:
            set_text(code)
            wait_clipboard_ready()
            self.focus_input()
            self.sim.paste()

    def press_tab(self) -> None:
        self.sim.press_tab()

    def press_esc(self) -> None:
        self.sim.press_esc()
