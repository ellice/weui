"""平台依赖的延迟/保护式导入。

微信桌面自动化只能运行在 Windows 上（依赖 ``pywinauto`` / ``pywin32``）。
但是为了让本包能在任意平台被导入、做静态检查、跑单元测试，这里把所有
Windows 专有依赖收敛到一处，按需懒加载，缺失时抛出统一异常。
"""

from __future__ import annotations

import sys
from typing import Any

from .exceptions import DependencyNotInstalledError

IS_WINDOWS = sys.platform.startswith("win")


def require_windows() -> None:
    """断言当前处于 Windows 平台，否则报错。"""
    if not IS_WINDOWS:
        raise DependencyNotInstalledError(
            "桌面版微信自动化依赖 Windows 平台与 pywinauto/pywin32，"
            f"当前平台为 {sys.platform!r}，无法实际操作微信窗口。"
        )


def load_pywinauto() -> Any:
    """加载 pywinauto，缺失时抛出统一异常。"""
    require_windows()
    try:
        import pywinauto  # type: ignore

        return pywinauto
    except ImportError as exc:  # pragma: no cover - 取决于运行环境
        raise DependencyNotInstalledError(
            "未安装 pywinauto，请执行: pip install pywinauto"
        ) from exc


def load_keyboard() -> Any:
    """加载 pywinauto.keyboard 模块。"""
    require_windows()
    try:
        from pywinauto import keyboard  # type: ignore

        return keyboard
    except ImportError as exc:  # pragma: no cover
        raise DependencyNotInstalledError(
            "未安装 pywinauto，请执行: pip install pywinauto"
        ) from exc


def load_mouse() -> Any:
    """加载 pywinauto.mouse 模块。"""
    require_windows()
    try:
        from pywinauto import mouse  # type: ignore

        return mouse
    except ImportError as exc:  # pragma: no cover
        raise DependencyNotInstalledError(
            "未安装 pywinauto，请执行: pip install pywinauto"
        ) from exc


def load_win32() -> Any:
    """加载 pywin32 中的 win32clipboard / win32con 等。返回一个命名空间对象。"""
    require_windows()
    try:
        import win32clipboard  # type: ignore
        import win32con  # type: ignore

        class _Win32:
            clipboard = win32clipboard
            con = win32con

        return _Win32
    except ImportError as exc:  # pragma: no cover
        raise DependencyNotInstalledError(
            "未安装 pywin32，请执行: pip install pywin32"
        ) from exc
