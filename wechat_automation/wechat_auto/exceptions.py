"""自定义异常集合。

把自动化过程中的常见错误归类，方便上层捕获与重试。
"""


class WeChatAutomationError(Exception):
    """所有自动化异常的基类。"""


class WeChatNotRunningError(WeChatAutomationError):
    """未检测到正在运行的微信主窗口。"""


class WindowNotFoundError(WeChatAutomationError):
    """目标窗口未找到。"""


class ControlNotFoundError(WeChatAutomationError):
    """目标控件未找到（可能是版本差异或界面未加载）。"""


class ControlTimeoutError(WeChatAutomationError):
    """等待控件出现/就绪超时。"""


class ContactNotFoundError(WeChatAutomationError):
    """根据备注/昵称搜索不到联系人或群聊。"""


class ClipboardError(WeChatAutomationError):
    """剪贴板读写失败。"""


class SendMessageError(WeChatAutomationError):
    """消息发送失败。"""
