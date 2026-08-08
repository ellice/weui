"""剪贴板工具：文本、文件路径写入剪贴板。

文本使用 ``pyperclip``（跨平台，便于在非 Windows 上做纯逻辑测试）。
文件/图片的“复制文件对象”能力依赖 Windows 剪贴板的 ``CF_HDROP`` 格式，
只能在 Windows 上通过 ``pywin32`` 实现，见 :func:`copy_files`。
"""

from __future__ import annotations

import os
from typing import Iterable, List

from ._compat import IS_WINDOWS
from .exceptions import DependencyMissingError, WeChatAutomationError


def copy_text(text: str) -> None:
    """把文本写入系统剪贴板。"""
    try:
        import pyperclip  # type: ignore
    except ImportError as exc:  # pragma: no cover
        raise DependencyMissingError(
            "未安装 pyperclip，请执行 `pip install pyperclip`。"
        ) from exc
    pyperclip.copy(text)


def get_text() -> str:
    """读取系统剪贴板文本。"""
    try:
        import pyperclip  # type: ignore
    except ImportError as exc:  # pragma: no cover
        raise DependencyMissingError(
            "未安装 pyperclip，请执行 `pip install pyperclip`。"
        ) from exc
    return pyperclip.paste()


def _normalize_paths(paths: Iterable[str]) -> List[str]:
    """校验并规范化文件路径列表。"""
    result: List[str] = []
    for p in paths:
        ap = os.path.abspath(os.path.expanduser(p))
        if not os.path.exists(ap):
            raise WeChatAutomationError(f"文件不存在：{p}")
        result.append(ap)
    if not result:
        raise WeChatAutomationError("未提供任何文件路径。")
    return result


def copy_files(paths: Iterable[str]) -> List[str]:
    """把一个或多个**文件对象**复制到剪贴板（Windows ``CF_HDROP``）。

    之后在微信输入框 ``Ctrl+V`` 即可作为文件/图片发送。这是本项目发送
    文件的核心原理（不去点击微信自带的“文件”弹窗，规避控件难定位问题）。

    :param paths: 本地文件路径，可多个（批量发送）。
    :return: 规范化后的绝对路径列表。
    """
    files = _normalize_paths(paths)
    if not IS_WINDOWS:
        raise DependencyMissingError(
            "复制文件对象到剪贴板依赖 Windows 剪贴板 CF_HDROP，"
            f"当前平台不支持；文件列表：{files}"
        )
    try:  # pragma: no cover - 仅 Windows 运行
        import struct

        import win32clipboard  # type: ignore
        import win32con  # type: ignore
    except ImportError as exc:  # pragma: no cover
        raise DependencyMissingError(
            "复制文件需要 pywin32，请执行 `pip install pywin32`。"
        ) from exc

    # 构造 DROPFILES 结构：头部 20 字节 + 以 \0 分隔、以 \0\0 结尾的宽字符路径。
    files_str = "\0".join(files) + "\0\0"
    files_bytes = files_str.encode("utf-16-le")
    # DROPFILES: pFiles(offset)=20, pt(0,0), fNC=0, fWide=1
    dropfiles = struct.pack("<IIIII", 20, 0, 0, 0, 1) + files_bytes

    win32clipboard.OpenClipboard()
    try:
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32con.CF_HDROP, dropfiles)
    finally:
        win32clipboard.CloseClipboard()
    return files
