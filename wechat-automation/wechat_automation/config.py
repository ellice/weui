"""可配置项。

不同微信版本的控件命名（AutomationId / 标题）可能存在差异，
集中放在这里方便按需覆盖，而不用改动核心逻辑。
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class WeChatConfig:
    """微信自动化行为与控件命名配置。"""

    # ---- 主窗口定位 ----
    window_class_name: str = "WeChatMainWndForPC"
    window_title: str = "微信"
    # 部分版本（微信 4.x / Weixin）主窗口类名不同，作为兜底匹配
    fallback_class_names: List[str] = field(
        default_factory=lambda: ["WeChatMainWndForPC", "Chrome_WidgetWin_0", "mmui::MainWindow"]
    )

    # ---- 常用控件文本（中文界面）----
    search_edit_name: str = "搜索"
    search_result_list_name: str = "@str:IDS_FAV_SEARCH_RESULT"
    session_list_name: str = "会话"
    message_list_name: str = "消息"
    input_edit_name: str = "输入"
    send_button_name: str = "发送(S)"

    # ---- 行为参数 ----
    # 默认操作/等待超时（秒）
    default_timeout: float = 10.0
    # 轮询间隔（秒）
    poll_interval: float = 0.3
    # 模拟真人输入时，每个字符之间的基础延时（秒）
    type_interval: float = 0.03
    # 慢速输入的随机抖动上限（秒），用于防风控
    type_jitter: float = 0.04
    # 搜索框输入后等待结果出现的时间（秒）
    search_settle_delay: float = 1.0
    # 每次群发之间的间隔（秒），降低被限制风险
    batch_send_delay: float = 1.5
    # 剪贴板操作后等待生效的时间（秒）
    clipboard_settle_delay: float = 0.3

    # pywinauto 后端，微信桌面端使用 UIA
    backend: str = "uia"
