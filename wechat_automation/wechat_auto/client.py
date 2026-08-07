"""桌面版微信自动化统一入口 :class:`WeChatClient`。

组合窗口管理、控件操作、键鼠模拟、消息发送、文件发送、会话管理，
对外提供一个简单的门面（facade）。

典型用法::

    from wechat_auto import WeChatClient

    wx = WeChatClient()
    wx.connect()                      # 连接已登录的微信
    wx.bring_to_front()               # 唤起窗口

    wx.open_chat("文件传输助手")
    wx.send_text("你好，这是一条自动化消息")
    wx.send_file(r"D:\\report.pdf")

    wx.batch_send_text(["张三", "李四"], "群发通知：今晚 8 点开会")
"""

from __future__ import annotations

from typing import Dict, Iterable, List, Optional

from .config import WeChatConfig
from .controls import ControlHelper
from .files import FileSender
from .inputs import InputController
from .messaging import MessageSender
from .sessions import SessionManager
from .window import WindowManager


class WeChatClient:
    """桌面版微信自动化门面类。"""

    def __init__(self, config: Optional[WeChatConfig] = None) -> None:
        self.config = config or WeChatConfig()
        self.window_manager = WindowManager(self.config)
        # 以下模块在 connect() 后初始化（依赖主窗口对象）
        self.controls: Optional[ControlHelper] = None
        self.inputs: InputController = InputController(
            type_interval=self.config.type_interval,
            action_delay=self.config.action_delay,
        )
        self.messaging: Optional[MessageSender] = None
        self.files: Optional[FileSender] = None
        self.sessions: Optional[SessionManager] = None

    # ------------------------------------------------------------------ #
    # 连接 / 窗口
    # ------------------------------------------------------------------ #
    def connect(self, start_if_not_running: bool = False) -> "WeChatClient":
        """连接（可选启动）微信并初始化各功能模块。"""
        window = self.window_manager.connect(start_if_not_running=start_if_not_running)
        self._init_modules(window)
        return self

    def start(self) -> "WeChatClient":
        """启动微信并初始化各功能模块。"""
        window = self.window_manager.start()
        self._init_modules(window)
        return self

    def _init_modules(self, window) -> None:
        self.window = window
        self.controls = ControlHelper(window, self.config)
        self.messaging = MessageSender(window, self.controls, self.inputs, self.config)
        self.files = FileSender(window, self.controls, self.inputs, self.config)
        self.sessions = SessionManager(window, self.controls, self.inputs, self.config)

    def bring_to_front(self):
        return self.window_manager.bring_to_front()

    def minimize(self):
        return self.window_manager.minimize()

    def restore(self):
        return self.window_manager.restore()

    def maximize(self):
        return self.window_manager.maximize()

    def set_topmost(self, topmost: bool = True):
        return self.window_manager.set_topmost(topmost)

    # ------------------------------------------------------------------ #
    # 消息（第一类）
    # ------------------------------------------------------------------ #
    def open_chat(self, keyword: str) -> "WeChatClient":
        """搜索并进入指定好友 / 群聊。"""
        self._require_connected()
        self.messaging.search_and_open(keyword)
        return self

    def send_text(self, text: str, use_clipboard: bool = True) -> None:
        self._require_connected()
        self.messaging.send_text(text, use_clipboard=use_clipboard)

    def send_text_slowly(self, text: str, interval: Optional[float] = None) -> None:
        self._require_connected()
        self.messaging.send_text_slowly(text, interval=interval)

    def send_long_text(self, text: str, max_chars: int = 1000) -> int:
        self._require_connected()
        return self.messaging.send_long_text(text, max_chars=max_chars)

    def batch_send_text(
        self,
        contacts: Iterable[str],
        text: str,
        interval: Optional[float] = None,
    ) -> Dict[str, bool]:
        self._require_connected()
        return self.messaging.batch_send_text(contacts, text, interval=interval)

    def mention(self, name: str) -> None:
        self._require_connected()
        self.messaging.mention(name)

    def paste_and_send(self, text: str) -> None:
        self._require_connected()
        self.messaging.paste_and_send(text)

    # ------------------------------------------------------------------ #
    # 文件 / 图片（第二类）
    # ------------------------------------------------------------------ #
    def send_file(self, path: str, caption: Optional[str] = None) -> None:
        self._require_connected()
        self.files.send_file(path, caption=caption)

    def send_image(self, path: str, caption: Optional[str] = None) -> None:
        self._require_connected()
        self.files.send_image(path, caption=caption)

    def send_files(self, paths: Iterable[str], caption: Optional[str] = None) -> List[str]:
        self._require_connected()
        return self.files.send_files(paths, caption=caption)

    # ------------------------------------------------------------------ #
    # 会话列表（第三类）
    # ------------------------------------------------------------------ #
    def list_sessions(self) -> List[str]:
        self._require_connected()
        return self.sessions.list_sessions()

    def open_session(self, name: str) -> bool:
        self._require_connected()
        return self.sessions.open_session(name)

    def get_current_messages(self) -> List[str]:
        self._require_connected()
        return self.sessions.get_current_messages()

    def scroll_messages(self, up: bool = True, amount: int = 3) -> None:
        self._require_connected()
        self.sessions.scroll_messages(up=up, amount=amount)

    def is_group_chat(self, name: str) -> bool:
        self._require_connected()
        return self.sessions.is_group_chat(name)

    # ------------------------------------------------------------------ #
    # 控件通用操作（第四类）
    # ------------------------------------------------------------------ #
    def click_button(self, title: str):
        self._require_connected()
        return self.controls.click_button(title)

    def button_exists(self, title: str) -> bool:
        self._require_connected()
        return self.controls.button_exists(title)

    def get_control_text(self, **criteria) -> str:
        self._require_connected()
        return self.controls.get_text(**criteria)

    def clear_input(self) -> None:
        """清空底部消息输入框。"""
        self._require_connected()
        self.controls.clear_edit(
            title=self.config.input_edit_title, control_type="Edit"
        )

    def clear_search(self) -> None:
        """清空顶部搜索框。"""
        self._require_connected()
        self.controls.clear_edit(
            title=self.config.search_box_title, control_type="Edit"
        )

    def dump_control_tree(self, depth: Optional[int] = None, filename: Optional[str] = None) -> str:
        self._require_connected()
        return self.controls.dump_control_tree(depth=depth, filename=filename)

    # ------------------------------------------------------------------ #
    # 内部
    # ------------------------------------------------------------------ #
    def _require_connected(self) -> None:
        if self.controls is None:
            raise RuntimeError("请先调用 connect() 或 start() 连接微信。")
