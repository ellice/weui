"""会话列表管理（第三类）。

- 读取左侧全部会话名称
- 遍历会话、点击切换任意聊天窗口
- 读取当前聊天窗口历史消息区域文本
- 下拉滚动会话列表加载更多
- 区分私聊 / 群聊
"""

from __future__ import annotations

import re
import time
from typing import List, Optional

from .config import WeChatConfig
from .controls import ControlHelper
from .exceptions import ControlNotFoundError
from .inputs import InputController

# 群聊名称通常带有人数后缀，例如 "项目讨论组 (128)"
_GROUP_NAME_PATTERN = re.compile(r".+\(\d+\)\s*$")


class SessionManager:
    """左侧会话列表与聊天记录读取。"""

    def __init__(
        self,
        window,
        controls: ControlHelper,
        inputs: InputController,
        config: WeChatConfig,
    ) -> None:
        self.window = window
        self.controls = controls
        self.inputs = inputs
        self.config = config

    # ------------------------------------------------------------------ #
    # 会话列表
    # ------------------------------------------------------------------ #
    def _session_list(self):
        return self.controls.wait_control(
            title=self.config.session_list_title, control_type="List"
        )

    def list_sessions(self) -> List[str]:
        """读取当前可见的全部会话名称。"""
        session_list = self._session_list()
        names: List[str] = []
        try:
            for item in session_list.children(control_type="ListItem"):
                name = item.window_text()
                if name:
                    names.append(name)
        except Exception as exc:  # noqa: BLE001
            raise ControlNotFoundError(f"读取会话列表失败：{exc}") from exc
        return names

    def open_session(self, name: str, timeout: Optional[float] = None) -> bool:
        """在会话列表中点击指定名称的会话进行切换。

        :returns: 是否成功找到并点击。
        """
        timeout = self.config.default_timeout if timeout is None else timeout
        session_list = self._session_list()
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                for item in session_list.children(control_type="ListItem"):
                    if item.window_text() == name:
                        self.controls._invoke_or_click(item)
                        time.sleep(self.config.action_delay)
                        return True
            except Exception:  # noqa: BLE001
                pass
            # 没找到就滚动加载更多
            self.scroll_session_list(down=True)
        return False

    def iterate_sessions(self, limit: Optional[int] = None):
        """遍历会话：依次点击每个会话并 yield 其名称。

        :param limit: 最多遍历的会话数量。
        """
        session_list = self._session_list()
        visited = 0
        seen = set()
        items = session_list.children(control_type="ListItem")
        for item in items:
            name = item.window_text()
            if not name or name in seen:
                continue
            seen.add(name)
            try:
                self.controls._invoke_or_click(item)
                time.sleep(self.config.action_delay)
            except Exception:  # noqa: BLE001
                continue
            yield name
            visited += 1
            if limit and visited >= limit:
                return

    def scroll_session_list(self, down: bool = True, amount: int = 3) -> None:
        """滚动会话列表以加载更多历史会话。

        :param down: True 向下滚动，False 向上。
        """
        session_list = self._session_list()
        try:
            rect = session_list.rectangle()
            coords = (rect.mid_point().x, rect.mid_point().y)
            wheel = -amount if down else amount
            self.inputs.scroll(coords, wheel)
        except Exception:  # noqa: BLE001
            # 回退：用键盘翻页
            session_list.set_focus()
            self.inputs.send_keys("{PGDN}" if down else "{PGUP}")

    # ------------------------------------------------------------------ #
    # 私聊 / 群聊判断
    # ------------------------------------------------------------------ #
    def is_group_chat(self, name: str) -> bool:
        """根据名称启发式判断是否群聊（名称带人数后缀，如 "xxx (128)"）。

        更可靠的方式是打开会话后检查是否存在"聊天成员 / 群公告"等群专属控件，
        见 :meth:`is_current_group_chat`。
        """
        return bool(_GROUP_NAME_PATTERN.match(name.strip()))

    def is_current_group_chat(self) -> bool:
        """打开某会话后，通过是否存在"聊天信息"群专属控件判断当前是否群聊。"""
        # 群聊标题栏右侧一般有"聊天信息"按钮且点击后有成员列表；
        # 这里用是否存在群人数标识做轻量判断。
        for hint in ("聊天成员", "群公告", "查看更多群成员"):
            if self.controls.exists(title=hint):
                return True
        return False

    # ------------------------------------------------------------------ #
    # 聊天记录读取
    # ------------------------------------------------------------------ #
    def get_current_messages(self) -> List[str]:
        """读取当前聊天窗口消息区域的文本（按气泡逐条返回）。"""
        msg_list = self.controls.wait_control(
            title=self.config.message_list_title, control_type="List"
        )
        messages: List[str] = []
        try:
            for item in msg_list.children(control_type="ListItem"):
                text = item.window_text()
                if text:
                    messages.append(text)
        except Exception as exc:  # noqa: BLE001
            raise ControlNotFoundError(f"读取聊天记录失败：{exc}") from exc
        return messages

    def scroll_messages(self, up: bool = True, amount: int = 3) -> None:
        """在聊天记录区域上下翻页（上滑查看更早消息）。"""
        msg_list = self.controls.wait_control(
            title=self.config.message_list_title, control_type="List"
        )
        try:
            rect = msg_list.rectangle()
            coords = (rect.mid_point().x, rect.mid_point().y)
            wheel = amount if up else -amount
            self.inputs.scroll(coords, wheel)
        except Exception:  # noqa: BLE001
            msg_list.set_focus()
            self.inputs.send_keys("{PGUP}" if up else "{PGDN}")
