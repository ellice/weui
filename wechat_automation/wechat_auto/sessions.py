"""会话列表管理。

对应需求"三、会话列表管理"：

- 读取左侧全部会话列表名称
- 遍历会话、自动点击切换任意聊天窗口
- 获取当前聊天窗口历史消息区域文本（UI 读取文字）
- 下拉滚动会话列表加载更多历史会话
- 区分私聊、群聊会话
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import List, Optional

from .config import WeChatConfig
from .exceptions import ContactNotFoundError, ControlNotFoundError
from .window import WeChatWindow

logger = logging.getLogger("wechat_auto.sessions")

# 群聊名称常见形态："群名 (12)" 结尾带成员数
_GROUP_COUNT_RE = re.compile(r"[(（]\s*\d+\s*[)）]\s*$")


@dataclass
class SessionItem:
    """单个会话条目。"""

    name: str            # 会话显示名（含可能的未读角标文本已剥离）
    is_group: bool       # 是否群聊（启发式判断）
    raw_text: str        # 控件原始文本，便于调试


@dataclass
class ChatMessage:
    """聊天记录中的一条消息文本（UI 读取，非协议层）。"""

    sender: Optional[str]
    text: str


class SessionManager:
    """左侧会话列表与聊天记录读取。"""

    def __init__(self, window: WeChatWindow):
        self.window = window
        self.input = window.input

    @property
    def config(self) -> WeChatConfig:
        return self.window.config

    # ————————————————————— 会话列表控件 —————————————————————
    def _session_list(self):
        """定位左侧会话列表容器（List 控件）。"""
        candidates = [self.config.session_list_title, "会话", "Conversations"]
        for name in candidates:
            try:
                ctrl = self.window.main.child_window(
                    title=name, control_type="List"
                )
                if ctrl.exists(timeout=self.config.short_delay):
                    return ctrl
            except Exception:  # noqa: BLE001
                continue
        # 退化：返回窗口内第一个 List
        try:
            lists = self.window.main.descendants(control_type="List")
            if lists:
                return lists[0]
        except Exception as exc:  # noqa: BLE001
            raise ControlNotFoundError(f"未找到会话列表：{exc}") from exc
        raise ControlNotFoundError("未找到会话列表控件。")

    @staticmethod
    def _guess_is_group(name: str) -> bool:
        """启发式判断是否群聊：名称以 (数字) 结尾通常是群聊。"""
        return bool(_GROUP_COUNT_RE.search(name))

    @staticmethod
    def _clean_name(raw: str) -> str:
        """从会话条目原始文本中提取会话名（去除未读数 / 时间等噪声）。"""
        # 会话条目 window_text 常为多段拼接，取首个非空片段作为名称
        parts = [p.strip() for p in re.split(r"[\r\n\t]", raw) if p.strip()]
        return parts[0] if parts else raw.strip()

    # ————————————————————— 读取 / 遍历 —————————————————————
    def list_sessions(self) -> List[SessionItem]:
        """读取当前可见的全部会话条目名称。

        Returns:
            :class:`SessionItem` 列表（仅当前视口内已加载的条目）。
        """
        lst = self._session_list()
        items: List[SessionItem] = []
        try:
            children = lst.children(control_type="ListItem")
        except Exception:  # noqa: BLE001
            children = lst.descendants(control_type="ListItem")

        for item in children:
            try:
                raw = item.window_text()
            except Exception:  # noqa: BLE001
                continue
            name = self._clean_name(raw)
            if not name:
                continue
            items.append(
                SessionItem(
                    name=name,
                    is_group=self._guess_is_group(name),
                    raw_text=raw,
                )
            )
        return items

    def list_session_names(self) -> List[str]:
        """仅返回会话名称字符串列表。"""
        return [s.name for s in self.list_sessions()]

    def switch_to(self, name: str) -> None:
        """点击切换到指定名称的会话（需已在可见列表中）。

        若当前视口内找不到，可先调用 :meth:`scroll_down` 加载更多。
        """
        lst = self._session_list()
        try:
            children = lst.descendants(control_type="ListItem")
        except Exception as exc:  # noqa: BLE001
            raise ControlNotFoundError(f"无法遍历会话条目：{exc}") from exc

        for item in children:
            try:
                if self._clean_name(item.window_text()) == name:
                    item.click_input()
                    self.input.sleep_medium()
                    logger.info("已切换会话：%s", name)
                    return
            except Exception:  # noqa: BLE001
                continue
        raise ContactNotFoundError(f"当前会话列表中未找到：{name}")

    def iterate_sessions(self, max_count: Optional[int] = None):
        """生成器：依次点击并切入每个可见会话，产出会话名。

        Args:
            max_count: 最多遍历的会话数量，None 表示遍历当前全部可见项。

        Yields:
            当前切入的会话名。
        """
        sessions = self.list_sessions()
        if max_count is not None:
            sessions = sessions[:max_count]
        for s in sessions:
            try:
                self.switch_to(s.name)
                yield s.name
            except Exception as exc:  # noqa: BLE001
                logger.warning("切换会话失败 %s：%s", s.name, exc)

    # ————————————————————— 滚动加载 —————————————————————
    def scroll_down(self, times: int = 1, wheel_dist: int = -3) -> None:
        """向下滚动会话列表以加载更多历史会话。

        Args:
            times: 滚动次数。
            wheel_dist: 每次滚动的滚轮增量（负数向下）。
        """
        lst = self._session_list()
        rect = lst.rectangle()
        center = (rect.mid_point().x, rect.mid_point().y)
        for _ in range(max(1, times)):
            self.input.scroll(center, wheel_dist)
            self.input.sleep_short()

    def scroll_up(self, times: int = 1, wheel_dist: int = 3) -> None:
        """向上滚动会话列表（回到较新的会话）。"""
        self.scroll_down(times=times, wheel_dist=abs(wheel_dist))

    def load_all_sessions(self, max_scrolls: int = 20) -> List[SessionItem]:
        """滚动加载并聚合尽可能多的会话（去重）。

        Args:
            max_scrolls: 最大滚动次数上限，防止无限循环。

        Returns:
            去重后的会话条目列表（按首次出现顺序）。
        """
        seen = set()
        result: List[SessionItem] = []
        for _ in range(max_scrolls):
            batch = self.list_sessions()
            new_found = False
            for s in batch:
                if s.name not in seen:
                    seen.add(s.name)
                    result.append(s)
                    new_found = True
            if not new_found:
                break  # 一轮没有新增，认为已到底
            self.scroll_down()
        return result

    # ————————————————————— 聊天记录读取 —————————————————————
    def _message_list(self):
        """定位聊天记录消息列表容器。"""
        candidates = [self.config.message_list_title, "消息", "Messages"]
        for name in candidates:
            try:
                ctrl = self.window.main.child_window(
                    title=name, control_type="List"
                )
                if ctrl.exists(timeout=self.config.short_delay):
                    return ctrl
            except Exception:  # noqa: BLE001
                continue
        try:
            lists = self.window.main.descendants(control_type="List")
            # 消息列表通常是较大的那个，取最后一个 List 作为启发式
            if len(lists) >= 2:
                return lists[-1]
            if lists:
                return lists[0]
        except Exception as exc:  # noqa: BLE001
            raise ControlNotFoundError(f"未找到消息列表：{exc}") from exc
        raise ControlNotFoundError("未找到聊天记录消息列表控件。")

    def read_messages(self) -> List[ChatMessage]:
        """读取当前聊天窗口消息区域的可见文本（UI 层读取）。

        Returns:
            :class:`ChatMessage` 列表。sender 尽力解析，可能为空。
        """
        msg_list = self._message_list()
        messages: List[ChatMessage] = []
        try:
            items = msg_list.descendants(control_type="ListItem")
        except Exception as exc:  # noqa: BLE001
            raise ControlNotFoundError(f"无法读取消息条目：{exc}") from exc

        for item in items:
            try:
                text = item.window_text().strip()
            except Exception:  # noqa: BLE001
                continue
            if not text:
                continue
            sender, body = self._parse_message(text)
            messages.append(ChatMessage(sender=sender, text=body))
        return messages

    @staticmethod
    def _parse_message(raw: str) -> tuple:
        """尝试从消息条目文本中拆分发送者与正文。

        微信消息条目文本形态多样，这里只做保守解析：
        形如 "昵称: 正文" 时拆分，否则整体作为正文。
        """
        m = re.match(r"^(?P<sender>[^:：]{1,30})[:：]\s*(?P<body>.+)$", raw, re.S)
        if m:
            return m.group("sender").strip(), m.group("body").strip()
        return None, raw

    def read_messages_text(self) -> List[str]:
        """仅返回消息正文文本列表。"""
        return [m.text for m in self.read_messages()]

    def scroll_history_up(self, times: int = 1, wheel_dist: int = 3) -> None:
        """在聊天记录区域向上滚动，加载更早的历史消息。"""
        msg_list = self._message_list()
        rect = msg_list.rectangle()
        center = (rect.mid_point().x, rect.mid_point().y)
        for _ in range(max(1, times)):
            self.input.scroll(center, wheel_dist)
            self.input.sleep_short()

    def scroll_history_down(self, times: int = 1, wheel_dist: int = -3) -> None:
        """在聊天记录区域向下滚动，回到最新消息。"""
        self.scroll_history_up(times=times, wheel_dist=-abs(wheel_dist))
