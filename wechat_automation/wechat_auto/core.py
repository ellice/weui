# -*- coding: utf-8 -*-
"""微信桌面自动化主入口。

``WeChat`` 聚合了窗口/控件、消息、文件、会话四大类能力，
基于 pywinauto 的 ``uia`` 后端连接微信 PC 版主窗口。

示例::

    from wechat_auto import WeChat

    wx = WeChat()                 # 自动连接已登录的微信
    wx.send_text("你好", to="文件传输助手")
    wx.send_file(r"D:\\report.pdf", to="张三")
    print(wx.get_session_list())
"""

from __future__ import annotations

import time
from typing import Optional

from .controls import ControlMixin
from .exceptions import WeChatNotRunningError, WindowNotFoundError
from .files import FileMixin
from .messaging import MessageMixin
from .session import SessionMixin

# 微信 PC 版主窗口类名与进程名
WECHAT_WINDOW_CLASS = "WeChatMainWndForPC"
WECHAT_PROCESS = "WeChat.exe"


class WeChat(ControlMixin, MessageMixin, FileMixin, SessionMixin):
    """微信桌面自动化主类。"""

    def __init__(self, *, timeout: float = 10.0, auto_connect: bool = True,
                 exe_path: Optional[str] = None):
        """
        :param timeout: 控件等待默认超时（秒）。
        :param auto_connect: 实例化时是否立即连接微信窗口。
        :param exe_path: 微信可执行文件路径，用于在未运行时尝试启动。
        """
        self.timeout = timeout
        self.exe_path = exe_path
        self.app = None
        self.window = None
        if auto_connect:
            self.connect()

    # ----------------------------- 连接 / 启动 ----------------------------- #
    def connect(self, retry: int = 3, interval: float = 1.0) -> "WeChat":
        """连接到已登录运行中的微信主窗口。

        :raises WeChatNotRunningError: 多次重试后仍未找到微信窗口。
        """
        from pywinauto import Application  # 延迟导入，便于非 Windows 环境加载模块

        last_err: Exception | None = None
        for _ in range(max(1, retry)):
            try:
                app = Application(backend="uia").connect(
                    class_name=WECHAT_WINDOW_CLASS, timeout=self.timeout
                )
                self.app = app
                self.window = app.window(class_name=WECHAT_WINDOW_CLASS)
                self.window.wait("exists", timeout=self.timeout)
                return self
            except Exception as exc:  # noqa: BLE001
                last_err = exc
                time.sleep(interval)
        raise WeChatNotRunningError(
            f"未找到运行中的微信主窗口（class={WECHAT_WINDOW_CLASS}）: {last_err}"
        )

    def launch(self, wait_login: float = 10.0) -> "WeChat":
        """启动微信进程（需提供 ``exe_path``）并尝试连接。"""
        if not self.exe_path:
            raise WeChatNotRunningError("未提供 exe_path，无法启动微信")
        from pywinauto import Application

        try:
            self.app = Application(backend="uia").start(self.exe_path)
        except Exception as exc:  # noqa: BLE001
            raise WeChatNotRunningError(f"启动微信失败: {exc}") from exc
        time.sleep(wait_login)
        return self.connect()

    def close(self) -> None:
        """断开引用（不会关闭微信本体）。"""
        self.app = None
        self.window = None

    # 上下文管理器支持
    def __enter__(self) -> "WeChat":
        if self.window is None:
            self.connect()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
