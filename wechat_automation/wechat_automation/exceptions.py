"""自定义异常体系。

将所有自动化过程中可能出现的错误归类，便于上层统一捕获与处理。
"""

from __future__ import annotations


class WeChatAutomationError(Exception):
    """所有微信自动化异常的基类。"""


class WeChatNotRunningError(WeChatAutomationError):
    """未检测到正在运行的微信主窗口。"""


class WindowNotFoundError(WeChatAutomationError):
    """目标窗口未找到。"""


class ControlNotFoundError(WeChatAutomationError):
    """目标控件未找到。"""


class TimeoutError(WeChatAutomationError):  # noqa: A001 - 故意覆盖内置名，限定命名空间内
    """等待控件/状态超时。"""


class ContactNotFoundError(WeChatAutomationError):
    """搜索不到指定的好友或群聊。"""


class ClipboardError(WeChatAutomationError):
    """剪贴板读写失败。"""


class FileSendError(WeChatAutomationError):
    """文件/图片发送失败。"""


class DependencyNotInstalledError(WeChatAutomationError):
    """缺少运行所需的依赖（pywinauto / pywin32 等）。"""
