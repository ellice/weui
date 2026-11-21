"""桌面微信自动化主入口 :class:`WeChatBot`。

将窗口控制、键鼠模拟、消息发送、文件发送、会话管理组合为统一门面，
业务侧只需与本类交互即可覆盖五大类能力。

典型用法::

    from wechat_automation import WeChatBot

    bot = WeChatBot().connect()
    bot.open_chat("文件传输助手")
    bot.send_text("你好，WeChat 自动化！\\n支持换行与特殊符号 @#￥%")
    bot.send_file(r"C:\\reports\\周报.xlsx")
    print(bot.sessions.list_sessions())
"""

from typing import Dict, Iterable, List, Optional

from .config import WeChatConfig
from .core.input_device import InputDevice
from .core.window import WindowController
from .features.media import MediaSender
from .features.message import MessageSender
from .features.session import SessionManager


class WeChatBot:
    def __init__(self, config: Optional[WeChatConfig] = None, **overrides):
        base = config or WeChatConfig()
        self.config = base.with_overrides(**overrides) if overrides else base

        self.window = WindowController(self.config)
        self.device = InputDevice(self.config)
        self.messages = MessageSender(self.window, self.device, self.config)
        self.media = MediaSender(self.window, self.device, self.config)
        self.sessions = SessionManager(self.window, self.device, self.config)

    # ------------------------------------------------------------------
    # 连接 / 窗口
    # ------------------------------------------------------------------
    def connect(self, launch_path: Optional[str] = None) -> "WeChatBot":
        """连接（或拉起）微信并聚焦主窗口。"""
        self.window.connect(launch_path=launch_path)
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

    def dump_control_tree(self, to_file: Optional[str] = None) -> str:
        """导出主窗口控件树，便于调试定位。"""
        return self.window.dump_control_tree(to_file=to_file)

    # ------------------------------------------------------------------
    # 消息（委托 MessageSender）
    # ------------------------------------------------------------------
    def open_chat(self, keyword: str) -> None:
        self.messages.open_chat(keyword)

    def send_text(self, text: str, via_clipboard: bool = True, humanize: bool = True) -> None:
        self.messages.send_text(text, via_clipboard=via_clipboard, humanize=humanize)

    def send_segments(self, segments: Iterable[str], interval: float = 0.8) -> None:
        self.messages.send_segments(segments, interval=interval)

    def broadcast(
        self, contacts: Iterable[str], text: str, interval: float = 1.5
    ) -> Dict[str, bool]:
        return self.messages.broadcast(contacts, text, interval=interval)

    def mention(self, name: str) -> None:
        self.messages.mention(name)

    # ------------------------------------------------------------------
    # 文件 / 媒体（委托 MediaSender）
    # ------------------------------------------------------------------
    def send_file(self, path: str, send: bool = True) -> List[str]:
        return self.media.send_file(path, send=send)

    def send_files(self, paths: Iterable[str], send: bool = True) -> List[str]:
        return self.media.send_files(paths, send=send)

    def send_images(self, paths: Iterable[str], send: bool = True) -> List[str]:
        return self.media.send_images(paths, send=send)

    # ------------------------------------------------------------------
    # 会话（委托 SessionManager）
    # ------------------------------------------------------------------
    def list_sessions(self) -> List[str]:
        return self.sessions.list_sessions()

    def read_messages(self) -> List[str]:
        return self.sessions.read_messages()
