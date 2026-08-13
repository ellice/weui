"""剪贴板工具：文本与文件（CF_HDROP）读写。

- 文本使用 ``pyperclip``（跨版本稳定）。
- 文件复制需要写入 ``CF_HDROP`` 结构，微信才能通过 Ctrl+V 识别为“文件/图片”。
  这一步依赖 pywin32（``win32clipboard`` / ``win32con``），仅在 Windows 可用。
"""

from __future__ import annotations

import os
import struct
import time
from typing import List, Sequence

from .exceptions import ClipboardError


def copy_text(text: str) -> None:
    """将纯文本写入剪贴板。"""
    try:
        import pyperclip

        pyperclip.copy(text)
    except Exception as exc:  # pragma: no cover - 依赖运行环境
        raise ClipboardError(f"写入文本到剪贴板失败: {exc}") from exc


def get_text() -> str:
    """读取剪贴板中的文本内容。"""
    try:
        import pyperclip

        return pyperclip.paste()
    except Exception as exc:  # pragma: no cover
        raise ClipboardError(f"读取剪贴板文本失败: {exc}") from exc


def _build_dropfiles(paths: Sequence[str]) -> bytes:
    """构造 Windows ``DROPFILES`` + 文件路径列表的二进制数据。

    结构：DROPFILES 头(20 字节) + 以 ``\\0`` 分隔、``\\0\\0`` 结尾的宽字符路径串。
    """
    # DROPFILES 结构:
    #   DWORD pFiles;  // 文件列表相对结构体的偏移(=20)
    #   POINT pt;      // x, y
    #   BOOL  fNC;
    #   BOOL  fWide;   // 是否为宽字符(Unicode)，这里为 True
    offset = 20
    header = struct.pack("Iiiii", offset, 0, 0, 0, 1)

    files_str = "".join(f"{os.path.abspath(p)}\0" for p in paths) + "\0"
    files_bytes = files_str.encode("utf-16-le")
    return header + files_bytes


def copy_files(paths: Sequence[str]) -> None:
    """把一个或多个本地文件路径写入剪贴板（CF_HDROP）。

    写入后即可在微信输入框执行 Ctrl+V，将文件作为附件/图片粘贴。

    :param paths: 本地文件的绝对或相对路径列表。
    """
    if not paths:
        raise ClipboardError("copy_files 需要至少一个文件路径")

    missing = [p for p in paths if not os.path.exists(p)]
    if missing:
        raise ClipboardError(f"以下文件不存在: {missing}")

    try:
        import win32clipboard
        import win32con
    except Exception as exc:  # pragma: no cover - 仅 Windows 可用
        raise ClipboardError(
            "复制文件到剪贴板需要 pywin32（win32clipboard），仅支持 Windows"
        ) from exc

    data = _build_dropfiles(paths)

    last_err: Exception | None = None
    # 剪贴板偶尔会被其它进程占用，做少量重试
    for _ in range(5):
        try:
            win32clipboard.OpenClipboard()
            try:
                win32clipboard.EmptyClipboard()
                win32clipboard.SetClipboardData(win32con.CF_HDROP, data)
            finally:
                win32clipboard.CloseClipboard()
            return
        except Exception as exc:  # pragma: no cover
            last_err = exc
            time.sleep(0.2)

    raise ClipboardError(f"复制文件到剪贴板失败: {last_err}")


def copy_file(path: str) -> None:
    """复制单个文件到剪贴板，:func:`copy_files` 的便捷封装。"""
    copy_files([path])
