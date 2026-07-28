"""核心：连接微信主窗口、窗口状态管理、控件树导出。

其余功能模块（消息、文件、会话、键鼠）都通过 :class:`WeChatAuto`
持有的主窗口引用来工作。
"""

from __future__ import annotations

import logging
from typing import List, Optional

from .exceptions import (
    ControlNotFoundError,
    WeChatNotRunningError,
    WindowNotFoundError,
)
from .utils import human_sleep, logger, setup_logger, wait_until

# 微信桌面版主窗口的类名与标题（3.x 版本）
WECHAT_PROCESS = "WeChat.exe"
WECHAT_WINDOW_CLASS = "WeChatMainWndForPC"
WECHAT_WINDOW_TITLE = "微信"


class WeChatAuto:
    """桌面版微信自动化的统一入口。

    典型用法::

        wx = WeChatAuto()
        wx.connect()                    # 连接已登录的微信
        wx.send_text("文件传输助手", "你好")

    :param backend: pywinauto 后端，默认 ``uia``（推荐，控件信息更全）。
    :param input_delay: 每个输入 / 点击动作后的默认停顿秒数，用于“拟人”节奏。
    :param default_timeout: 查找窗口 / 控件的默认超时秒数。
    :param log_level: 日志级别。
    """

    def __init__(
        self,
        backend: str = "uia",
        input_delay: float = 0.2,
        default_timeout: float = 10.0,
        log_level: int = logging.INFO,
    ) -> None:
        self.backend = backend
        self.input_delay = input_delay
        self.default_timeout = default_timeout
        setup_logger(log_level)

        self._app = None          # pywinauto.Application
        self._main_win = None     # 主窗口 WindowSpecification / 包装器

        self._inputs = None
        self._messages = None
        self._files = None
        self._sessions = None

    # ------------------------------------------------------------------ #
    # 连接 / 唤起
    # ------------------------------------------------------------------ #
    def connect(self, timeout: Optional[float] = None) -> "WeChatAuto":
        """连接到一个已经登录并正在运行的微信进程。

        :raises WeChatNotRunningError: 未找到微信主窗口。
        """
        from pywinauto import Application  # 延迟导入，非 Windows 环境也能 import 本模块

        timeout = timeout or self.default_timeout
        try:
            self._app = Application(backend=self.backend).connect(
                class_name=WECHAT_WINDOW_CLASS, timeout=timeout
            )
        except Exception as exc:  # noqa: BLE001
            raise WeChatNotRunningError(
                "未检测到正在运行的微信，请先启动并登录微信桌面版"
            ) from exc

        self._main_win = self._app.window(class_name=WECHAT_WINDOW_CLASS)
        self._main_win.wait("exists ready", timeout=timeout)
        logger.info("已连接到微信主窗口")
        return self

    def launch(self, exe_path: str, timeout: Optional[float] = None) -> "WeChatAuto":
        """启动微信程序（若未运行），随后连接。

        :param exe_path: ``WeChat.exe`` 的完整路径。
        """
        from pywinauto import Application

        timeout = timeout or self.default_timeout
        try:
            self._app = Application(backend=self.backend).start(exe_path)
        except Exception:  # noqa: BLE001 - 可能已在运行，退回到 connect
            logger.info("启动失败，尝试连接已运行实例")
        return self.connect(timeout=timeout)

    # ------------------------------------------------------------------ #
    # 子模块（懒加载）
    # ------------------------------------------------------------------ #
    @property
    def inputs(self):
        """键鼠模拟控制器 :class:`~wechat_auto.inputs.InputController`。"""
        from .inputs import InputController

        if self._inputs is None:
            self._inputs = InputController(default_delay=self.input_delay)
        return self._inputs

    @property
    def messages(self):
        """消息发送器 :class:`~wechat_auto.messaging.MessageSender`。"""
        from .messaging import MessageSender

        if self._messages is None:
            self._messages = MessageSender(self, self.inputs)
        return self._messages

    @property
    def files(self):
        """文件 / 图片发送器 :class:`~wechat_auto.files.FileSender`。"""
        from .files import FileSender

        if self._files is None:
            self._files = FileSender(self, self.inputs)
        return self._files

    @property
    def sessions(self):
        """会话列表管理器 :class:`~wechat_auto.sessions.SessionManager`。"""
        from .sessions import SessionManager

        if self._sessions is None:
            self._sessions = SessionManager(self, self.inputs)
        return self._sessions

    # -- 常用操作的快捷转发 --------------------------------------------- #
    def send_text(self, keyword, text, **kwargs):
        """快捷方法：转发到 :meth:`MessageSender.send_text`。"""
        return self.messages.send_text(keyword, text, **kwargs)

    def broadcast(self, keywords, text, **kwargs):
        """快捷方法：转发到 :meth:`MessageSender.broadcast`。"""
        return self.messages.broadcast(keywords, text, **kwargs)

    def send_file(self, keyword, file_path):
        """快捷方法：转发到 :meth:`FileSender.send_file`。"""
        return self.files.send_file(keyword, file_path)

    def send_image(self, keyword, image_path):
        """快捷方法：转发到 :meth:`FileSender.send_image`。"""
        return self.files.send_image(keyword, image_path)

    def list_sessions(self):
        """快捷方法：转发到 :meth:`SessionManager.list_sessions`。"""
        return self.sessions.list_sessions()

    # ------------------------------------------------------------------ #
    # 窗口状态
    # ------------------------------------------------------------------ #
    @property
    def main_window(self):
        """返回主窗口的 pywinauto 包装器，未连接时抛异常。"""
        if self._main_win is None:
            raise WeChatNotRunningError("尚未连接微信，请先调用 connect()")
        return self._main_win

    def activate(self) -> None:
        """唤起并激活微信窗口（从最小化 / 后台恢复到前台）。"""
        win = self.main_window
        try:
            if win.is_minimized():
                win.restore()
        except Exception:  # noqa: BLE001
            pass
        win.set_focus()
        human_sleep(self.input_delay)

    def bring_to_top(self) -> None:
        """将窗口置顶到最前。"""
        self.activate()
        try:
            self.main_window.set_focus()
        except Exception:  # noqa: BLE001
            pass

    def minimize(self) -> None:
        """最小化微信窗口。"""
        self.main_window.minimize()

    def restore(self) -> None:
        """从最小化状态还原窗口。"""
        self.main_window.restore()
        human_sleep(self.input_delay)

    def maximize(self) -> None:
        """最大化微信窗口。"""
        self.main_window.maximize()

    def is_running(self) -> bool:
        """判断主窗口是否仍然存在。"""
        try:
            return bool(self._main_win and self._main_win.exists())
        except Exception:  # noqa: BLE001
            return False

    # ------------------------------------------------------------------ #
    # 控件查找 / 调试
    # ------------------------------------------------------------------ #
    def find_control(
        self,
        timeout: Optional[float] = None,
        **criteria,
    ):
        """在主窗口下按条件查找一个控件，超时未找到抛异常。

        ``criteria`` 直接透传给 pywinauto，如 ``title=``、``control_type=``、
        ``auto_id=``、``class_name=`` 等。
        """
        timeout = timeout or self.default_timeout
        ctrl = self.main_window.child_window(**criteria)
        try:
            ctrl.wait("exists", timeout=timeout)
        except Exception as exc:  # noqa: BLE001
            raise ControlNotFoundError(f"未找到控件：{criteria}") from exc
        return ctrl

    def control_exists(self, **criteria) -> bool:
        """判断某个控件当前是否存在（不等待）。"""
        try:
            return self.main_window.child_window(**criteria).exists()
        except Exception:  # noqa: BLE001
            return False

    def wait_control_ready(self, timeout: Optional[float] = None, **criteria):
        """等待控件出现并变为可交互（exists + ready）。"""
        timeout = timeout or self.default_timeout
        ctrl = self.main_window.child_window(**criteria)
        try:
            ctrl.wait("exists ready", timeout=timeout)
        except Exception as exc:  # noqa: BLE001
            raise ControlNotFoundError(f"控件未就绪：{criteria}") from exc
        return ctrl

    def get_control_text(self, **criteria) -> str:
        """获取某个控件的文本。"""
        ctrl = self.find_control(**criteria)
        try:
            return ctrl.window_text()
        except Exception:  # noqa: BLE001
            return ""

    def dump_control_tree(
        self,
        depth: Optional[int] = None,
        to_file: Optional[str] = None,
    ) -> str:
        """导出主窗口的完整控件树，便于调试定位控件。

        :param depth: 打印的最大层级深度，None 表示全部。
        :param to_file: 若提供路径，则同时写入该文件。
        :return: 控件树的文本表示。
        """
        import io
        from contextlib import redirect_stdout

        buf = io.StringIO()
        with redirect_stdout(buf):
            if depth is not None:
                self.main_window.print_control_identifiers(depth=depth)
            else:
                self.main_window.print_control_identifiers()
        text = buf.getvalue()

        if to_file:
            with open(to_file, "w", encoding="utf-8") as fh:
                fh.write(text)
            logger.info("控件树已导出到 %s", to_file)
        return text

    def list_buttons(self) -> List[str]:
        """列出主窗口中所有按钮的文本，便于查看可点击项。"""
        names: List[str] = []
        try:
            for child in self.main_window.descendants(control_type="Button"):
                txt = child.window_text()
                if txt:
                    names.append(txt)
        except Exception as exc:  # noqa: BLE001
            logger.warning("枚举按钮失败：%s", exc)
        return names

    def click_button(self, title: str, timeout: Optional[float] = None) -> None:
        """按名称点击一个按钮（更多、表情、语音、截图等）。"""
        btn = self.find_control(
            title=title, control_type="Button", timeout=timeout
        )
        btn.click_input()
        human_sleep(self.input_delay)
