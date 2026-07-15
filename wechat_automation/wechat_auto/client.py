"""高层门面 :class:`WeChatClient`。

把窗口、消息、文件、会话四大能力聚合到一个对象，作为最常用的入口。
细粒度控制可直接使用各子模块（``window`` / ``messenger`` / ``files`` / ``sessions``）。
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Sequence

from .config import WeChatConfig, default_config
from .files import FileSender
from .messaging import Messenger
from .sessions import ChatMessage, SessionItem, SessionManager
from .window import WeChatWindow

logger = logging.getLogger("wechat_auto.client")


class WeChatClient:
    """桌面版微信自动化统一客户端。

    Example::

        wx = WeChatClient()
        wx.connect()
        wx.send_text("文件传输助手", "你好")
        wx.send_file("文件传输助手", r"C:\\a.pdf")
        for name in wx.list_session_names():
            print(name)
    """

    def __init__(self, config: Optional[WeChatConfig] = None):
        self.config = config or default_config
        self.window = WeChatWindow(self.config)
        self.messenger = Messenger(self.window)
        self.files = FileSender(self.window, self.messenger)
        self.sessions = SessionManager(self.window)

    # ————————————————————— 生命周期 —————————————————————
    def connect(self, launch_if_needed: bool = True) -> "WeChatClient":
        """连接（必要时唤起）微信主窗口。"""
        self.window.connect(launch_if_needed=launch_if_needed)
        return self

    def activate(self) -> None:
        self.window.activate()

    def minimize(self) -> None:
        self.window.minimize()

    def restore(self) -> None:
        self.window.restore()

    # ————————————————————— 文本消息 —————————————————————
    def send_text(self, keyword: str, text: str, **kwargs) -> None:
        """发送文本，见 :meth:`Messenger.send_text`。"""
        self.messenger.send_text(keyword, text, **kwargs)

    def send_long_text(self, keyword: str, text: str, **kwargs) -> int:
        return self.messenger.send_long_text(keyword, text, **kwargs)

    def broadcast(
        self, keywords: Sequence[str], text: str, **kwargs
    ) -> Dict[str, bool]:
        return self.messenger.broadcast(keywords, text, **kwargs)

    def send_with_mentions(
        self, keyword: str, members, text: str
    ) -> None:
        self.messenger.send_with_mentions(keyword, members, text)

    def open_chat(self, keyword: str) -> None:
        self.messenger.open_chat(keyword)

    # ————————————————————— 文件 / 图片 —————————————————————
    def send_file(self, keyword: str, path: str) -> str:
        return self.files.send_file(keyword, path)

    def send_files(self, keyword: str, paths: Sequence[str]) -> List[str]:
        return self.files.send_files(keyword, paths)

    def send_image(self, keyword: str, image_path: str) -> None:
        self.files.send_image(keyword, image_path)

    def send_images(self, keyword: str, image_paths: Sequence[str]) -> List[str]:
        return self.files.send_images(keyword, image_paths)

    # ————————————————————— 会话列表 —————————————————————
    def list_sessions(self) -> List[SessionItem]:
        return self.sessions.list_sessions()

    def list_session_names(self) -> List[str]:
        return self.sessions.list_session_names()

    def switch_to(self, name: str) -> None:
        self.sessions.switch_to(name)

    def load_all_sessions(self, max_scrolls: int = 20) -> List[SessionItem]:
        return self.sessions.load_all_sessions(max_scrolls=max_scrolls)

    def read_messages(self) -> List[ChatMessage]:
        return self.sessions.read_messages()

    def read_messages_text(self) -> List[str]:
        return self.sessions.read_messages_text()

    # ————————————————————— 调试 —————————————————————
    def dump_control_tree(self, depth: Optional[int] = None) -> str:
        return self.window.dump_control_tree(depth=depth)

    def save_control_tree(self, path: str, depth: Optional[int] = None) -> str:
        return self.window.save_control_tree(path, depth=depth)
