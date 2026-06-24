"""桌面版微信自动化工具包。

技术栈：Python + pywinauto（仅支持 Windows）。

主入口为 :class:`WeChatAuto`，聚合了消息发送、文件发送、会话管理、
窗口/控件操作、键鼠模拟等能力。

示例::

    from wechat_auto import WeChatAuto

    wx = WeChatAuto()
    wx.activate()                       # 唤起并置顶微信窗口
    wx.send_text("文件传输助手", "你好，世界！")
    wx.send_files("张三", [r"C:\\report.pdf"])
"""

from .core import WeChatAuto
from .exceptions import (
    WeChatAutoError,
    WeChatNotFoundError,
    ControlNotFoundError,
    SessionNotFoundError,
    OperationTimeoutError,
)

__all__ = [
    "WeChatAuto",
    "WeChatAutoError",
    "WeChatNotFoundError",
    "ControlNotFoundError",
    "SessionNotFoundError",
    "OperationTimeoutError",
]

__version__ = "0.1.0"
