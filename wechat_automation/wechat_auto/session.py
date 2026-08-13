"""会话列表管理（第三类能力）。

- 读取左侧全部会话名称
- 遍历并点击切换任意会话
- 下拉滚动加载更多历史会话
- 区分私聊 / 群聊
- 读取当前聊天窗口历史消息文本
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import List, Optional

from .config import WeChatConfig, DEFAULT_CONFIG
from .exceptions import ControlNotFoundError
from .window import WindowManager


@dataclass
class SessionItem:
    """一条会话的抽象信息。"""

    name: str
    is_group: bool
    # 对应的 pywinauto 控件（ListItem），用于点击切换
    control: object = None


class SessionManager:
    """会话列表操作。"""

    def __init__(
        self,
        window: WindowManager,
        config: WeChatConfig = DEFAULT_CONFIG,
    ):
        self.window = window
        self.config = config

    # ------------------------------------------------------------------ #
    # 内部：定位会话列表容器
    # ------------------------------------------------------------------ #
    def _session_list_ctrl(self):
        """定位左侧会话列表 List 控件。"""
        return self.window.wait_control(
            title=self.config.controls.session_list,
            control_type="List",
        )

    def _is_group(self, name: str) -> bool:
        """根据名称粗略判断是否群聊（含人数后缀特征）。

        更精确的判断可在切入会话后读取顶栏是否有“群公告/成员”等控件，
        这里提供轻量启发式，避免频繁切换会话。
        """
        for suffix in self.config.group_name_suffixes:
            if suffix in name:
                return True
        return False

    # ------------------------------------------------------------------ #
    # 读取 / 遍历
    # ------------------------------------------------------------------ #
    def list_sessions(self) -> List[SessionItem]:
        """读取当前会话列表中所有可见会话。"""
        lst = self._session_list_ctrl()
        items: List[SessionItem] = []
        for item in lst.children(control_type="ListItem"):
            name = item.window_text()
            if not name:
                continue
            items.append(
                SessionItem(
                    name=name,
                    is_group=self._is_group(name),
                    control=item,
                )
            )
        return items

    def list_session_names(self) -> List[str]:
        """仅返回会话名称列表。"""
        return [s.name for s in self.list_sessions()]

    def scroll_more(self, times: int = 3, wheel_dist: int = -3) -> None:
        """在会话列表上向下滚动，加载更多历史会话。"""
        lst = self._session_list_ctrl()
        rect = lst.rectangle()
        cx = (rect.left + rect.right) // 2
        cy = (rect.top + rect.bottom) // 2
        from . import input_sim

        for _ in range(times):
            input_sim.scroll((cx, cy), wheel_dist=wheel_dist)
            time.sleep(self.config.timing.action_pause)

    def load_all_sessions(self, max_scroll: int = 20) -> List[str]:
        """尽力滚动加载并去重收集所有会话名称。"""
        seen: List[str] = []
        seen_set = set()
        stable_rounds = 0
        for _ in range(max_scroll):
            for name in self.list_session_names():
                if name not in seen_set:
                    seen_set.add(name)
                    seen.append(name)
            before = len(seen)
            self.scroll_more(times=1)
            time.sleep(self.config.timing.action_pause)
            # 连续两轮数量不增长则认为到底
            after = len(seen)
            for name in self.list_session_names():
                if name not in seen_set:
                    seen_set.add(name)
                    seen.append(name)
            if len(seen) == before == after:
                stable_rounds += 1
                if stable_rounds >= 2:
                    break
            else:
                stable_rounds = 0
        return seen

    # ------------------------------------------------------------------ #
    # 切换会话
    # ------------------------------------------------------------------ #
    def switch_to(self, name: str, exact: bool = False) -> bool:
        """在当前可见会话中点击切换到指定会话。

        若在可见列表中未找到，返回 False（可结合搜索或滚动再试）。
        """
        for session in self.list_sessions():
            matched = session.name == name if exact else name in session.name
            if matched:
                session.control.click_input()
                time.sleep(self.config.timing.action_pause)
                return True
        return False

    def iterate_sessions(self, callback, max_scroll: int = 10) -> None:
        """遍历所有会话，逐个切入并回调。

        :param callback: ``callback(session_item)``，在会话切入后调用。
        """
        visited = set()
        for _ in range(max_scroll):
            progressed = False
            for session in self.list_sessions():
                if session.name in visited:
                    continue
                visited.add(session.name)
                session.control.click_input()
                time.sleep(self.config.timing.action_pause)
                callback(session)
                progressed = True
            self.scroll_more(times=1)
            time.sleep(self.config.timing.action_pause)
            if not progressed:
                break

    # ------------------------------------------------------------------ #
    # 历史消息读取
    # ------------------------------------------------------------------ #
    def get_current_messages(self) -> List[str]:
        """读取当前聊天窗口消息区域的全部可见文本。"""
        try:
            area = self.window.wait_control(
                title=self.config.controls.message_area,
                control_type="List",
            )
        except Exception as exc:
            raise ControlNotFoundError("未找到消息列表区域") from exc

        messages: List[str] = []
        for item in area.children(control_type="ListItem"):
            text = item.window_text()
            if text:
                messages.append(text)
        return messages

    def scroll_messages(self, up: bool = True, times: int = 3) -> None:
        """上/下滚动聊天记录以翻页加载历史消息。"""
        area = self.window.wait_control(
            title=self.config.controls.message_area,
            control_type="List",
        )
        rect = area.rectangle()
        cx = (rect.left + rect.right) // 2
        cy = (rect.top + rect.bottom) // 2
        from . import input_sim

        wheel = 3 if up else -3
        for _ in range(times):
            input_sim.scroll((cx, cy), wheel_dist=wheel)
            time.sleep(self.config.timing.action_pause)
