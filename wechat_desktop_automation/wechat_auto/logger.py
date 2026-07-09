"""日志工具。

提供一个统一的 logger 获取入口，默认输出到控制台，
调用方可以通过 :func:`set_level` 调整日志级别。
"""

from __future__ import annotations

import logging
import sys

_LOGGER_NAME = "wechat_auto"
_DEFAULT_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

_configured = False


def get_logger(name: str | None = None) -> logging.Logger:
    """获取库内统一的 logger。

    :param name: 子模块名称，最终 logger 名为 ``wechat_auto.<name>``。
    """
    global _configured
    root = logging.getLogger(_LOGGER_NAME)
    if not _configured:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(_DEFAULT_FORMAT))
        root.addHandler(handler)
        root.setLevel(logging.INFO)
        # 避免向上冒泡导致重复打印
        root.propagate = False
        _configured = True

    if name:
        return root.getChild(name)
    return root


def set_level(level: int | str) -> None:
    """设置全局日志级别，例如 ``logging.DEBUG`` 或 ``"DEBUG"``。"""
    get_logger().setLevel(level)
