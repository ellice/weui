"""自定义异常，便于上层做差异化的错误处理。"""


class WeChatAutoError(Exception):
    """所有微信自动化异常的基类。"""


class WeChatNotRunningError(WeChatAutoError):
    """未检测到正在运行的微信主窗口。"""


class WindowNotFoundError(WeChatAutoError):
    """目标窗口/控件未能找到。"""


class ControlNotFoundError(WeChatAutoError):
    """指定控件不存在或不可见。"""


class WaitTimeoutError(WeChatAutoError):
    """等待控件出现/就绪超时。"""


class ContactNotFoundError(WeChatAutoError):
    """搜索好友 / 群聊时未找到匹配项。"""


class ClipboardError(WeChatAutoError):
    """剪贴板读写失败。"""


class PlatformError(WeChatAutoError):
    """运行平台不受支持（仅支持 Windows）。"""
