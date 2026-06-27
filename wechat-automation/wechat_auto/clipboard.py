"""剪贴板工具：纯文本、文件路径(CF_HDROP)、图片(DIB)。

文件/图片发送的核心原理：
    把内容写入系统剪贴板，再聚焦到微信输入框执行 Ctrl+V 粘贴，最后回车发送。
这样可以绕过「文件」按钮弹出的系统选择框（该弹窗控件难以稳定定位）。
"""

from __future__ import annotations

import time
from typing import List, Sequence, Union

from .exceptions import ClipboardError

try:  # pywin32，仅 Windows 可用
    import win32clipboard
    import win32con

    _HAS_WIN32 = True
except Exception:  # pragma: no cover - 非 Windows 环境
    _HAS_WIN32 = False


def _retry(func, retries: int = 5, delay: float = 0.1):
    """剪贴板常被其它进程占用，做简单重试。"""
    last_exc = None
    for _ in range(retries):
        try:
            return func()
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            time.sleep(delay)
    raise ClipboardError(f"剪贴板操作失败: {last_exc}")


def copy_text(text: str) -> None:
    """复制纯文本到剪贴板。优先 pyperclip，回退到 win32。"""
    try:
        import pyperclip

        pyperclip.copy(text)
        return
    except Exception:  # noqa: BLE001
        pass

    if not _HAS_WIN32:
        raise ClipboardError("当前环境缺少剪贴板支持（需 pyperclip 或 pywin32）")

    def _do():
        win32clipboard.OpenClipboard()
        try:
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32con.CF_UNICODETEXT, text)
        finally:
            win32clipboard.CloseClipboard()

    _retry(_do)


def paste_text() -> str:
    """读取剪贴板中的纯文本。"""
    try:
        import pyperclip

        return pyperclip.paste()
    except Exception:  # noqa: BLE001
        pass

    if not _HAS_WIN32:
        raise ClipboardError("当前环境缺少剪贴板支持（需 pyperclip 或 pywin32）")

    def _do():
        win32clipboard.OpenClipboard()
        try:
            if win32clipboard.IsClipboardFormatAvailable(win32con.CF_UNICODETEXT):
                return win32clipboard.GetClipboardData(win32con.CF_UNICODETEXT)
            return ""
        finally:
            win32clipboard.CloseClipboard()

    return _retry(_do)


def copy_files(paths: Union[str, Sequence[str]]) -> List[str]:
    """把一个或多个本地文件路径写入剪贴板（CF_HDROP 格式）。

    写入后在微信输入框 Ctrl+V，即可像在资源管理器里复制文件后粘贴一样，
    将文件/图片/压缩包等作为附件发送。

    返回实际写入的绝对路径列表。
    """
    import os

    if isinstance(paths, str):
        paths = [paths]

    abs_paths: List[str] = []
    for p in paths:
        ap = os.path.abspath(os.path.expanduser(p))
        if not os.path.exists(ap):
            raise ClipboardError(f"文件不存在: {ap}")
        abs_paths.append(ap)

    if not abs_paths:
        raise ClipboardError("未提供任何文件路径")

    if not _HAS_WIN32:
        raise ClipboardError("复制文件到剪贴板需要 pywin32（仅 Windows）")

    import struct

    # 构造 DROPFILES 结构体 + 以 \0 分隔、\0\0 结尾的宽字符路径列表
    # DROPFILES: pFiles(DWORD=20) + pt(8 bytes) + fNC(DWORD) + fWide(DWORD=1)
    files_str = "\0".join(abs_paths) + "\0\0"
    files_bytes = files_str.encode("utf-16-le")
    dropfiles = struct.pack("<lll", 20, 0, 0) + struct.pack("<ll", 0, 1)
    data = dropfiles + files_bytes

    def _do():
        win32clipboard.OpenClipboard()
        try:
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32con.CF_HDROP, data)
        finally:
            win32clipboard.CloseClipboard()

    _retry(_do)
    return abs_paths


def copy_image(image_path: str) -> str:
    """把本地图片写入剪贴板（DIB 格式），用于「图片」形式而非「文件」形式发送。"""
    import os

    ap = os.path.abspath(os.path.expanduser(image_path))
    if not os.path.exists(ap):
        raise ClipboardError(f"图片不存在: {ap}")

    if not _HAS_WIN32:
        raise ClipboardError("复制图片到剪贴板需要 pywin32 + Pillow（仅 Windows）")

    try:
        from PIL import Image
        import io

        image = Image.open(ap)
        output = io.BytesIO()
        image.convert("RGB").save(output, "BMP")
        # BMP 文件头 14 字节，DIB 数据从第 14 字节开始
        data = output.getvalue()[14:]
        output.close()
    except Exception as exc:  # noqa: BLE001
        raise ClipboardError(f"读取图片失败: {exc}")

    def _do():
        win32clipboard.OpenClipboard()
        try:
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32con.CF_DIB, data)
        finally:
            win32clipboard.CloseClipboard()

    _retry(_do)
    return ap


def clear() -> None:
    """清空剪贴板。"""
    if not _HAS_WIN32:
        try:
            import pyperclip

            pyperclip.copy("")
            return
        except Exception:  # noqa: BLE001
            raise ClipboardError("当前环境缺少剪贴板支持")

    def _do():
        win32clipboard.OpenClipboard()
        try:
            win32clipboard.EmptyClipboard()
        finally:
            win32clipboard.CloseClipboard()

    _retry(_do)
