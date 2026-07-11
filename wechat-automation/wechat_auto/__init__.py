"""桌面版微信自动化工具包。

技术栈：Python + pywinauto（UIA 后端），仅支持 Windows 平台。

主要模块：
    - :mod:`wechat_auto.exceptions`  统一异常定义
    - :mod:`wechat_auto.clipboard`   剪贴板文本 / 文件 / 图片操作
    - :mod:`wechat_auto.inputs`      键盘、鼠标模拟
    - :mod:`wechat_auto.window`      窗口与控件通用操作
    - :mod:`wechat_auto.messaging`   基础消息发送能力
    - :mod:`wechat_auto.files`       文件、图片、媒体发送
    - :mod:`wechat_auto.sessions`    会话列表管理
    - :mod:`wechat_auto.wechat`      对外统一入口 :class:`WeChat`

快速开始::

    from wechat_auto import WeChat

    wx = WeChat()                 # 自动连接 / 唤起微信
    wx.send_text("文件传输助手", "你好，世界！")
    wx.send_file("文件传输助手", r"D:\\report.xlsx")
"""

from .exceptions import (
    WeChatError,
    WeChatNotFoundError,
    ContactNotFoundError,
    ControlNotFoundError,
    ControlTimeoutError,
)
from .wechat import WeChat

__all__ = [
    "WeChat",
    "WeChatError",
    "WeChatNotFoundError",
    "ContactNotFoundError",
    "ControlNotFoundError",
    "ControlTimeoutError",
]

__version__ = "0.1.0"
