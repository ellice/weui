"""会话列表管理能力（第三类能力）。

- 读取左侧全部会话名称；
- 遍历并点击切换任意聊天窗口；
- 读取当前聊天窗口消息区域文本；
- 下拉滚动会话列表加载更多；
- 区分私聊 / 群聊。
"""

import re
from typing import List, Optional

from ..config import WeChatConfig
from ..core.input_device import InputDevice
from ..core.window import WindowController
from ..exceptions import ControlNotFoundError
from ..utils.humanize import human_sleep


class SessionManager:
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
    # 会话列表控件
    # ------------------------------------------------------------------
    def _session_list(self):
        """定位左侧会话列表（List 控件）。"""
        if self.window.exists(
            title=self.config.session_list_title, control_type="List"
        ):
            return self.window.find(
                title=self.config.session_list_title, control_type="List"
            )
        lists = self.window.main.descendants(control_type="List")
        if not lists:
            raise ControlNotFoundError("未找到会话列表控件。")
        # 会话列表通常是最左侧、条目较多的那个 List。
        return max(lists, key=lambda lst: len(lst.children()))

    def list_sessions(self) -> List[str]:
        """读取当前已加载的全部会话名称。"""
        session_list = self._session_list()
        names: List[str] = []
        for item in session_list.children(control_type="ListItem"):
            name = item.window_text()
            if name:
                names.append(name)
        return names

    def open_session(self, name: str) -> bool:
        """在会话列表中点击切换到指定名称的会话，成功返回 ``True``。"""
        session_list = self._session_list()
        for item in session_list.children(control_type="ListItem"):
            if item.window_text() == name:
                item.click_input()
                human_sleep(self.config.action_pause)
                return True
        return False

    def iter_open_sessions(self):
        """依次切换到当前列表中的每个会话，生成 ``(名称, 列表项控件)``。"""
        session_list = self._session_list()
        for item in session_list.children(control_type="ListItem"):
            name = item.window_text()
            if not name:
                continue
            item.click_input()
            human_sleep(self.config.action_pause)
            yield name, item

    def scroll_sessions(self, times: int = 3, direction: str = "down") -> List[str]:
        """下拉（或上滚）会话列表加载更多，返回滚动后汇总的会话名称。"""
        session_list = self._session_list()
        seen: List[str] = []
        for _ in range(times):
            self.device.scroll(session_list, direction=direction, amount=3)
            human_sleep(self.config.action_pause)
            for name in self.list_sessions():
                if name not in seen:
                    seen.append(name)
        return seen

    # ------------------------------------------------------------------
    # 当前聊天窗口消息文本
    # ------------------------------------------------------------------
    def read_messages(self) -> List[str]:
        """读取当前聊天窗口消息区域内的文本（按 UI 顺序）。"""
        msg_list = self._message_list()
        messages: List[str] = []
        for item in msg_list.descendants(control_type="ListItem"):
            text = item.window_text()
            if text:
                messages.append(text)
        if not messages:
            # 部分版本消息以文本控件呈现，退而求其次收集可见文本。
            for item in msg_list.descendants():
                text = item.window_text()
                if text:
                    messages.append(text)
        return messages

    def _message_list(self):
        if self.window.exists(
            title=self.config.message_list_title, control_type="List"
        ):
            return self.window.find(
                title=self.config.message_list_title, control_type="List"
            )
        lists = self.window.main.descendants(control_type="List")
        if not lists:
            raise ControlNotFoundError("未找到消息展示区域。")
        return max(lists, key=lambda lst: len(lst.children()))

    def scroll_history(self, times: int = 3, direction: str = "up") -> None:
        """上翻 / 下翻当前聊天窗口的历史消息。"""
        msg_list = self._message_list()
        for _ in range(times):
            self.device.scroll(msg_list, direction=direction, amount=3)
            human_sleep(self.config.action_pause)

    # ------------------------------------------------------------------
    # 私聊 / 群聊判断
    # ------------------------------------------------------------------
    def is_group_chat(self, name: Optional[str] = None) -> bool:
        """判断会话是否为群聊。

        依据：群聊标题通常带「(N)」人数后缀；可传入标题文本或读取当前窗口标题。
        """
        title = name if name is not None else self._current_chat_title()
        if not title:
            return False
        return bool(re.search(r"[\(（]\s*\d+\s*[\)）]\s*$", title))

    def _current_chat_title(self) -> str:
        """读取当前聊天窗口顶部的标题文本。"""
        try:
            for ctrl in self.window.main.descendants(control_type="Text"):
                text = ctrl.window_text()
                if text and re.search(r"[\(（]\s*\d+\s*[\)）]", text):
                    return text
        except Exception:
            pass
        return ""
