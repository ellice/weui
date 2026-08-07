"""窗口管理：连接微信、唤起 / 置顶 / 最小化 / 还原。"""

from __future__ import annotations

import sys
import time
from typing import Optional

from .config import WeChatConfig
from .exceptions import (
    PlatformNotSupportedError,
    WeChatNotRunningError,
    WindowNotFoundError,
)

try:  # pragma: no cover - 仅 Windows
    from pywinauto import Application
    from pywinauto.findwindows import ElementNotFoundError
except Exception:  # noqa: BLE001
    Application = None
    ElementNotFoundError = Exception

try:  # pragma: no cover - 仅 Windows
    import win32con  # type: ignore
    import win32gui  # type: ignore
except Exception:  # noqa: BLE001
    win32con = None
    win32gui = None


class WindowManager:
    """负责连接 / 启动微信主窗口，并管理窗口状态。"""

    def __init__(self, config: Optional[WeChatConfig] = None) -> None:
        self.config = config or WeChatConfig()
        self.app = None
        self.window = None

    # ------------------------------------------------------------------ #
    # 连接 / 启动
    # ------------------------------------------------------------------ #
    def connect(self, start_if_not_running: bool = False):
        """连接到运行中的微信主窗口。

        :param start_if_not_running: 若微信未运行，是否尝试启动。
        :returns: pywinauto 主窗口对象（WindowSpecification 已 wrap）。
        """
        self._ensure_platform()

        try:
            self.app = Application(backend=self.config.backend).connect(
                title=self.config.window_title,
                class_name=self.config.window_class_name or None,
                timeout=5,
            )
        except (ElementNotFoundError, Exception):  # noqa: BLE001
            if start_if_not_running:
                return self.start()
            raise WeChatNotRunningError(
                "未找到运行中的微信主窗口，请确认微信已登录，"
                "或使用 start()/connect(start_if_not_running=True) 启动。"
            )

        self.window = self._resolve_main_window()
        return self.window

    def start(self):
        """启动微信进程并等待主窗口出现。"""
        self._ensure_platform()
        try:
            self.app = Application(backend=self.config.backend).start(
                self.config.process_path
            )
        except Exception as exc:  # noqa: BLE001
            raise WeChatNotRunningError(
                f"启动微信失败（路径：{self.config.process_path}）：{exc}"
            ) from exc

        # 微信启动后可能先弹登录窗口，这里轮询等待主窗口
        deadline = time.time() + self.config.default_timeout
        last_exc: Optional[Exception] = None
        while time.time() < deadline:
            try:
                self.app = Application(backend=self.config.backend).connect(
                    title=self.config.window_title,
                    class_name=self.config.window_class_name or None,
                    timeout=2,
                )
                self.window = self._resolve_main_window()
                return self.window
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                time.sleep(self.config.poll_interval)
        raise WeChatNotRunningError(f"等待微信主窗口超时：{last_exc}")

    def _resolve_main_window(self):
        win = self.app.window(
            title=self.config.window_title,
            class_name=self.config.window_class_name or None,
        )
        if not win.exists():
            raise WindowNotFoundError("已连接微信进程，但未定位到主窗口。")
        return win

    # ------------------------------------------------------------------ #
    # 窗口状态
    # ------------------------------------------------------------------ #
    def bring_to_front(self):
        """唤起并激活微信窗口（若最小化则先还原）。"""
        self._require_window()
        try:
            if self.is_minimized():
                self.restore()
            self.window.set_focus()
            time.sleep(self.config.action_delay)
        except Exception as exc:  # noqa: BLE001
            raise WindowNotFoundError(f"唤起微信窗口失败：{exc}") from exc
        return self.window

    def minimize(self):
        """最小化窗口。"""
        self._require_window()
        self.window.minimize()
        time.sleep(self.config.action_delay)

    def restore(self):
        """还原窗口。"""
        self._require_window()
        self.window.restore()
        time.sleep(self.config.action_delay)

    def maximize(self):
        """最大化窗口。"""
        self._require_window()
        self.window.maximize()
        time.sleep(self.config.action_delay)

    def is_minimized(self) -> bool:
        self._require_window()
        try:
            return bool(self.window.is_minimized())
        except Exception:  # noqa: BLE001
            return False

    def set_topmost(self, topmost: bool = True):
        """置顶 / 取消置顶窗口。"""
        self._require_window()
        if win32gui is None or win32con is None:
            raise PlatformNotSupportedError("窗口置顶需要 pywin32（仅支持 Windows）")
        try:
            hwnd = self.window.handle
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
        except Exception as exc:  # noqa: BLE001
            raise WindowNotFoundError(f"设置窗口置顶失败：{exc}") from exc

    # ------------------------------------------------------------------ #
    # 内部
    # ------------------------------------------------------------------ #
    def _require_window(self) -> None:
        if self.window is None:
            raise WeChatNotRunningError("尚未连接微信窗口，请先调用 connect()。")

    @staticmethod
    def _ensure_platform() -> None:
        if Application is None or not sys.platform.startswith("win"):
            raise PlatformNotSupportedError(
                "本库依赖 pywinauto，仅支持 Windows 平台运行。"
            )
