"""基础消息发送能力（第一类）。

- 按备注 / 昵称搜索好友、群聊并切入会话
- 发送纯文本（换行、特殊符号、空格兼容）
- 回车一键发送、分段长文本
- 循环批量群发
- 快捷键输入（@、表情、换行、Tab、ESC 等）
- 剪贴板粘贴内容发送（大段文字、链接）
"""

from __future__ import annotations

import time
from typing import Dict, Iterable, List, Optional

from . import clipboard
from .config import WeChatConfig
from .controls import ControlHelper
from .exceptions import ContactNotFoundError, SendMessageError
from .inputs import InputController


class MessageSender:
    """文本消息发送与联系人切换。"""

    def __init__(
        self,
        window,
        controls: ControlHelper,
        inputs: InputController,
        config: WeChatConfig,
    ) -> None:
        self.window = window
        self.controls = controls
        self.inputs = inputs
        self.config = config

    # ------------------------------------------------------------------ #
    # 搜索并切入会话
    # ------------------------------------------------------------------ #
    def search_and_open(self, keyword: str, timeout: Optional[float] = None) -> None:
        """按备注 / 昵称 / 群名搜索并进入对应聊天窗口。

        原理：聚焦搜索框 → 清空 → 输入关键字 → 等待搜索结果 → 回车选中第一项。
        """
        timeout = self.config.default_timeout if timeout is None else timeout
        search_box = self.controls.find_first(
            [
                {"title": t, "control_type": "Edit"}
                for t in self.config.search_box_fallback_titles
            ],
            timeout=timeout,
        )
        try:
            search_box.set_focus()
            # 清空原有内容
            search_box.type_keys("^a{BACKSPACE}", set_foreground=True)
            time.sleep(self.config.action_delay)
            # 用剪贴板粘贴关键字，兼容中文 / 特殊字符
            clipboard.copy_text(keyword)
            self.inputs.hotkey_paste()
            time.sleep(max(self.config.action_delay, 0.8))
            # 回车选中第一条搜索结果
            self.inputs.press_enter()
            time.sleep(max(self.config.action_delay, 0.8))
        except Exception as exc:  # noqa: BLE001
            raise ContactNotFoundError(f"搜索并打开会话失败（{keyword}）：{exc}") from exc

        # 校验是否成功进入会话：输入框应可用
        if not self._input_available():
            raise ContactNotFoundError(
                f"未能切入会话「{keyword}」，可能是关键字无匹配或控件标题不同。"
            )

    # ------------------------------------------------------------------ #
    # 发送文本
    # ------------------------------------------------------------------ #
    def send_text(
        self,
        text: str,
        use_clipboard: bool = True,
        clear_first: bool = True,
    ) -> None:
        """在当前会话发送纯文本消息。

        :param use_clipboard: True 用剪贴板粘贴（推荐，兼容换行 / 特殊符号 /
            空格 / 表情 emoji / 链接）；False 用慢速逐字输入（防风控）。
        :param clear_first: 发送前是否先清空输入框。
        """
        edit = self._get_input_edit()
        edit.set_focus()
        if clear_first:
            self.inputs.hotkey_select_all()
            self.inputs.press_backspace()

        if use_clipboard:
            clipboard.copy_text(text)
            self.inputs.hotkey_paste()
            time.sleep(self.config.action_delay)
        else:
            self.inputs.type_text_slowly(text)

        self._send()

    def send_text_slowly(self, text: str, interval: Optional[float] = None) -> None:
        """慢速逐字输入并发送（模拟真人，降低风控风险）。"""
        edit = self._get_input_edit()
        edit.set_focus()
        self.inputs.type_text_slowly(text, interval=interval)
        self._send()

    def send_long_text(
        self,
        text: str,
        max_chars: int = 1000,
        segment_interval: Optional[float] = None,
    ) -> int:
        """把超长文本按 ``max_chars`` 分段发送，返回发送的段数。

        微信单条消息过长可能被截断或失败，分段更稳妥。
        """
        segment_interval = (
            self.config.batch_interval if segment_interval is None else segment_interval
        )
        segments = _split_text(text, max_chars)
        for i, seg in enumerate(segments):
            self.send_text(seg, use_clipboard=True, clear_first=True)
            if i < len(segments) - 1:
                time.sleep(segment_interval)
        return len(segments)

    # ------------------------------------------------------------------ #
    # 批量群发
    # ------------------------------------------------------------------ #
    def batch_send_text(
        self,
        contacts: Iterable[str],
        text: str,
        interval: Optional[float] = None,
        use_clipboard: bool = True,
    ) -> Dict[str, bool]:
        """循环给多个联系人 / 群聊发送同一段文本。

        :returns: {联系人: 是否成功} 的结果字典。
        """
        interval = self.config.batch_interval if interval is None else interval
        results: Dict[str, bool] = {}
        contacts = list(contacts)
        for i, name in enumerate(contacts):
            try:
                self.search_and_open(name)
                self.send_text(text, use_clipboard=use_clipboard)
                results[name] = True
            except Exception:  # noqa: BLE001
                results[name] = False
            if i < len(contacts) - 1:
                time.sleep(interval)
        return results

    # ------------------------------------------------------------------ #
    # 快捷键 / 组合按键
    # ------------------------------------------------------------------ #
    def mention(self, name: str) -> None:
        """在群聊输入框 @ 某人：输入 @ 后弹出候选，输入名字并回车选中。"""
        edit = self._get_input_edit()
        edit.set_focus()
        self.inputs.send_keys("@")
        time.sleep(self.config.action_delay)
        self.inputs.type_text_slowly(name)
        time.sleep(self.config.action_delay)
        self.inputs.press_enter()  # 选中候选中的第一个

    def insert_newline(self) -> None:
        """在输入框中插入换行（Shift+Enter），不发送。"""
        self._get_input_edit().set_focus()
        self.inputs.new_line()

    def open_emoji_panel(self) -> None:
        """点击表情按钮打开表情面板。"""
        self.controls.click_button("表情")

    def press_tab(self) -> None:
        self.inputs.press_tab()

    def press_esc(self) -> None:
        self.inputs.press_esc()

    def paste_and_send(self, text: str) -> None:
        """把大段文字 / 链接复制到剪贴板后粘贴并发送。"""
        self.send_text(text, use_clipboard=True)

    # ------------------------------------------------------------------ #
    # 内部
    # ------------------------------------------------------------------ #
    def _get_input_edit(self):
        return self.controls.find_first(
            [
                {"title": t, "control_type": "Edit"}
                for t in self.config.input_edit_fallback_titles
            ],
            timeout=self.config.default_timeout,
        )

    def _input_available(self) -> bool:
        try:
            return self.controls.exists(
                title=self.config.input_edit_title, control_type="Edit"
            ) or any(
                self.controls.exists(title=t, control_type="Edit")
                for t in self.config.input_edit_fallback_titles
            )
        except Exception:  # noqa: BLE001
            return False

    def _send(self) -> None:
        """回车一键发送。"""
        try:
            self.inputs.press_enter()
            time.sleep(self.config.action_delay)
        except Exception as exc:  # noqa: BLE001
            raise SendMessageError(f"发送消息失败：{exc}") from exc


def _split_text(text: str, max_chars: int) -> List[str]:
    """把文本按 ``max_chars`` 分段，尽量在换行处断开。"""
    if max_chars <= 0:
        return [text]
    if len(text) <= max_chars:
        return [text]

    segments: List[str] = []
    remaining = text
    while len(remaining) > max_chars:
        window = remaining[:max_chars]
        cut = window.rfind("\n")
        if cut <= 0:
            cut = max_chars
        segments.append(remaining[:cut])
        remaining = remaining[cut:].lstrip("\n")
    if remaining:
        segments.append(remaining)
    return segments
