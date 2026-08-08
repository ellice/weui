"""模块三：会话列表管理。

- 读取左侧全部会话列表名称；
- 遍历会话、自动点击切换任意聊天窗口；
- 获取当前聊天窗口历史消息区域文本；
- 下拉滚动会话列表加载更多历史会话；
- 区分私聊 / 群聊会话。
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from .controls import ControlHelper
from .input_simulator import InputSimulator


class SessionManager:
    """左侧会话列表与消息区域读取。

    :param main: 主窗口包装对象。
    :param controls: 控件助手。
    :param sim: 键鼠模拟器。
    """

    def __init__(self, main: Any, controls: ControlHelper,
                 sim: InputSimulator) -> None:
        self.main = main
        self.controls = controls
        self.sim = sim

    # ------------------------------------------------------ 会话列表
    def _session_list(self) -> Optional[Any]:
        """定位左侧“会话”列表控件。"""
        for criteria in (
            {"title": "会话", "control_type": "List"},
            {"control_type": "List", "found_index": 0},
        ):
            try:
                ctrl = self.controls.wait_control(timeout=3.0, **criteria)
                return ctrl
            except Exception:  # noqa: BLE001
                continue
        return None

    def list_sessions(self) -> List[str]:
        """读取当前可见的全部会话名称。"""
        lst = self._session_list()
        names: List[str] = []
        if lst is None:
            return names
        try:
            for item in lst.children(control_type="ListItem"):
                text = item.window_text()
                if text:
                    names.append(text)
        except Exception:  # noqa: BLE001
            pass
        return names

    def switch_to(self, name: str, timeout: float = 5.0) -> bool:
        """点击切换到名称为 ``name`` 的会话（左侧列表内直接命中）。

        :return: 是否成功点击到该会话。
        """
        lst = self._session_list()
        if lst is None:
            return False
        try:
            item = lst.child_window(title=name, control_type="ListItem")
            deadline = time.time() + timeout
            while time.time() < deadline:
                if item.exists():
                    item.click_input()
                    time.sleep(0.3)
                    return True
                time.sleep(0.3)
        except Exception:  # noqa: BLE001
            return False
        return False

    def iter_sessions(self):
        """遍历当前可见会话：依次点击并 yield 会话名称。"""
        for name in self.list_sessions():
            if self.switch_to(name):
                yield name

    def scroll_session_list(self, times: int = 3, wheel_dist: int = -3,
                            interval: float = 0.4) -> None:
        """在会话列表区域下拉滚动，加载更多历史会话。"""
        lst = self._session_list()
        if lst is None:
            return
        try:
            rect = lst.rectangle()
            cx = (rect.left + rect.right) // 2
            cy = (rect.top + rect.bottom) // 2
        except Exception:  # noqa: BLE001
            return
        for _ in range(times):
            self.sim.scroll((cx, cy), wheel_dist=wheel_dist)
            time.sleep(interval)

    def load_all_sessions(self, max_scroll: int = 20) -> List[str]:
        """反复下拉直到会话数量不再增长，返回去重后的全部会话名称。"""
        seen: List[str] = []
        seen_set = set()
        stable = 0
        for _ in range(max_scroll):
            for name in self.list_sessions():
                if name not in seen_set:
                    seen_set.add(name)
                    seen.append(name)
            before = len(seen)
            self.scroll_session_list(times=1)
            time.sleep(0.3)
            after_names = self.list_sessions()
            for name in after_names:
                if name not in seen_set:
                    seen_set.add(name)
                    seen.append(name)
            if len(seen) == before:
                stable += 1
                if stable >= 2:
                    break
            else:
                stable = 0
        return seen

    # ------------------------------------------------------ 消息区域
    def _message_list(self) -> Optional[Any]:
        """定位当前聊天窗口的“消息”区域控件。"""
        for criteria in (
            {"title": "消息", "control_type": "List"},
            {"control_type": "List", "found_index": -1},
        ):
            try:
                return self.controls.wait_control(timeout=3.0, **criteria)
            except Exception:  # noqa: BLE001
                continue
        return None

    def get_history_texts(self) -> List[str]:
        """读取当前聊天窗口历史消息区域的可见文本（按消息项）。"""
        msg = self._message_list()
        texts: List[str] = []
        if msg is None:
            return texts
        try:
            for item in msg.children(control_type="ListItem"):
                t = item.window_text()
                if t:
                    texts.append(t)
        except Exception:  # noqa: BLE001
            pass
        return texts

    def scroll_history(self, times: int = 3, wheel_dist: int = 3,
                       interval: float = 0.4) -> None:
        """在消息区域上下翻页（正数向上看更早的历史）。"""
        msg = self._message_list()
        if msg is None:
            return
        try:
            rect = msg.rectangle()
            cx = (rect.left + rect.right) // 2
            cy = (rect.top + rect.bottom) // 2
        except Exception:  # noqa: BLE001
            return
        for _ in range(times):
            self.sim.scroll((cx, cy), wheel_dist=wheel_dist)
            time.sleep(interval)

    # ------------------------------------------------------ 私聊/群聊
    @staticmethod
    def is_group_name(name: str) -> bool:
        """根据会话名启发式判断是否群聊。

        群聊名常带“群”“(N)”成员数量后缀等；这是轻量启发式，精确判断需读控件。
        """
        import re

        if "群" in name:
            return True
        # 形如 "某某某(35)" 的群成员计数后缀
        if re.search(r"[（(]\s*\d+\s*[)）]\s*$", name):
            return True
        return False

    def classify_sessions(self) -> Dict[str, List[str]]:
        """把可见会话粗分为私聊 / 群聊两类。"""
        groups: List[str] = []
        singles: List[str] = []
        for name in self.list_sessions():
            (groups if self.is_group_name(name) else singles).append(name)
        return {"groups": groups, "singles": singles}
