# -*- coding: utf-8 -*-
"""自定义异常体系。

所有异常都继承自 :class:`WeChatAutoError`，方便上层调用方做统一捕获。
"""


class WeChatAutoError(Exception):
    """微信自动化基础异常。"""


class WeChatNotRunningError(WeChatAutoError):
    """微信进程 / 主窗口未找到。"""


class WindowNotFoundError(WeChatAutoError):
    """目标窗口未找到。"""


class ControlNotFoundError(WeChatAutoError):
    """目标控件未找到。"""


class ControlTimeoutError(WeChatAutoError):
    """等待控件出现 / 就绪超时。"""


class ContactNotFoundError(WeChatAutoError):
    """搜索不到对应的好友 / 群聊。"""


class ClipboardError(WeChatAutoError):
    """剪贴板读写失败。"""


class FileSendError(WeChatAutoError):
    """文件发送相关失败（路径不存在、复制失败等）。"""
