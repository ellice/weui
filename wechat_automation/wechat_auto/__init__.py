"""桌面版微信自动化（Python + pywinauto）。

提供基础消息发送、文件 / 图片发送、会话列表管理、窗口与控件通用操作、
键鼠模拟等能力。仅支持 Windows 平台运行。

推荐从门面类 :class:`WeChatClient` 开始使用。
"""

from .client import WeChatClient
from .config import WeChatConfig
from .controls import ControlHelper
from .exceptions import (
    ClipboardError,
    ContactNotFoundError,
    ControlNotFoundError,
    PlatformNotSupportedError,
    SendMessageError,
    WeChatAutomationError,
    WeChatNotRunningError,
    WindowNotFoundError,
)
from .files import FileSender
from .inputs import InputController
from .messaging import MessageSender
from .sessions import SessionManager
from .window import WindowManager

__version__ = "0.1.0"

__all__ = [
    "WeChatClient",
    "WeChatConfig",
    "ControlHelper",
    "FileSender",
    "InputController",
    "MessageSender",
    "SessionManager",
    "WindowManager",
    "WeChatAutomationError",
    "WeChatNotRunningError",
    "WindowNotFoundError",
    "ControlNotFoundError",
    "ContactNotFoundError",
    "ClipboardError",
    "SendMessageError",
    "PlatformNotSupportedError",
]
