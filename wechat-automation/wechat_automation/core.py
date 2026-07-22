"""核心入口：:class:`WeChat` 组合全部功能混入类。"""

from __future__ import annotations

from typing import Optional

from .config import WeChatConfig
from .controls import ControlMixin
from .files import FileMixin
from .message import MessageMixin
from .session import SessionMixin


class WeChat(ControlMixin, MessageMixin, FileMixin, SessionMixin):
    """桌面版微信自动化主类。

    组合了窗口/控件通用操作、消息发送、文件发送、会话管理四大能力。

    用法::

        from wechat_automation import WeChat

        wx = WeChat()            # 连接已登录的微信
        wx.bring_to_front()
        wx.search_and_open("文件传输助手")
        wx.send_text("你好，世界！\\n这是第二行")
        wx.send_file(r"C:\\报表.xlsx")

    :param config: 可选的行为/控件配置，缺省使用默认值
    :param connect: 初始化时是否立即连接微信窗口
    """

    def __init__(self, config: Optional[WeChatConfig] = None, connect: bool = True):
        self.config = config or WeChatConfig()
        self.app = None
        self.window = None
        if connect:
            self.connect()

    def __repr__(self) -> str:  # pragma: no cover
        state = "connected" if self.is_running() else "disconnected"
        return f"<WeChat {state}>"
