"""统一的异常定义。

所有自定义异常都继承自 :class:`WeChatAutoError`，方便调用方用一个
``except WeChatAutoError`` 捕获本库抛出的全部异常。
"""

from __future__ import annotations


class WeChatAutoError(Exception):
    """本库所有异常的基类。"""


class WeChatNotRunningError(WeChatAutoError):
    """未检测到正在运行的微信主窗口。"""


class WindowNotFoundError(WeChatAutoError):
    """在超时时间内没有找到目标窗口。"""


class ControlNotFoundError(WeChatAutoError):
    """在超时时间内没有找到目标控件。"""


class ContactNotFoundError(WeChatAutoError):
    """搜索好友 / 群聊后没有命中任何结果。"""


class SendMessageError(WeChatAutoError):
    """发送消息（文本 / 文件）过程中出现错误。"""


class ClipboardError(WeChatAutoError):
    """剪贴板读写失败。"""


class OperationTimeoutError(WeChatAutoError):
    """等待某个条件成立超时。"""
