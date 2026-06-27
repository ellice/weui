"""控件通用操作：等待、查找、控件树导出、按钮点击/存在性判断、取文本。

这些函数对任意 pywinauto 控件包装器(WrapperObject)通用，
不局限于微信，方便调试定位。
"""

from __future__ import annotations

import time
from typing import List, Optional

from .exceptions import ControlNotFoundError, WaitTimeoutError


def wait_visible(ctrl, timeout: float = 10.0, interval: float = 0.3):
    """等待控件存在且可见，超时抛 WaitTimeoutError。返回该控件。"""
    deadline = time.time() + timeout
    last_exc = None
    while time.time() < deadline:
        try:
            if ctrl.exists() and ctrl.is_visible():
                return ctrl
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
        time.sleep(interval)
    raise WaitTimeoutError(f"等待控件可见超时({timeout}s): {last_exc}")


def exists(ctrl) -> bool:
    """安全判断控件是否存在。"""
    try:
        return bool(ctrl.exists())
    except Exception:  # noqa: BLE001
        return False


def is_button_present(parent, title: str, control_type: str = "Button") -> bool:
    """判断父容器下是否存在指定标题的按钮/控件。"""
    try:
        ctrl = parent.child_window(title=title, control_type=control_type)
        return bool(ctrl.exists())
    except Exception:  # noqa: BLE001
        return False


def click_button(parent, title: str, control_type: str = "Button", timeout: float = 5.0):
    """按标题点击按钮（更多、表情、语音、截图等）。"""
    ctrl = parent.child_window(title=title, control_type=control_type)
    wait_visible(ctrl, timeout=timeout)
    ctrl.click_input()
    return ctrl


def get_text(ctrl) -> str:
    """获取控件文本，兼容 window_text / texts / value。"""
    try:
        txt = ctrl.window_text()
        if txt:
            return txt
    except Exception:  # noqa: BLE001
        pass
    try:
        texts = ctrl.texts()
        return "".join(t for t in texts if t)
    except Exception:  # noqa: BLE001
        return ""


def dump_control_tree(ctrl, max_depth: int = 8) -> str:
    """导出控件树为可读字符串，用于调试定位控件。

    类似 ctrl.print_control_identifiers，但返回字符串便于写日志/文件。
    """
    lines: List[str] = []

    def _walk(node, depth: int):
        if depth > max_depth:
            return
        indent = "  " * depth
        try:
            ctype = node.element_info.control_type
        except Exception:  # noqa: BLE001
            ctype = "?"
        try:
            name = node.window_text()
        except Exception:  # noqa: BLE001
            name = ""
        try:
            cls = node.element_info.class_name
        except Exception:  # noqa: BLE001
            cls = ""
        try:
            rect = node.rectangle()
        except Exception:  # noqa: BLE001
            rect = ""
        lines.append(f"{indent}[{ctype}] '{name}' class={cls} {rect}")
        try:
            for child in node.children():
                _walk(child, depth + 1)
        except Exception:  # noqa: BLE001
            pass

    _walk(ctrl, 0)
    return "\n".join(lines)


def clear_edit(edit_ctrl) -> None:
    """清空 Edit 输入框内容（全选 + 删除）。"""
    try:
        edit_ctrl.set_focus()
    except Exception:  # noqa: BLE001
        pass
    try:
        # 优先用控件自带方法
        edit_ctrl.set_edit_text("")
        return
    except Exception:  # noqa: BLE001
        pass
    from .input_utils import select_all, press_backspace

    select_all()
    time.sleep(0.05)
    press_backspace()
