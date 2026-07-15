"""桌面版微信自动化工具包（Python + pywinauto）。

该包封装了对 Windows 桌面版微信的常用自动化能力，按职责拆分为多个模块：

- :mod:`wechat_auto.config`      —— 全局配置（延时、窗口标题、控件名等）
- :mod:`wechat_auto.exceptions`  —— 统一异常定义
- :mod:`wechat_auto.clipboard`   —— 剪贴板文本 / 文件 / 图片写入
- :mod:`wechat_auto.input_utils` —— 键鼠模拟、慢速输入、快捷键组合
- :mod:`wechat_auto.window`      —— 窗口唤起 / 置顶 / 最小化 / 控件树导出
- :mod:`wechat_auto.messaging`   —— 搜索好友、发送文本、群发、分段长文本
- :mod:`wechat_auto.files`       —— 文件 / 图片 / 多文件粘贴发送
- :mod:`wechat_auto.sessions`    —— 会话列表读取、切换、历史消息读取、滚动加载
- :mod:`wechat_auto.client`      —— 组合上述能力的高层门面 :class:`WeChatClient`

典型用法::

    from wechat_auto import WeChatClient

    wx = WeChatClient()
    wx.connect()                       # 连接（必要时唤起）微信主窗口
    wx.send_text("文件传输助手", "你好，世界")
    wx.send_file("文件传输助手", r"C:\\report.pdf")

平台要求：仅支持 Windows；请先 ``pip install -r requirements.txt``。
"""

from .config import WeChatConfig, default_config
from .exceptions import (
    WeChatAutomationError,
    WindowNotFoundError,
    ControlNotFoundError,
    ContactNotFoundError,
    TimeoutError,
)
from .client import WeChatClient

__version__ = "0.1.0"

__all__ = [
    "WeChatClient",
    "WeChatConfig",
    "default_config",
    "WeChatAutomationError",
    "WindowNotFoundError",
    "ControlNotFoundError",
    "ContactNotFoundError",
    "TimeoutError",
    "__version__",
]
