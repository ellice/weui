"""对外统一入口。

:class:`WeChat` 组合了窗口、消息、文件、会话四大模块，
提供简洁的一站式 API，同时保留各子模块以便高级用法。

示例::

    from wechat_auto import WeChat

    wx = WeChat()

    # 发送文本
    wx.send_text("文件传输助手", "你好\\n这是第二行")

    # 发送文件 / 图片
    wx.send_file("张三", r"D:\\report.xlsx")
    wx.send_image("张三", r"D:\\screenshot.png")

    # 批量群发
    wx.broadcast(["张三", "项目组", "李四"], "周会 10:00 开始")

    # 会话列表
    print(wx.list_sessions())

    # 读取当前聊天历史
    wx.open("张三")
    print(wx.read_messages())
"""

from __future__ import annotations

from typing import Dict, Iterable, List, Optional, Sequence, Union
import os

from .files import FileSender
from .messaging import Messaging
from .sessions import SessionManager
from .window import WeChatWindow


PathLike = Union[str, "os.PathLike[str]"]


class WeChat:
    """桌面版微信自动化统一入口。"""

    def __init__(
        self,
        backend: str = "uia",
        timeout: float = 10.0,
        input_delay: float = 0.05,
        activate: bool = True,
    ):
        self.window = WeChatWindow(backend=backend, timeout=timeout)
        self.messaging = Messaging(self.window, input_delay=input_delay)
        self.files = FileSender(self.messaging)
        self.sessions = SessionManager(self.window)
        if activate:
            self.window.activate()

    # ---- 窗口 ----

    def activate(self) -> None:
        """唤起并激活微信窗口。"""
        self.window.activate()

    def minimize(self) -> None:
        self.window.minimize()

    def restore(self) -> None:
        self.window.restore()

    def set_topmost(self, on: bool = True) -> None:
        self.window.set_topmost(on)

    def dump_tree(self, depth: int = 20, to_file: Optional[str] = None) -> str:
        """导出控件树，用于调试定位控件。"""
        return self.window.dump_tree(depth=depth, to_file=to_file)

    def list_buttons(self) -> List[str]:
        """列出当前窗口所有按钮标题。"""
        return self.window.list_buttons()

    def click_button(self, title: str = None, **kwargs) -> None:
        """点击可见按钮（更多、表情、语音、截图等）。"""
        self.window.click_button(title=title, **kwargs)

    # ---- 搜索 / 打开会话 ----

    def open(self, contact: str) -> None:
        """搜索并进入指定好友 / 群聊的聊天窗口。"""
        self.messaging.search_and_open(contact)

    def clear_search(self) -> None:
        self.messaging.clear_search()

    def clear_input(self) -> None:
        self.messaging.clear_input()

    # ---- 发送文本 ----

    def send_text(
        self,
        contact_or_text: str,
        text: Optional[str] = None,
        **kwargs,
    ) -> None:
        """发送文本。

        两种用法：
            - ``send_text("你好")``：向当前会话发送
            - ``send_text("张三", "你好")``：先搜索张三再发送
        """
        if text is None:
            self.messaging.send_text(contact_or_text, **kwargs)
        else:
            self.messaging.send_to(contact_or_text, text, **kwargs)

    def send_long_text(self, text: str, **kwargs) -> None:
        """分段发送长文本。"""
        self.messaging.send_long_text(text, **kwargs)

    def broadcast(
        self,
        contacts: Iterable[str],
        text: str,
        interval: float = 1.0,
        human_like: bool = False,
    ) -> Dict[str, bool]:
        """批量群发文本给多个联系人。"""
        return self.messaging.broadcast(
            contacts, text, interval=interval, human_like=human_like
        )

    def at_member(self, name: str, text: str = "", send: bool = False) -> None:
        """群聊中 @ 某成员。"""
        self.messaging.at_member(name, text=text, send=send)

    # ---- 发送文件 / 图片 ----

    def send_file(
        self,
        contact_or_path: PathLike,
        path: Optional[PathLike] = None,
        **kwargs,
    ) -> None:
        """发送文件。

        用法：
            - ``send_file(r"D:\\a.xlsx")``：发到当前会话
            - ``send_file("张三", r"D:\\a.xlsx")``：先搜索张三再发送
        """
        if path is None:
            self.files.send_file(contact_or_path, **kwargs)
        else:
            self.files.send_to(str(contact_or_path), path, **kwargs)

    def send_files(self, paths: Sequence[PathLike], **kwargs) -> None:
        """批量发送多个文件到当前会话。"""
        self.files.send_files(paths, **kwargs)

    def send_image(
        self,
        contact_or_path: PathLike,
        path: Optional[PathLike] = None,
        **kwargs,
    ) -> None:
        """发送图片。用法同 :meth:`send_file`。"""
        if path is None:
            self.files.send_image(contact_or_path, **kwargs)
        else:
            self.messaging.search_and_open(str(contact_or_path))
            self.files.send_image(path, **kwargs)

    # ---- 会话列表 ----

    def list_sessions(self) -> List[str]:
        """读取当前可见会话名称列表。"""
        return self.sessions.list_sessions()

    def list_all_sessions(self, **kwargs) -> List[str]:
        """滚动加载并读取全部会话名称。"""
        return self.sessions.list_all_sessions(**kwargs)

    def scroll_sessions(self, wheel_dist: int = -3) -> None:
        self.sessions.scroll_sessions(wheel_dist=wheel_dist)

    def iterate_sessions(self, callback, **kwargs) -> List[str]:
        """遍历所有会话并回调。"""
        return self.sessions.iterate_sessions(callback, **kwargs)

    def is_group_chat(self) -> bool:
        """判断当前会话是否为群聊。"""
        return self.sessions.is_group_chat()

    # ---- 历史消息 ----

    def read_messages(self) -> List[str]:
        """读取当前聊天窗口可见消息文本。"""
        return self.sessions.read_messages()

    def load_history_messages(self, **kwargs) -> List[str]:
        """向上滚动加载并汇总历史消息。"""
        return self.sessions.load_history_messages(**kwargs)

    def scroll_messages_up(self, times: int = 3, **kwargs) -> None:
        self.sessions.scroll_messages_up(times=times, **kwargs)
