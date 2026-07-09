"""统一异常定义。

所有对外抛出的自定义异常都继承自 :class:`WeChatAutoError`，
方便调用方使用 ``except WeChatAutoError`` 一次性捕获本库的全部异常。
"""

from __future__ import annotations


class WeChatAutoError(Exception):
    """本库所有自定义异常的基类。"""


class WeChatNotRunningError(WeChatAutoError):
    """未检测到正在运行的微信主窗口。"""


class WindowNotFoundError(WeChatAutoError):
    """在超时时间内没有找到目标窗口。"""


class ControlNotFoundError(WeChatAutoError):
    """在超时时间内没有找到目标控件。"""


class ContactNotFoundError(WeChatAutoError):
    """搜索联系人 / 群聊后没有命中任何结果。"""


class TimeoutError(WeChatAutoError):
    """等待某个条件成立超时。"""


class ClipboardError(WeChatAutoError):
    """读写系统剪贴板失败。"""


class SendMessageError(WeChatAutoError):
    """发送消息过程中出现异常。"""
