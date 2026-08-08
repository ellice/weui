"""模块四（窗口部分）：微信主窗口连接与状态控制。

负责：唤起/连接微信主窗口、置顶、最小化 / 还原、激活。
封装 ``pywinauto.Application``，对外暴露稳定的窗口句柄 ``main``。
"""

from __future__ import annotations

import time
from typing import Any, Optional

from ._compat import load_application
from .exceptions import NotConnectedError, WindowNotFoundError

# 微信桌面版主窗口的类名/标题（不同版本略有差异，做多重兜底）。
_WECHAT_CLASS_NAMES = ("WeChatMainWndForPC", "mmui::MainWindow")
_WECHAT_TITLES = ("微信", "Weixin", "WeChat")
_DEFAULT_EXE = "WeChat.exe"


class WeChatWindow:
    """微信主窗口管理器。

    :param backend: pywinauto 后端，默认 ``"uia"``（对微信兼容性最好）。
    :param exe_name: 微信进程名，用于按进程连接。
    """

    def __init__(self, backend: str = "uia", exe_name: str = _DEFAULT_EXE) -> None:
        self.backend = backend
        self.exe_name = exe_name
        self.app: Optional[Any] = None
        self.main: Optional[Any] = None

    # ------------------------------------------------------------ 连接
    def connect(self, timeout: float = 10.0, retry_interval: float = 0.5) -> Any:
        """连接已登录的微信主窗口。

        依次尝试按窗口类名、按标题、按进程名连接，全部失败则抛出
        :class:`WindowNotFoundError`。

        :return: 主窗口包装对象（pywinauto WindowSpecification 的 ``.wrapper``）。
        """
        Application = load_application()
        deadline = time.time() + timeout
        last_err: Optional[Exception] = None

        while time.time() < deadline:
            for class_name in _WECHAT_CLASS_NAMES:
                try:
                    app = Application(backend=self.backend).connect(
                        class_name=class_name, timeout=1
                    )
                    self.app = app
                    self.main = app.window(class_name=class_name)
                    if self.main.exists():
                        return self.main
                except Exception as exc:  # noqa: BLE001 - 逐个后备尝试
                    last_err = exc
            for title in _WECHAT_TITLES:
                try:
                    app = Application(backend=self.backend).connect(
                        title=title, timeout=1
                    )
                    self.app = app
                    self.main = app.window(title=title)
                    if self.main.exists():
                        return self.main
                except Exception as exc:  # noqa: BLE001
                    last_err = exc
            try:
                app = Application(backend=self.backend).connect(
                    path=self.exe_name, timeout=1
                )
                self.app = app
                self.main = app.top_window()
                if self.main.exists():
                    return self.main
            except Exception as exc:  # noqa: BLE001
                last_err = exc
            time.sleep(retry_interval)

        raise WindowNotFoundError(
            "未找到微信主窗口，请确认微信桌面版已启动并完成登录。"
            f"最后一次错误：{last_err!r}"
        )

    # ------------------------------------------------------------ 状态
    def _require(self) -> Any:
        if self.main is None:
            raise NotConnectedError("请先调用 connect() 连接微信窗口。")
        return self.main

    def activate(self) -> None:
        """唤起并激活窗口（置于前台、获取焦点）。"""
        main = self._require()
        try:
            if hasattr(main, "restore"):
                main.restore()
        except Exception:  # noqa: BLE001 - 某些状态下不可 restore
            pass
        main.set_focus()

    def minimize(self) -> None:
        """最小化窗口。"""
        self._require().minimize()

    def restore(self) -> None:
        """还原窗口。"""
        self._require().restore()

    def maximize(self) -> None:
        """最大化窗口。"""
        self._require().maximize()

    def set_topmost(self, topmost: bool = True) -> None:
        """设置窗口置顶 / 取消置顶。"""
        main = self._require()
        try:
            main.set_ex_style  # noqa: B018 - 存在性探测
            import win32con  # type: ignore
            import win32gui  # type: ignore

            flag = win32con.HWND_TOPMOST if topmost else win32con.HWND_NOTOPMOST
            win32gui.SetWindowPos(
                main.handle, flag, 0, 0, 0, 0,
                win32con.SWP_NOMOVE | win32con.SWP_NOSIZE,
            )
        except Exception:  # noqa: BLE001 - 缺 pywin32 时降级为仅激活
            main.set_focus()

    def is_minimized(self) -> bool:
        """窗口是否处于最小化状态。"""
        return bool(self._require().is_minimized())

    @property
    def handle(self) -> int:
        """主窗口的原生句柄（HWND）。"""
        return int(self._require().handle)
