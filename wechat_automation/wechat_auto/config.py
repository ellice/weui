"""全局配置与控件常量。

不同版本 / 语言的微信，控件标题（title / automation_id）可能不同。
把这些"魔法字符串"集中到一处，方便根据实际环境用
``print_control_identifiers`` 调试后按需覆盖。
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class WeChatConfig:
    """桌面版微信自动化的可调参数。

    绝大多数场景使用默认值即可；如遇控件定位失败，可用
    :meth:`WeChatClient.dump_control_tree` 导出控件树，
    再实例化本类覆盖对应字段。
    """

    # ---- 主窗口识别 ----
    # 经典版微信（3.x）主窗口类名；4.x 可能不同，可传空字符串后仅用 title 匹配
    window_class_name: str = "WeChatMainWndForPC"
    window_title: str = "微信"
    process_path: str = r"C:\Program Files\Tencent\WeChat\WeChat.exe"

    # ---- 关键子控件标题 ----
    search_box_title: str = "搜索"          # 顶部搜索框
    search_result_list_title: str = "@str:IDS_FAV_SEARCH_RESULT"  # 搜索结果列表（备用）
    session_list_title: str = "会话"        # 左侧会话列表
    message_list_title: str = "消息"        # 聊天记录列表
    input_edit_title: str = "输入"          # 底部消息输入框
    send_button_title: str = "发送(S)"      # 发送按钮

    # ---- 行为参数 ----
    backend: str = "uia"                    # pywinauto 后端，微信必须用 uia
    default_timeout: float = 20.0           # 控件等待默认超时（秒）
    poll_interval: float = 0.4              # 控件轮询间隔（秒）
    action_delay: float = 0.3               # 每步操作之间的间隔，防风控
    type_interval: float = 0.02             # 逐字输入间隔（秒），模拟真人
    batch_interval: float = 1.5             # 群发时联系人之间的间隔（秒）

    # 备选输入框 automation_id / 类名（新版微信可能变化）
    input_edit_fallback_titles: List[str] = field(
        default_factory=lambda: ["输入", "Input", "消息输入框"]
    )
    search_box_fallback_titles: List[str] = field(
        default_factory=lambda: ["搜索", "Search"]
    )
