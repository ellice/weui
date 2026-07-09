"""桌面版微信自动化库（Python + pywinauto）。

对外主要入口是 :class:`~wechat_auto.app.WeChatAuto`。

示例::

    from wechat_auto import WeChatAuto

    wx = WeChatAuto().connect()
    wx.send_text("你好", to="文件传输助手")

仅支持 Windows 平台（依赖 pywinauto / pywin32）。
"""

from __future__ import annotations

from .app import WeChatAuto
from .config import Config
from .exceptions import (
    ClipboardError,
    ContactNotFoundError,
    ControlNotFoundError,
    SendMessageError,
    TimeoutError,
    WeChatAutoError,
    WeChatNotRunningError,
    WindowNotFoundError,
)
from .inputs import InputSimulator
from .logger import get_logger, set_level

__all__ = [
    "WeChatAuto",
    "Config",
    "InputSimulator",
    "get_logger",
    "set_level",
    "WeChatAutoError",
    "WeChatNotRunningError",
    "WindowNotFoundError",
    "ControlNotFoundError",
    "ContactNotFoundError",
    "TimeoutError",
    "ClipboardError",
    "SendMessageError",
]

__version__ = "0.1.0"
