"""桌面版微信自动化工具包。

基于 Python + pywinauto (UIA 后端) 实现，覆盖：

* 基础消息发送（搜索好友/群、文本、批量群发、快捷键、剪贴板粘贴）
* 文件/图片/媒体发送（剪贴板路径 + Ctrl+V）
* 会话列表管理（读取、遍历、切换、滚动加载、私聊/群聊区分）
* 窗口与控件通用操作（唤起、置顶、最小化/还原、控件树导出）
* 键鼠模拟配套（点击、拖拽滚动、快捷键、慢速输入防风控）

仅支持在 Windows 平台上运行。
"""

from .config import WeChatConfig
from .exceptions import (
    WeChatAutomationError,
    WeChatNotFoundError,
    ContactNotFoundError,
    ControlNotFoundError,
    WeChatTimeoutError,
)
from .core import WeChat
from .models import SessionItem, SessionType

__all__ = [
    "WeChat",
    "WeChatConfig",
    "SessionItem",
    "SessionType",
    "WeChatAutomationError",
    "WeChatNotFoundError",
    "ContactNotFoundError",
    "ControlNotFoundError",
    "WeChatTimeoutError",
]

__version__ = "0.1.0"
