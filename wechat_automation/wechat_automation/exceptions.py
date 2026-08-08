"""统一异常定义。

所有对外抛出的异常都继承自 :class:`WeChatAutomationError`，方便调用方
用一个 ``except`` 兜住全部自动化相关错误。
"""

from __future__ import annotations


class WeChatAutomationError(Exception):
    """微信自动化基础异常。"""


class DependencyMissingError(WeChatAutomationError):
    """缺少运行依赖（如非 Windows 平台没有 ``pywinauto``）。"""


class WindowNotFoundError(WeChatAutomationError):
    """未找到微信主窗口（未启动或未登录）。"""


class NotConnectedError(WeChatAutomationError):
    """尚未调用 :meth:`WeChat.connect` 就使用了需要窗口句柄的能力。"""


class ControlNotFoundError(WeChatAutomationError):
    """在超时时间内未定位到目标控件。"""


class ContactNotFoundError(WeChatAutomationError):
    """搜索不到指定备注/昵称的好友或群聊。"""


class TimeoutError(WeChatAutomationError):  # noqa: A001 - 语义上确实是超时
    """等待控件加载超时。"""
