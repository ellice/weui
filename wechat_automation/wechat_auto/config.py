"""集中管理微信窗口/控件标识与默认参数。

不同微信版本（3.x）控件名称基本稳定，如遇版本差异，可在此处统一调整，
或在实例化 :class:`~wechat_auto.core.WeChatAuto` 时通过参数覆盖。
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class WeChatConfig:
    """微信窗口与控件定位配置。"""

    # 进程与主窗口
    process_name: str = "WeChat.exe"
    main_window_class: str = "WeChatMainWndForPC"
    main_window_title_re: str = "微信|WeChat"

    # 顶部搜索框（自动化名称在不同版本里为「搜索」/「Search」）
    search_box_names: List[str] = field(
        default_factory=lambda: ["搜索", "Search"]
    )

    # 会话列表
    session_list_name: str = "会话"
    session_list_names: List[str] = field(
        default_factory=lambda: ["会话", "Sessions", "Conversations"]
    )

    # 聊天消息区域
    message_list_name: str = "消息"
    message_list_names: List[str] = field(
        default_factory=lambda: ["消息", "Message", "Messages"]
    )

    # 输入框（Edit 控件，通常无固定名称，按类型定位）
    input_edit_name: str = "输入"

    # 默认延时（秒）
    default_timeout: float = 10.0          # 控件等待默认超时
    short_pause: float = 0.3               # 操作之间的短暂停顿
    type_interval: float = 0.05            # 模拟输入字符间隔（防风控）

    # pywinauto 后端，微信使用 uia
    backend: str = "uia"
