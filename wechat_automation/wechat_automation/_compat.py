"""平台与依赖兼容层。

``pywinauto`` 只能在 Windows 上运行。为了让本包在 Linux/macOS 上也能被
导入（用于代码检查、纯逻辑单测、文档生成），这里对第三方依赖做**惰性导入**：

- 只有真正调用需要操作系统 UI 的能力时，才会去 import ``pywinauto``；
- 在非 Windows 平台或缺少依赖时，抛出清晰的 :class:`DependencyMissingError`。

这样 ``import wechat_automation`` 永远不会因为环境缺依赖而失败。
"""

from __future__ import annotations

import sys
from typing import Any

from .exceptions import DependencyMissingError

IS_WINDOWS = sys.platform.startswith("win")


def require_windows() -> None:
    """确认当前运行在 Windows 上，否则抛出异常。"""
    if not IS_WINDOWS:
        raise DependencyMissingError(
            "微信桌面自动化依赖 pywinauto，只能在 Windows 平台运行；"
            f"当前平台为 {sys.platform!r}。"
        )


def load_pywinauto() -> Any:
    """惰性加载 ``pywinauto`` 主模块。"""
    require_windows()
    try:
        import pywinauto  # type: ignore

        return pywinauto
    except ImportError as exc:  # pragma: no cover - 依赖缺失路径
        raise DependencyMissingError(
            "未安装 pywinauto，请先执行 `pip install pywinauto`。"
        ) from exc


def load_application() -> Any:
    """惰性加载 ``pywinauto.Application`` 类。"""
    require_windows()
    try:
        from pywinauto.application import Application  # type: ignore

        return Application
    except ImportError as exc:  # pragma: no cover
        raise DependencyMissingError(
            "未安装 pywinauto，请先执行 `pip install pywinauto`。"
        ) from exc


def load_keyboard() -> Any:
    """惰性加载 ``pywinauto.keyboard`` 模块（发送组合键）。"""
    require_windows()
    try:
        from pywinauto import keyboard  # type: ignore

        return keyboard
    except ImportError as exc:  # pragma: no cover
        raise DependencyMissingError(
            "未安装 pywinauto，请先执行 `pip install pywinauto`。"
        ) from exc


def load_mouse() -> Any:
    """惰性加载 ``pywinauto.mouse`` 模块（鼠标点击/拖拽/滚动）。"""
    require_windows()
    try:
        from pywinauto import mouse  # type: ignore

        return mouse
    except ImportError as exc:  # pragma: no cover
        raise DependencyMissingError(
            "未安装 pywinauto，请先执行 `pip install pywinauto`。"
        ) from exc
