"""统一门面 :class:`WeChat`，聚合各能力模块，提供简洁的一站式 API。

大多数使用者只需要::

    from wechat_auto import WeChat

    wx = WeChat()
    wx.send_text("张三", "在吗？")
    wx.send_files("张三", [r"D:\\合同.pdf"])

若需要更细粒度控制，可直接使用 ``wx.messaging`` / ``wx.files`` /
``wx.sessions`` / ``wx.controls`` / ``wx.mouse`` 等子模块。
"""

from __future__ import annotations

import logging
from typing import Dict, Iterable, List, Optional

from .core import WeChatWindow
from .messaging import Messaging
from .files import FileSender
from .sessions import SessionManager
from .inputsim import InputSimulator
from .controls import ControlHelper

logger = logging.getLogger("wechat_auto")


class WeChat:
    """微信桌面自动化门面。"""

    def __init__(self, backend: str = "uia", connect_timeout: float = 15.0,
                 wake: bool = True):
        self.window = WeChatWindow(backend=backend, connect_timeout=connect_timeout)
        if wake:
            self.window.wake()
        self.messaging = Messaging(self.window)
        self.files = FileSender(self.window)
        self.sessions = SessionManager(self.window)
        self.controls = ControlHelper(self.window)
        self.mouse = InputSimulator(self.window)
        self.keyboard = self.mouse  # 键鼠共用同一模拟器

    # ------------------------------------------------------------------ #
    # 窗口
    # ------------------------------------------------------------------ #
    def wake(self):
        return self.window.wake()

    def minimize(self):
        return self.window.minimize()

    def restore(self):
        return self.window.restore()

    def bring_to_top(self):
        return self.window.bring_to_top()

    def dump_control_tree(self, depth: Optional[int] = None,
                          to_file: Optional[str] = None) -> str:
        return self.window.dump_control_tree(depth=depth, to_file=to_file)

    # ------------------------------------------------------------------ #
    # 消息（带自动搜索进入）
    # ------------------------------------------------------------------ #
    def open_chat(self, name: str) -> None:
        """搜索并进入某个好友 / 群聊。"""
        self.messaging.search_and_open(name)

    def send_text(self, to: Optional[str], text: str, send: bool = True,
                  use_clipboard: bool = True) -> None:
        """给指定联系人发送文本；``to=None`` 表示发给当前已打开的聊天。"""
        if to is not None:
            self.messaging.search_and_open(to)
        self.messaging.send_text(text, send=send, use_clipboard=use_clipboard)

    def send_long_text(self, to: Optional[str], text: str,
                       max_len: int = 2000) -> int:
        if to is not None:
            self.messaging.search_and_open(to)
        return self.messaging.send_long_text(text, max_len=max_len)

    def broadcast_text(self, contacts: Iterable[str], text: str,
                       interval: float = 1.5) -> Dict[str, bool]:
        return self.messaging.broadcast_text(contacts, text, interval=interval)

    # ------------------------------------------------------------------ #
    # 文件 / 图片
    # ------------------------------------------------------------------ #
    def send_files(self, to: Optional[str], paths: Iterable[str],
                   send: bool = True) -> List[str]:
        if to is not None:
            self.messaging.search_and_open(to)
        return self.files.send_files(paths, send=send)

    def send_image(self, to: Optional[str], image_path: str,
                   send: bool = True) -> None:
        if to is not None:
            self.messaging.search_and_open(to)
        self.files.send_image(image_path, send=send)

    # ------------------------------------------------------------------ #
    # 会话
    # ------------------------------------------------------------------ #
    def list_sessions(self) -> List[str]:
        return self.sessions.list_sessions()

    def get_history_text(self, of: Optional[str] = None) -> str:
        """读取聊天历史文本；``of`` 指定会话名则先切入该会话。"""
        if of is not None:
            self.sessions.open_session(of)
        return self.sessions.get_history_text()
