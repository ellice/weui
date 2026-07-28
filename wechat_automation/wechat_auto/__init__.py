"""wechat_auto —— 基于 pywinauto 的桌面版微信自动化工具库。

快速开始::

    from wechat_auto import WeChatAuto

    wx = WeChatAuto()
    wx.connect()                       # 连接已登录的微信桌面版
    wx.send_text("文件传输助手", "Hello, 微信自动化!")
    wx.send_file("文件传输助手", r"C:\\report.xlsx")
    wx.broadcast(["张三", "李四"], "群发通知")

模块划分：

* :mod:`wechat_auto.core` —— 窗口连接、状态管理、控件调试
* :mod:`wechat_auto.messaging` —— 文本消息、搜索切换、批量群发
* :mod:`wechat_auto.files` —— 文件 / 图片 / 媒体发送
* :mod:`wechat_auto.sessions` —— 会话列表、历史消息读取
* :mod:`wechat_auto.inputs` —— 键鼠模拟
* :mod:`wechat_auto.clipboard` —— 剪贴板读写

注意：pywinauto 仅支持 Windows，本库需在 Windows 上运行。
"""

from __future__ import annotations

from .core import WeChatAuto
from .exceptions import (
    ClipboardError,
    ContactNotFoundError,
    ControlNotFoundError,
    OperationTimeoutError,
    SendMessageError,
    WeChatAutoError,
    WeChatNotRunningError,
    WindowNotFoundError,
)
from .files import FileSender
from .inputs import InputController
from .messaging import MessageSender
from .sessions import SessionManager

__version__ = "0.1.0"

__all__ = [
    "WeChatAuto",
    "MessageSender",
    "FileSender",
    "SessionManager",
    "InputController",
    "WeChatAutoError",
    "WeChatNotRunningError",
    "WindowNotFoundError",
    "ControlNotFoundError",
    "ContactNotFoundError",
    "SendMessageError",
    "ClipboardError",
    "OperationTimeoutError",
]
