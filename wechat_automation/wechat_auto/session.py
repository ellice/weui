# -*- coding: utf-8 -*-
"""会话列表管理 Mixin。

包含：读取左侧会话名称、遍历点击切换会话、读取当前聊天历史文本、
下拉滚动加载更多、私聊 / 群聊区分。
"""

from __future__ import annotations

import time
from typing import List, Optional

from . import inputs


class SessionMixin:
    """会话列表与聊天记录读取能力。"""

    # ----------------------------- 会话列表 ----------------------------- #
    def _find_session_list(self):
        """定位左侧会话列表控件（List 类型，包含若干 ListItem）。"""
        # 微信会话列表通常 name 为 "会话"，control_type='List'
        for crit in (
            {"title": "会话", "control_type": "List"},
            {"control_type": "List", "found_index": 0},
        ):
            try:
                ctrl = self.find(**crit)  # type: ignore[attr-defined]
                if ctrl.exists():
                    return ctrl
            except Exception:  # noqa: BLE001
                continue
        return None

    def get_session_list(self) -> List[str]:
        """读取当前左侧可见的全部会话名称。"""
        lst = self._find_session_list()
        if lst is None:
            return []
        names: List[str] = []
        try:
            for item in lst.children(control_type="ListItem"):
                name = item.window_text()
                if name:
                    names.append(name)
        except Exception:  # noqa: BLE001
            pass
        return names

    def switch_session(self, name: str) -> bool:
        """在会话列表中点击切换到指定会话（仅匹配当前可见项）。

        :returns: 是否成功点击。
        """
        lst = self._find_session_list()
        if lst is None:
            return False
        try:
            for item in lst.children(control_type="ListItem"):
                if item.window_text() == name:
                    item.click_input()
                    time.sleep(0.4)
                    return True
        except Exception:  # noqa: BLE001
            pass
        return False

    def iter_sessions(self):
        """逐个切换并产出会话名称的生成器（仅当前可见项）。"""
        for name in self.get_session_list():
            if self.switch_session(name):
                yield name

    def scroll_session_list(self, times: int = 3, down: bool = True,
                            pause: float = 0.5) -> None:
        """下拉 / 上滑会话列表以加载更多历史会话。"""
        lst = self._find_session_list()
        if lst is None:
            return
        cx, cy = self.rect_center(lst)  # type: ignore[attr-defined]
        wheel = -3 if down else 3
        for _ in range(max(1, times)):
            inputs.scroll((cx, cy), wheel_dist=wheel)
            time.sleep(pause)

    def load_all_sessions(self, max_scroll: int = 20) -> List[str]:
        """持续下滑会话列表，聚合去重所有加载到的会话名称。"""
        seen: List[str] = []
        seen_set = set()
        last_count = -1
        for _ in range(max_scroll):
            for n in self.get_session_list():
                if n not in seen_set:
                    seen_set.add(n)
                    seen.append(n)
            if len(seen) == last_count:
                break  # 没有新增，认为已到底
            last_count = len(seen)
            self.scroll_session_list(times=1, down=True)
        return seen

    # ----------------------------- 聊天记录读取 ----------------------------- #
    def _find_message_list(self):
        """定位当前会话的消息记录区域（List 类型）。"""
        lists = self.find_all(control_type="List")  # type: ignore[attr-defined]
        if not lists:
            return None
        # 消息区域一般是面积最大的 List（排除左侧会话列表）
        session = self._find_session_list()

        def area(c):
            try:
                r = c.rectangle()
                return r.width() * r.height()
            except Exception:  # noqa: BLE001
                return 0

        candidates = [c for c in lists if session is None or c != session]
        if not candidates:
            candidates = lists
        return max(candidates, key=area)

    def get_chat_messages(self) -> List[str]:
        """读取当前聊天窗口历史消息区域的文本列表。"""
        msg_list = self._find_message_list()
        if msg_list is None:
            return []
        out: List[str] = []
        try:
            for item in msg_list.children(control_type="ListItem"):
                text = item.window_text()
                if text:
                    out.append(text)
        except Exception:  # noqa: BLE001
            pass
        return out

    def scroll_chat(self, times: int = 3, up: bool = True,
                    pause: float = 0.5) -> None:
        """上翻 / 下翻聊天记录（鼠标滚轮）。"""
        msg_list = self._find_message_list()
        if msg_list is None:
            return
        cx, cy = self.rect_center(msg_list)  # type: ignore[attr-defined]
        wheel = 3 if up else -3
        for _ in range(max(1, times)):
            inputs.scroll((cx, cy), wheel_dist=wheel)
            time.sleep(pause)

    def load_history_messages(self, scroll_times: int = 5,
                              pause: float = 0.6) -> List[str]:
        """向上滚动加载更多历史消息并聚合去重文本。"""
        seen: List[str] = []
        seen_set = set()
        for _ in range(max(1, scroll_times)):
            for m in self.get_chat_messages():
                if m not in seen_set:
                    seen_set.add(m)
                    seen.append(m)
            self.scroll_chat(times=1, up=True, pause=pause)
        # 收尾再读一次顶部内容
        for m in self.get_chat_messages():
            if m not in seen_set:
                seen_set.add(m)
                seen.append(m)
        return seen

    # ----------------------------- 私聊 / 群聊区分 ----------------------------- #
    def is_group_chat(self) -> Optional[bool]:
        """粗略判断当前会话是否为群聊。

        判据：群聊标题通常带成员数后缀（如 "项目群 (35)"），且存在群相关按钮。
        无法判断时返回 None。
        """
        try:
            title = self.current_chat_title()
            if title and title.rstrip().endswith(")") and "(" in title:
                # 形如 "名称 (N)"，括号内是数字则极可能是群聊
                inner = title.rsplit("(", 1)[-1].rstrip(")")
                if inner.strip().isdigit():
                    return True
            # 存在"聊天信息"中的群管理控件也可佐证，这里保持保守
            return False
        except Exception:  # noqa: BLE001
            return None

    def current_chat_title(self) -> str:
        """读取当前聊天窗口标题（对方昵称 / 群名）。"""
        for crit in (
            {"control_type": "Text", "found_index": 0},
        ):
            try:
                return self.get_text(**crit)  # type: ignore[attr-defined]
            except Exception:  # noqa: BLE001
                continue
        return ""
