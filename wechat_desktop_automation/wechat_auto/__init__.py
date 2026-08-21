"""桌面版微信自动化工具包。

技术栈：Python + pywinauto（UIAutomation 后端）。

仅支持 Windows 平台运行，需要本机已登录微信 PC 客户端。

模块划分：
    core        窗口与控件通用操作（唤起 / 置顶 / 最小化 / 控件树 / 等待）
    messaging   基础消息发送能力（搜索、文本、快捷键、剪贴板、群发）
    files       文件 / 图片 / 媒体发送（剪贴板路径 + Ctrl+V）
    sessions    会话列表管理（读取、切换、历史、滚动、私聊/群聊区分）
    inputsim    键鼠模拟配套（点击、拖拽、快捷键、慢速输入）
    controls    控件通用工具（控件树、查找、文本、存在性判断）
    utils       剪贴板 / 重试 / 异常等基础工具

快速上手::

    from wechat_auto import WeChat

    wx = WeChat()          # 连接已登录的微信窗口
    wx.send_text("文件传输助手", "你好，世界！\\n这是第二行")
    wx.send_files("文件传输助手", [r"C:\\报表.xlsx", r"C:\\图片.png"])
"""

from .core import WeChatWindow
from .messaging import Messaging
from .files import FileSender
from .sessions import SessionManager
from .inputsim import InputSimulator
from .controls import ControlHelper
from .exceptions import (
    WeChatAutomationError,
    WeChatNotFoundError,
    ContactNotFoundError,
    ControlNotFoundError,
    OperationTimeout,
)
from .facade import WeChat

__all__ = [
    "WeChat",
    "WeChatWindow",
    "Messaging",
    "FileSender",
    "SessionManager",
    "InputSimulator",
    "ControlHelper",
    "WeChatAutomationError",
    "WeChatNotFoundError",
    "ContactNotFoundError",
    "ControlNotFoundError",
    "OperationTimeout",
]

__version__ = "0.1.0"
