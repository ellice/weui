"""桌面版微信自动化工具（Python + pywinauto）。

对外暴露主入口 :class:`WeChatBot` 以及常用的配置、异常类型。

仅支持 Windows 平台上的 PC 版微信（WeChat.exe）。
"""

from .config import WeChatConfig
from .exceptions import (
    WeChatAutomationError,
    WeChatNotRunningError,
    ControlNotFoundError,
    ContactNotFoundError,
    TimeoutError as WeChatTimeoutError,
)
from .bot import WeChatBot

__all__ = [
    "WeChatBot",
    "WeChatConfig",
    "WeChatAutomationError",
    "WeChatNotRunningError",
    "ControlNotFoundError",
    "ContactNotFoundError",
    "WeChatTimeoutError",
]

__version__ = "0.1.0"
