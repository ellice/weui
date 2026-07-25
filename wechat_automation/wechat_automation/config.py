"""微信自动化全局配置。

集中管理窗口标识、控件名称、超时与输入节奏等常量，方便在不同
微信版本或语言环境下快速调整，而无需修改业务代码。
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class WeChatConfig:
    """微信自动化运行参数。

    大部分默认值针对简体中文版微信 PC 客户端（3.9.x）。若使用其他
    语言或版本，可在实例化时覆盖相应字段。
    """

    # 主窗口标识：微信主窗口的 Win32 类名保持稳定，优先按类名匹配。
    main_window_class: str = "WeChatMainWndForPC"
    main_window_title: str = "微信"
    # 进程可执行文件名，用于按进程连接。
    process_name: str = "WeChat.exe"

    # 常用控件文本（简体中文界面）。
    search_edit_name: str = "搜索"
    input_edit_name: str = "输入"          # 聊天输入框（部分版本为空，需回退定位）
    send_button_name: str = "发送(S)"
    session_list_name: str = "会话"
    message_list_name: str = "消息"

    # UI Automation 后端，微信主窗口需使用 "uia"。
    backend: str = "uia"

    # 超时与轮询（秒）。
    default_timeout: float = 10.0
    poll_interval: float = 0.4

    # 输入节奏，用于模拟真人、规避风控（秒）。
    type_interval_min: float = 0.02
    type_interval_max: float = 0.08
    action_delay: float = 0.3          # 关键动作之间的基础间隔
    send_delay: float = 0.5            # 单条消息发送后的间隔

    # 批量群发时每个联系人之间的间隔（秒），避免触发频率限制。
    batch_interval: float = 1.5

    # 剪贴板操作重试次数与间隔。
    clipboard_retry: int = 5
    clipboard_retry_delay: float = 0.1

    # 会话列表滚动加载时每次滚动的鼠标滚轮步数。
    scroll_step: int = -3

    # 群聊判定关键词：会话 / 标题中包含这些字样时视为群聊的辅助判据。
    group_hint_keywords: List[str] = field(
        default_factory=lambda: ["群聊", "群", "(", "（"]
    )


DEFAULT_CONFIG = WeChatConfig()
