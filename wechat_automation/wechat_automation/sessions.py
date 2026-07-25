"""会话列表管理。

提供：

* 读取左侧全部会话列表名称
* 遍历会话并点击切换到任意聊天窗口
* 获取当前聊天窗口历史消息区域文本（UI 读取）
* 下拉滚动会话列表加载更多历史会话
* 区分私聊 / 群聊会话

由于微信左侧会话列表是虚拟化列表（仅渲染可见项），读取「全部」会话
需配合滚动逐屏采集并去重。
"""

from __future__ import annotations

import time
from typing import Dict, List, Optional

from . import input_sim
from .config import WeChatConfig, DEFAULT_CONFIG
from .exceptions import ControlNotFoundError
from .window import WindowManager


class SessionManager:
    """封装左侧会话列表与聊天消息区域的读取 / 切换操作。"""

    def __init__(
        self,
        window: WindowManager,
        config: Optional[WeChatConfig] = None,
    ):
        self.win = window
        self.config = config or window.config or DEFAULT_CONFIG

    # ------------------------------------------------------------------
    # 会话列表控件定位
    # ------------------------------------------------------------------
    def _session_list(self):
        """定位左侧会话列表 List 控件。"""
        cfg = self.config
        try:
            return self.win.find_control(
                title=cfg.session_list_name, control_type="List"
            )
        except Exception:
            # 回退：取第一个 List 控件。
            return self.win.find_control(control_type="List")

    def _list_items(self):
        """返回当前会话列表中可见的 ListItem 控件集合。"""
        lst = self._session_list()
        try:
            return lst.children(control_type="ListItem")
        except Exception:
            return []

    # ------------------------------------------------------------------
    # 读取会话名称
    # ------------------------------------------------------------------
    def get_visible_sessions(self) -> List[str]:
        """读取当前可见的会话名称列表。"""
        names: List[str] = []
        for item in self._list_items():
            try:
                name = item.window_text()
                if name:
                    names.append(name)
            except Exception:
                continue
        return names

    def get_all_sessions(self, max_scroll: int = 30) -> List[str]:
        """滚动会话列表，尽可能读取全部会话名称（自动去重）。

        Args:
            max_scroll: 最大滚动次数上限，防止死循环。

        Returns:
            去重且保持出现顺序的会话名称列表。
        """
        seen: Dict[str, None] = {}
        stable_rounds = 0

        def collect() -> int:
            added = 0
            for name in self.get_visible_sessions():
                if name not in seen:
                    seen[name] = None
                    added += 1
            return added

        collect()
        for _ in range(max_scroll):
            self.scroll_session_list(down=True)
            time.sleep(0.4)
            added = collect()
            # 连续两轮没有新增，认为已到底。
            if added == 0:
                stable_rounds += 1
                if stable_rounds >= 2:
                    break
            else:
                stable_rounds = 0
        return list(seen.keys())

    # ------------------------------------------------------------------
    # 切换会话
    # ------------------------------------------------------------------
    def switch_to(self, name: str, max_scroll: int = 30) -> bool:
        """在会话列表中查找并点击切换到指定会话。

        若当前可见列表中没有该会话，会滚动查找。

        Returns:
            是否成功切换。
        """
        for _ in range(max_scroll):
            for item in self._list_items():
                try:
                    if item.window_text() == name:
                        item.click_input()
                        time.sleep(self.config.action_delay)
                        return True
                except Exception:
                    continue
            self.scroll_session_list(down=True)
            time.sleep(0.4)
        return False

    def iterate_sessions(self, max_scroll: int = 30):
        """遍历会话：依次点击每个会话并 yield 其名称。

        适合「逐个会话读取消息」等批处理场景。
        """
        visited = set()
        stable_rounds = 0
        while True:
            progressed = False
            for item in list(self._list_items()):
                try:
                    name = item.window_text()
                except Exception:
                    continue
                if not name or name in visited:
                    continue
                visited.add(name)
                progressed = True
                try:
                    item.click_input()
                    time.sleep(self.config.action_delay)
                except Exception:
                    pass
                yield name
            if not progressed:
                stable_rounds += 1
                if stable_rounds >= 2:
                    break
            else:
                stable_rounds = 0
            self.scroll_session_list(down=True)
            time.sleep(0.4)
            max_scroll -= 1
            if max_scroll <= 0:
                break

    # ------------------------------------------------------------------
    # 滚动
    # ------------------------------------------------------------------
    def scroll_session_list(self, down: bool = True, step: Optional[int] = None) -> None:
        """在会话列表区域滚动以加载更多会话。"""
        lst = self._session_list()
        try:
            rect = lst.rectangle()
            coords = (rect.mid_point().x, rect.mid_point().y)
        except Exception:
            coords = (150, 400)
        dist = step if step is not None else self.config.scroll_step
        input_sim.scroll(coords, dist if down else abs(dist))

    # ------------------------------------------------------------------
    # 历史消息读取
    # ------------------------------------------------------------------
    def _message_list(self):
        cfg = self.config
        try:
            return self.win.find_control(
                title=cfg.message_list_name, control_type="List"
            )
        except Exception:
            lists = []
            try:
                lists = self.win._require_window().descendants(control_type="List")
            except Exception:
                pass
            if lists:
                # 消息列表通常是较大的那个 List，简单取最后一个。
                return lists[-1]
            raise ControlNotFoundError("未能定位聊天消息区域。")

    def get_current_messages(self) -> List[str]:
        """读取当前聊天窗口消息区域中可见的文本消息。

        返回按界面顺序排列的消息文本列表（图片 / 文件等非文本消息可能
        表现为占位文本或空）。
        """
        msgs: List[str] = []
        try:
            mlist = self._message_list()
            for item in mlist.children(control_type="ListItem"):
                try:
                    txt = item.window_text()
                    if txt:
                        msgs.append(txt)
                except Exception:
                    continue
        except Exception:
            pass
        return msgs

    def scroll_messages(self, up: bool = True, step: Optional[int] = None) -> None:
        """上下滚动聊天记录（up=True 向上翻看历史）。"""
        try:
            mlist = self._message_list()
            rect = mlist.rectangle()
            coords = (rect.mid_point().x, rect.mid_point().y)
        except Exception:
            coords = (600, 400)
        base = step if step is not None else abs(self.config.scroll_step)
        input_sim.scroll(coords, base if up else -base)

    def load_more_history(self, times: int = 3) -> List[str]:
        """向上滚动多次加载更多历史消息并返回聚合的可见文本。"""
        collected: List[str] = []
        seen = set()
        for _ in range(times):
            for m in self.get_current_messages():
                if m not in seen:
                    seen.add(m)
                    collected.append(m)
            self.scroll_messages(up=True)
            time.sleep(0.5)
        return collected

    # ------------------------------------------------------------------
    # 私聊 / 群聊判定
    # ------------------------------------------------------------------
    def is_group_chat(self, name: Optional[str] = None) -> bool:
        """判断当前（或指定名称）会话是否为群聊。

        判据（启发式）：
        1. 名称中带有「群聊」等关键词，或形如 ``名称 (人数)``；
        2. 当前聊天标题栏中出现群成员数量或群公告等群聊特征控件。
        """
        cfg = self.config
        target = name
        if target is None:
            # 尝试读取聊天窗口标题。
            target = self.win.get_control_text(control_type="Text")

        if target:
            for kw in cfg.group_hint_keywords:
                if kw in target:
                    return True

        # 群聊聊天窗口通常存在「聊天信息」中的群成员列表，或标题含人数括号。
        try:
            title = self.win.get_control_text(control_type="Text")
            if title and ("(" in title or "（" in title):
                return True
        except Exception:
            pass
        return False
