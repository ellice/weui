"""桌面版微信自动化（python + pywinauto）。

提供基于 UI 自动化的微信桌面端操作能力：搜索切换会话、收发文本 /
文件 / 图片、读取会话列表与聊天记录、窗口与控件操作、键鼠模拟等。

仅支持 Windows 平台运行（依赖 pywinauto / pywin32）；在其它平台可正常
导入用于静态检查与单元测试，实际调用窗口操作时会抛出明确异常。
"""

from __future__ import annotations

from .exceptions import (
    ClipboardError,
    ContactNotFoundError,
    ControlNotFoundError,
    DependencyNotInstalledError,
    FileSendError,
    TimeoutError,
    WeChatAutomationError,
    WeChatNotRunningError,
    WindowNotFoundError,
)
from .input_simulator import InputSimulator
from .wechat import WeChat

__version__ = "0.1.0"

__all__ = [
    "WeChat",
    "InputSimulator",
    "WeChatAutomationError",
    "WeChatNotRunningError",
    "WindowNotFoundError",
    "ControlNotFoundError",
    "TimeoutError",
    "ContactNotFoundError",
    "ClipboardError",
    "FileSendError",
    "DependencyNotInstalledError",
    "__version__",
]
