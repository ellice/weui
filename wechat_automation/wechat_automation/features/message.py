"""基础消息发送能力（第一类能力）。

- 根据备注 / 昵称搜索好友、群聊并切入聊天窗口；
- 发送纯文本（换行、特殊符号、空格兼容）；
- 回车一键发送，支持分段长文本；
- 循环批量群发；
- 快捷键（@、表情、换行、Tab、ESC）；
- 剪贴板粘贴大段文字 / 链接后发送。
"""

import time
from typing import Dict, Iterable, List, Optional

from ..config import WeChatConfig
from ..core.input_device import InputDevice
from ..core.window import WindowController
from ..exceptions import ContactNotFoundError
from ..utils.clipboard import set_clipboard_text
from ..utils.humanize import human_sleep


class MessageSender:
    def __init__(
        self,
        window: WindowController,
        device: InputDevice,
        config: Optional[WeChatConfig] = None,
    ):
        self.window = window
        self.device = device
        self.config = config or window.config

    # ------------------------------------------------------------------
    # 搜索并切入聊天窗口
    # ------------------------------------------------------------------
    def open_chat(self, keyword: str) -> None:
        """根据备注 / 昵称 / 群名搜索并切入对应聊天窗口。

        流程：聚焦搜索框 → 清空 → 输入关键字 → 等待联想 → 回车进入首个结果。
        """
        self.window.activate()
        search = self.window.find(
            title=self.config.search_box_title, control_type="Edit"
        )
        search.click_input()
        self.clear_edit(search)
        set_clipboard_text(keyword)
        self.device.send_keys("^v")
        human_sleep(self.config.action_pause * 2)
        # 回车选中搜索结果中高亮的首个联系人。
        self.device.send_keys("{ENTER}")
        human_sleep(self.config.action_pause * 2)

        if not self._chat_ready():
            raise ContactNotFoundError(f"未能切入与「{keyword}」的聊天窗口。")

    def _chat_ready(self) -> bool:
        """通过消息输入框是否存在，判断是否已进入某个聊天窗口。"""
        return self.window.exists(
            title=self.config.input_edit_title, control_type="Edit"
        ) or self.window.exists(control_type="Edit")

    # ------------------------------------------------------------------
    # 文本发送
    # ------------------------------------------------------------------
    def _input_edit(self):
        """定位消息输入框（优先按 title，回退到最后一个 Edit）。"""
        if self.window.exists(
            title=self.config.input_edit_title, control_type="Edit"
        ):
            return self.window.find(
                title=self.config.input_edit_title, control_type="Edit"
            )
        edits = self.window.main.descendants(control_type="Edit")
        if not edits:
            raise ContactNotFoundError("未找到消息输入框，请确认已进入聊天窗口。")
        return edits[-1]

    def send_text(
        self,
        text: str,
        via_clipboard: bool = True,
        humanize: bool = True,
    ) -> None:
        """向当前聊天窗口发送一段文本并回车发送。

        - ``via_clipboard=True``：整段粘贴，适合大段文字、链接、含特殊符号内容，
          速度快且不丢字符；
        - ``via_clipboard=False``：逐字模拟输入，更拟人（配合 ``humanize``）。
        """
        edit = self._input_edit()
        edit.click_input()
        self.clear_edit(edit)

        if via_clipboard:
            set_clipboard_text(text)
            self.device.send_keys("^v")
        else:
            self.device.type_text(text, humanize=humanize)

        human_sleep(self.config.action_pause)
        self.device.send_keys("{ENTER}")
        human_sleep(self.config.action_pause)

    def send_multiline(self, lines: Iterable[str], via_clipboard: bool = True) -> None:
        """在同一条消息内发送多行（行间以 Shift+Enter 换行），最后一次性发送。"""
        text = "\n".join(lines)
        self.send_text(text, via_clipboard=via_clipboard)

    def send_segments(
        self,
        segments: Iterable[str],
        interval: float = 0.8,
        via_clipboard: bool = True,
    ) -> None:
        """将长文本分段，逐条独立发送（每段一条消息），段间停顿。"""
        for seg in segments:
            self.send_text(seg, via_clipboard=via_clipboard)
            human_sleep(interval)

    @staticmethod
    def split_long_text(text: str, max_len: int = 500) -> List[str]:
        """按长度把超长文本切分为多段，尽量在换行处断开。"""
        segments: List[str] = []
        remaining = text
        while len(remaining) > max_len:
            window = remaining[:max_len]
            cut = window.rfind("\n")
            if cut <= 0:
                cut = max_len
            segments.append(remaining[:cut])
            remaining = remaining[cut:].lstrip("\n")
        if remaining:
            segments.append(remaining)
        return segments

    # ------------------------------------------------------------------
    # 批量群发
    # ------------------------------------------------------------------
    def broadcast(
        self,
        contacts: Iterable[str],
        text: str,
        interval: float = 1.5,
        via_clipboard: bool = True,
    ) -> Dict[str, bool]:
        """循环向多个联系人 / 群聊群发同一段文本。

        返回每个目标的发送结果；单个目标失败不会中断整体流程。
        """
        results: Dict[str, bool] = {}
        for name in contacts:
            try:
                self.open_chat(name)
                self.send_text(text, via_clipboard=via_clipboard)
                results[name] = True
            except Exception:  # noqa: BLE001 - 群发容错，记录失败继续
                results[name] = False
            human_sleep(interval)
        return results

    # ------------------------------------------------------------------
    # 快捷键 / 清空
    # ------------------------------------------------------------------
    def mention(self, name: str) -> None:
        """在群聊中 @ 某人：输入 ``@`` 触发列表后，输入名称并回车选中。"""
        edit = self._input_edit()
        edit.click_input()
        self.device.send_keys("@")
        human_sleep(self.config.action_pause)
        self.device.type_text(name)
        human_sleep(self.config.action_pause)
        self.device.send_keys("{ENTER}")

    def clear_edit(self, edit=None) -> None:
        """清空输入框内容（Ctrl+A 全选后删除）。"""
        if edit is None:
            edit = self._input_edit()
        edit.click_input()
        self.device.send_keys("^a")
        self.device.send_keys("{BACKSPACE}")

    def clear_search(self) -> None:
        """清空搜索框内容。"""
        search = self.window.find(
            title=self.config.search_box_title, control_type="Edit"
        )
        search.click_input()
        self.device.send_keys("^a")
        self.device.send_keys("{BACKSPACE}")
        self.device.send_keys("{ESC}")
