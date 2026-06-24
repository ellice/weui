"""核心入口：:class:`WeChatAuto`，聚合所有能力并管理微信主窗口。"""

import logging
from typing import Optional

from .config import WeChatConfig
from .controls import ControlMixin
from .exceptions import WeChatNotFoundError
from .files import FileMixin
from .inputs import InputMixin
from .messaging import MessagingMixin
from .sessions import SessionMixin
from .utils import human_sleep, logger, setup_logger, wait_until


class WeChatAuto(
    ControlMixin,
    InputMixin,
    MessagingMixin,
    FileMixin,
    SessionMixin,
):
    """桌面版微信自动化主类。

    通过多重继承聚合：

    * :class:`ControlMixin` —— 通用控件查找/点击/取文本/导出控件树
    * :class:`InputMixin` —— 键鼠模拟、快捷键、慢速输入
    * :class:`MessagingMixin` —— 搜索、切换、文本发送、批量群发、读消息
    * :class:`FileMixin` —— 文件/图片/媒体粘贴发送
    * :class:`SessionMixin` —— 会话列表读取/遍历/滚动/分类

    :param config: 自定义 :class:`WeChatConfig`，默认使用内置配置。
    :param auto_connect: 实例化时是否立即连接微信窗口。
    :param log_level: 日志级别。
    """

    def __init__(
        self,
        config: Optional[WeChatConfig] = None,
        auto_connect: bool = True,
        log_level: int = logging.INFO,
    ):
        self.config = config or WeChatConfig()
        self.app = None
        self.window = None
        setup_logger(log_level)
        if auto_connect:
            self.connect()

    # ------------------------------------------------------------------ 连接
    def connect(self, timeout: Optional[float] = None) -> "WeChatAuto":
        """连接到正在运行的微信进程并获取主窗口。

        :raises WeChatNotFoundError: 微信未运行或窗口未找到。
        """
        from pywinauto import Application
        from pywinauto.findwindows import ElementNotFoundError

        timeout = self.config.default_timeout if timeout is None else timeout

        def _connect():
            try:
                app = Application(backend=self.config.backend).connect(
                    class_name=self.config.main_window_class
                )
            except (ElementNotFoundError, Exception):  # noqa: BLE001
                # 退化：按标题正则连接
                app = Application(backend=self.config.backend).connect(
                    title_re=self.config.main_window_title_re
                )
            return app

        try:
            self.app = wait_until(
                _connect, timeout=timeout, message="未连接到微信进程"
            )
        except Exception as exc:  # noqa: BLE001
            raise WeChatNotFoundError(
                "未找到运行中的微信，请确认已登录桌面版微信。原因：%s" % exc
            ) from exc

        self.window = self.app.window(class_name=self.config.main_window_class)
        if not self.window.exists():
            self.window = self.app.window(title_re=self.config.main_window_title_re)
        logger.info("已连接到微信主窗口")
        return self

    # ------------------------------------------------------------------ 窗口控制
    def activate(self) -> "WeChatAuto":
        """唤起并激活（前置）微信窗口，确保后续键鼠操作生效。"""
        if self.window is None:
            self.connect()
        try:
            if self.window.is_minimized():
                self.window.restore()
        except Exception:  # noqa: BLE001
            pass
        self.window.set_focus()
        human_sleep(self.config.short_pause)
        logger.info("微信窗口已激活")
        return self

    def set_topmost(self, topmost: bool = True) -> "WeChatAuto":
        """将微信窗口置顶 / 取消置顶。"""
        try:
            self.window.set_focus()
            self.window.wrapper_object().set_keyboard_focus()
        except Exception:  # noqa: BLE001
            pass
        try:
            import win32con  # type: ignore
            import win32gui  # type: ignore

            hwnd = self.window.handle
            flag = win32con.HWND_TOPMOST if topmost else win32con.HWND_NOTOPMOST
            win32gui.SetWindowPos(
                hwnd, flag, 0, 0, 0, 0,
                win32con.SWP_NOMOVE | win32con.SWP_NOSIZE,
            )
            logger.info("窗口置顶=%s", topmost)
        except ImportError:
            logger.warning("缺少 pywin32，无法设置置顶")
        return self

    def minimize(self) -> "WeChatAuto":
        """最小化微信窗口。"""
        self.window.minimize()
        return self

    def restore(self) -> "WeChatAuto":
        """从最小化还原微信窗口。"""
        self.window.restore()
        self.window.set_focus()
        return self

    def maximize(self) -> "WeChatAuto":
        """最大化微信窗口。"""
        self.window.maximize()
        return self

    def is_running(self) -> bool:
        """微信主窗口是否存在且可用。"""
        try:
            return self.window is not None and self.window.exists()
        except Exception:  # noqa: BLE001
            return False
