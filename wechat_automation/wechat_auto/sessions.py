"""会话列表管理。

* 读取左侧全部会话名称
* 遍历会话、点击切换任意聊天窗口
* 读取当前聊天窗口历史消息区域文本
* 下拉滚动会话列表加载更多
* 区分私聊 / 群聊
"""

from __future__ import annotations

from typing import List, Optional

from .exceptions import ControlNotFoundError
from .inputs import InputController
from .utils import human_sleep, logger


class SessionManager:
    """会话列表管理器，依附于已连接的 :class:`WeChatAuto`。"""

    def __init__(self, wx, inputs: Optional[InputController] = None) -> None:
        self.wx = wx
        self.inputs = inputs or InputController(default_delay=wx.input_delay)

    # ------------------------------------------------------------------ #
    # 会话列表
    # ------------------------------------------------------------------ #
    def _session_list_control(self):
        """定位左侧会话列表容器（List 控件）。"""
        for criteria in (
            {"title": "会话", "control_type": "List"},
            {"control_type": "List"},
        ):
            try:
                ctrl = self.wx.main_window.child_window(**criteria)
                if ctrl.exists():
                    return ctrl
            except Exception:  # noqa: BLE001
                continue
        raise ControlNotFoundError("未找到左侧会话列表控件")

    def list_sessions(self) -> List[str]:
        """读取当前左侧会话列表中所有可见会话的名称。"""
        names: List[str] = []
        try:
            container = self._session_list_control()
            for item in container.children(control_type="ListItem"):
                name = item.window_text()
                if name:
                    names.append(name)
        except Exception as exc:  # noqa: BLE001
            logger.warning("读取会话列表失败：%s", exc)
        return names

    def open_session(self, name: str) -> bool:
        """在会话列表中点击切换到指定名称的会话。

        :return: 是否成功找到并点击。
        """
        try:
            container = self._session_list_control()
            item = container.child_window(title=name, control_type="ListItem")
            if item.exists():
                item.click_input()
                human_sleep(self.wx.input_delay)
                logger.info("已切换到会话：%s", name)
                return True
        except Exception as exc:  # noqa: BLE001
            logger.warning("切换会话「%s」失败：%s", name, exc)
        return False

    def iterate_sessions(self, callback) -> None:
        """遍历当前可见的每个会话，依次点击并执行 ``callback(name)``。"""
        for name in self.list_sessions():
            if self.open_session(name):
                try:
                    callback(name)
                except Exception as exc:  # noqa: BLE001
                    logger.error("处理会话「%s」时出错：%s", name, exc)

    def scroll_session_list(self, times: int = 1, wheel_dist: int = -3) -> None:
        """在会话列表区域向下滚动以加载更多历史会话。"""
        try:
            container = self._session_list_control()
            rect = container.rectangle()
            cx = (rect.left + rect.right) // 2
            cy = (rect.top + rect.bottom) // 2
            for _ in range(times):
                self.inputs.scroll(cx, cy, wheel_dist=wheel_dist)
                human_sleep(self.wx.input_delay)
        except Exception as exc:  # noqa: BLE001
            logger.warning("滚动会话列表失败：%s", exc)

    def load_all_sessions(self, max_scroll: int = 20) -> List[str]:
        """反复下拉直到会话数量不再增加，返回聚合后的全部会话名称。"""
        seen: List[str] = []
        stable = 0
        for _ in range(max_scroll):
            for name in self.list_sessions():
                if name not in seen:
                    seen.append(name)
            before = len(seen)
            self.scroll_session_list(times=1)
            after_names = self.list_sessions()
            for name in after_names:
                if name not in seen:
                    seen.append(name)
            if len(seen) == before:
                stable += 1
                if stable >= 2:  # 连续两次没有新增，认为已到底
                    break
            else:
                stable = 0
        return seen

    # ------------------------------------------------------------------ #
    # 私聊 / 群聊判断
    # ------------------------------------------------------------------ #
    def is_group_chat(self, name: Optional[str] = None) -> bool:
        """判断当前（或指定）会话是否为群聊。

        依据：群聊标题通常带有成员数量后缀，如“某某群 (35)”；
        且群聊聊天窗口存在“聊天成员”相关控件。
        """
        title = name
        if title is None:
            from .messaging import MessageSender

            title = MessageSender(self.wx, self.inputs).get_current_chat_title()
        if title and title.rstrip().endswith(")") and "(" in title:
            return True
        # 群聊右上角通常有“聊天信息 / 成员”入口
        try:
            if self.wx.main_window.child_window(title="聊天成员").exists():
                return True
        except Exception:  # noqa: BLE001
            pass
        return False

    # ------------------------------------------------------------------ #
    # 历史消息读取
    # ------------------------------------------------------------------ #
    def _message_list_control(self):
        """定位聊天消息区域列表控件。"""
        for criteria in (
            {"title": "消息", "control_type": "List"},
            {"auto_id": "MessageList"},
        ):
            try:
                ctrl = self.wx.main_window.child_window(**criteria)
                if ctrl.exists():
                    return ctrl
            except Exception:  # noqa: BLE001
                continue
        raise ControlNotFoundError("未找到聊天消息区域控件")

    def get_history_messages(self) -> List[str]:
        """读取当前聊天窗口消息区域中可见的历史消息文本。"""
        messages: List[str] = []
        try:
            container = self._message_list_control()
            for item in container.children(control_type="ListItem"):
                text = item.window_text()
                if text:
                    messages.append(text)
        except Exception as exc:  # noqa: BLE001
            logger.warning("读取历史消息失败：%s", exc)
        return messages

    def scroll_history_up(self, times: int = 3, wheel_dist: int = 3) -> None:
        """在消息区域向上滚动，加载更早的聊天记录。"""
        try:
            container = self._message_list_control()
            rect = container.rectangle()
            cx = (rect.left + rect.right) // 2
            cy = (rect.top + rect.bottom) // 2
            for _ in range(times):
                self.inputs.scroll(cx, cy, wheel_dist=wheel_dist)
                human_sleep(self.wx.input_delay)
        except Exception as exc:  # noqa: BLE001
            logger.warning("滚动聊天记录失败：%s", exc)

    def load_history_messages(self, scroll_times: int = 5) -> List[str]:
        """先向上滚动若干次加载更多历史，再聚合去重返回消息文本。"""
        collected: List[str] = []
        for _ in range(scroll_times):
            for msg in self.get_history_messages():
                if msg not in collected:
                    collected.append(msg)
            self.scroll_history_up(times=1)
        for msg in self.get_history_messages():
            if msg not in collected:
                collected.append(msg)
        return collected
