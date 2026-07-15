"""全局配置。

将窗口标题、控件名称、各类延时等易变项集中到一处，避免散落在代码各处的
"魔法字符串"。不同微信版本控件名可能存在差异，可在实例化时覆盖对应字段。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class WeChatConfig:
    """微信自动化的可调参数集合。

    Attributes:
        window_title: 主窗口标题（一般为 "微信"，英文版为 "WeChat"）。
        window_class: 主窗口类名，用于精确匹配窗口。
        process_path: 微信可执行文件路径，用于在未启动时自动拉起。
        backend: pywinauto 后端，桌面版微信推荐使用 ``"uia"``。
        search_box_title: 顶部搜索框控件名。
        edit_box_title_candidates: 聊天输入框可能的控件名（不同版本有差异）。
        session_list_title: 左侧会话列表控件名。
        message_list_title: 聊天记录消息列表控件名。
        short_delay / medium_delay / long_delay: 三档统一延时（秒）。
        type_interval: 慢速输入时每个字符之间的间隔（秒），用于防风控。
        default_timeout: 等待控件加载的默认超时（秒）。
        retry_interval: 轮询等待时的间隔（秒）。
    """

    # —— 窗口相关 ——
    window_title: str = "微信"
    window_class: str = "WeChatMainWndForPC"
    process_path: str = r"C:\Program Files\Tencent\WeChat\WeChat.exe"
    backend: str = "uia"

    # —— 控件名（随版本可能变化，可覆盖）——
    search_box_title: str = "搜索"
    edit_box_title_candidates: List[str] = field(
        default_factory=lambda: ["输入", "Input", "Edit"]
    )
    session_list_title: str = "会话"
    message_list_title: str = "消息"
    send_button_title: str = "发送(S)"

    # —— 延时（秒），可整体缩放以适配不同机器性能 ——
    short_delay: float = 0.3
    medium_delay: float = 0.6
    long_delay: float = 1.2

    # —— 输入 / 等待 ——
    type_interval: float = 0.03
    default_timeout: float = 15.0
    retry_interval: float = 0.5

    def scaled(self, factor: float) -> "WeChatConfig":
        """按比例缩放所有延时，返回新的配置对象（不修改自身）。

        在低性能机器上可传入 ``>1`` 放大延时，提升稳定性。
        """
        import dataclasses

        return dataclasses.replace(
            self,
            short_delay=self.short_delay * factor,
            medium_delay=self.medium_delay * factor,
            long_delay=self.long_delay * factor,
            type_interval=self.type_interval * factor,
            retry_interval=self.retry_interval * factor,
        )


#: 默认配置单例，便于快速使用。
default_config = WeChatConfig()
