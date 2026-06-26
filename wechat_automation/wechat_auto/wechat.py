"""WeChat 门面类：整合五大类能力，提供统一入口。

用法::

    from wechat_auto import WeChat

    wx = WeChat().connect()
    wx.activate()
    wx.send_text("张三", "你好，在吗？")
    wx.send_file("张三", r"D:\\报表.xlsx")
    print(wx.list_sessions())
"""

from __future__ import annotations

from typing import Dict, List, Optional, Sequence

from .base import WeChatBase
from .input_sim import InputSimulator
from .media import MediaSender
from .message import MessageSender
from .session import SessionManager


class WeChat:
    """对外统一的高层 API。"""

    def __init__(
        self,
        exe_path: Optional[str] = None,
        timeout: float = 15.0,
        key_interval: float = 0.0,
        human_like: bool = True,
    ) -> None:
        self.base = WeChatBase(exe_path=exe_path, timeout=timeout)
        self.input = InputSimulator(key_interval=key_interval, human_like=human_like)
        self.msg = MessageSender(self.base, self.input)
        self.media = MediaSender(self.base, self.input, self.msg)
        self.session = SessionManager(self.base, self.input)

    # ---------------- 连接 / 窗口（类别四） ----------------
    def connect(self) -> "WeChat":
        self.base.connect()
        return self

    def activate(self) -> None:
        self.base.activate()

    def minimize(self) -> None:
        self.base.minimize()

    def restore(self) -> None:
        self.base.restore()

    def maximize(self) -> None:
        self.base.maximize()

    def is_running(self) -> bool:
        return self.base.is_running()

    def dump_tree(self, to_file: Optional[str] = None, depth: int = 12) -> None:
        self.base.dump_tree(to_file=to_file, depth=depth)

    def list_buttons(self) -> List[str]:
        return self.base.list_buttons()

    def click_button(self, title: str) -> bool:
        return self.base.click_button(title)

    def has_control(self, **criteria) -> bool:
        return self.base.exists(**criteria)

    # ---------------- 消息（类别一） ----------------
    def open_chat(self, keyword: str) -> bool:
        return self.msg.search_and_open(keyword)

    def send_text(
        self,
        contact: Optional[str],
        text: str,
        slow: bool = False,
        via_clipboard: bool = False,
    ) -> None:
        """发送文本。contact 为空表示对当前已打开的聊天发送。"""
        if contact:
            self.msg.search_and_open(contact)
        if via_clipboard:
            self.msg.send_text_via_clipboard(text)
        else:
            self.msg.send_text(text, slow=slow)

    def send_long_text(self, contact: Optional[str], text: str, chunk_size: int = 1000) -> int:
        if contact:
            self.msg.search_and_open(contact)
        return self.msg.send_long_text_in_chunks(text, chunk_size=chunk_size)

    def broadcast(self, contacts: Sequence[str], text: str, **kw) -> Dict[str, bool]:
        return self.msg.broadcast(contacts, text, **kw)

    def at_member(self, contact: Optional[str], name: str, text: str = "", send: bool = True) -> None:
        if contact:
            self.msg.search_and_open(contact)
        self.msg.at_member(name, text, send=send)

    def clear_input(self) -> None:
        self.msg.clear_input()

    def clear_search(self) -> None:
        self.msg.clear_search()

    # ---------------- 文件 / 图片（类别二） ----------------
    def send_file(self, contact: Optional[str], file_path: str) -> str:
        if contact:
            self.msg.search_and_open(contact)
        return self.media.send_file(file_path)

    def send_files(self, contact: Optional[str], file_paths: Sequence[str]) -> List[str]:
        if contact:
            self.msg.search_and_open(contact)
        return self.media.send_files(file_paths)

    def send_image(self, contact: Optional[str], image_path: str, as_file: bool = False) -> str:
        if contact:
            self.msg.search_and_open(contact)
        return self.media.send_image(image_path, as_file=as_file)

    def send_images(self, contact: Optional[str], image_paths: Sequence[str]) -> List[str]:
        if contact:
            self.msg.search_and_open(contact)
        return self.media.send_images(image_paths)

    # ---------------- 会话列表（类别三） ----------------
    def list_sessions(self) -> List[str]:
        return self.session.list_sessions()

    def load_all_sessions(self, max_scrolls: int = 20) -> List[str]:
        return self.session.load_all_sessions(max_scrolls=max_scrolls)

    def open_session(self, name: str) -> bool:
        return self.session.open_session(name)

    def get_history_messages(self, limit: Optional[int] = None) -> List[str]:
        return self.session.get_history_messages(limit=limit)

    def scroll_history(self, steps: int = 3, up: bool = True) -> None:
        self.session.scroll_history(steps=steps, up=up)

    def is_group_chat(self) -> bool:
        return self.session.is_group_chat()

    def classify_sessions(self) -> Dict[str, List[str]]:
        return self.session.classify_sessions()
