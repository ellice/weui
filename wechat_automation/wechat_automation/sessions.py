"""会话列表管理。

提供：
- 读取左侧全部会话名称；
- 遍历会话并点击切换；
- 读取当前聊天窗口历史消息文本；
- 下拉滚动会话列表加载更多；
- 区分私聊 / 群聊。
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from .controls import ControlHelper
from .input_simulator import InputSimulator


class SessionManager:
    """左侧会话列表与聊天记录读取。"""

    def __init__(self, window: Any, controls: ControlHelper,
                 simulator: InputSimulator) -> None:
        self.window = window
        self.controls = controls
        self.sim = simulator

    # ----- 会话列表 -----
    def _session_list(self) -> Optional[Any]:
        """获取左侧会话列表容器（List 控件）。"""
        for criteria in (
            dict(title="会话", control_type="List"),
            dict(control_type="List", found_index=0),
        ):
            ctrl = self.controls.find_optional(**criteria)
            if ctrl is not None:
                return ctrl
        return None

    def list_sessions(self) -> List[str]:
        """读取当前可见的全部会话名称。"""
        lst = self._session_list()
        if lst is None:
            return []
        names: List[str] = []
        try:
            for item in lst.children(control_type="ListItem"):
                name = self.controls.get_text(item)
                if name:
                    names.append(name)
        except Exception:  # noqa: BLE001  # pragma: no cover
            pass
        return names

    def open_session(self, name: str, timeout: float = 5.0) -> bool:
        """在可见会话中点击切换到指定会话。

        :return: 是否成功点击到。找不到返回 False（可先滚动加载更多）。
        """
        lst = self._session_list()
        if lst is None:
            return False
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                for item in lst.children(control_type="ListItem"):
                    if self.controls.get_text(item) == name:
                        self.controls.click_control(item)
                        time.sleep(0.4)
                        return True
            except Exception:  # noqa: BLE001
                pass
            time.sleep(0.3)
        return False

    def iter_sessions(self):
        """生成器：逐个切换会话并产出 (名称, ListItem 控件)。"""
        lst = self._session_list()
        if lst is None:
            return
        for item in lst.children(control_type="ListItem"):
            name = self.controls.get_text(item)
            if not name:
                continue
            self.controls.click_control(item)
            time.sleep(0.4)
            yield name, item

    def scroll_sessions(self, steps: int = 3, down: bool = True) -> None:
        """下拉（或上拉）滚动会话列表加载更多历史会话。"""
        lst = self._session_list()
        if lst is None:
            return
        rect = lst.rectangle()
        coords = (rect.mid_point().x, rect.mid_point().y)
        if down:
            self.sim.scroll_down(coords, steps)
        else:
            self.sim.scroll_up(coords, steps)
        time.sleep(0.4)

    def load_all_sessions(self, max_scrolls: int = 20) -> List[str]:
        """反复下拉直到没有新会话，返回去重后的全部会话名称。"""
        seen: List[str] = []
        seen_set = set()
        stable = 0
        for _ in range(max_scrolls):
            for name in self.list_sessions():
                if name not in seen_set:
                    seen_set.add(name)
                    seen.append(name)
            before = len(seen)
            self.scroll_sessions(steps=3, down=True)
            after = len(self.list_sessions())
            # 连续两次无新增则认为到底。
            if len(seen) == before and after <= before:
                stable += 1
                if stable >= 2:
                    break
            else:
                stable = 0
        return seen

    # ----- 私聊 / 群聊判断 -----
    def is_group_chat(self) -> bool:
        """根据标题是否含成员数量（如「群名 (12)」）粗略判断当前会话是否群聊。"""
        title = self.current_chat_title()
        return "(" in title and ")" in title

    def current_chat_title(self) -> str:
        """读取当前聊天窗口标题（对方昵称 / 群名）。"""
        for criteria in (
            dict(control_type="Text", found_index=0),
            dict(control_type="Button", found_index=0),
        ):
            ctrl = self.controls.find_optional(**criteria)
            if ctrl is not None:
                txt = self.controls.get_text(ctrl)
                if txt:
                    return txt
        return ""

    def classify_session(self, name: str) -> str:
        """打开会话后返回 'group' 或 'private'。"""
        self.open_session(name)
        return "group" if self.is_group_chat() else "private"

    # ----- 历史消息读取 -----
    def _message_list(self) -> Optional[Any]:
        """获取聊天记录区域（消息 List 控件）。"""
        for criteria in (
            dict(title="消息", control_type="List"),
            dict(control_type="List", found_index=1),
        ):
            ctrl = self.controls.find_optional(**criteria)
            if ctrl is not None:
                return ctrl
        return None

    def read_messages(self) -> List[str]:
        """读取当前聊天窗口可见的历史消息文本。"""
        msg_list = self._message_list()
        if msg_list is None:
            return []
        messages: List[str] = []
        try:
            for item in msg_list.children(control_type="ListItem"):
                txt = self.controls.get_text(item)
                if txt:
                    messages.append(txt)
        except Exception:  # noqa: BLE001  # pragma: no cover
            pass
        return messages

    def scroll_chat(self, steps: int = 3, up: bool = True) -> None:
        """上翻（看更早）或下翻聊天记录。"""
        msg_list = self._message_list()
        if msg_list is None:
            return
        rect = msg_list.rectangle()
        coords = (rect.mid_point().x, rect.mid_point().y)
        if up:
            self.sim.scroll_up(coords, steps)
        else:
            self.sim.scroll_down(coords, steps)
        time.sleep(0.4)

    def read_history(self, max_scrolls: int = 10) -> List[str]:
        """上翻加载并聚合更多历史消息（去重保序）。"""
        collected: List[str] = []
        seen = set()
        for _ in range(max_scrolls):
            for msg in self.read_messages():
                if msg not in seen:
                    seen.add(msg)
                    collected.append(msg)
            self.scroll_chat(steps=3, up=True)
        # 上翻得到的是更早的消息，反转为时间正序近似。
        return list(reversed(collected))

    def snapshot(self) -> Dict[str, Any]:
        """返回当前会话的概要信息，便于调试。"""
        return {
            "title": self.current_chat_title(),
            "is_group": self.is_group_chat(),
            "messages": self.read_messages(),
        }
