"""统一异常定义。

所有自定义异常均继承自 :class:`WeChatError`，方便调用方统一捕获。
"""


class WeChatError(Exception):
    """微信自动化基础异常，所有异常的父类。"""


class WeChatNotFoundError(WeChatError):
    """未找到微信进程或主窗口。"""


class ContactNotFoundError(WeChatError):
    """按备注 / 昵称搜索不到对应的好友或群聊。"""


class ControlNotFoundError(WeChatError):
    """在窗口中未找到期望的控件。"""


class ControlTimeoutError(WeChatError):
    """等待控件加载超时。"""
