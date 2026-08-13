"""统一的异常定义。

自动化过程中所有可预期的失败都尽量抛出这里的异常，方便调用方
用 ``try/except WeChatAutoError`` 做统一捕获与重试。
"""

from __future__ import annotations


class WeChatAutoError(Exception):
    """所有微信自动化异常的基类。"""


class WeChatNotRunningError(WeChatAutoError):
    """未找到正在运行的微信主窗口。"""


class ControlNotFoundError(WeChatAutoError):
    """在超时时间内没有定位到目标控件。"""


class ControlTimeoutError(WeChatAutoError):
    """等待控件出现 / 就绪超时。"""


class ContactNotFoundError(WeChatAutoError):
    """搜索后没有匹配到对应的好友或群聊。"""


class SendMessageError(WeChatAutoError):
    """消息 / 文件发送过程中出现异常。"""


class ClipboardError(WeChatAutoError):
    """剪贴板读写失败（文本或文件）。"""
