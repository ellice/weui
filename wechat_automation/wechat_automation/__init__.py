"""桌面版微信自动化工具包。

技术栈：Python + pywinauto（UI Automation 后端）。仅支持 Windows 平台
运行，需登录 PC 版微信客户端。

主要能力：

1. 基础消息发送：搜索好友 / 群聊、发送文本（换行 / 特殊符号 / 空格）、
   回车发送、分段长文本、批量群发、快捷键、剪贴板粘贴发送。
2. 文件 / 图片 / 媒体发送：本地文件、图片、多文件批量粘贴发送。
3. 会话列表管理：读取全部会话、遍历切换、读取历史消息、下拉加载、
   区分私聊 / 群聊。
4. 窗口与控件通用操作：唤起 / 置顶 / 最小化、等待与超时、控件树导出、
   点击按钮、读取控件文本、清空输入 / 搜索框。
5. 键鼠模拟：精准点击 / 右键 / 双击、拖拽滚动、全局快捷键、慢速输入。

快速开始::

    from wechat_automation import WeChatAuto

    wx = WeChatAuto().connect()
    wx.send("文件传输助手", "Hello, WeChat!")
"""

from .config import WeChatConfig, DEFAULT_CONFIG
from .exceptions import (
    WeChatAutoError,
    WeChatNotRunningError,
    WindowNotFoundError,
    ControlNotFoundError,
    ContactNotFoundError,
    SendMessageError,
    ClipboardError,
    FileSendError,
)
from .window import WindowManager
from .messaging import Messenger
from .files import FileSender
from .sessions import SessionManager
from .wechat import WeChatAuto

__version__ = "0.1.0"

__all__ = [
    "WeChatAuto",
    "WeChatConfig",
    "DEFAULT_CONFIG",
    "WindowManager",
    "Messenger",
    "FileSender",
    "SessionManager",
    "WeChatAutoError",
    "WeChatNotRunningError",
    "WindowNotFoundError",
    "ControlNotFoundError",
    "ContactNotFoundError",
    "SendMessageError",
    "ClipboardError",
    "FileSendError",
]
