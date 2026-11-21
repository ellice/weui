"""窗口与控件通用操作（第四类能力）。

职责：
- 连接 / 唤起微信主窗口，置顶、最小化、还原；
- 等待控件加载、超时判断、统一异常捕获；
- 导出控件树，便于调试定位；
- 查找控件、读取控件文本、判断按钮是否存在、点击可见按钮。
"""

import io
import time
from contextlib import redirect_stdout
from typing import Callable, List, Optional

from ..config import WeChatConfig
from ..exceptions import (
    ControlNotFoundError,
    WeChatNotRunningError,
    TimeoutError as WeChatTimeoutError,
)


class WindowController:
    """封装对微信主窗口及其内部控件的底层操作。"""

    def __init__(self, config: Optional[WeChatConfig] = None):
        self.config = config or WeChatConfig()
        self._app = None
        self._main = None

    # ------------------------------------------------------------------
    # 连接 / 唤起
    # ------------------------------------------------------------------
    def connect(self, launch_path: Optional[str] = None) -> "WindowController":
        """连接到正在运行的微信；必要时可通过 ``launch_path`` 拉起进程。

        连接成功后缓存 :class:`Application` 与主窗口句柄。
        """
        from pywinauto import Application
        from pywinauto.findwindows import ElementNotFoundError

        try:
            app = Application(backend=self.config.backend).connect(
                class_name=self.config.window_class_name,
                timeout=self.config.default_timeout,
            )
        except (ElementNotFoundError, RuntimeError) as exc:
            if launch_path:
                app = Application(backend=self.config.backend).start(launch_path)
                time.sleep(3)
            else:
                raise WeChatNotRunningError(
                    "未检测到正在运行的微信，请先登录 PC 版微信，"
                    "或通过 launch_path 指定 WeChat.exe 路径。"
                ) from exc

        self._app = app
        self._main = app.window(class_name=self.config.window_class_name)
        self.wait_ready(self._main)
        return self

    @property
    def main(self):
        """微信主窗口包装器；未连接时抛出异常。"""
        if self._main is None:
            raise WeChatNotRunningError("尚未连接微信，请先调用 connect()。")
        return self._main

    # ------------------------------------------------------------------
    # 窗口状态：唤起、置顶、最小化、还原
    # ------------------------------------------------------------------
    def activate(self) -> None:
        """将微信窗口唤到前台（从最小化恢复并聚焦）。"""
        win = self.main
        try:
            if win.is_minimized():
                win.restore()
        except Exception:
            pass
        win.set_focus()
        self._pause()

    def set_topmost(self, topmost: bool = True) -> None:
        """置顶 / 取消置顶微信窗口。"""
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
        self.main.set_focus()

    # ------------------------------------------------------------------
    # 控件等待 / 查找 / 文本
    # ------------------------------------------------------------------
    def wait_ready(self, ctrl, timeout: Optional[float] = None) -> None:
        """等待控件进入可见且可用状态，超时抛出 :class:`WeChatTimeoutError`。"""
        timeout = self.config.default_timeout if timeout is None else timeout
        try:
            ctrl.wait("visible enabled ready", timeout=timeout)
        except Exception as exc:  # pywinauto 抛 TimeoutError/ElementNotFound
            raise WeChatTimeoutError(f"等待控件就绪超时（{timeout}s）。") from exc

    def find(
        self,
        timeout: Optional[float] = None,
        parent=None,
        **criteria,
    ):
        """在给定父控件（默认主窗口）下按条件查找控件并等待其存在。

        ``criteria`` 直接透传给 pywinauto，例如 ``title=``、``control_type=``、
        ``auto_id=``、``class_name=`` 等。
        """
        timeout = self.config.default_timeout if timeout is None else timeout
        root = parent if parent is not None else self.main
        deadline = time.time() + timeout
        last_exc: Optional[Exception] = None
        while time.time() < deadline:
            try:
                ctrl = root.child_window(**criteria)
                if ctrl.exists():
                    return ctrl
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
            time.sleep(self.config.control_retry_interval)
        raise ControlNotFoundError(
            f"在 {timeout}s 内未找到控件: {criteria}"
        ) from last_exc

    def exists(self, parent=None, **criteria) -> bool:
        """判断控件 / 按钮是否存在（不等待，立即返回）。"""
        root = parent if parent is not None else self.main
        try:
            return root.child_window(**criteria).exists()
        except Exception:
            return False

    def get_text(self, parent=None, **criteria) -> str:
        """获取目标控件的文本（优先 ``window_text``，回退到 ``texts()``）。"""
        ctrl = self.find(parent=parent, **criteria)
        try:
            text = ctrl.window_text()
            if text:
                return text
        except Exception:
            pass
        try:
            return "\n".join(t for t in ctrl.texts() if t)
        except Exception:
            return ""

    # ------------------------------------------------------------------
    # 按钮操作
    # ------------------------------------------------------------------
    def click_button(
        self,
        title: str,
        parent=None,
        double: bool = False,
        right: bool = False,
    ) -> None:
        """点击指定名称的按钮，支持双击 / 右键。"""
        btn = self.find(parent=parent, title=title, control_type="Button")
        self.wait_ready(btn)
        if right:
            btn.right_click_input()
        elif double:
            btn.double_click_input()
        else:
            btn.click_input()
        self._pause()

    def button_exists(self, title: str, parent=None) -> bool:
        """判断某个按钮当前是否可见存在。"""
        return self.exists(parent=parent, title=title, control_type="Button")

    def list_buttons(self, parent=None) -> List[str]:
        """列出当前可见的所有按钮名称，便于调试与定位。"""
        root = parent if parent is not None else self.main
        names: List[str] = []
        try:
            for btn in root.descendants(control_type="Button"):
                name = btn.window_text()
                if name:
                    names.append(name)
        except Exception:
            pass
        return names

    # ------------------------------------------------------------------
    # 调试：导出控件树
    # ------------------------------------------------------------------
    def dump_control_tree(
        self,
        parent=None,
        depth: Optional[int] = None,
        to_file: Optional[str] = None,
    ) -> str:
        """打印 / 导出控件树字符串，用于调试定位控件标识。"""
        root = parent if parent is not None else self.main
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            try:
                root.print_control_identifiers(depth=depth)
            except TypeError:
                root.print_control_identifiers()
        tree = buffer.getvalue()
        if to_file:
            with open(to_file, "w", encoding="utf-8") as fh:
                fh.write(tree)
        return tree

    # ------------------------------------------------------------------
    # 通用重试包装
    # ------------------------------------------------------------------
    def retry(
        self,
        func: Callable,
        timeout: Optional[float] = None,
        interval: Optional[float] = None,
    ):
        """在超时时间内反复执行 ``func`` 直至其返回真值或不再抛异常。"""
        timeout = self.config.default_timeout if timeout is None else timeout
        interval = self.config.control_retry_interval if interval is None else interval
        deadline = time.time() + timeout
        last_exc: Optional[Exception] = None
        while time.time() < deadline:
            try:
                result = func()
                if result:
                    return result
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
            time.sleep(interval)
        raise WeChatTimeoutError("操作在超时时间内未成功完成。") from last_exc

    def _pause(self) -> None:
        time.sleep(self.config.action_pause)
