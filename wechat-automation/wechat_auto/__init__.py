"""wechat_auto —— 桌面版微信自动化 (Python + pywinauto)

仅支持 Windows。请先登录微信 PC 客户端，再运行脚本。

快速上手：
    from wechat_auto import WeChatAuto, MessageSender, FileSender, SessionManager

    wx = WeChatAuto()                 # 连接已运行的微信
    wx.bring_to_front()               # 唤起并置顶

    msg = MessageSender(wx)
    wx.search_and_open("文件传输助手")
    msg.send_text("你好，世界！\n这是第二行")          # 支持换行/空格/特殊符号
    msg.broadcast(["张三", "李四"], "群发通知")          # 批量群发

    files = FileSender(wx)
    files.send_file(r"C:\\report.pdf")                # 文件粘贴发送
    files.send_image(r"C:\\screenshot.png")           # 图片粘贴发送

    sm = SessionManager(wx)
    print(sm.list_sessions())                          # 读取会话列表
    print(sm.get_chat_messages())                      # 读取历史消息
"""

from .core import WeChatAuto
from .message import MessageSender
from .files import FileSender
from .session import SessionManager
from . import clipboard, controls, input_utils, exceptions
from .exceptions import (
    WeChatAutoError,
    WeChatNotRunningError,
    WindowNotFoundError,
    ControlNotFoundError,
    WaitTimeoutError,
    ContactNotFoundError,
    ClipboardError,
    PlatformError,
)

__version__ = "0.1.0"

__all__ = [
    "WeChatAuto",
    "MessageSender",
    "FileSender",
    "SessionManager",
    "clipboard",
    "controls",
    "input_utils",
    "exceptions",
    "WeChatAutoError",
    "WeChatNotRunningError",
    "WindowNotFoundError",
    "ControlNotFoundError",
    "WaitTimeoutError",
    "ContactNotFoundError",
    "ClipboardError",
    "PlatformError",
    "__version__",
]
