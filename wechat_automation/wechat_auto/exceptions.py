"""统一异常定义。

集中管理自动化过程中可能抛出的异常，方便调用方按需捕获与降级处理。
"""

from __future__ import annotations


class WeChatAutomationError(Exception):
    """所有微信自动化异常的基类。"""


class WindowNotFoundError(WeChatAutomationError):
    """未找到微信主窗口（未启动 / 未登录 / 标题不匹配）。"""


class ControlNotFoundError(WeChatAutomationError):
    """在超时时间内未定位到目标控件。"""


class ContactNotFoundError(WeChatAutomationError):
    """按备注 / 昵称搜索联系人或群聊失败。"""


class TimeoutError(WeChatAutomationError):
    """等待控件加载或状态满足条件超时。

    刻意与内建 ``TimeoutError`` 同名但独立，便于统一从
    :class:`WeChatAutomationError` 捕获。
    """


class ClipboardError(WeChatAutomationError):
    """剪贴板读写失败（如文件不存在、图片格式不支持）。"""
