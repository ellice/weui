"""运行参数与控件标识配置。

不同微信版本控件的 ``title`` / ``class_name`` 可能存在差异，
将这些易变的标识集中到配置对象，便于在不改动业务代码的前提下覆盖。
"""

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class WeChatConfig:
    """桌面微信自动化的全局配置。

    控件标识字段既可被 ``window.py`` 用于精确定位，也支持在实例化
    :class:`~wechat_automation.bot.WeChatBot` 时按需覆盖。
    """

    # ---- 进程 / 主窗口 ----
    process_name: str = "WeChat.exe"
    window_class_name: str = "WeChatMainWndForPC"
    window_title: str = "微信"

    # ---- 后端 ----
    # UIA 对微信新版控件树支持更完整；个别老版本可切换为 "win32"。
    backend: str = "uia"

    # ---- 超时与节流（单位：秒）----
    default_timeout: float = 15.0
    control_retry_interval: float = 0.5

    # 模拟真人输入的字符间隔范围，用于降低风控风险。
    typing_interval_min: float = 0.02
    typing_interval_max: float = 0.08

    # 关键动作（切换会话、发送、粘贴）之间的停顿，等待 UI 稳定。
    action_pause: float = 0.3

    # ---- 控件标识 ----
    # 搜索框、会话列表、消息输入框、消息展示区等核心控件的 title/automation_id。
    search_box_title: str = "搜索"
    session_list_title: str = "会话"
    message_list_title: str = "消息"
    input_edit_title: str = "输入"
    send_button_title: str = "发送(S)"

    # 顶部工具栏 / 常见按钮名称，供「点击任意可见按钮」使用。
    known_buttons: Dict[str, str] = field(
        default_factory=lambda: {
            "emoji": "表情",
            "file": "发送文件",
            "screenshot": "截图",
            "voice": "语音聊天",
            "video": "视频聊天",
            "chat_history": "聊天记录",
            "more": "更多",
        }
    )

    def with_overrides(self, **overrides) -> "WeChatConfig":
        """返回在当前配置基础上应用覆盖项的新配置实例。"""
        data = self.__dict__.copy()
        data.update({k: v for k, v in overrides.items() if v is not None})
        return WeChatConfig(**data)
