"""全局配置项。

微信（Windows 版）不同版本的控件 ``title`` / ``automation_id`` 可能不同，
这里集中维护，便于在新版本微信上快速适配，无需改动业务代码。
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class WeChatConfig:
    """微信自动化运行参数。"""

    # 进程名 / 窗口类名，用于定位微信主窗口
    process_name: str = "WeChat.exe"
    window_class_name: str = "WeChatMainWndForPC"
    window_title_regex: str = "微信|WeChat"

    # pywinauto 后端，微信 PC 版使用 UIA
    backend: str = "uia"

    # 常用控件文案（随微信版本可能变化）
    search_box_title: str = "搜索"
    search_result_list_title: str = "@str:IDS_FAV_SEARCH_RESULT"
    input_edit_title: str = "输入"
    send_button_title: str = "发送(S)"
    session_list_title: str = "会话"
    message_list_title: str = "消息"

    # 超时与轮询（秒）
    default_timeout: float = 10.0
    poll_interval: float = 0.3

    # 模拟真人输入的字符间隔（秒），防止触发风控
    type_interval: float = 0.03
    # 关键操作之间的停顿（搜索、切换会话、粘贴后等待渲染等）
    action_delay: float = 0.6

    # 群发时每个联系人之间的间隔（秒）
    batch_interval: float = 1.5

    # 群聊名称的判定关键字（可根据需要扩展）
    group_keywords: List[str] = field(default_factory=lambda: ["群", "(", "（"])


DEFAULT_CONFIG = WeChatConfig()
