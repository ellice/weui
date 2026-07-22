"""基础消息发送能力。

* 根据备注 / 昵称搜索好友、群聊并切入聊天窗口
* 发送纯文本（支持换行、特殊符号、空格）
* 回车一键发送、分段长文本
* 循环批量群发
* 快捷键组合（@、换行、Tab、Esc 等）
* 剪贴板粘贴发送（大段文字、链接）
"""

from __future__ import annotations

import time
from typing import Iterable, List, Optional, Sequence

from . import clipboard, input_utils
from .exceptions import ContactNotFoundError


class MessageMixin:
    """消息发送混入类。"""

    config: "object"

    # -------------------------------------------------------- 搜索切换 ----
    def _focus_search_box(self):
        """定位并聚焦左上角搜索框。"""
        cfg = self.config
        # 优先按名称匹配，失败则退化到第一个 Edit
        try:
            box = self.find_control(
                title=cfg.search_edit_name, control_type="Edit", timeout=cfg.default_timeout
            )
        except Exception:  # noqa: BLE001
            box = self.find_control(control_type="Edit", timeout=cfg.default_timeout)
        box.click_input()
        return box

    def clear_search(self):
        """清空搜索框内容。"""
        self._focus_search_box()
        input_utils.clear_edit()
        return self

    def search_and_open(self, keyword: str, timeout: Optional[float] = None):
        """根据备注 / 昵称搜索好友或群聊，并切入其聊天窗口。

        :param keyword: 好友备注 / 昵称 / 群名
        :raises ContactNotFoundError: 未搜索到匹配项
        """
        cfg = self.config
        self.bring_to_front()
        box = self._focus_search_box()

        # 先清空，避免残留内容
        input_utils.clear_edit()
        # 用剪贴板粘贴关键字，兼容 emoji / 特殊字符
        clipboard.copy_text(keyword)
        clipboard.wait_settle(cfg.clipboard_settle_delay)
        input_utils.paste()
        time.sleep(cfg.search_settle_delay)

        # 回车打开第一个匹配的会话
        input_utils.press_enter()
        time.sleep(cfg.poll_interval)

        # 校验聊天窗口标题是否切到目标（尽力而为，不同版本控件不同）
        if not self._chat_opened(keyword, timeout):
            raise ContactNotFoundError(f"未搜索到联系人/群聊: {keyword}")
        return self

    def _chat_opened(self, keyword: str, timeout: Optional[float] = None) -> bool:
        """判断聊天窗口是否已打开（尽力校验，失败不抛异常）。"""
        cfg = self.config
        timeout = cfg.default_timeout if timeout is None else timeout
        deadline = time.time() + timeout
        while time.time() < deadline:
            # 输入框可编辑通常意味着已进入某个会话
            if self.control_exists(control_type="Edit"):
                return True
            time.sleep(cfg.poll_interval)
        return False

    # ---------------------------------------------------------- 输入框 ----
    def _focus_input_box(self):
        """定位并聚焦聊天输入框（通常是聊天区域下方最大的 Edit）。"""
        cfg = self.config
        try:
            box = self.find_control(
                title=cfg.input_edit_name, control_type="Edit", timeout=cfg.default_timeout
            )
        except Exception:  # noqa: BLE001
            # 退化：取最后一个可编辑 Edit（搜索框通常在最前）
            edits = self._require_window().descendants(control_type="Edit")
            if not edits:
                raise
            box = edits[-1]
        box.click_input()
        return box

    def clear_input(self):
        """清空聊天输入框内容。"""
        self._focus_input_box()
        input_utils.clear_edit()
        return self

    # -------------------------------------------------------- 发送文本 ----
    def send_text(
        self,
        text: str,
        human_like: bool = False,
        clear_first: bool = True,
    ):
        """向当前聊天窗口发送一条纯文本消息。

        支持换行、空格与特殊符号。换行使用 Shift+Enter，最后回车发送。

        :param text: 消息内容，``\\n`` 表示换行
        :param human_like: 是否使用慢速真人输入（防风控）
        :param clear_first: 发送前是否先清空输入框
        """
        cfg = self.config
        self._focus_input_box()
        if clear_first:
            input_utils.clear_edit()

        lines = text.split("\n")
        for idx, line in enumerate(lines):
            if line:
                if human_like:
                    input_utils.type_text_human(
                        line, cfg.type_interval, cfg.type_jitter
                    )
                else:
                    input_utils.type_text_fast(line)
            if idx < len(lines) - 1:
                input_utils.press_shift_enter()  # 段内换行，不发送

        input_utils.press_enter()  # 一键发送
        return self

    def send_text_via_clipboard(self, text: str, clear_first: bool = True):
        """通过剪贴板粘贴发送文本（适合大段文字、链接，速度快且稳定）。

        换行会随文本原样粘贴，最后回车发送。
        """
        cfg = self.config
        self._focus_input_box()
        if clear_first:
            input_utils.clear_edit()
        clipboard.copy_text(text)
        clipboard.wait_settle(cfg.clipboard_settle_delay)
        input_utils.paste()
        time.sleep(cfg.poll_interval)
        input_utils.press_enter()
        return self

    def send_long_text_in_segments(
        self,
        text: str,
        max_chars: int = 500,
        segment_delay: float = 1.0,
    ):
        """把超长文本按 ``max_chars`` 分段，逐段发送。

        :param max_chars: 每段最大字符数
        :param segment_delay: 段与段之间的延时（秒）
        """
        segments = [text[i : i + max_chars] for i in range(0, len(text), max_chars)]
        for seg in segments:
            self.send_text_via_clipboard(seg)
            time.sleep(segment_delay)
        return self

    # ------------------------------------------------------ 快捷键组合 ----
    def send_at(self, member: str = "", human_like: bool = False):
        """在群聊中 @ 某位成员。

        输入 ``@`` 后微信会弹出成员列表，继续输入成员名并回车选中。

        :param member: 成员昵称，留空则仅输入 @ 符号
        """
        self._focus_input_box()
        input_utils.press_at()
        time.sleep(self.config.poll_interval)
        if member:
            if human_like:
                input_utils.type_text_human(member)
            else:
                input_utils.type_text_fast(member)
            time.sleep(self.config.poll_interval)
            input_utils.press_enter()  # 选中候选成员
        return self

    def press_hotkey(self, keys: str):
        """发送任意快捷键组合（send_keys 语法），如 ``^a``、``{ESC}``、``{TAB}``。"""
        input_utils.send_keys(keys)
        return self

    # -------------------------------------------------------- 批量群发 ----
    def batch_send_text(
        self,
        contacts: Sequence[str],
        text: str,
        human_like: bool = False,
        delay: Optional[float] = None,
        via_clipboard: bool = True,
    ) -> List[str]:
        """循环给多个联系人 / 群聊群发同一段文本。

        :param contacts: 联系人备注 / 昵称 / 群名列表
        :param text: 群发文本
        :param delay: 每个联系人之间的间隔（秒），默认取配置降低风控风险
        :param via_clipboard: 是否用剪贴板粘贴方式发送（更快更稳）
        :return: 发送失败的联系人列表
        """
        cfg = self.config
        delay = cfg.batch_send_delay if delay is None else delay
        failed: List[str] = []
        for name in contacts:
            try:
                self.search_and_open(name)
                if via_clipboard:
                    self.send_text_via_clipboard(text)
                else:
                    self.send_text(text, human_like=human_like)
            except Exception:  # noqa: BLE001 - 单个失败不影响整体群发
                failed.append(name)
            time.sleep(delay)
        return failed
