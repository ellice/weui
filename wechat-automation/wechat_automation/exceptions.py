"""自定义异常。"""


class WeChatAutomationError(Exception):
    """所有微信自动化异常的基类。"""


class WeChatNotFoundError(WeChatAutomationError):
    """未找到微信主窗口（微信未启动或未登录）。"""


class ContactNotFoundError(WeChatAutomationError):
    """搜索后未匹配到目标好友 / 群聊。"""


class ControlNotFoundError(WeChatAutomationError):
    """在超时时间内未定位到目标控件。"""


class WeChatTimeoutError(WeChatAutomationError):
    """等待某个条件成立超时。"""
