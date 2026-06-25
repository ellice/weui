# -*- coding: utf-8 -*-
"""wechat_auto —— 微信桌面版自动化工具包。

技术栈：Python + pywinauto（uia 后端）。

主要能力：
- 基础消息发送（搜索切入、文本、换行/特殊符号、回车发送、分段、批量群发、@/表情/快捷键、剪贴板）
- 文件 / 图片 / 媒体发送（剪贴板 CF_HDROP + Ctrl+V）
- 会话列表管理（读取、遍历切换、读取聊天记录、滚动加载、私聊/群聊区分）
- 窗口与控件通用操作（唤起/置顶/最小化、等待/超时/异常、控件树导出、点击按钮、清空输入）
- 键鼠模拟（点击/右键/双击/拖拽滚动、全局快捷键、真人慢速输入防风控）
"""

from . import clipboard, inputs
from .core import WeChat
from .exceptions import (
    ClipboardError,
    ContactNotFoundError,
    ControlNotFoundError,
    ControlTimeoutError,
    FileSendError,
    WeChatAutoError,
    WeChatNotRunningError,
    WindowNotFoundError,
)

__version__ = "0.1.0"

__all__ = [
    "WeChat",
    "clipboard",
    "inputs",
    "WeChatAutoError",
    "WeChatNotRunningError",
    "WindowNotFoundError",
    "ControlNotFoundError",
    "ControlTimeoutError",
    "ContactNotFoundError",
    "ClipboardError",
    "FileSendError",
]
