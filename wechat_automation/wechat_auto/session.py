"""会话列表管理（需求类别三）。

能力：
- 读取左侧全部会话列表名称
- 遍历会话、点击切换任意聊天窗口
- 获取当前聊天窗口历史消息区域文本（UI 读取）
- 下拉滚动会话列表加载更多历史会话
- 区分私聊 / 群聊
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional

from .base import WeChatBase
from .exceptions import ControlNotFoundError
from .input_sim import InputSimulator
from .utils import human_sleep, logger


class SessionManager:
    def __init__(self, base: WeChatBase, inp: InputSimulator) -> None:
        self.base = base
        self.inp = inp

    # ---------------- 会话列表控件 ----------------
    def _session_list(self):
        """左侧会话列表 List 控件（名称通常为「会话」）。"""
        ctrl = self.base.find_optional(title="会话", control_type="List", timeout=3.0)
        if ctrl is None:
            # 兜底：取最左侧的 List
            lists = self.base.window.descendants(control_type="List")
            if not lists:
                raise ControlNotFoundError("未找到会话列表控件。")
            ctrl = sorted(lists, key=lambda c: c.rectangle().left)[0]
        return ctrl

    def list_sessions(self) -> List[str]:
        """读取当前可见的全部会话名称。"""
        names: List[str] = []
        try:
            session_list = self._session_list()
            for item in session_list.children(control_type="ListItem"):
                name = item.window_text()
                if name:
                    names.append(name)
        except Exception as exc:  # noqa: BLE001
            logger.warning("读取会话列表失败: %s", exc)
        return names

    def open_session(self, name: str) -> bool:
        """点击切换到指定会话（仅在当前可见列表中查找）。"""
        try:
            session_list = self._session_list()
            for item in session_list.children(control_type="ListItem"):
                if item.window_text() == name:
                    item.click_input()
                    human_sleep(0.4, 0.2)
                    logger.info("已切换到会话: %s", name)
                    return True
        except Exception as exc:  # noqa: BLE001
            logger.warning("切换会话失败: %s", exc)
        return False

    def iterate_sessions(self):
        """生成器：遍历当前可见会话，逐个切入并 yield 会话名。"""
        for name in self.list_sessions():
            if self.open_session(name):
                yield name

    def scroll_sessions(self, steps: int = 3, down: bool = True) -> None:
        """下拉/上滚会话列表以加载更多历史会话。"""
        session_list = self._session_list()
        rect = session_list.rectangle()
        coords = (rect.mid_point().x, rect.mid_point().y)
        if down:
            self.inp.scroll_down(coords, steps)
        else:
            self.inp.scroll_up(coords, steps)
        human_sleep(0.5, 0.3)

    def load_all_sessions(self, max_scrolls: int = 20) -> List[str]:
        """持续下拉直到无新增会话，返回去重后的全部会话名。"""
        seen: List[str] = []
        seen_set = set()
        stagnant = 0
        for _ in range(max_scrolls):
            for name in self.list_sessions():
                if name not in seen_set:
                    seen_set.add(name)
                    seen.append(name)
            before = len(seen)
            self.scroll_sessions(steps=3, down=True)
            after = len(seen)
            # 滚动后再读一次
            for name in self.list_sessions():
                if name not in seen_set:
                    seen_set.add(name)
                    seen.append(name)
            if len(seen) == before == after:
                stagnant += 1
                if stagnant >= 2:
                    break
            else:
                stagnant = 0
        return seen

    # ---------------- 历史消息读取 ----------------
    def _message_list(self):
        """聊天记录区 List 控件（名称通常为「消息」）。"""
        ctrl = self.base.find_optional(title="消息", control_type="List", timeout=3.0)
        if ctrl is None:
            lists = self.base.window.descendants(control_type="List")
            # 排除最左侧会话列表，取偏右的那个
            if len(lists) >= 2:
                ctrl = sorted(lists, key=lambda c: c.rectangle().left)[-1]
            elif lists:
                ctrl = lists[0]
            else:
                raise ControlNotFoundError("未找到聊天消息区控件。")
        return ctrl

    def get_history_messages(self, limit: Optional[int] = None) -> List[str]:
        """读取当前聊天窗口可见的历史消息文本。"""
        messages: List[str] = []
        try:
            msg_list = self._message_list()
            for item in msg_list.children(control_type="ListItem"):
                text = item.window_text()
                if text:
                    messages.append(text)
        except Exception as exc:  # noqa: BLE001
            logger.warning("读取历史消息失败: %s", exc)
        if limit is not None:
            return messages[-limit:]
        return messages

    def scroll_history(self, steps: int = 3, up: bool = True) -> None:
        """上滚/下滚聊天记录，翻页加载更早消息。"""
        msg_list = self._message_list()
        rect = msg_list.rectangle()
        coords = (rect.mid_point().x, rect.mid_point().y)
        if up:
            self.inp.scroll_up(coords, steps)
        else:
            self.inp.scroll_down(coords, steps)
        human_sleep(0.5, 0.3)

    # ---------------- 私聊 / 群聊区分 ----------------
    def is_group_chat(self) -> bool:
        """判断当前聊天是否为群聊。

        依据：群聊标题通常带成员数后缀，如「项目讨论组 (38)」；
        且群聊一般存在「聊天信息」中的成员列表。这里用标题正则做轻量判断。
        """
        title = self.current_chat_title()
        return bool(re.search(r"[\(（]\s*\d+\s*[\)）]\s*$", title or ""))

    def current_chat_title(self) -> str:
        """获取当前聊天对象名称（聊天区顶部标题）。"""
        # 顶部标题区通常是聊天对象名；取消息区上方的 Text/Button
        candidates = self.base.window.descendants(control_type="Text")
        for c in candidates:
            try:
                rect = c.rectangle()
                # 顶部区域（y 较小）且文本非空
                if rect.top < self.base.window.rectangle().top + 120:
                    t = c.window_text()
                    if t and t not in ("微信", "搜索"):
                        return t
            except Exception:  # noqa: BLE001
                continue
        return ""

    def classify_sessions(self) -> Dict[str, List[str]]:
        """遍历当前会话并粗分类为私聊/群聊。

        注意：需要逐个切入会话判断，开销较大；仅对当前可见会话操作。
        """
        result: Dict[str, List[str]] = {"group": [], "private": []}
        for name in self.list_sessions():
            if not self.open_session(name):
                continue
            human_sleep(0.3, 0.2)
            if self.is_group_chat():
                result["group"].append(name)
            else:
                result["private"].append(name)
        return result
