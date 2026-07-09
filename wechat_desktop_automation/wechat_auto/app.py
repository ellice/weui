"""顶层门面类 :class:`WeChatAuto`。

把窗口管理、键鼠模拟、导航、消息、文件、会话六大模块组装为一个统一入口，
既提供子模块访问（``wx.window`` / ``wx.messenger`` ...），也把最常用的方法
直接代理到门面对象上，方便快速调用。

典型用法::

    from wechat_auto import WeChatAuto

    wx = WeChatAuto().connect()
    wx.send_text("你好，在吗？", to="张三")
    wx.send_files([r"C:\\报表.xlsx"], to="工作群")
    print(wx.list_sessions())
"""

from __future__ import annotations

from typing import Dict, List, Optional, Sequence

from .config import Config
from .files import FileSender
from .inputs import InputSimulator
from .logger import get_logger
from .messaging import Messenger
from .navigation import Navigator
from .sessions import SessionManager
from .window import WindowManager

log = get_logger("app")


class WeChatAuto:
    """桌面版微信自动化统一入口。

    :param config: 可选的运行期配置；不传使用默认值。
    """

    def __init__(self, config: Optional[Config] = None) -> None:
        self.config = config or Config()
        self.window = WindowManager(self.config)
        self.inputs = InputSimulator(self.config)
        self.navigator = Navigator(self.window)
        self.messenger = Messenger(self.window, self.navigator, self.inputs)
        self.files = FileSender(self.window, self.navigator, self.inputs)
        self.sessions = SessionManager(self.window, self.navigator, self.inputs)

    # ------------------------------------------------------------------ #
    # 连接 / 窗口
    # ------------------------------------------------------------------ #
    def connect(self, timeout: Optional[float] = None) -> "WeChatAuto":
        """连接正在运行的微信主窗口，返回自身以支持链式调用。"""
        self.window.connect(timeout=timeout)
        return self

    def activate(self) -> None:
        """唤起并置顶微信窗口。"""
        self.window.activate()

    def minimize(self) -> None:
        self.window.minimize()

    def restore(self) -> None:
        self.window.restore()

    def is_running(self) -> bool:
        return self.window.is_running()

    def dump_control_tree(self, depth: Optional[int] = None, to_file: Optional[str] = None) -> str:
        """导出控件树用于调试。"""
        return self.window.dump_control_tree(depth=depth, to_file=to_file)

    # ------------------------------------------------------------------ #
    # 导航
    # ------------------------------------------------------------------ #
    def open_chat(self, keyword: str, exact: bool = True) -> str:
        """搜索并切入某个联系人 / 群聊。"""
        return self.navigator.search_and_open(keyword, exact=exact)

    def current_chat_title(self) -> Optional[str]:
        return self.navigator.current_chat_title()

    # ------------------------------------------------------------------ #
    # 消息（第一类）
    # ------------------------------------------------------------------ #
    def send_text(
        self,
        text: str,
        to: Optional[str] = None,
        use_paste: bool = True,
        human_like: bool = False,
    ) -> None:
        """发送文本消息。"""
        self.messenger.send_text(text, to=to, use_paste=use_paste, human_like=human_like)

    def send_long_text(self, text: str, to: Optional[str] = None, max_len: int = 2000) -> int:
        """分段发送长文本。"""
        return self.messenger.send_long_text(text, to=to, max_len=max_len)

    def broadcast_text(
        self, text: str, contacts: Sequence[str], interval: Optional[float] = None
    ) -> Dict[str, bool]:
        """批量群发文本。"""
        return self.messenger.broadcast_text(text, contacts, interval=interval)

    def mention(self, member: str, to: Optional[str] = None) -> None:
        """群聊中 @ 某位成员。"""
        self.messenger.mention(member, to=to)

    # ------------------------------------------------------------------ #
    # 文件（第二类）
    # ------------------------------------------------------------------ #
    def send_files(
        self, paths: Sequence[str] | str, to: Optional[str] = None, send_together: bool = True
    ) -> List[str]:
        """粘贴发送文件 / 图片（支持多文件）。"""
        return self.files.send_files(paths, to=to, send_together=send_together)

    def send_image(self, path: str, to: Optional[str] = None) -> List[str]:
        """发送单张图片。"""
        return self.files.send_image(path, to=to)

    # ------------------------------------------------------------------ #
    # 会话（第三类）
    # ------------------------------------------------------------------ #
    def list_sessions(self) -> List[str]:
        """读取当前可见的会话名称。"""
        return self.sessions.list_sessions()

    def list_all_sessions(self, max_scroll: int = 20) -> List[str]:
        """滚动读取尽可能多的会话名称。"""
        return self.sessions.list_all_sessions(max_scroll=max_scroll)

    def switch_to(self, name: str) -> bool:
        """点击切换到某个会话。"""
        return self.sessions.switch_to(name)

    def get_chat_history_text(self) -> List[str]:
        """读取当前聊天窗口的历史消息文本。"""
        return self.sessions.get_chat_history_text()

    def is_group_chat(self, name: Optional[str] = None) -> bool:
        """判断是否群聊。"""
        return self.sessions.is_group_chat(name)
