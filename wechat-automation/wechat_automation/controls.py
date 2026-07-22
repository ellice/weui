"""窗口与控件通用操作。

包含微信主窗口的连接 / 唤起 / 置顶 / 最小化 / 还原，以及控件等待、
控件树导出、通用点击、文本读取、按钮存在性判断等调试与操作工具。

``ControlMixin`` 会被 :class:`wechat_automation.core.WeChat` 继承使用，
它假定实例上已有 ``self.config``、``self.app``、``self.window`` 属性。
"""

from __future__ import annotations

import time
from typing import Callable, List, Optional

from .exceptions import (
    ControlNotFoundError,
    WeChatNotFoundError,
    WeChatTimeoutError,
)


class ControlMixin:
    """窗口与控件通用操作混入类。"""

    # 下列属性由 WeChat.__init__ 提供，这里仅做类型声明提示
    config: "object"
    app: "object"
    window: "object"

    # ------------------------------------------------------------ 窗口 ----
    def connect(self):
        """连接到已启动并登录的微信主窗口。

        :raises WeChatNotFoundError: 未找到微信主窗口
        """
        from pywinauto import Application  # 延迟导入，避免非 Windows 导入报错

        cfg = self.config
        last_err: Optional[Exception] = None
        for class_name in [cfg.window_class_name, *cfg.fallback_class_names]:
            try:
                app = Application(backend=cfg.backend).connect(
                    class_name=class_name, timeout=cfg.default_timeout
                )
                window = app.window(class_name=class_name)
                if window.exists():
                    self.app = app
                    self.window = window
                    return self
            except Exception as exc:  # noqa: BLE001 - 逐个类名尝试
                last_err = exc
                continue

        # 再尝试用标题匹配
        try:
            app = Application(backend=cfg.backend).connect(
                title=cfg.window_title, timeout=cfg.default_timeout
            )
            window = app.window(title=cfg.window_title)
            if window.exists():
                self.app = app
                self.window = window
                return self
        except Exception as exc:  # noqa: BLE001
            last_err = exc

        raise WeChatNotFoundError(
            f"未找到微信主窗口，请确认微信已启动并登录。最后错误: {last_err}"
        )

    def bring_to_front(self):
        """唤起并置顶微信窗口（还原 + 激活 + 前置）。"""
        win = self._require_window()
        if win.is_minimized():
            win.restore()
        win.set_focus()
        try:
            win.set_focus()
        except Exception:  # noqa: BLE001 - 某些情况下二次聚焦可忽略
            pass
        return self

    def minimize(self):
        """最小化微信窗口。"""
        self._require_window().minimize()
        return self

    def restore(self):
        """还原微信窗口。"""
        self._require_window().restore()
        return self

    def maximize(self):
        """最大化微信窗口。"""
        self._require_window().maximize()
        return self

    def is_running(self) -> bool:
        """微信主窗口是否仍然存在。"""
        try:
            return bool(self.window) and self.window.exists()
        except Exception:  # noqa: BLE001
            return False

    # ------------------------------------------------------------ 等待 ----
    def wait_for(
        self,
        predicate: Callable[[], bool],
        timeout: Optional[float] = None,
        interval: Optional[float] = None,
        message: str = "等待条件超时",
    ) -> bool:
        """轮询等待某个条件成立。

        :param predicate: 返回 bool 的可调用对象
        :param timeout: 超时时间（秒），默认取配置
        :param interval: 轮询间隔（秒），默认取配置
        :raises WeChatTimeoutError: 超时仍未成立
        """
        timeout = self.config.default_timeout if timeout is None else timeout
        interval = self.config.poll_interval if interval is None else interval
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                if predicate():
                    return True
            except Exception:  # noqa: BLE001 - 轮询期间控件可能尚未就绪
                pass
            time.sleep(interval)
        raise WeChatTimeoutError(message)

    def find_control(
        self,
        timeout: Optional[float] = None,
        **criteria,
    ):
        """按条件查找单个控件，带超时等待。

        :param criteria: 传给 pywinauto ``child_window`` 的查找条件，
            例如 ``title="搜索"``、``control_type="Edit"``、``auto_id=...``
        :raises ControlNotFoundError: 超时仍未找到
        """
        win = self._require_window()
        timeout = self.config.default_timeout if timeout is None else timeout
        ctrl = win.child_window(**criteria)
        try:
            ctrl.wait("exists ready", timeout=timeout)
        except Exception as exc:  # noqa: BLE001
            raise ControlNotFoundError(f"未找到控件: {criteria}，错误: {exc}") from exc
        return ctrl

    def control_exists(self, **criteria) -> bool:
        """判断某控件当前是否存在（不等待）。"""
        try:
            return self._require_window().child_window(**criteria).exists()
        except Exception:  # noqa: BLE001
            return False

    def button_exists(self, name: str) -> bool:
        """判断某个按钮是否存在。"""
        return self.control_exists(title=name, control_type="Button")

    def click_button(self, name: str, timeout: Optional[float] = None):
        """点击指定名称的按钮（更多、表情、语音、截图等）。"""
        btn = self.find_control(title=name, control_type="Button", timeout=timeout)
        btn.click_input()
        return self

    def get_control_text(self, **criteria) -> str:
        """获取某控件的文本内容。"""
        ctrl = self.find_control(**criteria)
        try:
            return ctrl.window_text()
        except Exception:  # noqa: BLE001
            return ""

    # ------------------------------------------------------- 调试辅助 ----
    def dump_control_tree(self, depth: Optional[int] = None) -> str:
        """打印并返回窗口的控件树，用于调试定位控件。

        :param depth: 打印深度，None 表示全部
        """
        import io
        from contextlib import redirect_stdout

        win = self._require_window()
        buf = io.StringIO()
        with redirect_stdout(buf):
            if depth is None:
                win.print_control_identifiers()
            else:
                win.print_control_identifiers(depth=depth)
        tree = buf.getvalue()
        print(tree)
        return tree

    def list_descendants(self, control_type: Optional[str] = None) -> List[str]:
        """列出窗口内所有（或指定类型）后代控件的文本，便于排查。"""
        win = self._require_window()
        kwargs = {"control_type": control_type} if control_type else {}
        result = []
        for ctrl in win.descendants(**kwargs):
            try:
                result.append(ctrl.window_text())
            except Exception:  # noqa: BLE001
                continue
        return result

    # -------------------------------------------------------- 内部工具 ----
    def _require_window(self):
        if not getattr(self, "window", None):
            raise WeChatNotFoundError("尚未连接微信窗口，请先调用 connect()。")
        return self.window
