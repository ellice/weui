"""窗口与控件通用操作（第四类能力）。

封装微信主窗口的连接、唤起、置顶、最小化/还原，以及控件等待、
控件树导出、按钮点击、文本读取等通用调试/操作能力。
"""

from __future__ import annotations

import time
from typing import Callable, List, Optional

from .config import WeChatConfig, DEFAULT_CONFIG
from .exceptions import (
    ControlNotFoundError,
    ControlTimeoutError,
    WeChatNotRunningError,
)


class WindowManager:
    """负责微信主窗口的连接与生命周期操作。"""

    def __init__(self, config: WeChatConfig = DEFAULT_CONFIG):
        self.config = config
        self._app = None
        self._main = None

    # ------------------------------------------------------------------ #
    # 连接 / 唤起
    # ------------------------------------------------------------------ #
    def connect(self) -> "WindowManager":
        """连接到已运行的微信主窗口。

        若微信未启动或未登录，抛出 :class:`WeChatNotRunningError`。
        """
        from pywinauto import Application
        from pywinauto.findwindows import ElementNotFoundError

        spec = self.config.window
        try:
            self._app = Application(backend=spec.backend).connect(
                class_name=spec.window_class
            )
            self._main = self._app.window(class_name=spec.window_class)
            # 触发一次访问，确认窗口存在
            self._main.wait("exists", timeout=self.config.timing.control_timeout)
        except (ElementNotFoundError, RuntimeError, Exception) as exc:
            raise WeChatNotRunningError(
                "未找到微信主窗口，请确认微信已启动并登录"
            ) from exc
        return self

    @property
    def main(self):
        """微信主窗口 WrapperObject。"""
        if self._main is None:
            raise WeChatNotRunningError("尚未连接微信窗口，请先调用 connect()")
        return self._main

    # ------------------------------------------------------------------ #
    # 窗口操作
    # ------------------------------------------------------------------ #
    def activate(self) -> None:
        """唤起并激活微信窗口（还原+置前+获取焦点）。"""
        win = self.main
        try:
            if win.is_minimized():
                win.restore()
        except Exception:
            pass
        win.set_focus()
        time.sleep(self.config.timing.action_pause)

    def set_topmost(self, topmost: bool = True) -> None:
        """将窗口置顶 / 取消置顶。"""
        import win32con
        import win32gui

        handle = self.main.handle
        flag = win32con.HWND_TOPMOST if topmost else win32con.HWND_NOTOPMOST
        win32gui.SetWindowPos(
            handle,
            flag,
            0,
            0,
            0,
            0,
            win32con.SWP_NOMOVE | win32con.SWP_NOSIZE,
        )

    def minimize(self) -> None:
        self.main.minimize()

    def restore(self) -> None:
        self.main.restore()

    def maximize(self) -> None:
        self.main.maximize()

    # ------------------------------------------------------------------ #
    # 控件等待 / 查找
    # ------------------------------------------------------------------ #
    def wait_control(
        self,
        timeout: Optional[float] = None,
        **criteria,
    ):
        """按条件等待并返回控件；超时抛出 :class:`ControlTimeoutError`。

        criteria 直接透传给 pywinauto ``child_window``，
        例如 ``title="搜索", control_type="Edit"``。
        """
        timeout = timeout if timeout is not None else self.config.timing.control_timeout
        interval = self.config.timing.control_retry_interval
        ctrl = self.main.child_window(**criteria)
        try:
            ctrl.wait("exists ready", timeout=timeout, retry_interval=interval)
        except Exception as exc:
            raise ControlTimeoutError(
                f"等待控件超时({timeout}s): {criteria}"
            ) from exc
        return ctrl

    def find_control(self, **criteria):
        """查找控件，找不到抛出 :class:`ControlNotFoundError`（不等待）。"""
        ctrl = self.main.child_window(**criteria)
        if not ctrl.exists():
            raise ControlNotFoundError(f"未找到控件: {criteria}")
        return ctrl

    def control_exists(self, **criteria) -> bool:
        """判断控件是否存在。"""
        try:
            return self.main.child_window(**criteria).exists()
        except Exception:
            return False

    def get_text(self, **criteria) -> str:
        """读取指定控件的文本内容。"""
        ctrl = self.find_control(**criteria)
        try:
            texts = ctrl.texts()
            return "\n".join(t for t in texts if t)
        except Exception:
            return ctrl.window_text()

    def click_button(self, title: str, timeout: Optional[float] = None) -> None:
        """按名称点击一个按钮（更多/表情/语音/截图等）。"""
        btn = self.wait_control(
            title=title, control_type="Button", timeout=timeout
        )
        btn.click_input()
        time.sleep(self.config.timing.action_pause)

    def button_exists(self, title: str) -> bool:
        """判断某个按钮是否存在。"""
        return self.control_exists(title=title, control_type="Button")

    # ------------------------------------------------------------------ #
    # 调试：控件树
    # ------------------------------------------------------------------ #
    def dump_control_tree(self, depth: int = 8, to_file: Optional[str] = None) -> str:
        """打印/导出全部控件树，用于调试定位控件。

        :param depth: 遍历深度。
        :param to_file: 若提供路径则同时写入文件。
        :return: 控件树文本。
        """
        import io
        from contextlib import redirect_stdout

        buffer = io.StringIO()
        with redirect_stdout(buffer):
            self.main.print_control_identifiers(depth=depth)
        text = buffer.getvalue()

        if to_file:
            with open(to_file, "w", encoding="utf-8") as fh:
                fh.write(text)
        return text
