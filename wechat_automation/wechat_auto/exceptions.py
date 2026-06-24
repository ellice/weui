"""自定义异常类型。"""


class WeChatAutoError(Exception):
    """所有微信自动化异常的基类。"""


class WeChatNotFoundError(WeChatAutoError):
    """未找到微信主窗口 / 进程时抛出。"""


class ControlNotFoundError(WeChatAutoError):
    """在超时时间内未能定位到目标控件时抛出。"""


class SessionNotFoundError(WeChatAutoError):
    """在会话列表中找不到指定会话时抛出。"""


class OperationTimeoutError(WeChatAutoError):
    """等待某个条件超时时抛出。"""
