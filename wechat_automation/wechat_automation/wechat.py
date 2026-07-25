"""顶层门面：:class:`WeChatAuto`。

将窗口、消息、文件、会话四大子模块整合为统一入口，覆盖需求中的全部
能力：基础消息发送、文件 / 图片发送、会话列表管理、窗口与控件通用
操作、键鼠模拟配套功能。

用法::

    from wechat_automation import WeChatAuto

    wx = WeChatAuto().connect()
    wx.bring_to_front()
    wx.send("张三", "你好，这是一条自动化消息")
    wx.send_file("张三", r"C:\\report.pdf")
    for name in wx.sessions.iterate_sessions():
        print(name, wx.get_messages())
"""

from __future__ import annotations

from typing import Iterable, List, Optional, Sequence

from . import clipboard, input_sim
from .config import WeChatConfig, DEFAULT_CONFIG
from .files import FileSender
from .messaging import Messenger
from .sessions import SessionManager
from .window import WindowManager


class WeChatAuto:
    """桌面版微信自动化统一门面。"""

    def __init__(self, config: Optional[WeChatConfig] = None):
        self.config = config or WeChatConfig()
        self.window = WindowManager(self.config)
        # 子模块在 connect 后惰性初始化，先占位。
        self.messenger: Optional[Messenger] = None
        self.files: Optional[FileSender] = None
        self.sessions: Optional[SessionManager] = None

    # ------------------------------------------------------------------
    # 连接
    # ------------------------------------------------------------------
    def connect(self) -> "WeChatAuto":
        """连接微信并初始化各子模块。"""
        self.window.connect()
        self.messenger = Messenger(self.window, self.config)
        self.files = FileSender(self.window, self.messenger, self.config)
        self.sessions = SessionManager(self.window, self.config)
        return self

    def _require_connected(self) -> None:
        if self.messenger is None:
            raise RuntimeError("请先调用 connect() 连接微信。")

    # ------------------------------------------------------------------
    # 窗口操作（转发）
    # ------------------------------------------------------------------
    def bring_to_front(self) -> None:
        self.window.bring_to_front()

    def minimize(self) -> None:
        self.window.minimize()

    def restore(self) -> None:
        self.window.restore()

    def maximize(self) -> None:
        self.window.maximize()

    def set_topmost(self, topmost: bool = True) -> None:
        self.window.set_topmost(topmost)

    def dump_control_tree(self, depth: int = 8) -> str:
        return self.window.dump_control_tree(depth=depth)

    def click_button(self, name: str) -> bool:
        return self.window.click_button(name)

    def button_exists(self, name: str) -> bool:
        return self.window.button_exists(name)

    def get_control_text(self, **criteria) -> str:
        return self.window.get_control_text(**criteria)

    # ------------------------------------------------------------------
    # 消息（转发）
    # ------------------------------------------------------------------
    def open_chat(self, keyword: str) -> None:
        """搜索并进入指定好友 / 群聊。"""
        self._require_connected()
        self.messenger.search_and_open(keyword)

    def send(
        self,
        to: Optional[str],
        text: str,
        human_like: bool = False,
        use_clipboard: bool = True,
    ) -> None:
        """向 ``to``（为 None 时发往当前会话）发送文本。"""
        self._require_connected()
        if to:
            self.messenger.search_and_open(to)
        self.messenger.send_text(
            text, use_clipboard=use_clipboard, human_like=human_like
        )

    def send_long(self, to: Optional[str], text: str, chunk_size: int = 1500) -> int:
        """分段发送长文本。"""
        self._require_connected()
        if to:
            self.messenger.search_and_open(to)
        return self.messenger.send_long_text_in_chunks(text, chunk_size=chunk_size)

    def batch_send(
        self,
        contacts: Iterable[str],
        text: str,
        interval: Optional[float] = None,
        human_like: bool = False,
    ) -> dict:
        """批量群发文本给多个联系人。"""
        self._require_connected()
        return self.messenger.batch_send(
            contacts, text, interval=interval, human_like=human_like
        )

    def mention(self, nickname: str) -> None:
        """群聊中 @ 某成员。"""
        self._require_connected()
        self.messenger.mention(nickname)

    def clear_input(self) -> None:
        self._require_connected()
        self.messenger.clear_input()

    def clear_search(self) -> None:
        self._require_connected()
        self.messenger.clear_search()

    # ------------------------------------------------------------------
    # 文件 / 图片（转发）
    # ------------------------------------------------------------------
    def send_file(
        self, to: Optional[str], path: str, caption: Optional[str] = None
    ) -> None:
        self._require_connected()
        self.files.send_file(path, to=to, caption=caption)

    def send_image(
        self, to: Optional[str], path: str, caption: Optional[str] = None
    ) -> None:
        self._require_connected()
        self.files.send_image(path, to=to, caption=caption)

    def send_files(
        self, to: Optional[str], paths: Sequence[str], one_by_one: bool = False
    ) -> None:
        self._require_connected()
        self.files.send_files(paths, to=to, one_by_one=one_by_one)

    # ------------------------------------------------------------------
    # 会话（转发）
    # ------------------------------------------------------------------
    def list_sessions(self, all_sessions: bool = False) -> List[str]:
        """读取会话名称；all_sessions=True 时滚动读取全部。"""
        self._require_connected()
        if all_sessions:
            return self.sessions.get_all_sessions()
        return self.sessions.get_visible_sessions()

    def switch_to(self, name: str) -> bool:
        self._require_connected()
        return self.sessions.switch_to(name)

    def get_messages(self) -> List[str]:
        """读取当前会话可见的历史消息文本。"""
        self._require_connected()
        return self.sessions.get_current_messages()

    def load_more_history(self, times: int = 3) -> List[str]:
        self._require_connected()
        return self.sessions.load_more_history(times=times)

    def is_group_chat(self, name: Optional[str] = None) -> bool:
        self._require_connected()
        return self.sessions.is_group_chat(name)
