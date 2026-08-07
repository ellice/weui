"""自定义异常类型。"""


class WeChatAutomationError(Exception):
    """所有微信自动化异常的基类。"""


class WeChatNotRunningError(WeChatAutomationError):
    """未找到运行中的微信主窗口。"""


class WindowNotFoundError(WeChatAutomationError):
    """未找到目标窗口或控件。"""


class ControlNotFoundError(WeChatAutomationError):
    """在超时时间内未定位到指定控件。"""


class ContactNotFoundError(WeChatAutomationError):
    """搜索联系人 / 群聊失败，无法切入会话。"""


class ClipboardError(WeChatAutomationError):
    """剪贴板读写失败。"""


class SendMessageError(WeChatAutomationError):
    """消息发送失败。"""


class PlatformNotSupportedError(WeChatAutomationError):
    """当前平台不支持（本库仅支持 Windows）。"""
