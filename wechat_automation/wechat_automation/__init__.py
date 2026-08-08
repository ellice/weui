"""wechat_automation：微信桌面版自动化（Python + pywinauto）。

覆盖五大能力模块：

1. 基础消息发送（搜索切会话、纯文本/多行/特殊符号、回车发送、批量群发、
   快捷键、剪贴板粘贴）
2. 文件 / 图片 / 媒体发送（剪贴板 CF_HDROP + Ctrl+V 粘贴发送，支持批量）
3. 会话列表管理（读取/遍历/切换、读取历史消息、下拉加载、私聊/群聊区分）
4. 窗口与控件通用操作（唤起/置顶/最小化、等待/超时/异常捕获、控件树导出、
   点击任意按钮、读取文本、清空输入框）
5. 键鼠模拟配套（精准点击/右键/双击、拖拽滚动、全局快捷键、拟人慢速输入）

对外主要入口是 :class:`WeChat`。在非 Windows 平台也可安全 ``import``（
需要操作系统 UI 的能力会在调用时抛出清晰异常）。
"""

from __future__ import annotations

from . import clipboard
from .exceptions import (
    ContactNotFoundError,
    ControlNotFoundError,
    DependencyMissingError,
    NotConnectedError,
    WeChatAutomationError,
    WindowNotFoundError,
)
from .input_simulator import InputSimulator, escape_send_keys
from .wechat import WeChat

__all__ = [
    "WeChat",
    "InputSimulator",
    "escape_send_keys",
    "clipboard",
    "WeChatAutomationError",
    "DependencyMissingError",
    "WindowNotFoundError",
    "NotConnectedError",
    "ControlNotFoundError",
    "ContactNotFoundError",
]

__version__ = "0.1.0"
