"""全局配置与微信控件定位常量。

微信 PC 版不同大版本（3.x / 4.x）的控件名称、窗口类名可能存在差异，
这里把所有与界面强相关的常量集中管理，方便按实际环境调整。

如果你的微信版本控件名称不同，可在实例化 :class:`~wechat_auto.app.WeChatAuto`
时传入自定义的 :class:`Config` 覆盖默认值，或直接修改本文件。
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Config:
    """运行期配置。"""

    # --- 后端 ---
    # pywinauto 后端，微信 PC 版推荐使用 "uia"（UI Automation）
    backend: str = "uia"

    # --- 窗口定位 ---
    # 微信主窗口类名（3.x 为 WeChatMainWndForPC，4.x 为 mmui::MainWindow 之类）
    main_window_class: str = "WeChatMainWndForPC"
    # 主窗口标题（不同语言环境可能是 "微信" / "WeChat"）
    main_window_title: str = "微信"
    # 微信进程名
    process_name: str = "WeChat.exe"

    # --- 常用控件文本 ---
    search_box_title: str = "搜索"           # 顶部搜索框
    input_edit_title: str = "输入"           # 聊天输入框（部分版本为空标题的 Edit）
    send_button_title: str = "发送(S)"        # 发送按钮
    message_list_title: str = "消息"          # 聊天记录列表
    session_list_title: str = "会话"          # 左侧会话列表

    # --- 超时与延时（秒） ---
    default_timeout: float = 10.0            # 查找窗口 / 控件的默认超时
    poll_interval: float = 0.5               # 轮询间隔
    after_click_delay: float = 0.3           # 点击后的短暂等待
    after_search_delay: float = 1.0          # 搜索后的等待（等待结果加载）
    send_interval: float = 0.5               # 群发时每条消息之间的间隔

    # --- 模拟真人输入 ---
    # 逐字符输入时每个字符之间的延时区间（秒），用于防风控
    type_delay_min: float = 0.02
    type_delay_max: float = 0.08

    # --- 群聊标题特征 ---
    # 群聊窗口标题通常包含人数，如 "某某群(23)"；用括号数字作为判断特征之一
    group_title_pattern: str = r".*\(\d+\)$"

    # 已知的非会话项（会话列表里可能混入的功能入口），遍历时可用于过滤
    non_session_names: tuple = field(
        default_factory=lambda: ("折叠置顶聊天", "折叠的群聊", "")
    )
