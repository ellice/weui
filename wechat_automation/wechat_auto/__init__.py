"""桌面版微信自动化（Windows / pywinauto）。

五大能力模块：
- message  基础消息发送
- media    文件 / 图片 / 媒体发送
- session  会话列表管理
- base     窗口与控件通用操作
- input_sim 键鼠模拟配套

入口类：``WeChat``。
"""

from .wechat import WeChat
from .base import WeChatBase
from .input_sim import InputSimulator
from .message import MessageSender
from .media import MediaSender
from .session import SessionManager
from . import clipboard, exceptions, utils
from .exceptions import (
    WeChatAutomationError,
    WeChatNotRunningError,
    WindowNotFoundError,
    ControlNotFoundError,
    ControlTimeoutError,
    ContactNotFoundError,
    ClipboardError,
    SendMessageError,
)

__version__ = "0.1.0"

__all__ = [
    "WeChat",
    "WeChatBase",
    "InputSimulator",
    "MessageSender",
    "MediaSender",
    "SessionManager",
    "clipboard",
    "exceptions",
    "utils",
    "WeChatAutomationError",
    "WeChatNotRunningError",
    "WindowNotFoundError",
    "ControlNotFoundError",
    "ControlTimeoutError",
    "ContactNotFoundError",
    "ClipboardError",
    "SendMessageError",
]
