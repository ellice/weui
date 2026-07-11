"""会话列表管理。

    - 读取左侧全部会话列表名称
    - 遍历会话、自动点击切换任意聊天窗口
    - 获取当前聊天窗口历史消息区域文本（UI 读取）
    - 下拉滚动会话列表加载更多历史会话
    - 区分私聊、群聊会话

由于微信左侧会话列表是虚拟列表（只渲染可见项），读取全部需要配合滚动。
"""

from __future__ import annotations

import time
from typing import Dict, List, Optional

from . import inputs
from .exceptions import ControlNotFoundError
from .window import WeChatWindow


class SessionManager:
    """左侧会话列表与聊天记录读取。"""

    # 会话列表容器的常见定位（title 因版本而异，做多重兜底）
    SESSION_LIST_TITLES = ("会话", "会话列表", "聊天列表")
    MESSAGE_LIST_TITLES = ("消息", "消息列表")

    def __init__(self, win: WeChatWindow):
        self.win = win

    # ---- 会话列表 ----

    def _get_session_list(self):
        for title in self.SESSION_LIST_TITLES:
            ctrl = self.win.try_find(title=title, control_type="List")
            if ctrl is not None:
                return ctrl
        # 兜底：取第一个 List
        lists = self._descendants(control_type="List")
        if lists:
            return lists[0]
        raise ControlNotFoundError("未找到左侧会话列表")

    def _descendants(self, **criteria) -> List:
        try:
            return self.win.window.descendants(**criteria)
        except Exception:
            return []

    def list_sessions(self) -> List[str]:
        """读取当前可见的会话名称列表。"""
        session_list = self._get_session_list()
        names: List[str] = []
        try:
            for item in session_list.children(control_type="ListItem"):
                name = item.window_text()
                if name:
                    names.append(name)
        except Exception:
            pass
        return names

    def list_all_sessions(self, max_scroll: int = 30, pause: float = 0.4) -> List[str]:
        """滚动加载并读取尽可能全部的会话名称（去重、保序）。

        :param max_scroll: 最大滚动次数
        :param pause: 每次滚动后的等待
        """
        session_list = self._get_session_list()
        seen: Dict[str, None] = {}
        rect = session_list.rectangle()
        center = (rect.mid_point().x, rect.mid_point().y)

        last_count = -1
        for _ in range(max_scroll):
            for name in self.list_sessions():
                if name not in seen:
                    seen[name] = None
            # 向下滚动加载更多
            inputs.scroll(center, wheel_dist=-3)
            time.sleep(pause)
            if len(seen) == last_count:
                # 连续无新增，认为到底
                break
            last_count = len(seen)
        return list(seen.keys())

    def scroll_sessions(self, wheel_dist: int = -3) -> None:
        """下拉 / 上拉滚动会话列表（负数向下加载更多历史会话）。"""
        session_list = self._get_session_list()
        rect = session_list.rectangle()
        center = (rect.mid_point().x, rect.mid_point().y)
        inputs.scroll(center, wheel_dist=wheel_dist)

    def open_session(self, name: str) -> bool:
        """在当前可见会话列表中点击切换到指定会话。

        :return: 是否点击成功（未找到返回 False）
        """
        session_list = self._get_session_list()
        try:
            for item in session_list.children(control_type="ListItem"):
                if item.window_text() == name:
                    item.click_input()
                    return True
        except Exception:
            pass
        return False

    def iterate_sessions(self, callback, max_scroll: int = 30, pause: float = 0.5):
        """遍历所有会话：逐个点击切换并回调。

        :param callback: 形如 ``callback(name)`` 的函数，在每个会话被打开后调用
        :param max_scroll: 会话列表最大滚动次数
        """
        visited = set()
        session_list = self._get_session_list()
        rect = session_list.rectangle()
        center = (rect.mid_point().x, rect.mid_point().y)

        for _ in range(max_scroll):
            new_found = False
            try:
                items = session_list.children(control_type="ListItem")
            except Exception:
                items = []
            for item in items:
                name = item.window_text()
                if not name or name in visited:
                    continue
                visited.add(name)
                new_found = True
                try:
                    item.click_input()
                    time.sleep(0.3)
                    callback(name)
                except Exception:
                    continue
            inputs.scroll(center, wheel_dist=-3)
            time.sleep(pause)
            if not new_found:
                break
        return list(visited)

    # ---- 私聊 / 群聊区分 ----

    def is_group_chat(self) -> bool:
        """判断当前打开的会话是否为群聊。

        依据：群聊标题通常带有成员数后缀（如 "项目组 (25)"），
        且存在「聊天信息 / 群公告」等群聊特有控件。
        """
        # 群聊标题常包含形如 " (25)" 的人数
        title = self.current_chat_title()
        if title and title.rstrip().endswith(")") and "(" in title:
            inside = title[title.rfind("(") + 1 : title.rfind(")")]
            if inside.isdigit():
                return True
        # 存在「查看更多群成员」/ 群相关按钮也可判定
        if self.win.exists(title="聊天成员") or self.win.exists(title="查看更多群成员"):
            return True
        return False

    def current_chat_title(self) -> Optional[str]:
        """获取当前聊天窗口标题（对方昵称 / 群名）。"""
        # 聊天标题一般在顶部，控件类型多为 Text / Button
        for title in ("会话标题", "聊天标题"):
            ctrl = self.win.try_find(title=title)
            if ctrl is not None:
                return ctrl.window_text()
        # 兜底：尝试读取顶部第一个较大的文本控件
        return None

    # ---- 历史消息读取 ----

    def _get_message_list(self):
        for title in self.MESSAGE_LIST_TITLES:
            ctrl = self.win.try_find(title=title, control_type="List")
            if ctrl is not None:
                return ctrl
        lists = self._descendants(control_type="List")
        # 消息列表通常是较靠后的 List
        if len(lists) >= 2:
            return lists[-1]
        if lists:
            return lists[0]
        raise ControlNotFoundError("未找到消息列表")

    def read_messages(self) -> List[str]:
        """读取当前聊天窗口消息区域可见的文本消息。"""
        msg_list = self._get_message_list()
        messages: List[str] = []
        try:
            for item in msg_list.children(control_type="ListItem"):
                text = item.window_text()
                if text:
                    messages.append(text)
        except Exception:
            pass
        return messages

    def scroll_messages_up(self, times: int = 3, pause: float = 0.4) -> None:
        """向上滚动聊天记录，加载更早的历史消息。"""
        msg_list = self._get_message_list()
        rect = msg_list.rectangle()
        center = (rect.mid_point().x, rect.mid_point().y)
        for _ in range(times):
            inputs.scroll(center, wheel_dist=3)
            time.sleep(pause)

    def load_history_messages(self, max_scroll: int = 10, pause: float = 0.5) -> List[str]:
        """向上滚动多次并汇总历史消息文本（去重、保序）。"""
        seen: Dict[str, None] = {}
        msg_list = self._get_message_list()
        rect = msg_list.rectangle()
        center = (rect.mid_point().x, rect.mid_point().y)

        for _ in range(max_scroll):
            for msg in self.read_messages():
                if msg not in seen:
                    seen[msg] = None
            inputs.scroll(center, wheel_dist=3)
            time.sleep(pause)
        # 结果按滚动顺序（新->旧）收集，反转为旧->新
        return list(reversed(list(seen.keys())))
