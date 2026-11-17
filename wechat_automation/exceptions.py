"""自定义异常，统一异常捕获与错误提示。"""


class WeChatAutomationError(Exception):
    """所有微信自动化异常的基类。"""


class WeChatWindowNotFoundError(WeChatAutomationError):
    """未找到微信主窗口（微信未启动或未登录）。"""


class ControlNotFoundError(WeChatAutomationError):
    """在超时时间内未找到目标控件。"""


class ContactNotFoundError(WeChatAutomationError):
    """搜索好友 / 群聊失败，未命中任何会话。"""


class SendMessageError(WeChatAutomationError):
    """发送消息（文本 / 文件 / 图片）失败。"""


class ClipboardError(WeChatAutomationError):
    """剪贴板读写失败。"""
