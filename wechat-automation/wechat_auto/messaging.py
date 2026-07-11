"""基础消息发送能力。

    - 根据备注 / 昵称搜索好友、群聊并切入聊天窗口
    - 发送纯文本消息（支持换行、特殊符号、空格）
    - 模拟回车一键发送，支持分段长文本
    - 循环批量给多个联系人群发文本
    - 快捷键：@、换行、Tab、ESC 等组合按键
    - 剪贴板粘贴发送（大段文字、链接）
"""

from __future__ import annotations

import time
from typing import Dict, Iterable, List, Optional

from . import clipboard, inputs
from .exceptions import ContactNotFoundError, ControlNotFoundError
from .window import WeChatWindow


class Messaging:
    """消息发送相关能力，依赖 :class:`WeChatWindow`。"""

    # 搜索框、输入框的常见定位条件（不同微信版本可能略有差异）
    SEARCH_BOX = dict(title="搜索", control_type="Edit")

    def __init__(self, win: WeChatWindow, input_delay: float = 0.05):
        self.win = win
        self.input_delay = input_delay

    # ---- 搜索并切入会话 ----

    def search_and_open(self, keyword: str, wait: float = 1.2) -> None:
        """根据备注 / 昵称搜索好友或群聊，并进入其聊天窗口。

        :param keyword: 备注、昵称或群名（需与微信中显示的名称一致或前缀匹配）
        :param wait: 搜索结果加载等待时间
        :raises ContactNotFoundError: 未搜索到联系人
        """
        self.win.activate()
        search_box = self._get_search_box()
        search_box.click_input()
        # 先清空搜索框
        inputs.select_all()
        inputs.backspace()
        time.sleep(0.1)

        # 用剪贴板粘贴关键词，兼容表情 / 特殊字符
        clipboard.set_text(keyword)
        inputs.paste()
        time.sleep(wait)

        # 回车选中第一个搜索结果
        inputs.enter()
        time.sleep(wait)

        # 校验是否成功进入会话（输入框应可用）
        if self._try_get_edit() is None:
            raise ContactNotFoundError(f"未找到联系人 / 群聊: {keyword}")

    def clear_search(self) -> None:
        """清空搜索框内容。"""
        box = self.win.try_find(**self.SEARCH_BOX)
        if box is not None:
            box.click_input()
            inputs.select_all()
            inputs.backspace()

    def _get_search_box(self):
        box = self.win.try_find(**self.SEARCH_BOX)
        if box is None:
            # 退回：用名称近似匹配
            box = self.win.try_find(control_type="Edit")
        if box is None:
            raise ControlNotFoundError("未找到搜索框")
        return box

    # ---- 输入框 ----

    def _get_edit(self):
        """获取当前聊天窗口的消息输入框。"""
        edit = self._try_get_edit()
        if edit is None:
            raise ControlNotFoundError("未找到消息输入框，请确认已进入某个聊天窗口")
        return edit

    def _try_get_edit(self):
        # 聊天输入框通常是最后一个可编辑的 Edit / Document 控件
        for ct in ("Edit", "Document"):
            candidates = self._descendants(control_type=ct)
            # 排除搜索框
            for c in reversed(candidates):
                try:
                    if c.window_text() != "搜索":
                        return c
                except Exception:
                    continue
        return None

    def _descendants(self, **criteria) -> List:
        try:
            return self.win.window.descendants(**criteria)
        except Exception:
            return []

    def clear_input(self) -> None:
        """清空输入框内容。"""
        edit = self._get_edit()
        edit.click_input()
        inputs.select_all()
        inputs.backspace()

    # ---- 发送文本 ----

    def send_text(
        self,
        text: str,
        send: bool = True,
        human_like: bool = False,
        use_clipboard: bool = True,
    ) -> None:
        """在当前聊天窗口发送文本。

        :param text: 文本内容，``\\n`` 视为消息内软换行（Shift+Enter）
        :param send: 是否直接回车发送
        :param human_like: 是否模拟真人慢速逐字输入（防风控），
            为 True 时忽略 ``use_clipboard``
        :param use_clipboard: 是否用剪贴板粘贴（推荐，兼容大段文字、链接、特殊符号）
        """
        edit = self._get_edit()
        edit.click_input()
        time.sleep(self.input_delay)

        if human_like:
            self._type_human(text)
        elif use_clipboard:
            clipboard.set_text(text)
            inputs.paste()
        else:
            self._type_with_soft_newline(text)

        time.sleep(self.input_delay)
        if send:
            inputs.enter()

    def _type_with_soft_newline(self, text: str) -> None:
        """逐段输入，段间用 Shift+Enter 软换行，避免提前发送。"""
        lines = text.split("\n")
        for i, line in enumerate(lines):
            inputs.type_text(line)
            if i < len(lines) - 1:
                inputs.newline()

    def _type_human(self, text: str) -> None:
        lines = text.split("\n")
        for i, line in enumerate(lines):
            inputs.type_text(line, human_like=True)
            if i < len(lines) - 1:
                inputs.newline()

    def send_long_text(self, text: str, chunk_size: int = 1000, interval: float = 0.6) -> None:
        """分段发送长文本，避免单条过长。

        :param chunk_size: 每段字符数
        :param interval: 每段之间的间隔
        """
        for i in range(0, len(text), chunk_size):
            self.send_text(text[i : i + chunk_size], send=True)
            time.sleep(interval)

    def send_paste(self, content: str) -> None:
        """将内容写入剪贴板后粘贴并发送（大段文字 / 链接）。"""
        self.send_text(content, send=True, use_clipboard=True)

    # ---- 搜索 + 发送 组合 ----

    def send_to(self, contact: str, text: str, **kwargs) -> None:
        """搜索联系人并发送文本（一步到位）。"""
        self.search_and_open(contact)
        self.send_text(text, **kwargs)

    def broadcast(
        self,
        contacts: Iterable[str],
        text: str,
        interval: float = 1.0,
        human_like: bool = False,
    ) -> Dict[str, bool]:
        """循环批量给多个联系人 / 群聊群发文本。

        :param contacts: 联系人 / 群名列表
        :param text: 消息内容
        :param interval: 每个联系人之间的间隔（防风控）
        :param human_like: 是否模拟真人输入
        :return: {联系人: 是否成功} 的结果字典
        """
        results: Dict[str, bool] = {}
        for contact in contacts:
            try:
                self.search_and_open(contact)
                self.send_text(text, send=True, human_like=human_like)
                results[contact] = True
            except Exception:
                results[contact] = False
            time.sleep(interval)
        return results

    # ---- 快捷键组合 ----

    def at_member(self, name: str, text: str = "", send: bool = False) -> None:
        """群聊中 @ 某位成员，可跟随文本。"""
        edit = self._get_edit()
        edit.click_input()
        inputs.at_someone(name)
        time.sleep(0.4)
        inputs.enter()  # 选中 @ 候选
        if text:
            inputs.type_text(" " + text)
        if send:
            inputs.enter()
