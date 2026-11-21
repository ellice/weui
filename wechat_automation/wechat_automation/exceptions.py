"""自动化过程中可能抛出的异常类型。"""


class WeChatAutomationError(Exception):
    """所有自动化异常的基类。"""


class WeChatNotRunningError(WeChatAutomationError):
    """未检测到正在运行的 PC 版微信进程/主窗口。"""


class ControlNotFoundError(WeChatAutomationError):
    """在超时时间内未能定位到目标控件。"""


class ContactNotFoundError(WeChatAutomationError):
    """搜索好友 / 群聊后未能切入对应聊天窗口。"""


class TimeoutError(WeChatAutomationError):
    """等待控件 / 条件满足时超时。"""
