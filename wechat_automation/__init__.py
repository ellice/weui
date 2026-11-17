"""桌面版微信自动化（Windows）—— 基于 pywinauto。

模块划分对应需求五大能力：

- :mod:`wechat_automation.messaging`  一、基础消息发送（文本/群发/剪贴板）
- :mod:`wechat_automation.messaging`  二、文件/图片/媒体发送
- :mod:`wechat_automation.session`    三、会话列表管理
- :mod:`wechat_automation.window`     四、窗口与控件通用操作
- :mod:`wechat_automation.input_control`  五、键鼠模拟配套功能

统一入口为 :class:`wechat_automation.WeChat`。
"""

from .config import DEFAULT_CONFIG, WeChatConfig
from .exceptions import (
    ClipboardError,
    ContactNotFoundError,
    ControlNotFoundError,
    SendMessageError,
    WeChatAutomationError,
    WeChatWindowNotFoundError,
)
from .input_control import InputController
from .messaging import Messenger
from .session import SessionManager
from .wechat import WeChat
from .window import WeChatWindow

__version__ = "0.1.0"

__all__ = [
    "WeChat",
    "WeChatWindow",
    "Messenger",
    "SessionManager",
    "InputController",
    "WeChatConfig",
    "DEFAULT_CONFIG",
    "WeChatAutomationError",
    "WeChatWindowNotFoundError",
    "ControlNotFoundError",
    "ContactNotFoundError",
    "SendMessageError",
    "ClipboardError",
]
