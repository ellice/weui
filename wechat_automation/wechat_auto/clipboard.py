# -*- coding: utf-8 -*-
"""剪贴板工具：支持文本与文件（CF_HDROP）写入。

文件发送的核心原理：把本地文件路径以 ``CF_HDROP`` 格式写入剪贴板，
然后在微信输入框里 ``Ctrl+V`` 粘贴，微信会自动识别为文件 / 图片并附带发送。
"""

from __future__ import annotations

import os
import time
from typing import List, Sequence, Union

from .exceptions import ClipboardError, FileSendError

try:  # pyperclip 用于纯文本，跨平台
    import pyperclip
except Exception:  # pragma: no cover - 环境缺失时降级
    pyperclip = None


def copy_text(text: str, retries: int = 3, interval: float = 0.1) -> None:
    """把纯文本写入剪贴板。

    :param text: 待写入的文本，支持换行、特殊符号、空格。
    :param retries: 写入失败时的重试次数（剪贴板偶发被其它进程占用）。
    :param interval: 每次重试的间隔秒数。
    """
    last_err: Exception | None = None
    for _ in range(max(1, retries)):
        try:
            if pyperclip is not None:
                pyperclip.copy(text)
            else:
                _win32_copy_text(text)
            return
        except Exception as exc:  # noqa: BLE001
            last_err = exc
            time.sleep(interval)
    raise ClipboardError(f"写入文本到剪贴板失败: {last_err}")


def paste_text() -> str:
    """读取剪贴板中的纯文本。"""
    try:
        if pyperclip is not None:
            return pyperclip.paste()
        return _win32_paste_text()
    except Exception as exc:  # noqa: BLE001
        raise ClipboardError(f"读取剪贴板文本失败: {exc}") from exc


def copy_files(paths: Union[str, Sequence[str]], retries: int = 3,
               interval: float = 0.15) -> List[str]:
    """把一个或多个本地文件路径写入剪贴板（CF_HDROP）。

    :param paths: 单个路径字符串或路径列表。
    :param retries: 重试次数。
    :param interval: 重试间隔。
    :returns: 实际写入的绝对路径列表。
    :raises FileSendError: 当任意路径不存在时抛出。
    """
    if isinstance(paths, str):
        paths = [paths]

    abs_paths: List[str] = []
    for p in paths:
        ap = os.path.abspath(os.path.expanduser(p))
        if not os.path.exists(ap):
            raise FileSendError(f"待发送文件不存在: {ap}")
        abs_paths.append(ap)

    last_err: Exception | None = None
    for _ in range(max(1, retries)):
        try:
            _win32_copy_files(abs_paths)
            return abs_paths
        except Exception as exc:  # noqa: BLE001
            last_err = exc
            time.sleep(interval)
    raise ClipboardError(f"写入文件到剪贴板失败: {last_err}")


def clear() -> None:
    """清空剪贴板内容。"""
    try:
        import win32clipboard  # type: ignore

        win32clipboard.OpenClipboard()
        try:
            win32clipboard.EmptyClipboard()
        finally:
            win32clipboard.CloseClipboard()
    except ImportError:
        if pyperclip is not None:
            pyperclip.copy("")
        else:
            raise ClipboardError("当前环境无法清空剪贴板（缺少 pywin32 / pyperclip）")
    except Exception as exc:  # noqa: BLE001
        raise ClipboardError(f"清空剪贴板失败: {exc}") from exc


# --------------------------------------------------------------------------- #
# 底层 win32 实现（仅 Windows 可用）
# --------------------------------------------------------------------------- #
def _require_win32clipboard():
    try:
        import win32clipboard  # type: ignore

        return win32clipboard
    except ImportError as exc:  # pragma: no cover - 非 Windows 环境
        raise ClipboardError(
            "文件 / 文件路径剪贴板操作需要 pywin32，请在 Windows 上 `pip install pywin32`"
        ) from exc


def _win32_copy_text(text: str) -> None:
    win32clipboard = _require_win32clipboard()
    win32clipboard.OpenClipboard()
    try:
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardText(text, win32clipboard.CF_UNICODETEXT)
    finally:
        win32clipboard.CloseClipboard()


def _win32_paste_text() -> str:
    win32clipboard = _require_win32clipboard()
    win32clipboard.OpenClipboard()
    try:
        if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_UNICODETEXT):
            return win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT)
        return ""
    finally:
        win32clipboard.CloseClipboard()


def _win32_copy_files(abs_paths: Sequence[str]) -> None:
    """使用 CF_HDROP 把文件路径写入剪贴板。"""
    import struct

    win32clipboard = _require_win32clipboard()
    win32con = _import_win32con()

    # DROPFILES 结构：
    #   pFiles(偏移, DWORD) | pt.x(LONG) | pt.y(LONG) | fNC(BOOL) | fWide(BOOL)
    # 之后接以 \0 分隔、并以 \0\0 结尾的宽字符路径串。
    offset = 20  # DROPFILES 结构大小（5 个 4 字节字段）
    dropfiles = struct.pack("Iiiii", offset, 0, 0, 0, 1)  # fWide=1 表示 Unicode
    files_str = "".join(p + "\0" for p in abs_paths) + "\0"
    data = dropfiles + files_str.encode("utf-16-le")

    win32clipboard.OpenClipboard()
    try:
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32con.CF_HDROP, data)
    finally:
        win32clipboard.CloseClipboard()


def _import_win32con():
    try:
        import win32con  # type: ignore

        return win32con
    except ImportError:  # pragma: no cover
        class _Fallback:
            CF_HDROP = 15

        return _Fallback()
