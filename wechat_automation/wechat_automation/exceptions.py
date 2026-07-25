"""微信自动化模块统一异常定义。"""


class WeChatAutoError(Exception):
    """所有微信自动化异常的基类。"""


class WeChatNotRunningError(WeChatAutoError):
    """未检测到正在运行的微信客户端窗口。"""


class WindowNotFoundError(WeChatAutoError):
    """未能找到指定的微信窗口或子窗口。"""


class ControlNotFoundError(WeChatAutoError):
    """在超时时间内未能定位到目标控件。"""


class ContactNotFoundError(WeChatAutoError):
    """搜索后未能找到匹配的好友或群聊。"""


class SendMessageError(WeChatAutoError):
    """消息发送过程中出现错误。"""


class ClipboardError(WeChatAutoError):
    """剪贴板读写操作失败。"""


class FileSendError(WeChatAutoError):
    """文件 / 图片发送过程中出现错误。"""
