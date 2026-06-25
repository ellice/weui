# -*- coding: utf-8 -*-
"""基础消息发送能力 Mixin。

包含：搜索好友/群聊切入会话、纯文本发送（兼容换行/特殊符号/空格）、
回车发送、分段长文本、批量群发、@/表情/快捷键、剪贴板粘贴发送。
"""

from __future__ import annotations

import time
from typing import Dict, Iterable, List, Optional, Sequence

from . import clipboard, inputs
from .exceptions import ContactNotFoundError


class MessageMixin:
    """消息相关操作，依赖 ControlMixin 提供的控件能力。"""

    timeout: float = 10.0

    # ----------------------------- 搜索 / 切换会话 ----------------------------- #
    def search_contact(self, keyword: str, *, human: bool = False,
                       wait: float = 1.2) -> None:
        """根据备注 / 昵称 / 群名搜索并切入聊天窗口。

        :param keyword: 备注、昵称或群名关键字。
        :param human: 是否模拟真人输入。
        :param wait: 搜索结果加载等待时间。
        :raises ContactNotFoundError: 搜索框定位失败。
        """
        self.show()  # type: ignore[attr-defined]
        # 微信搜索框：control_type='Edit'，name 通常为 "搜索"
        try:
            search_box = self._find_search_box()
        except Exception as exc:  # noqa: BLE001
            raise ContactNotFoundError(f"未找到搜索框: {exc}") from exc

        search_box.click_input()
        time.sleep(0.2)
        inputs.select_all()
        inputs.press_backspace()
        time.sleep(0.1)

        # 用剪贴板粘贴，规避特殊字符输入问题
        clipboard.copy_text(keyword)
        inputs.paste()
        time.sleep(wait)
        inputs.press_enter()
        time.sleep(0.6)

    # 兼容别名
    open_chat = search_contact

    def _find_search_box(self):
        for crit in (
            {"title": "搜索", "control_type": "Edit"},
            {"control_type": "Edit", "found_index": 0},
        ):
            try:
                ctrl = self.find(**crit)  # type: ignore[attr-defined]
                if ctrl.exists():
                    return ctrl
            except Exception:  # noqa: BLE001
                continue
        raise ContactNotFoundError("搜索框未找到")

    def clear_search(self) -> None:
        """清空搜索框内容。"""
        try:
            box = self._find_search_box()
            box.click_input()
            inputs.select_all()
            inputs.press_backspace()
            inputs.press_esc()
        except Exception:  # noqa: BLE001
            inputs.press_esc()

    # ----------------------------- 输入框定位 ----------------------------- #
    def _find_message_edit(self):
        """定位聊天输入框（会话页右下角的大 Edit）。"""
        # 微信消息输入框通常是最后一个 / 面积最大的 Edit
        edits = self.find_all(control_type="Edit")  # type: ignore[attr-defined]
        if not edits:
            raise ContactNotFoundError("未找到消息输入框，请确认已打开会话")
        # 选面积最大的 Edit 作为消息输入框
        def area(c):
            try:
                r = c.rectangle()
                return r.width() * r.height()
            except Exception:  # noqa: BLE001
                return 0
        return max(edits, key=area)

    def focus_input(self):
        """聚焦消息输入框。"""
        edit = self._find_message_edit()
        edit.click_input()
        time.sleep(0.1)
        return edit

    def clear_input(self) -> None:
        """清空输入框内容。"""
        self.focus_input()
        inputs.select_all()
        inputs.press_backspace()

    # ----------------------------- 文本发送 ----------------------------- #
    def send_text(self, text: str, *, to: Optional[str] = None,
                  enter_to_send: bool = True, human: bool = False,
                  use_clipboard: bool = True) -> None:
        """发送纯文本消息，兼容换行、特殊符号、空格。

        :param text: 消息内容，``\n`` 会作为软换行写入（不会提前发送）。
        :param to: 若提供，则先搜索并切入该联系人 / 群。
        :param enter_to_send: True 用回车发送；False 仅输入不发送。
        :param human: 模拟真人慢速输入（仅在不使用剪贴板时生效）。
        :param use_clipboard: True 用剪贴板粘贴（推荐，兼容性最好）。
        """
        if to:
            self.search_contact(to, human=human)
        self.focus_input()

        if use_clipboard:
            clipboard.copy_text(text)
            inputs.paste()
            time.sleep(0.2)
        else:
            inputs.type_text(text, human=human)

        if enter_to_send:
            time.sleep(0.15)
            inputs.press_enter()

    def send_lines(self, lines: Sequence[str], *, to: Optional[str] = None,
                   interval: float = 0.4, human: bool = False) -> None:
        """分段发送长文本：每个元素作为一条独立消息发送。"""
        if to:
            self.search_contact(to, human=human)
        for i, line in enumerate(lines):
            self.send_text(line, enter_to_send=True, human=human)
            if i != len(lines) - 1:
                inputs.sleep_jitter(interval, 0.3)

    def send_long_text(self, text: str, *, to: Optional[str] = None,
                       chunk_size: int = 1500, interval: float = 0.5) -> None:
        """把超长文本自动按 ``chunk_size`` 切分为多条发送。"""
        if to:
            self.search_contact(to)
        chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]
        self.send_lines(chunks, interval=interval)

    def send_clipboard(self, *, to: Optional[str] = None,
                       enter_to_send: bool = True) -> None:
        """直接发送当前剪贴板内容（大段文字、链接等）。"""
        if to:
            self.search_contact(to)
        self.focus_input()
        inputs.paste()
        time.sleep(0.2)
        if enter_to_send:
            inputs.press_enter()

    # ----------------------------- 批量群发 ----------------------------- #
    def broadcast_text(self, contacts: Iterable[str], text: str, *,
                       interval: float = 1.0, human: bool = False
                       ) -> Dict[str, bool]:
        """循环批量给多个联系人 / 群群发同一段文本。

        :returns: ``{联系人: 是否成功}`` 的结果字典。
        """
        results: Dict[str, bool] = {}
        for name in contacts:
            try:
                self.send_text(text, to=name, human=human)
                results[name] = True
            except Exception:  # noqa: BLE001
                results[name] = False
            inputs.sleep_jitter(interval, 0.4)
        return results

    # ----------------------------- 快捷键 / @ / 表情 ----------------------------- #
    def at_member(self, name: str = "", *, human: bool = False) -> None:
        """群聊中 @ 某人（name 为空仅弹出 @ 列表）。"""
        self.focus_input()
        inputs.at_someone(name, human=human)

    def send_emoji_panel(self) -> None:
        """打开表情面板（点击表情按钮）。"""
        try:
            self.click_button("表情")  # type: ignore[attr-defined]
        except Exception:  # noqa: BLE001
            # 退化：聚焦输入框
            self.focus_input()
