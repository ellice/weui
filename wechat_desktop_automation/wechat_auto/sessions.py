"""会话列表管理。

对应需求「三、会话列表管理」：

* 读取左侧全部会话列表名称
* 遍历会话、自动点击切换任意聊天窗口
* 获取当前聊天窗口历史消息区域文本（UI 读取文字）
* 下拉滚动会话列表加载更多历史会话
* 区分私聊、群聊会话
"""

from __future__ import annotations

import logging
import time
from typing import Dict, List, Optional

from .exceptions import ControlNotFoundError

logger = logging.getLogger("wechat_auto")


class SessionManager:
    """左侧会话列表与聊天记录读取。依赖 :class:`WeChatWindow`。"""

    def __init__(self, win):
        self.win = win

    # ------------------------------------------------------------------ #
    # 会话列表控件定位
    # ------------------------------------------------------------------ #
    def _session_list(self):
        """定位左侧会话列表（List 控件）。"""
        # 微信会话列表通常有名为「会话」的 List，回退到第一个 List
        lst = self.win.window.child_window(title="会话", control_type="List")
        if not lst.exists():
            lst = self.win.window.child_window(control_type="List", found_index=0)
        if not lst.exists():
            raise ControlNotFoundError("未找到左侧会话列表控件。")
        return lst

    # ------------------------------------------------------------------ #
    # 读取会话名称
    # ------------------------------------------------------------------ #
    def list_sessions(self) -> List[str]:
        """读取当前可见的左侧全部会话名称。"""
        lst = self._session_list()
        names: List[str] = []
        for item in lst.children(control_type="ListItem"):
            text = item.window_text()
            if text:
                names.append(text)
        return names

    def get_sessions_detail(self) -> List[Dict]:
        """读取当前可见会话的详细信息（名称 + 是否群聊 + 矩形位置）。"""
        lst = self._session_list()
        details: List[Dict] = []
        for item in lst.children(control_type="ListItem"):
            name = item.window_text()
            if not name:
                continue
            details.append(
                {
                    "name": name,
                    "is_group": self.is_group_name(item),
                    "item": item,
                }
            )
        return details

    # ------------------------------------------------------------------ #
    # 切换会话
    # ------------------------------------------------------------------ #
    def open_session(self, name: str, timeout: float = 6.0) -> bool:
        """点击左侧会话列表中指定名称的会话进入聊天。

        :return: 是否成功找到并点击。
        """
        deadline = time.time() + timeout
        while time.time() < deadline:
            lst = self._session_list()
            for item in lst.children(control_type="ListItem"):
                if item.window_text() == name:
                    item.click_input()
                    time.sleep(0.3)
                    logger.info("已切换到会话「%s」", name)
                    return True
            # 没找到就向下滚动加载更多
            self.scroll_sessions(down=True, amount=1)
            time.sleep(0.2)
        return False

    def iterate_sessions(self, callback, max_count: Optional[int] = None) -> int:
        """遍历当前可见会话，逐个点击进入并回调。

        :param callback: 形如 ``callback(name, session_manager)`` 的可调用对象。
        :param max_count: 最多遍历数量。
        :return: 实际遍历数量。
        """
        names = self.list_sessions()
        if max_count is not None:
            names = names[:max_count]
        count = 0
        for name in names:
            if self.open_session(name):
                callback(name, self)
                count += 1
        return count

    # ------------------------------------------------------------------ #
    # 滚动加载更多
    # ------------------------------------------------------------------ #
    def scroll_sessions(self, down: bool = True, amount: int = 3) -> None:
        """下拉 / 上拉滚动会话列表以加载更多历史会话。"""
        lst = self._session_list()
        rect = lst.rectangle()
        cx = (rect.left + rect.right) // 2
        cy = (rect.top + rect.bottom) // 2
        try:
            lst.set_focus()
        except Exception:  # noqa: BLE001
            pass
        wheel = -amount if down else amount
        try:
            lst.wheel_mouse_input(coords=(cx - rect.left, cy - rect.top), wheel_dist=wheel)
        except Exception:
            # 回退到全局鼠标滚轮
            from pywinauto.mouse import scroll

            scroll(coords=(cx, cy), wheel_dist=wheel)

    def load_all_sessions(self, max_scrolls: int = 30) -> List[str]:
        """反复下拉直到不再有新会话出现，返回累积到的全部会话名称。"""
        seen: List[str] = []
        seen_set = set()
        stable = 0
        for _ in range(max_scrolls):
            for name in self.list_sessions():
                if name not in seen_set:
                    seen_set.add(name)
                    seen.append(name)
            before = len(seen)
            self.scroll_sessions(down=True, amount=3)
            time.sleep(0.4)
            for name in self.list_sessions():
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

    # ------------------------------------------------------------------ #
    # 当前聊天历史消息读取
    # ------------------------------------------------------------------ #
    def _message_list(self):
        """定位当前聊天窗口的消息列表控件。"""
        lst = self.win.window.child_window(title="消息", control_type="List")
        if not lst.exists():
            # 回退：取最大面积的 List 视为消息区
            lists = self.win.window.descendants(control_type="List")
            if not lists:
                raise ControlNotFoundError("未找到聊天消息列表控件。")
            lst = max(lists, key=lambda c: _area(c.rectangle()))
        return lst

    def get_history_texts(self) -> List[str]:
        """读取当前聊天窗口消息区域可见的文本列表（UI 读取）。"""
        lst = self._message_list()
        texts: List[str] = []
        for item in lst.children(control_type="ListItem"):
            text = item.window_text()
            if text:
                texts.append(text)
        return texts

    def get_history_text(self, separator: str = "\n") -> str:
        """把当前聊天可见历史消息合并为单个字符串。"""
        return separator.join(self.get_history_texts())

    def scroll_history(self, up: bool = True, amount: int = 3) -> None:
        """滚动聊天记录（上翻加载更早消息 / 下翻）。"""
        lst = self._message_list()
        rect = lst.rectangle()
        cx = (rect.left + rect.right) // 2
        cy = (rect.top + rect.bottom) // 2
        wheel = amount if up else -amount
        try:
            lst.wheel_mouse_input(coords=(cx - rect.left, cy - rect.top), wheel_dist=wheel)
        except Exception:
            from pywinauto.mouse import scroll

            scroll(coords=(cx, cy), wheel_dist=wheel)

    # ------------------------------------------------------------------ #
    # 私聊 / 群聊区分
    # ------------------------------------------------------------------ #
    @staticmethod
    def is_group_name(item) -> bool:
        """根据会话项文本粗略判断是否群聊。

        微信群聊名称常带有「(人数)」后缀，如「产品讨论群 (58)」；
        也可结合无备注、含逗号等特征。此判断为启发式，可按需增强。
        """
        text = ""
        try:
            text = item.window_text()
        except Exception:  # noqa: BLE001
            return False
        return _looks_like_group(text)

    def classify_current_chat(self) -> str:
        """判断当前打开的聊天是「private」还是「group」。

        依据标题栏是否显示成员数量 / 群聊工具按钮做启发式判断。
        """
        title = self._current_chat_title()
        if title and _looks_like_group(title):
            return "group"
        # 存在「聊天信息」中的成员网格常见于群聊，这里保守返回 private
        return "private"

    def _current_chat_title(self) -> Optional[str]:
        """尝试读取当前聊天标题。"""
        for kwargs in (
            {"control_type": "Text", "found_index": 0},
        ):
            ctrl = self.win.window.child_window(**kwargs)
            if ctrl.exists():
                try:
                    return ctrl.window_text()
                except Exception:  # noqa: BLE001
                    continue
        return None


# --------------------------------------------------------------------------- #
# 内部工具
# --------------------------------------------------------------------------- #
def _area(rect) -> int:
    return max(0, (rect.right - rect.left)) * max(0, (rect.bottom - rect.top))


def _looks_like_group(text: str) -> bool:
    import re

    if not text:
        return False
    # 形如 "群名 (12)" / "群名（12）"
    return bool(re.search(r"[\(（]\s*\d+\s*[\)）]\s*$", text))
