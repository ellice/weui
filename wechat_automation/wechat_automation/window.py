"""窗口与控件通用操作。

封装微信主窗口的连接、唤起、置顶、最小化 / 还原，以及一套通用的
控件定位、等待、文本读取、按钮点击与调试工具（打印控件树）。

设计上把「连接与控件访问」集中在 :class:`WindowManager`，供上层业务
模块（消息、文件、会话）复用，避免每个模块各自持有 pywinauto 句柄。
"""

from __future__ import annotations

import time
from typing import List, Optional

from .config import WeChatConfig, DEFAULT_CONFIG
from .exceptions import (
    ControlNotFoundError,
    WeChatNotRunningError,
    WindowNotFoundError,
)

try:
    from pywinauto import Application  # type: ignore
    from pywinauto.findwindows import ElementNotFoundError  # type: ignore
    from pywinauto.timings import TimeoutError as PWATimeoutError  # type: ignore

    _HAS_PYWINAUTO = True
except Exception:  # pragma: no cover - 非 Windows / 未安装
    _HAS_PYWINAUTO = False
    ElementNotFoundError = Exception  # type: ignore
    PWATimeoutError = Exception  # type: ignore


class WindowManager:
    """负责连接微信并提供窗口 / 控件级别的通用操作。"""

    def __init__(self, config: Optional[WeChatConfig] = None):
        self.config = config or DEFAULT_CONFIG
        self.app = None  # type: ignore
        self.window = None  # 主窗口 WindowSpecification/wrapper

    # ------------------------------------------------------------------
    # 连接与窗口控制
    # ------------------------------------------------------------------
    def connect(self) -> "WindowManager":
        """连接到正在运行的微信主窗口。

        依次尝试：按窗口类名连接 -> 按进程名连接 -> 按标题连接。
        """
        if not _HAS_PYWINAUTO:
            raise WeChatNotRunningError(
                "pywinauto 未安装或当前非 Windows 环境，无法连接微信。"
            )
        cfg = self.config
        errors: List[str] = []

        for kwargs in (
            {"class_name": cfg.main_window_class},
            {"path": cfg.process_name},
            {"title": cfg.main_window_title},
        ):
            try:
                self.app = Application(backend=cfg.backend).connect(
                    timeout=cfg.default_timeout, **kwargs
                )
                self.window = self.app.window(
                    class_name=cfg.main_window_class
                )
                if not self.window.exists():
                    self.window = self.app.window(title=cfg.main_window_title)
                # 触碰一次以确认可用
                self.window.wait("exists", timeout=cfg.default_timeout)
                return self
            except Exception as exc:  # 尝试下一种连接方式
                errors.append(f"{kwargs}: {exc}")
                continue

        raise WeChatNotRunningError(
            "未找到运行中的微信客户端窗口，请确认已登录微信。\n"
            + "\n".join(errors)
        )

    def _require_window(self):
        if self.window is None:
            raise WindowNotFoundError("尚未连接微信窗口，请先调用 connect()。")
        return self.window

    def bring_to_front(self) -> None:
        """唤起微信窗口并置于最前（含还原、聚焦）。"""
        win = self._require_window()
        try:
            if hasattr(win, "restore"):
                win.restore()
        except Exception:
            pass
        try:
            win.set_focus()
        except Exception:
            # 某些情况下 set_focus 会因焦点竞争抛错，重试一次。
            time.sleep(0.2)
            win.set_focus()
        time.sleep(self.config.action_delay)

    def minimize(self) -> None:
        """最小化微信窗口。"""
        self._require_window().minimize()

    def restore(self) -> None:
        """还原微信窗口。"""
        self._require_window().restore()

    def maximize(self) -> None:
        """最大化微信窗口。"""
        self._require_window().maximize()

    def set_topmost(self, topmost: bool = True) -> None:
        """置顶 / 取消置顶微信窗口。"""
        win = self._require_window()
        try:
            win.set_focus()
            # 通过底层句柄设置窗口 Z 序为置顶。
            import win32con  # type: ignore
            import win32gui  # type: ignore

            hwnd = win.handle
            flag = win32con.HWND_TOPMOST if topmost else win32con.HWND_NOTOPMOST
            win32gui.SetWindowPos(
                hwnd,
                flag,
                0,
                0,
                0,
                0,
                win32con.SWP_NOMOVE | win32con.SWP_NOSIZE,
            )
        except Exception as exc:  # pragma: no cover
            raise WindowNotFoundError(f"设置窗口置顶失败：{exc}")

    # ------------------------------------------------------------------
    # 控件定位与等待
    # ------------------------------------------------------------------
    def find_control(self, timeout: Optional[float] = None, **criteria):
        """按条件定位一个控件（返回 pywinauto 包装对象）。

        Args:
            timeout: 等待控件出现的超时时间（秒），默认取配置值。
            **criteria: 传给 ``window.child_window`` 的定位条件，例如
                ``title=..., control_type=..., auto_id=...``。
        """
        win = self._require_window()
        timeout = self.config.default_timeout if timeout is None else timeout
        ctrl = win.child_window(**criteria)
        try:
            ctrl.wait("exists", timeout=timeout)
            return ctrl
        except Exception:
            raise ControlNotFoundError(f"超时未找到控件：{criteria}")

    def wait_control(
        self,
        timeout: Optional[float] = None,
        state: str = "visible",
        **criteria,
    ):
        """等待控件达到指定状态（exists/visible/enabled/ready）。"""
        win = self._require_window()
        timeout = self.config.default_timeout if timeout is None else timeout
        ctrl = win.child_window(**criteria)
        try:
            ctrl.wait(state, timeout=timeout)
            return ctrl
        except Exception:
            raise ControlNotFoundError(
                f"控件在 {timeout}s 内未达到状态 '{state}'：{criteria}"
            )

    def control_exists(self, **criteria) -> bool:
        """判断控件是否存在（不抛异常）。"""
        try:
            win = self._require_window()
            return win.child_window(**criteria).exists()
        except Exception:
            return False

    def get_control_text(self, **criteria) -> str:
        """获取控件文本；控件不存在时返回空字符串。"""
        try:
            ctrl = self.find_control(**criteria)
            texts = ctrl.texts()
            return "".join(texts) if texts else ctrl.window_text()
        except Exception:
            return ""

    def click_button(self, name: str, timeout: Optional[float] = None) -> bool:
        """按名称点击一个按钮（更多 / 表情 / 语音 / 截图等）。

        Returns:
            是否成功点击。
        """
        try:
            btn = self.find_control(
                title=name, control_type="Button", timeout=timeout
            )
            btn.click_input()
            time.sleep(self.config.action_delay)
            return True
        except Exception:
            return False

    def button_exists(self, name: str) -> bool:
        """判断某个按钮是否存在。"""
        return self.control_exists(title=name, control_type="Button")

    # ------------------------------------------------------------------
    # 调试工具
    # ------------------------------------------------------------------
    def dump_control_tree(self, depth: int = 8) -> str:
        """打印 / 导出主窗口的控件树，用于调试定位。

        Returns:
            控件树的文本表示。
        """
        win = self._require_window()
        import io
        from contextlib import redirect_stdout

        buf = io.StringIO()
        with redirect_stdout(buf):
            win.print_control_identifiers(depth=depth)
        tree = buf.getvalue()
        print(tree)
        return tree
