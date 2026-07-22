"""会话列表管理。

* 读取左侧全部会话名称
* 遍历会话并点击切换任意聊天窗口
* 获取当前聊天窗口历史消息区域文本
* 下拉滚动会话列表加载更多历史会话
* 区分私聊 / 群聊
"""

from __future__ import annotations

import re
import time
from typing import List, Optional

from . import input_utils
from .exceptions import ContactNotFoundError
from .models import SessionItem, SessionType

# 群名常见特征：包含「群」、带成员数括号，如「XX群(23)」
_GROUP_PATTERN = re.compile(r".+\(\d+\)$")


class SessionMixin:
    """会话列表管理混入类。"""

    config: "object"

    # -------------------------------------------------------- 列表定位 ----
    def _session_list(self):
        """定位左侧会话列表控件。"""
        cfg = self.config
        try:
            return self.find_control(
                title=cfg.session_list_name, control_type="List", timeout=cfg.default_timeout
            )
        except Exception:  # noqa: BLE001 - 退化为第一个 List
            lists = self._require_window().descendants(control_type="List")
            if not lists:
                raise
            return lists[0]

    @staticmethod
    def _guess_type(name: str) -> SessionType:
        """根据名称粗略推断会话类型。"""
        if _GROUP_PATTERN.match(name):
            return SessionType.GROUP
        return SessionType.UNKNOWN

    # -------------------------------------------------------- 读取列表 ----
    def list_sessions(self) -> List[SessionItem]:
        """读取当前可见的全部会话条目。

        注意：微信会话列表是虚拟列表，只有可见项才会被渲染，
        如需更多会话请配合 :meth:`scroll_sessions` 分批读取。
        """
        session_list = self._session_list()
        items: List[SessionItem] = []
        for item in session_list.children(control_type="ListItem"):
            try:
                name = item.window_text()
            except Exception:  # noqa: BLE001
                continue
            if not name:
                continue
            items.append(SessionItem(name=name, session_type=self._guess_type(name)))
        return items

    def list_session_names(self) -> List[str]:
        """只返回会话名称列表。"""
        return [it.name for it in self.list_sessions()]

    def scroll_sessions(self, wheel_dist: int = -3, times: int = 1, pause: float = 0.4):
        """在会话列表区域滚动以加载更多历史会话。

        :param wheel_dist: 每次滚动的滚轮距离，负数向下
        :param times: 滚动次数
        """
        session_list = self._session_list()
        rect = session_list.rectangle()
        cx = (rect.left + rect.right) // 2
        cy = (rect.top + rect.bottom) // 2
        for _ in range(times):
            input_utils.scroll(cx, cy, wheel_dist)
            time.sleep(pause)
        return self

    def collect_all_sessions(self, max_scrolls: int = 30) -> List[SessionItem]:
        """滚动会话列表，尽可能收集全部（去重）会话。

        :param max_scrolls: 最大滚动次数，防止死循环
        """
        seen = {}
        stable_rounds = 0
        for _ in range(max_scrolls):
            before = len(seen)
            for it in self.list_sessions():
                seen[it.name] = it
            self.scroll_sessions(wheel_dist=-3, times=1)
            # 连续两轮没有新增则认为已到底
            if len(seen) == before:
                stable_rounds += 1
                if stable_rounds >= 2:
                    break
            else:
                stable_rounds = 0
        return list(seen.values())

    # ---------------------------------------------------- 切换与遍历 ----
    def switch_to_session(self, name: str, timeout: Optional[float] = None):
        """点击会话列表中指定名称的会话，切换到该聊天窗口。

        若当前可见列表中不存在，会向下滚动查找。

        :raises ContactNotFoundError: 滚动到底仍未找到
        """
        cfg = self.config
        timeout = cfg.default_timeout if timeout is None else timeout
        deadline = time.time() + timeout
        while time.time() < deadline:
            session_list = self._session_list()
            for item in session_list.children(control_type="ListItem"):
                try:
                    if item.window_text() == name:
                        item.click_input()
                        return self
                except Exception:  # noqa: BLE001
                    continue
            self.scroll_sessions(wheel_dist=-3, times=1)
        raise ContactNotFoundError(f"会话列表中未找到: {name}")

    def iter_sessions(self, max_scrolls: int = 30):
        """生成器：依次切换到每个会话并 yield 其名称。

        适合遍历所有会话做批量读取 / 处理。
        """
        for item in self.collect_all_sessions(max_scrolls=max_scrolls):
            try:
                self.switch_to_session(item.name)
            except ContactNotFoundError:
                continue
            yield item.name

    # ------------------------------------------------ 历史消息读取 ----
    def _message_list(self):
        cfg = self.config
        try:
            return self.find_control(
                title=cfg.message_list_name, control_type="List", timeout=cfg.default_timeout
            )
        except Exception:  # noqa: BLE001
            lists = self._require_window().descendants(control_type="List")
            # 消息列表通常是靠右侧、条目更长的那个 List；退化取最后一个
            if not lists:
                raise
            return lists[-1]

    def get_chat_messages(self) -> List[str]:
        """读取当前聊天窗口消息区域内可见的文本消息。

        返回按界面从上到下顺序的文本列表。
        """
        msg_list = self._message_list()
        messages: List[str] = []
        for item in msg_list.children(control_type="ListItem"):
            try:
                text = item.window_text()
            except Exception:  # noqa: BLE001
                continue
            if text:
                messages.append(text)
        return messages

    def scroll_chat_history(self, wheel_dist: int = 3, times: int = 1, pause: float = 0.4):
        """在消息区域滚动，向上查看更早的聊天记录（正数向上）。"""
        msg_list = self._message_list()
        rect = msg_list.rectangle()
        cx = (rect.left + rect.right) // 2
        cy = (rect.top + rect.bottom) // 2
        for _ in range(times):
            input_utils.scroll(cx, cy, wheel_dist)
            time.sleep(pause)
        return self
