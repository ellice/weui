"""剪贴板操作工具。

微信桌面端不方便直接调用「文件」按钮的系统弹窗（弹窗控件难以定位），
因此发送文件 / 图片的通用做法是：

    把文件路径以「文件列表」格式写入剪贴板 -> 聊天输入框 Ctrl+V -> 回车发送

本模块封装了三类剪贴板写入能力：

    - :func:`set_text`   写入纯文本（大段文字、链接）
    - :func:`set_files`  写入一个或多个本地文件（CF_HDROP）
    - :func:`set_image`  写入图片位图（CF_DIB，供直接粘贴图片）

以及读取能力 :func:`get_text`。

除 :func:`set_text` / :func:`get_text` 在非 Windows 平台可用 ``pyperclip`` 兜底外，
文件 / 图片写入依赖 ``pywin32``，仅 Windows 可用。
"""

from __future__ import annotations

import os
import struct
import time
from typing import List, Sequence, Union

try:  # pywin32，仅 Windows 可用
    import win32clipboard  # type: ignore
    import win32con  # type: ignore

    _HAS_PYWIN32 = True
except Exception:  # pragma: no cover - 非 Windows 环境
    win32clipboard = None  # type: ignore
    win32con = None  # type: ignore
    _HAS_PYWIN32 = False

try:
    import pyperclip  # type: ignore

    _HAS_PYPERCLIP = True
except Exception:  # pragma: no cover
    pyperclip = None  # type: ignore
    _HAS_PYPERCLIP = False


PathLike = Union[str, "os.PathLike[str]"]


def _open_clipboard(retries: int = 5, delay: float = 0.05):
    """打开剪贴板，剪贴板常被其它进程占用，做重试。"""
    last_err = None
    for _ in range(retries):
        try:
            win32clipboard.OpenClipboard()
            return
        except Exception as exc:  # pragma: no cover - 依赖运行环境
            last_err = exc
            time.sleep(delay)
    raise RuntimeError(f"无法打开剪贴板: {last_err}")


def set_text(text: str) -> None:
    """将纯文本写入剪贴板。

    优先使用 pywin32（保证与微信兼容的 Unicode 文本格式），
    否则退回 pyperclip。
    """
    if _HAS_PYWIN32:
        _open_clipboard()
        try:
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32con.CF_UNICODETEXT, text)
        finally:
            win32clipboard.CloseClipboard()
        return

    if _HAS_PYPERCLIP:
        pyperclip.copy(text)
        return

    raise RuntimeError("当前环境缺少 pywin32 / pyperclip，无法写入剪贴板文本")


def get_text() -> str:
    """读取剪贴板中的纯文本。"""
    if _HAS_PYWIN32:
        _open_clipboard()
        try:
            if win32clipboard.IsClipboardFormatAvailable(win32con.CF_UNICODETEXT):
                return win32clipboard.GetClipboardData(win32con.CF_UNICODETEXT)
            return ""
        finally:
            win32clipboard.CloseClipboard()

    if _HAS_PYPERCLIP:
        return pyperclip.paste()

    raise RuntimeError("当前环境缺少 pywin32 / pyperclip，无法读取剪贴板文本")


def _build_dropfiles(paths: Sequence[str]) -> bytes:
    """构造 CF_HDROP 所需的 DROPFILES 结构体。

    结构：DROPFILES 头 (20 字节) + 以 \\0 分隔、以 \\0\\0 结尾的宽字符路径列表。
    """
    # DROPFILES 结构：pFiles(偏移), pt(x,y), fNC, fWide
    header = struct.pack("Iiiii", 20, 0, 0, 0, 1)  # fWide=1 表示宽字符
    data = "".join(p + "\0" for p in paths) + "\0"
    return header + data.encode("utf-16-le")


def set_files(paths: Union[PathLike, Sequence[PathLike]]) -> List[str]:
    """将一个或多个本地文件写入剪贴板（文件列表格式，CF_HDROP）。

    :param paths: 单个路径或路径列表
    :return: 规范化后的绝对路径列表
    :raises FileNotFoundError: 任一路径不存在
    """
    if not _HAS_PYWIN32:
        raise RuntimeError("发送文件需要 pywin32（仅 Windows 支持）")

    if isinstance(paths, (str, os.PathLike)):
        paths = [paths]

    abs_paths: List[str] = []
    for p in paths:
        ap = os.path.abspath(os.fspath(p))
        if not os.path.exists(ap):
            raise FileNotFoundError(f"文件不存在: {ap}")
        abs_paths.append(ap)

    dropfiles = _build_dropfiles(abs_paths)
    _open_clipboard()
    try:
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32con.CF_HDROP, dropfiles)
    finally:
        win32clipboard.CloseClipboard()
    return abs_paths


def set_image(image_path: PathLike) -> None:
    """将图片写入剪贴板（CF_DIB），可直接粘贴为图片而非文件。

    需要安装 Pillow。多数场景下直接用 :func:`set_files` 粘贴图片文件即可，
    此函数用于需要「作为图片消息」而非「文件消息」发送的场景。
    """
    if not _HAS_PYWIN32:
        raise RuntimeError("图片写入剪贴板需要 pywin32（仅 Windows 支持）")
    try:
        from PIL import Image  # type: ignore
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("图片写入剪贴板需要 Pillow: pip install Pillow") from exc

    import io

    image = Image.open(os.fspath(image_path))
    output = io.BytesIO()
    image.convert("RGB").save(output, "BMP")
    # BMP 文件头 14 字节，DIB 数据从第 14 字节开始
    data = output.getvalue()[14:]
    output.close()

    _open_clipboard()
    try:
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32con.CF_DIB, data)
    finally:
        win32clipboard.CloseClipboard()


def clear() -> None:
    """清空剪贴板。"""
    if not _HAS_PYWIN32:
        if _HAS_PYPERCLIP:
            pyperclip.copy("")
        return
    _open_clipboard()
    try:
        win32clipboard.EmptyClipboard()
    finally:
        win32clipboard.CloseClipboard()
