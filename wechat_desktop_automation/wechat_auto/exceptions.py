"""自动化过程中使用的异常类型。"""


class WeChatAutomationError(Exception):
    """所有微信自动化异常的基类。"""


class WeChatNotFoundError(WeChatAutomationError):
    """未找到运行中的微信主窗口（未启动或未登录）。"""


class ContactNotFoundError(WeChatAutomationError):
    """搜索后未能定位到目标好友 / 群聊。"""


class ControlNotFoundError(WeChatAutomationError):
    """在超时时间内未找到指定控件。"""


class OperationTimeout(WeChatAutomationError):
    """等待某个条件成立时超时。"""
