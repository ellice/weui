"""对外统一入口 :class:`WeChatAuto`。

把窗口、会话、聊天三大管理器聚合成一个易用的门面对象，
覆盖用户需求的五类能力。典型用法::

    from wechat_auto import WeChatAuto

    wx = WeChatAuto().connect()
    wx.send_to_contact("文件传输助手", "你好，世界！")
    wx.send_file("文件传输助手", r"C:\\report.pdf")
    print(wx.list_session_names())
"""

from __future__ import annotations

from typing import Iterable, List, Optional, Sequence

from .config import WeChatConfig, DEFAULT_CONFIG
from .window import WindowManager
from .session import SessionManager, SessionItem
from .chat import ChatManager


class WeChatAuto:
    """微信桌面自动化门面。"""

    def __init__(self, config: WeChatConfig = DEFAULT_CONFIG):
        self.config = config
        self.window = WindowManager(config)
        self.session = SessionManager(self.window, config)
        self.chat = ChatManager(self.window, config)

    # ------------------------------------------------------------------ #
    # 连接 / 窗口
    # ------------------------------------------------------------------ #
    def connect(self) -> "WeChatAuto":
        """连接微信主窗口并激活。"""
        self.window.connect()
        self.window.activate()
        return self

    def activate(self) -> None:
        self.window.activate()

    def set_topmost(self, topmost: bool = True) -> None:
        self.window.set_topmost(topmost)

    def minimize(self) -> None:
        self.window.minimize()

    def restore(self) -> None:
        self.window.restore()

    def dump_control_tree(self, depth: int = 8, to_file: Optional[str] = None) -> str:
        return self.window.dump_control_tree(depth=depth, to_file=to_file)

    def click_button(self, title: str) -> None:
        self.window.click_button(title)

    def button_exists(self, title: str) -> bool:
        return self.window.button_exists(title)

    # ------------------------------------------------------------------ #
    # 会话
    # ------------------------------------------------------------------ #
    def list_sessions(self) -> List[SessionItem]:
        return self.session.list_sessions()

    def list_session_names(self) -> List[str]:
        return self.session.list_session_names()

    def load_all_sessions(self, max_scroll: int = 20) -> List[str]:
        return self.session.load_all_sessions(max_scroll=max_scroll)

    def switch_to(self, name: str, exact: bool = False) -> bool:
        return self.session.switch_to(name, exact=exact)

    def iterate_sessions(self, callback, max_scroll: int = 10) -> None:
        self.session.iterate_sessions(callback, max_scroll=max_scroll)

    def get_current_messages(self) -> List[str]:
        return self.session.get_current_messages()

    # ------------------------------------------------------------------ #
    # 消息 / 文件
    # ------------------------------------------------------------------ #
    def search_and_open(self, keyword: str) -> None:
        self.chat.search_and_open(keyword)

    def send_text(self, text: str, human: bool = True, via_clipboard: bool = False) -> None:
        self.chat.send_text(text, human=human, via_clipboard=via_clipboard)

    def send_to_contact(
        self,
        keyword: str,
        text: str,
        via_clipboard: bool = False,
    ) -> None:
        self.chat.send_to_contact(keyword, text, via_clipboard=via_clipboard)

    def batch_send(
        self,
        contacts: Iterable[str],
        text: str,
        interval: float = 1.0,
        via_clipboard: bool = True,
    ) -> List[str]:
        return self.chat.batch_send(
            contacts, text, interval=interval, via_clipboard=via_clipboard
        )

    def send_file(self, keyword: str, path: str, caption: Optional[str] = None) -> None:
        self.chat.send_files_to_contact(keyword, [path], caption=caption)

    def send_files(
        self,
        keyword: str,
        paths: Sequence[str],
        caption: Optional[str] = None,
    ) -> None:
        self.chat.send_files_to_contact(keyword, paths, caption=caption)

    def send_image(self, keyword: str, path: str, caption: Optional[str] = None) -> None:
        self.chat.send_files_to_contact(keyword, [path], caption=caption)

    # ------------------------------------------------------------------ #
    # 输入框工具
    # ------------------------------------------------------------------ #
    def clear_input(self) -> None:
        self.chat.clear_input()

    def clear_search(self) -> None:
        self.chat.clear_search()
