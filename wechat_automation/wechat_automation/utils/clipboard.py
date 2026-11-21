"""剪贴板读写工具。

- 文本：优先使用 ``pyperclip``，保证换行、特殊符号、空格原样写入。
- 文件：构造 Windows ``CF_HDROP`` 结构，将一个或多个文件路径放入剪贴板，
  之后在微信输入框 ``Ctrl+V`` 即可作为文件/图片发送。
"""

import os
import struct
import time
from typing import Iterable, List, Optional


def set_clipboard_text(text: str) -> None:
    """将文本写入剪贴板（保留换行、空格与特殊符号）。"""
    try:
        import pyperclip

        pyperclip.copy(text)
        return
    except Exception:
        pass

    # 回退到 win32clipboard（仅 Windows 可用）。
    import win32clipboard
    import win32con

    _with_clipboard(
        lambda: (
            win32clipboard.EmptyClipboard(),
            win32clipboard.SetClipboardData(win32con.CF_UNICODETEXT, text),
        )
    )


def get_clipboard_text() -> str:
    """读取剪贴板中的文本内容，若无文本则返回空串。"""
    try:
        import pyperclip

        return pyperclip.paste() or ""
    except Exception:
        pass

    import win32clipboard
    import win32con

    def _read():
        if not win32clipboard.IsClipboardFormatAvailable(win32con.CF_UNICODETEXT):
            return ""
        return win32clipboard.GetClipboardData(win32con.CF_UNICODETEXT) or ""

    return _with_clipboard(_read, open_only=True)


def set_clipboard_files(paths: Iterable[str]) -> List[str]:
    """将若干本地文件路径以 ``CF_HDROP`` 形式放入剪贴板。

    返回实际放入的绝对路径列表；若存在不存在的路径会直接报错，
    避免粘贴时出现「文件已损坏 / 不存在」的静默失败。
    """
    import win32clipboard
    import win32con

    abs_paths: List[str] = []
    for p in paths:
        ap = os.path.abspath(p)
        if not os.path.exists(ap):
            raise FileNotFoundError(f"待发送的文件不存在: {ap}")
        abs_paths.append(ap)

    if not abs_paths:
        raise ValueError("至少需要提供一个文件路径")

    data = _build_dropfiles(abs_paths)

    def _write():
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32con.CF_HDROP, data)

    _with_clipboard(_write)
    return abs_paths


def _build_dropfiles(paths: List[str]) -> bytes:
    """构造 ``DROPFILES`` 结构 + 以 ``\\0`` 分隔、``\\0\\0`` 结尾的宽字符路径串。"""
    # DROPFILES 结构：
    #   DWORD pFiles;  文件名列表相对结构体起始的偏移
    #   POINT pt;      (x, y)
    #   BOOL  fNC;
    #   BOOL  fWide;   1 表示使用宽字符（Unicode）
    header = struct.pack("Iiiii", 20, 0, 0, 0, 1)
    files = "".join(p + "\0" for p in paths) + "\0"
    return header + files.encode("utf-16-le")


def _with_clipboard(func, open_only: bool = False, retries: int = 5):
    """带重试地打开剪贴板执行 ``func``，规避被其他进程占用的瞬时失败。"""
    import win32clipboard

    last_err: Optional[Exception] = None
    for _ in range(retries):
        try:
            win32clipboard.OpenClipboard()
            try:
                return func()
            finally:
                win32clipboard.CloseClipboard()
        except Exception as e:  # noqa: BLE001 - 剪贴板偶发占用需重试
            last_err = e
            time.sleep(0.1)
    if last_err:
        raise last_err
