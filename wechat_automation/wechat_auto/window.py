"""窗口与控件通用操作。

对应需求"四、窗口与控件通用操作"：

- 自动唤起微信窗口、置顶、最小化 / 还原
- 等待控件加载、超时判断、异常捕获
- 打印导出全部控件树，用于调试定位
- 点击任意可见按钮、获取控件文本、判断按钮是否存在
- 清空搜索框、清空输入框内容

:class:`WeChatWindow` 是所有上层能力（消息、文件、会话）共享的基础设施。
"""

from __future__ import annotations

import io
import logging
import subprocess
import time
from typing import Any, Callable, List, Optional

from .config import WeChatConfig, default_config
from .exceptions import (
    ControlNotFoundError,
    TimeoutError,
    WindowNotFoundError,
)
from .input_utils import InputController

logger = logging.getLogger("wechat_auto.window")


class WeChatWindow:
    """封装对微信主窗口及其内部控件的通用操作。"""

    def __init__(self, config: Optional[WeChatConfig] = None):
        self.config = config or default_config
        self.input = InputController(self.config)
        self._app = None          # pywinauto.Application
        self._main = None         # 主窗口 WindowSpecification / wrapper

    # ————————————————————— 连接 / 唤起 —————————————————————
    @property
    def main(self):
        """当前主窗口 wrapper，未连接时抛出异常。"""
        if self._main is None:
            raise WindowNotFoundError("尚未连接微信主窗口，请先调用 connect()。")
        return self._main

    def is_connected(self) -> bool:
        return self._main is not None

    def connect(self, launch_if_needed: bool = True) -> "WeChatWindow":
        """连接到微信主窗口；找不到且允许时自动拉起进程并重试。

        Args:
            launch_if_needed: 未找到窗口时是否尝试启动微信可执行文件。

        Returns:
            self，便于链式调用。
        """
        from pywinauto import Application  # type: ignore

        try:
            self._app = Application(backend=self.config.backend).connect(
                class_name=self.config.window_class,
                timeout=self.config.medium_delay,
            )
        except Exception:
            if not launch_if_needed:
                raise WindowNotFoundError(
                    "未找到微信窗口，且未启用自动启动。"
                )
            self._launch_process()
            self._app = self._wait_app()

        self._main = self._app.window(class_name=self.config.window_class)
        try:
            self._main.wait("exists ready", timeout=self.config.default_timeout)
        except Exception as exc:
            raise WindowNotFoundError(f"微信窗口加载超时：{exc}") from exc
        return self

    def _launch_process(self) -> None:
        logger.info("尝试启动微信：%s", self.config.process_path)
        try:
            subprocess.Popen([self.config.process_path])
        except Exception as exc:  # pragma: no cover
            raise WindowNotFoundError(
                f"无法启动微信进程：{self.config.process_path}（{exc}）"
            ) from exc

    def _wait_app(self):
        from pywinauto import Application  # type: ignore

        deadline = time.time() + self.config.default_timeout
        last_exc: Optional[Exception] = None
        while time.time() < deadline:
            try:
                return Application(backend=self.config.backend).connect(
                    class_name=self.config.window_class,
                    timeout=self.config.short_delay,
                )
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                time.sleep(self.config.retry_interval)
        raise WindowNotFoundError(
            f"启动后仍未找到微信窗口（可能未登录）：{last_exc}"
        )

    # ————————————————————— 窗口状态 —————————————————————
    def activate(self) -> None:
        """唤起并激活窗口（还原 + 置于前台 + 获取焦点）。"""
        win = self.main
        try:
            if win.is_minimized():
                win.restore()
        except Exception:  # noqa: BLE001 - 某些后端无 is_minimized
            pass
        win.set_focus()
        self.input.sleep_short()

    def bring_to_top(self) -> None:
        """将窗口置顶到最前。"""
        self.main.set_focus()

    def minimize(self) -> None:
        self.main.minimize()

    def restore(self) -> None:
        self.main.restore()

    def maximize(self) -> None:
        self.main.maximize()

    # ————————————————————— 控件查找 / 等待 —————————————————————
    def find_control(self, **criteria) -> Any:
        """在主窗口下查找控件（不等待），返回 WindowSpecification。"""
        return self.main.child_window(**criteria)

    def wait_control(
        self,
        timeout: Optional[float] = None,
        state: str = "exists ready",
        **criteria,
    ) -> Any:
        """等待控件满足指定状态，超时抛 :class:`ControlNotFoundError`。

        Args:
            timeout: 超时时间（秒），默认取配置。
            state: pywinauto 的 ``wait`` 状态串，如 ``"exists visible ready"``。
            **criteria: 传给 ``child_window`` 的匹配条件。
        """
        timeout = timeout if timeout is not None else self.config.default_timeout
        ctrl = self.main.child_window(**criteria)
        try:
            ctrl.wait(state, timeout=timeout)
        except Exception as exc:  # noqa: BLE001
            raise ControlNotFoundError(
                f"等待控件超时（{criteria}）：{exc}"
            ) from exc
        return ctrl

    def exists(self, **criteria) -> bool:
        """判断控件是否存在（不抛异常）。可用于"判断按钮是否存在"。"""
        try:
            return self.main.child_window(**criteria).exists(
                timeout=self.config.short_delay
            )
        except Exception:  # noqa: BLE001
            return False

    def wait_until(
        self,
        predicate: Callable[[], bool],
        timeout: Optional[float] = None,
        message: str = "条件等待超时",
    ) -> None:
        """轮询等待任意布尔条件成立，超时抛 :class:`TimeoutError`。"""
        timeout = timeout if timeout is not None else self.config.default_timeout
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                if predicate():
                    return
            except Exception:  # noqa: BLE001
                pass
            time.sleep(self.config.retry_interval)
        raise TimeoutError(message)

    # ————————————————————— 控件读写 / 点击 —————————————————————
    def get_text(self, **criteria) -> str:
        """获取控件文本（window_text）。"""
        ctrl = self.find_control(**criteria)
        try:
            return ctrl.window_text()
        except Exception as exc:  # noqa: BLE001
            raise ControlNotFoundError(f"读取控件文本失败（{criteria}）：{exc}") from exc

    def click_button(self, title: str, timeout: Optional[float] = None) -> None:
        """按标题点击按钮（更多、表情、语音、截图等可见按钮）。"""
        btn = self.wait_control(
            timeout=timeout, title=title, control_type="Button"
        )
        btn.click_input()
        self.input.sleep_short()

    def click_control(self, timeout: Optional[float] = None, **criteria) -> None:
        """点击任意匹配到的控件。"""
        ctrl = self.wait_control(timeout=timeout, **criteria)
        ctrl.click_input()
        self.input.sleep_short()

    def button_exists(self, title: str) -> bool:
        return self.exists(title=title, control_type="Button")

    # ————————————————————— 搜索框 / 输入框 —————————————————————
    def get_search_edit(self):
        """返回顶部搜索框控件。"""
        return self.wait_control(
            title=self.config.search_box_title, control_type="Edit"
        )

    def clear_search_box(self) -> None:
        """清空搜索框内容。"""
        edit = self.get_search_edit()
        edit.click_input()
        self.input.sleep_short()
        self.input.clear_edit()

    def get_message_edit(self):
        """返回聊天输入框控件（兼容多个候选控件名）。"""
        last_exc: Optional[Exception] = None
        for name in self.config.edit_box_title_candidates:
            try:
                ctrl = self.main.child_window(title=name, control_type="Edit")
                if ctrl.exists(timeout=self.config.short_delay):
                    return ctrl
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
        # 退化：返回窗口内第一个 Edit（排除搜索框）
        try:
            edits = self.main.descendants(control_type="Edit")
            for e in edits:
                if e.window_text() != self.config.search_box_title:
                    return e
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
        raise ControlNotFoundError(f"未找到聊天输入框：{last_exc}")

    def focus_message_edit(self):
        """聚焦聊天输入框并返回控件。"""
        edit = self.get_message_edit()
        edit.click_input()
        self.input.sleep_short()
        return edit

    def clear_message_edit(self) -> None:
        """清空聊天输入框内容。"""
        self.focus_message_edit()
        self.input.clear_edit()

    # ————————————————————— 控件树导出（调试） —————————————————————
    def dump_control_tree(self, depth: Optional[int] = None) -> str:
        """导出主窗口控件树文本，用于调试定位控件名 / 类型。

        Args:
            depth: 遍历深度，None 表示全部层级。

        Returns:
            控件树的文本表示。
        """
        buffer = io.StringIO()
        try:
            self.main.print_control_identifiers(depth=depth, filename=None)
            # print_control_identifiers 直接写 stdout，这里改用 dump_tree 兜底
        except Exception:  # noqa: BLE001
            pass
        # 通过重定向 stdout 捕获输出
        import contextlib

        with contextlib.redirect_stdout(buffer):
            self.main.print_control_identifiers(depth=depth)
        return buffer.getvalue()

    def save_control_tree(self, path: str, depth: Optional[int] = None) -> str:
        """将控件树导出到文件，返回文件路径。"""
        tree = self.dump_control_tree(depth=depth)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(tree)
        return path
