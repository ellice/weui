# -*- coding: utf-8 -*-
"""窗口与控件通用操作 Mixin。

封装窗口唤起/置顶/最小化、控件等待与查找、控件树打印、按钮点击等通用能力。
依赖 pywinauto 的 ``uia`` 后端（微信 PC 版控件基于 UIAutomation）。
"""

from __future__ import annotations

import time
from typing import List, Optional, Tuple

from .exceptions import (
    ControlNotFoundError,
    ControlTimeoutError,
    WindowNotFoundError,
)


class ControlMixin:
    """提供窗口与控件层面的通用操作，需由持有 ``self.window`` 的类继承。"""

    # 由 core.WeChat 在连接后赋值
    app = None
    window = None
    timeout: float = 10.0

    # ----------------------------- 窗口操作 ----------------------------- #
    def show(self) -> None:
        """唤起并激活微信主窗口（还原 + 置前）。"""
        win = self._win()
        try:
            if win.is_minimized():
                win.restore()
        except Exception:  # noqa: BLE001
            pass
        win.set_focus()

    def top_most(self, enable: bool = True) -> None:
        """设置 / 取消窗口置顶。"""
        self._win().set_focus()
        try:
            self._win().wrapper_object().iface_window.SetTopmost(enable)  # type: ignore[attr-defined]
        except Exception:  # noqa: BLE001
            # 退化方案：仅置前
            self._win().set_focus()

    def minimize(self) -> None:
        """最小化主窗口。"""
        self._win().minimize()

    def restore(self) -> None:
        """还原主窗口。"""
        self._win().restore()
        self._win().set_focus()

    def maximize(self) -> None:
        self._win().maximize()

    def is_window_alive(self) -> bool:
        """主窗口是否仍存在。"""
        try:
            return bool(self.window) and self.window.exists()
        except Exception:  # noqa: BLE001
            return False

    # ----------------------------- 控件等待 ----------------------------- #
    def wait_control(self, *, timeout: Optional[float] = None,
                     ready: bool = True, **criteria):
        """等待控件出现 / 就绪并返回。

        :param timeout: 超时秒数，默认使用 ``self.timeout``。
        :param ready: True 等待可见且可用，False 仅等待存在。
        :param criteria: pywinauto child_window 查找条件，如
            ``control_type='Edit'``、``title='发送'``、``auto_id=...``。
        :raises ControlTimeoutError: 超时未找到。
        """
        timeout = self.timeout if timeout is None else timeout
        ctrl = self._win().child_window(**criteria)
        wait_for = "ready" if ready else "exists"
        try:
            ctrl.wait(wait_for, timeout=timeout)
        except Exception as exc:  # noqa: BLE001
            raise ControlTimeoutError(
                f"等待控件超时({timeout}s): {criteria} -> {exc}"
            ) from exc
        return ctrl

    def find(self, *, parent=None, **criteria):
        """查找单个控件，未找到抛 :class:`ControlNotFoundError`。"""
        base = parent if parent is not None else self._win()
        ctrl = base.child_window(**criteria)
        if not ctrl.exists():
            raise ControlNotFoundError(f"控件不存在: {criteria}")
        return ctrl

    def find_all(self, *, parent=None, **criteria) -> List:
        """查找所有匹配控件，返回 wrapper 列表（可能为空）。"""
        base = parent if parent is not None else self._win()
        try:
            return base.children(**criteria) if criteria else base.children()
        except Exception:  # noqa: BLE001
            return []

    def exists(self, *, parent=None, **criteria) -> bool:
        """判断控件 / 按钮是否存在。"""
        base = parent if parent is not None else self._win()
        try:
            return base.child_window(**criteria).exists()
        except Exception:  # noqa: BLE001
            return False

    # ----------------------------- 控件读写 ----------------------------- #
    def get_text(self, *, parent=None, join: str = "\n", **criteria) -> str:
        """获取控件文本（合并 window_text 与 texts()）。"""
        ctrl = self.find(parent=parent, **criteria)
        try:
            texts = ctrl.texts()
            return join.join(t for t in texts if t)
        except Exception:  # noqa: BLE001
            return ctrl.window_text()

    def click_button(self, title: Optional[str] = None, *, parent=None,
                     control_type: str = "Button", **criteria) -> None:
        """点击任意可见按钮（更多、表情、语音、截图等）。

        :param title: 按钮名称（与 control_type 共同定位）。
        """
        if title is not None:
            criteria["title"] = title
        criteria["control_type"] = control_type
        ctrl = self.find(parent=parent, **criteria)
        ctrl.click_input()

    def set_edit_text(self, text: str, *, parent=None, **criteria) -> None:
        """直接给 Edit 控件赋值（适合无特殊符号场景）。"""
        ctrl = self.find(parent=parent, control_type="Edit", **criteria)
        ctrl.set_edit_text(text)

    # ----------------------------- 调试辅助 ----------------------------- #
    def dump_tree(self, depth: int = 12, filename: Optional[str] = None) -> str:
        """打印 / 导出全部控件树，用于调试定位。

        :param depth: 遍历深度。
        :param filename: 若提供则同时写入文件。
        :returns: 控件树文本。
        """
        import io
        import contextlib

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            self._win().print_control_identifiers(depth=depth)
        tree = buf.getvalue()
        if filename:
            with open(filename, "w", encoding="utf-8") as fh:
                fh.write(tree)
        return tree

    def rect_center(self, ctrl) -> Tuple[int, int]:
        """返回控件矩形的屏幕中心坐标（用于鼠标点击 / 滚动）。"""
        r = ctrl.rectangle()
        return (r.left + r.width() // 2), (r.top + r.height() // 2)

    # ----------------------------- 内部工具 ----------------------------- #
    def _win(self):
        if self.window is None:
            raise WindowNotFoundError("尚未连接微信主窗口，请先调用 connect()/show()")
        return self.window
