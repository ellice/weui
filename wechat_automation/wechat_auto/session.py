"""会话列表管理：读取左侧会话、遍历切换、读取历史消息、滚动加载、区分群聊。"""

from __future__ import annotations

import logging
import time
from typing import Dict, List, Optional

from . import input_utils
from .core import WeChatCore
from .exceptions import ControlNotFoundError

logger = logging.getLogger("wechat_auto")


class SessionManager:
    """封装左侧会话列表与聊天历史读取相关操作。"""

    def __init__(self, core: WeChatCore) -> None:
        self.core = core

    # ------------------------------------------------------------------
    # 会话列表控件
    # ------------------------------------------------------------------
    def _session_list(self):
        """定位左侧会话列表（List 控件）。"""

        win = self.core.main_window
        for kwargs in (
            {"title": "会话", "control_type": "List"},
            {"control_type": "List"},
        ):
            lists = self.core.find_controls(**kwargs)
            if lists:
                # 会话列表通常在左侧，取最靠左的 List
                try:
                    return min(lists, key=lambda c: c.rectangle().left)
                except Exception:
                    return lists[0]
        raise ControlNotFoundError("未能定位左侧会话列表。")

    def list_sessions(self) -> List[str]:
        """读取当前可见的全部会话名称。"""

        session_list = self._session_list()
        names: List[str] = []
        try:
            items = session_list.children(control_type="ListItem")
        except Exception:
            items = self.core.find_controls(parent=session_list)
        for item in items:
            name = self.core.get_text(item)
            if name:
                names.append(name.strip())
        return names

    def switch_to(self, name: str, timeout: float = 3.0) -> bool:
        """点击切换到名称为 ``name`` 的会话，成功返回 True。"""

        session_list = self._session_list()
        try:
            items = session_list.children(control_type="ListItem")
        except Exception:
            items = self.core.find_controls(parent=session_list)
        for item in items:
            if name in self.core.get_text(item):
                try:
                    item.click_input()
                    time.sleep(0.5)
                    return True
                except Exception as exc:  # noqa: BLE001
                    logger.error("点击会话 %s 失败：%s", name, exc)
                    return False
        logger.warning("当前可见会话中未找到：%s", name)
        return False

    def iterate_sessions(self, callback, max_sessions: Optional[int] = None) -> int:
        """遍历当前可见会话，逐个点击并对每个会话执行 ``callback(name)``。

        返回实际遍历数量。
        """

        names = self.list_sessions()
        if max_sessions is not None:
            names = names[:max_sessions]
        count = 0
        for name in names:
            if self.switch_to(name):
                try:
                    callback(name)
                except Exception as exc:  # noqa: BLE001
                    logger.error("处理会话 %s 时出错：%s", name, exc)
                count += 1
        return count

    def scroll_session_list(self, times: int = 3, direction: str = "down") -> None:
        """下拉 / 上拉滚动会话列表，加载更多历史会话。"""

        session_list = self._session_list()
        rect = session_list.rectangle()
        coords = (rect.mid_point().x, rect.mid_point().y)
        wheel = -3 if direction == "down" else 3
        for _ in range(times):
            input_utils.scroll(coords, wheel_dist=wheel)
            time.sleep(0.4)

    def load_all_sessions(self, max_scroll: int = 20) -> List[str]:
        """持续下拉直到不再有新会话，返回去重后的全部会话名称。"""

        seen: List[str] = []
        seen_set = set()
        for _ in range(max_scroll):
            for name in self.list_sessions():
                if name not in seen_set:
                    seen_set.add(name)
                    seen.append(name)
            before = len(seen)
            self.scroll_session_list(times=1)
            # 若一轮滚动后没有新增，认为已到底
            for name in self.list_sessions():
                if name not in seen_set:
                    seen_set.add(name)
                    seen.append(name)
            if len(seen) == before:
                break
        return seen

    # ------------------------------------------------------------------
    # 聊天历史读取
    # ------------------------------------------------------------------
    def _message_list(self):
        """定位当前聊天窗口的消息记录区域（List 控件）。"""

        lists = self.core.find_controls(control_type="List")
        if not lists:
            raise ControlNotFoundError("未能定位聊天消息区域。")
        # 消息区域通常在右侧、面积较大，取最靠右的 List
        try:
            return max(lists, key=lambda c: c.rectangle().left)
        except Exception:
            return lists[-1]

    def read_current_messages(self) -> List[str]:
        """读取当前聊天窗口可见的历史消息文本。"""

        msg_list = self._message_list()
        texts: List[str] = []
        try:
            items = msg_list.children(control_type="ListItem")
        except Exception:
            items = self.core.find_controls(parent=msg_list)
        for item in items:
            txt = self.core.get_text(item)
            if txt:
                texts.append(txt.strip())
        return texts

    def scroll_chat_history(self, times: int = 3, up: bool = True) -> None:
        """在消息区域滚动，向上翻看更早的聊天记录。"""

        msg_list = self._message_list()
        rect = msg_list.rectangle()
        coords = (rect.mid_point().x, rect.mid_point().y)
        wheel = 3 if up else -3
        for _ in range(times):
            input_utils.scroll(coords, wheel_dist=wheel)
            time.sleep(0.4)

    def load_more_history(self, max_scroll: int = 10) -> List[str]:
        """反复向上滚动读取更多历史消息，返回去重后的消息列表。"""

        seen: List[str] = []
        seen_set = set()
        for _ in range(max_scroll):
            for txt in self.read_current_messages():
                if txt not in seen_set:
                    seen_set.add(txt)
                    seen.append(txt)
            before = len(seen)
            self.scroll_chat_history(times=1, up=True)
            for txt in self.read_current_messages():
                if txt not in seen_set:
                    seen_set.add(txt)
                    seen.append(txt)
            if len(seen) == before:
                break
        # 按滚动方向，越早读取的越靠后，反转使其时间正序
        return list(reversed(seen))

    # ------------------------------------------------------------------
    # 区分私聊 / 群聊
    # ------------------------------------------------------------------
    def is_group_chat(self) -> bool:
        """判断当前会话是否为群聊。

        判断依据：群聊标题通常带成员数后缀（如 ``群名 (23)``），且存在
        "聊天成员"/"群公告" 相关控件。这里以标题括号数字为主，控件为辅。
        """

        from .message import MessageSender

        title = MessageSender(self.core).get_current_chat_title()
        if title and "(" in title and ")" in title:
            suffix = title[title.rfind("(") + 1 : title.rfind(")")]
            if suffix.strip().isdigit():
                return True
        # 辅助：存在群相关按钮
        for name in ("群公告", "聊天成员", "查看更多群成员"):
            if self.core.control_exists(title=name):
                return True
        return False

    def classify_sessions(self) -> Dict[str, str]:
        """遍历可见会话并标注为 ``group`` / ``private``。

        注意：需要逐个切换会话进行判断，会较慢。
        """

        result: Dict[str, str] = {}
        for name in self.list_sessions():
            if self.switch_to(name):
                result[name] = "group" if self.is_group_chat() else "private"
        return result
