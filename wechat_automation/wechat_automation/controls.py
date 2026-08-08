"""模块四（控件部分）：控件通用操作与调试工具。

提供：等待控件、超时判断、异常捕获、导出控件树、点击任意可见按钮、
读取控件文本、判断按钮是否存在、清空输入/搜索框等通用能力。
"""

from __future__ import annotations

import time
from typing import Any, List, Optional

from .exceptions import ControlNotFoundError


class ControlHelper:
    """围绕微信主窗口的控件工具集。

    :param main: 已连接的主窗口包装对象（来自 :class:`WeChatWindow`）。
    """

    def __init__(self, main: Any) -> None:
        self.main = main

    # ------------------------------------------------------ 等待 / 查找
    def wait_control(self, timeout: float = 10.0, retry_interval: float = 0.3,
                     **criteria: Any) -> Any:
        """在超时时间内等待某个控件出现并返回它。

        :param criteria: 传给 ``main.child_window`` 的查找条件，例如
            ``title="发送"``、``control_type="Button"``、``auto_id="xxx"``。
        :raises ControlNotFoundError: 超时仍未找到。
        """
        deadline = time.time() + timeout
        last_err: Optional[Exception] = None
        while time.time() < deadline:
            try:
                ctrl = self.main.child_window(**criteria)
                if ctrl.exists():
                    return ctrl
            except Exception as exc:  # noqa: BLE001
                last_err = exc
            time.sleep(retry_interval)
        raise ControlNotFoundError(
            f"等待控件超时（{timeout}s）：{criteria}；最后错误：{last_err!r}"
        )

    def exists(self, timeout: float = 0.0, **criteria: Any) -> bool:
        """判断控件（按钮等）是否存在，不抛异常。"""
        try:
            self.wait_control(timeout=timeout, **criteria)
            return True
        except ControlNotFoundError:
            return False

    def find(self, **criteria: Any) -> Any:
        """直接返回控件包装对象（不等待，可能不存在）。"""
        return self.main.child_window(**criteria)

    # ------------------------------------------------------ 读取 / 点击
    def get_text(self, timeout: float = 5.0, **criteria: Any) -> str:
        """读取控件文本（window_text）。"""
        ctrl = self.wait_control(timeout=timeout, **criteria)
        return ctrl.window_text()

    def get_texts(self, timeout: float = 5.0, **criteria: Any) -> List[str]:
        """读取控件的多行文本（texts()）。"""
        ctrl = self.wait_control(timeout=timeout, **criteria)
        return list(ctrl.texts())

    def click_button(self, timeout: float = 5.0, **criteria: Any) -> None:
        """点击任意可见按钮（更多、表情、语音、截图等）。

        优先使用 UIA ``invoke`` 模式，失败时退回普通 ``click``。
        """
        ctrl = self.wait_control(timeout=timeout, **criteria)
        try:
            ctrl.invoke()
        except Exception:  # noqa: BLE001 - 非 invoke 控件退回点击
            ctrl.click_input()

    def click(self, timeout: float = 5.0, double: bool = False,
              button: str = "left", **criteria: Any) -> None:
        """在控件上做真实鼠标点击（可双击、右键）。"""
        ctrl = self.wait_control(timeout=timeout, **criteria)
        ctrl.click_input(button=button, double=double)

    # ------------------------------------------------------ 清空输入
    def clear_edit(self, timeout: float = 5.0, **criteria: Any) -> None:
        """清空某个 Edit 输入框（搜索框 / 聊天输入框通用）。

        先聚焦，再 ``Ctrl+A`` 全选并删除。
        """
        ctrl = self.wait_control(timeout=timeout, **criteria)
        ctrl.set_focus()
        try:
            ctrl.type_keys("^a{BACKSPACE}", set_foreground=True)
        except Exception:  # noqa: BLE001 - 退回 set_edit_text
            try:
                ctrl.set_edit_text("")
            except Exception:  # noqa: BLE001
                pass

    # ------------------------------------------------------ 调试
    def dump_tree(self, depth: Optional[int] = None) -> str:
        """导出主窗口的完整控件树（用于调试定位）。

        返回字符串形式，便于写日志/文件。
        """
        import io
        from contextlib import redirect_stdout

        buf = io.StringIO()
        with redirect_stdout(buf):
            if depth is None:
                self.main.print_control_identifiers()
            else:
                self.main.print_control_identifiers(depth=depth)
        return buf.getvalue()

    def list_buttons(self) -> List[str]:
        """列出主窗口下所有按钮的文本，辅助定位。"""
        names: List[str] = []
        try:
            for ctrl in self.main.descendants(control_type="Button"):
                text = ctrl.window_text()
                if text:
                    names.append(text)
        except Exception:  # noqa: BLE001
            pass
        return names
