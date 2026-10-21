"""顶层门面：``WeChat``。

把窗口、控件、键鼠、搜索、消息、文件、会话各子模块组合成一个易用的入口，
覆盖需求中的五大模块能力。

典型用法::

    from wechat_automation import WeChat

    wx = WeChat()
    wx.connect()                       # 连接并唤起微信
    wx.open_chat("文件传输助手")        # 搜索并进入会话
    wx.send_text("你好\\n这是第二行")    # 发送多行文本
    wx.send_file(r"D:/报表.xlsx")       # 发送文件
    print(wx.list_sessions())          # 读取会话列表
"""

from __future__ import annotations

from typing import Dict, Iterable, List, Optional

from .controls import ControlHelper
from .files import FileSender
from .input_simulator import InputSimulator
from .messaging import MessageSender
from .navigation import Navigator
from .sessions import SessionManager
from .window import WeChatWindow


class WeChat:
    """微信桌面自动化统一入口。"""

    def __init__(self, backend: str = "uia", human_like: bool = True,
                 min_char_delay: float = 0.02,
                 max_char_delay: float = 0.12) -> None:
        """
        :param backend: pywinauto 后端，默认 ``uia``。
        :param human_like: 是否启用拟人慢速输入（防风控）。
        """
        self._backend = backend
        self.window = WeChatWindow(backend=backend)
        self.sim = InputSimulator(
            human_like=human_like,
            min_char_delay=min_char_delay,
            max_char_delay=max_char_delay,
        )
        # 这些在 connect() 后初始化（依赖主窗口句柄）。
        self.controls: Optional[ControlHelper] = None
        self.nav: Optional[Navigator] = None
        self.messages: Optional[MessageSender] = None
        self.files: Optional[FileSender] = None
        self.sessions: Optional[SessionManager] = None

    # ----- 连接 / 窗口 -----
    def connect(self, timeout: float = 10.0, activate: bool = True) -> "WeChat":
        """连接微信主窗口并初始化各子模块。"""
        self.window.connect(timeout=timeout)
        if activate:
            self.window.activate()
        root = self.window.main_window
        self.controls = ControlHelper(root)
        self.nav = Navigator(self.window, self.controls, self.sim)
        self.messages = MessageSender(self.window, self.controls, self.sim,
                                      self.nav)
        self.files = FileSender(self.window, self.controls, self.sim,
                                self.messages)
        self.sessions = SessionManager(self.window, self.controls, self.sim)
        return self

    def _ensure(self) -> None:
        if self.controls is None:
            self.connect()

    def is_running(self) -> bool:
        return self.window.is_running()

    def activate(self) -> None:
        self.window.activate()

    def minimize(self) -> None:
        self.window.minimize()

    def restore(self) -> None:
        self.window.restore()

    def bring_to_top(self) -> None:
        self.window.bring_to_top()

    # ----- 搜索 / 切换 -----
    def open_chat(self, keyword: str, use_clipboard: bool = True) -> "WeChat":
        """搜索备注 / 昵称 / 群名并进入会话。"""
        self._ensure()
        assert self.nav is not None
        self.nav.search_and_open(keyword, use_clipboard=use_clipboard)
        return self

    def clear_search(self) -> None:
        self._ensure()
        assert self.nav is not None
        self.nav.clear_search()

    # ----- 文本消息 -----
    def send_text(self, text: str, paste: bool = True, send: bool = True) -> None:
        self._ensure()
        assert self.messages is not None
        self.messages.send_text(text, paste=paste, send=send)

    def send_paragraphs(self, paragraphs: Iterable[str], interval: float = 0.8,
                        paste: bool = True) -> None:
        self._ensure()
        assert self.messages is not None
        self.messages.send_paragraphs(paragraphs, interval=interval, paste=paste)

    def send_long_text(self, text: str, chunk_size: int = 1500,
                       interval: float = 0.8) -> None:
        self._ensure()
        assert self.messages is not None
        self.messages.send_long_text(text, chunk_size=chunk_size,
                                     interval=interval)

    def broadcast(self, contacts: Iterable[str], text: str, interval: float = 1.0,
                  paste: bool = True,
                  per_contact_texts: Optional[Dict[str, str]] = None
                  ) -> Dict[str, bool]:
        """循环批量给多个联系人群发文本。"""
        self._ensure()
        assert self.messages is not None
        return self.messages.broadcast(
            contacts, text, interval=interval, paste=paste,
            per_contact_texts=per_contact_texts,
        )

    def mention(self, name: str = "") -> None:
        self._ensure()
        assert self.messages is not None
        self.messages.mention(name)

    def clear_input(self) -> None:
        self._ensure()
        assert self.messages is not None
        self.messages.clear_input()

    # ----- 文件 / 图片 -----
    def send_file(self, path: str, send: bool = True) -> str:
        self._ensure()
        assert self.files is not None
        return self.files.send_file(path, send=send)

    def send_files(self, paths: Iterable[str], send: bool = True) -> List[str]:
        self._ensure()
        assert self.files is not None
        return self.files.send_files(paths, send=send)

    def send_image(self, path: str, as_image: bool = False,
                   send: bool = True) -> str:
        self._ensure()
        assert self.files is not None
        return self.files.send_image(path, as_image=as_image, send=send)

    # ----- 会话列表 -----
    def list_sessions(self) -> List[str]:
        self._ensure()
        assert self.sessions is not None
        return self.sessions.list_sessions()

    def load_all_sessions(self, max_scrolls: int = 20) -> List[str]:
        self._ensure()
        assert self.sessions is not None
        return self.sessions.load_all_sessions(max_scrolls=max_scrolls)

    def read_messages(self) -> List[str]:
        self._ensure()
        assert self.sessions is not None
        return self.sessions.read_messages()

    def read_history(self, max_scrolls: int = 10) -> List[str]:
        self._ensure()
        assert self.sessions is not None
        return self.sessions.read_history(max_scrolls=max_scrolls)

    def is_group_chat(self) -> bool:
        self._ensure()
        assert self.sessions is not None
        return self.sessions.is_group_chat()

    # ----- 调试 -----
    def dump_control_tree(self, depth: Optional[int] = None) -> None:
        """打印导出全部控件树，用于调试定位。"""
        self._ensure()
        assert self.controls is not None
        self.controls.dump_tree(depth=depth)
