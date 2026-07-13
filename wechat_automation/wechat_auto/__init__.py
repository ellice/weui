"""wechat_auto —— 微信桌面版自动化工具库（Python + pywinauto）。

仅支持 Windows 平台。核心能力：
- 搜索好友 / 群聊并切入会话，发送文本 / 长文本 / 剪贴板内容；
- 通过剪贴板发送文件、图片、多文件批量发送；
- 会话列表读取、遍历、滚动加载、私聊 / 群聊区分；
- 窗口唤起 / 置顶 / 最小化，控件树导出，按钮点击；
- 键鼠模拟：慢速输入防风控、快捷键、鼠标点击 / 拖拽滚动。
"""

from .bot import WeChatBot
from .core import WeChatCore
from .exceptions import (
    ClipboardError,
    ContactNotFoundError,
    ControlNotFoundError,
    ControlTimeoutError,
    FileSendError,
    WeChatAutomationError,
    WeChatNotRunningError,
    WindowNotFoundError,
)
from .file_sender import FileSender
from .message import MessageSender
from .session import SessionManager
from .window import WindowController

__version__ = "0.1.0"

__all__ = [
    "WeChatBot",
    "WeChatCore",
    "MessageSender",
    "FileSender",
    "SessionManager",
    "WindowController",
    "WeChatAutomationError",
    "WeChatNotRunningError",
    "WindowNotFoundError",
    "ControlNotFoundError",
    "ControlTimeoutError",
    "ContactNotFoundError",
    "ClipboardError",
    "FileSendError",
]
