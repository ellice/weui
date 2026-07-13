"""自定义异常定义。

统一封装自动化过程中的错误类型，方便上层按需捕获与重试。
"""


class WeChatAutomationError(Exception):
    """所有微信自动化异常的基类。"""


class WeChatNotRunningError(WeChatAutomationError):
    """未检测到正在运行的微信主窗口。"""


class WindowNotFoundError(WeChatAutomationError):
    """在超时时间内未能找到目标窗口。"""


class ControlNotFoundError(WeChatAutomationError):
    """在超时时间内未能找到目标控件。"""


class ControlTimeoutError(WeChatAutomationError):
    """等待控件出现 / 就绪超时。"""


class ContactNotFoundError(WeChatAutomationError):
    """搜索后未能定位到指定联系人或群聊。"""


class ClipboardError(WeChatAutomationError):
    """剪贴板读写失败。"""


class FileSendError(WeChatAutomationError):
    """文件 / 图片发送失败（如路径不存在）。"""
