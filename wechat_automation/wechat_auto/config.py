"""集中管理各类可调参数（超时、延时、控件名称等）。

微信不同版本控件名称、AutomationId 可能存在差异，集中在此处便于快速适配。
默认值以 Windows 版微信（简体中文界面，3.9.x）为准。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class Timing:
    """时序 / 延时相关配置（单位：秒）。"""

    # 等待控件出现的默认超时时间
    control_timeout: float = 10.0
    # 轮询控件的间隔
    control_retry_interval: float = 0.3
    # 单个操作之间的短暂停顿，给微信 UI 刷新留时间
    action_pause: float = 0.3
    # 模拟真人逐字输入时，每个字符的最小 / 最大延时（防风控）
    typing_min_delay: float = 0.02
    typing_max_delay: float = 0.08
    # 发送文件后等待微信读取剪贴板并渲染的时间
    paste_render_delay: float = 1.0


@dataclass
class WindowSpec:
    """微信主窗口的定位信息。"""

    # 主窗口进程名
    process_name: str = "WeChat.exe"
    # 主窗口类名（PC 微信固定为该值）
    window_class: str = "WeChatMainWndForPC"
    # 窗口标题（简体中文为“微信”）
    window_title: str = "微信"
    # UI Automation 后端
    backend: str = "uia"


@dataclass
class ControlNames:
    """常用控件的界面文本 / 名称。

    这些名称来自微信简体中文界面，若微信升级导致定位失败，
    优先在这里调整对应文本即可，无需改动业务代码。
    """

    search_box: str = "搜索"
    search_result_list: str = "@str:IDS_FAV_SEARCH_RESULT"
    message_input: str = "输入"
    send_button: str = "发送(S)"
    session_list: str = "会话"
    message_area: str = "消息"
    # 顶部工具栏常见按钮
    button_emoji: str = "表情"
    button_file: str = "发送文件"
    button_screenshot: str = "截图"
    button_chat_history: str = "聊天记录"
    button_more: str = "更多"


@dataclass
class WeChatConfig:
    """聚合配置对象，供 :class:`WeChatAuto` 使用。"""

    timing: Timing = field(default_factory=Timing)
    window: WindowSpec = field(default_factory=WindowSpec)
    controls: ControlNames = field(default_factory=ControlNames)
    # 群聊会话名称中常见的“(人数)”后缀特征，用于区分群聊 / 私聊
    group_name_suffixes: List[str] = field(
        default_factory=lambda: ["(", "（"]
    )


DEFAULT_CONFIG = WeChatConfig()
