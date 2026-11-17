"""剪贴板工具：文本与文件两种格式。

发送文件 / 图片的核心原理：把 **文件路径** 以 Windows ``CF_HDROP`` 格式写入
剪贴板，再在微信输入框按 ``Ctrl+V`` 粘贴，微信会把它识别为文件附件；
大段文字 / 链接则以普通文本格式写入剪贴板再粘贴，避免逐字输入过慢。
"""

import os
import time
from typing import List, Sequence

from .exceptions import ClipboardError

try:  # pywin32，仅 Windows 可用
    import win32clipboard  # type: ignore
    import win32con  # type: ignore

    _HAS_PYWIN32 = True
except ImportError:  # pragma: no cover - 非 Windows 环境
    win32clipboard = None  # type: ignore
    win32con = None  # type: ignore
    _HAS_PYWIN32 = False

try:
    import pyperclip  # type: ignore

    _HAS_PYPERCLIP = True
except ImportError:  # pragma: no cover
    pyperclip = None  # type: ignore
    _HAS_PYPERCLIP = False


def _require_windows() -> None:
    if not _HAS_PYWIN32:
        raise ClipboardError(
            "复制文件到剪贴板需要 pywin32（win32clipboard），且只能在 Windows 上运行。"
        )


def copy_text(text: str, retry: int = 3) -> None:
    """把纯文本写入剪贴板。"""
    last_err: Exception | None = None
    for _ in range(max(1, retry)):
        try:
            if _HAS_PYWIN32:
                win32clipboard.OpenClipboard()
                try:
                    win32clipboard.EmptyClipboard()
                    win32clipboard.SetClipboardData(win32con.CF_UNICODETEXT, text)
                finally:
                    win32clipboard.CloseClipboard()
            elif _HAS_PYPERCLIP:
                pyperclip.copy(text)
            else:
                raise ClipboardError("未安装 pywin32 或 pyperclip，无法写入剪贴板。")
            return
        except Exception as exc:  # noqa: BLE001 - 剪贴板偶发占用，重试
            last_err = exc
            time.sleep(0.2)
    raise ClipboardError(f"写入文本到剪贴板失败: {last_err}")


def get_text() -> str:
    """读取剪贴板文本内容。"""
    if _HAS_PYWIN32:
        win32clipboard.OpenClipboard()
        try:
            if win32clipboard.IsClipboardFormatAvailable(win32con.CF_UNICODETEXT):
                return win32clipboard.GetClipboardData(win32con.CF_UNICODETEXT)
            return ""
        finally:
            win32clipboard.CloseClipboard()
    if _HAS_PYPERCLIP:
        return pyperclip.paste()
    raise ClipboardError("未安装 pywin32 或 pyperclip，无法读取剪贴板。")


def copy_files(paths: Sequence[str], retry: int = 3) -> List[str]:
    """把一个或多个文件路径以 ``CF_HDROP`` 写入剪贴板。

    返回成功写入的绝对路径列表；任意路径不存在都会直接报错。
    """
    _require_windows()

    abs_paths: List[str] = []
    for p in paths:
        ap = os.path.abspath(os.path.expanduser(p))
        if not os.path.exists(ap):
            raise ClipboardError(f"文件不存在: {ap}")
        abs_paths.append(ap)

    if not abs_paths:
        raise ClipboardError("未提供任何文件路径。")

    # DROPFILES 结构：20 字节头 + 以 \0 分隔、\0\0 结尾的宽字符路径串
    # struct DROPFILES { DWORD pFiles; POINT pt; BOOL fNC; BOOL fWide; }
    import struct

    files_str = "".join(p + "\0" for p in abs_paths) + "\0"
    file_bytes = files_str.encode("utf-16-le")
    # pFiles=20（数据偏移）, pt=(0,0), fNC=0, fWide=1（宽字符）
    header = struct.pack("<lllll", 20, 0, 0, 0, 1)
    data = header + file_bytes

    last_err: Exception | None = None
    for _ in range(max(1, retry)):
        try:
            win32clipboard.OpenClipboard()
            try:
                win32clipboard.EmptyClipboard()
                win32clipboard.SetClipboardData(win32con.CF_HDROP, data)
            finally:
                win32clipboard.CloseClipboard()
            return abs_paths
        except Exception as exc:  # noqa: BLE001
            last_err = exc
            time.sleep(0.2)
    raise ClipboardError(f"写入文件到剪贴板失败: {last_err}")
