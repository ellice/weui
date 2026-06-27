"""会话列表管理：读取列表、遍历切换、读取历史消息、滚动加载、区分私聊/群聊。"""

from __future__ import annotations

import time
from typing import Dict, List, Optional

from . import controls as C
from . import input_utils as K
from .core import WeChatAuto


class SessionManager:
    """左侧会话列表 + 聊天记录读取能力封装。"""

    def __init__(self, wechat: WeChatAuto):
        self.wx = wechat

    # ------------------------------------------------------------------ #
    # 列表控件定位
    # ------------------------------------------------------------------ #
    def _session_list(self):
        """左侧会话列表控件（List，title 常为 '会话'）。"""
        win = self.wx._ensure_window()
        for title in ("会话", "ConversationList", "聊天"):
            lst = win.child_window(title=title, control_type="List")
            if C.exists(lst):
                return lst
        # 回退取第一个 List
        return win.child_window(control_type="List", found_index=0)

    def _message_list(self):
        """右侧聊天记录列表控件（List，title 常为 '消息'）。"""
        win = self.wx._ensure_window()
        for title in ("消息", "MessageList"):
            lst = win.child_window(title=title, control_type="List")
            if C.exists(lst):
                return lst
        # 回退：会话列表之外的另一个 List
        lists = win.descendants(control_type="List")
        if len(lists) >= 2:
            return lists[-1]
        return win.child_window(control_type="List", found_index=0)

    # ------------------------------------------------------------------ #
    # 读取会话列表
    # ------------------------------------------------------------------ #
    def list_sessions(self) -> List[str]:
        """读取当前可见的全部会话名称。"""
        lst = self._session_list()
        C.wait_visible(lst, timeout=self.wx.default_timeout)
        names: List[str] = []
        for item in lst.children(control_type="ListItem"):
            name = C.get_text(item)
            if name:
                names.append(name)
        return names

    def list_sessions_with_scroll(self, max_scroll: int = 10) -> List[str]:
        """下拉滚动会话列表，加载并收集更多历史会话名称（去重保序）。"""
        seen: Dict[str, None] = {}
        lst = self._session_list()
        C.wait_visible(lst, timeout=self.wx.default_timeout)
        rect = lst.rectangle()
        center = ((rect.left + rect.right) // 2, (rect.top + rect.bottom) // 2)

        for _ in range(max_scroll):
            for item in lst.children(control_type="ListItem"):
                name = C.get_text(item)
                if name and name not in seen:
                    seen[name] = None
            K.scroll(center, wheel_dist=-3)
            time.sleep(0.4)
        return list(seen.keys())

    # ------------------------------------------------------------------ #
    # 切换会话
    # ------------------------------------------------------------------ #
    def open_session(self, name: str, timeout: float = 5.0) -> bool:
        """点击列表中指定名称的会话进行切换。找不到返回 False。"""
        lst = self._session_list()
        C.wait_visible(lst, timeout=timeout)
        try:
            item = lst.child_window(title=name, control_type="ListItem")
            if C.exists(item):
                item.click_input()
                time.sleep(0.4)
                return True
        except Exception:  # noqa: BLE001
            pass
        # 名称不完全匹配时遍历模糊匹配
        for item in lst.children(control_type="ListItem"):
            if name in C.get_text(item):
                item.click_input()
                time.sleep(0.4)
                return True
        return False

    def iterate_sessions(self, names: Optional[List[str]] = None, delay: float = 0.6):
        """生成器：依次切换每个会话，yield 会话名。可用于批量巡检。"""
        names = names or self.list_sessions()
        for name in names:
            if self.open_session(name):
                time.sleep(delay)
                yield name

    # ------------------------------------------------------------------ #
    # 读取聊天记录
    # ------------------------------------------------------------------ #
    def get_chat_messages(self) -> List[str]:
        """读取当前聊天窗口可见的历史消息文本。"""
        lst = self._message_list()
        C.wait_visible(lst, timeout=self.wx.default_timeout)
        messages: List[str] = []
        for item in lst.children(control_type="ListItem"):
            text = C.get_text(item)
            if text:
                messages.append(text)
        return messages

    def load_more_history(self, times: int = 5, wheel_dist: int = 3) -> List[str]:
        """向上滚动聊天记录加载更多历史消息，返回合并去重后的文本列表。"""
        seen: Dict[str, None] = {}
        lst = self._message_list()
        C.wait_visible(lst, timeout=self.wx.default_timeout)
        rect = lst.rectangle()
        center = ((rect.left + rect.right) // 2, (rect.top + rect.bottom) // 2)

        for _ in range(times):
            for item in lst.children(control_type="ListItem"):
                text = C.get_text(item)
                if text and text not in seen:
                    seen[text] = None
            K.scroll(center, wheel_dist=wheel_dist)  # 正数向上看更早消息
            time.sleep(0.5)
        return list(seen.keys())

    # ------------------------------------------------------------------ #
    # 区分私聊 / 群聊
    # ------------------------------------------------------------------ #
    def is_group_chat(self) -> bool:
        """判断当前打开的会话是否为群聊。

        依据：群聊标题通常带成员数后缀，如 "项目群 (128)"，
        且存在「聊天信息」中的群成员管理入口。
        """
        win = self.wx._ensure_window()
        # 群名常带 ( 数字 ) 后缀
        try:
            for title in ("聊天信息", "群聊"):
                if C.is_button_present(win, title, control_type="Button"):
                    return True
        except Exception:  # noqa: BLE001
            pass
        # 退回用标题中的成员数判断
        title = self.current_session_title()
        return "(" in title and ")" in title and any(ch.isdigit() for ch in title)

    def current_session_title(self) -> str:
        """获取当前聊天窗口标题（联系人/群名）。"""
        win = self.wx._ensure_window()
        # 聊天标题通常是顶部的一个文本控件
        for ct in ("Text", "Button"):
            try:
                ctrl = win.child_window(control_type=ct, found_index=0)
                txt = C.get_text(ctrl)
                if txt:
                    return txt
            except Exception:  # noqa: BLE001
                continue
        return ""

    def classify_sessions(self, names: Optional[List[str]] = None) -> Dict[str, str]:
        """遍历会话并标注 'group' / 'private'。"""
        result: Dict[str, str] = {}
        for name in self.iterate_sessions(names):
            result[name] = "group" if self.is_group_chat() else "private"
        return result
