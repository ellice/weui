"""微信主窗口的查找、唤起与窗口级操作。

负责：
- 连接 / 唤起微信主窗口（WeChatMainWndForPC）；
- 置顶、最小化、还原；
- 提供 ``main_window`` 句柄给其它模块复用。
"""

from __future__ import annotations

import time
from typing import Any, Optional

from ._compat import load_pywinauto, require_windows
from .exceptions import WeChatNotRunningError

# 微信 PC 版主窗口类名（3.x 版本）。
WECHAT_WINDOW_CLASS = "WeChatMainWndForPC"
WECHAT_PROCESS = "WeChat.exe"


class WeChatWindow:
    """封装微信主窗口及其所在的 Application 实例。"""

    def __init__(self, backend: str = "uia") -> None:
        """
        :param backend: pywinauto 后端，微信推荐使用 ``"uia"``。
        """
        require_windows()
        self.backend = backend
        self._pwa = load_pywinauto()
        self._app: Optional[Any] = None
        self._window: Optional[Any] = None

    @property
    def app(self) -> Any:
        if self._app is None:
            self.connect()
        return self._app

    @property
    def main_window(self) -> Any:
        """微信主窗口控件（已 wrapper）。"""
        if self._window is None:
            self.connect()
        return self._window

    def connect(self, timeout: float = 10.0) -> "WeChatWindow":
        """连接到已运行的微信主窗口。

        若未运行则抛 :class:`WeChatNotRunningError`。
        """
        from pywinauto import Application  # type: ignore
        from pywinauto.findwindows import ElementNotFoundError  # type: ignore

        deadline = time.time() + timeout
        last_err: Optional[Exception] = None
        while time.time() < deadline:
            try:
                app = Application(backend=self.backend).connect(
                    class_name=WECHAT_WINDOW_CLASS
                )
                window = app.window(class_name=WECHAT_WINDOW_CLASS)
                window.wait("exists", timeout=2)
                self._app = app
                self._window = window
                return self
            except (ElementNotFoundError, Exception) as exc:  # noqa: BLE001
                last_err = exc
                time.sleep(0.5)
        raise WeChatNotRunningError(
            "未找到正在运行的微信主窗口，请先登录微信桌面版。"
            f" 最后错误: {last_err}"
        )

    def is_running(self) -> bool:
        """检测微信主窗口是否存在。"""
        try:
            self.connect(timeout=2.0)
            return True
        except WeChatNotRunningError:
            return False

    # ----- 窗口级操作 -----
    def activate(self) -> None:
        """唤起并激活（置于前台）微信窗口。"""
        win = self.main_window
        if win.is_minimized():
            win.restore()
        win.set_focus()

    def bring_to_top(self) -> None:
        """置顶窗口。"""
        self.main_window.set_focus()

    def minimize(self) -> None:
        self.main_window.minimize()

    def restore(self) -> None:
        win = self.main_window
        if win.is_minimized():
            win.restore()
        win.set_focus()

    def maximize(self) -> None:
        self.main_window.maximize()
