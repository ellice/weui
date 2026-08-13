"""wechat_auto —— 桌面版微信自动化工具（Python + pywinauto）。

仅支持 Windows 平台的 PC 版微信。核心能力：
- 基础消息发送（搜索切入、文本、批量群发、快捷键、剪贴板）
- 文件/图片/媒体发送（剪贴板路径 + Ctrl+V）
- 会话列表管理（读取、遍历、滚动、私聊/群聊区分、历史消息读取）
- 窗口与控件通用操作（唤起/置顶/最小化、控件树导出、按钮点击）
- 键鼠模拟配套（点击/右键/双击/拖拽、组合键、慢速输入防风控）
"""

from __future__ import annotations

from .client import WeChatAuto
from .config import (
    WeChatConfig,
    Timing,
    WindowSpec,
    ControlNames,
    DEFAULT_CONFIG,
)
from .session import SessionItem, SessionManager
from .chat import ChatManager
from .window import WindowManager
from .exceptions import (
    WeChatAutoError,
    WeChatNotRunningError,
    ControlNotFoundError,
    ControlTimeoutError,
    ContactNotFoundError,
    SendMessageError,
    ClipboardError,
)
from . import input_sim, clipboard

__version__ = "0.1.0"

__all__ = [
    "WeChatAuto",
    "WeChatConfig",
    "Timing",
    "WindowSpec",
    "ControlNames",
    "DEFAULT_CONFIG",
    "SessionItem",
    "SessionManager",
    "ChatManager",
    "WindowManager",
    "WeChatAutoError",
    "WeChatNotRunningError",
    "ControlNotFoundError",
    "ControlTimeoutError",
    "ContactNotFoundError",
    "SendMessageError",
    "ClipboardError",
    "input_sim",
    "clipboard",
    "__version__",
]
