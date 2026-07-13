"""顶层封装 :class:`WeChatBot`，聚合各子模块，提供一站式 API。"""

from __future__ import annotations

import logging
from typing import Optional

from .core import WeChatCore
from .file_sender import FileSender
from .message import MessageSender
from .session import SessionManager
from .window import WindowController

logger = logging.getLogger("wechat_auto")


class WeChatBot:
    """微信桌面自动化统一入口。

    Example
    -------
    >>> bot = WeChatBot().connect()
    >>> bot.open_chat("文件传输助手")
    >>> bot.send_text("你好，世界！\\n这是第二行。")
    >>> bot.send_file(r"C:\\报表.xlsx")
    """

    def __init__(
        self,
        window_title: str = "微信",
        window_class: str = "WeChatMainWndForPC",
        default_timeout: float = 10.0,
    ) -> None:
        self.core = WeChatCore(
            window_title=window_title,
            window_class=window_class,
            default_timeout=default_timeout,
        )
        self.messages = MessageSender(self.core)
        self.files = FileSender(self.core, self.messages)
        self.sessions = SessionManager(self.core)
        self.window = WindowController(self.core)

    # ------------------------------------------------------------------
    # 连接 / 启动
    # ------------------------------------------------------------------
    def connect(self, timeout: Optional[float] = None) -> "WeChatBot":
        self.core.connect(timeout=timeout)
        return self

    def launch(self, exe_path: str, wait_login_timeout: float = 60.0) -> "WeChatBot":
        self.core.launch(exe_path, wait_login_timeout=wait_login_timeout)
        return self

    # ------------------------------------------------------------------
    # 便捷代理方法（常用操作直接暴露在 bot 上）
    # ------------------------------------------------------------------
    def open_chat(self, keyword: str, exact: bool = False):
        return self.messages.open_chat(keyword, exact=exact)

    def send_text(self, text: str, slow: bool = True):
        return self.messages.send_text(text, slow=slow)

    def send_text_fast(self, text: str):
        return self.messages.send_text_via_clipboard(text)

    def send_long_text(self, text: str, chunk_size: int = 500):
        return self.messages.send_long_text_in_chunks(text, chunk_size=chunk_size)

    def broadcast(self, contacts, text: str, interval: float = 1.5):
        return self.messages.broadcast_text(contacts, text, interval=interval)

    def mention(self, name: str, text: str = ""):
        return self.messages.send_mention(name, text)

    def send_file(self, path: str):
        return self.files.send_file(path)

    def send_files(self, paths):
        return self.files.send_files(paths)

    def send_image(self, path: str, as_image: bool = True):
        return self.files.send_image(path, as_image=as_image)

    def list_sessions(self):
        return self.sessions.list_sessions()

    def read_messages(self):
        return self.sessions.read_current_messages()

    def activate(self):
        return self.window.activate()

    def dump_tree(self, to_file: Optional[str] = None):
        return self.window.dump_tree(to_file=to_file)
