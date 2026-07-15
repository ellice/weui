"""剪贴板工具：文本 / 文件 / 图片写入。

微信发送文件、图片、大段文字的通用原理：
把内容写入 **系统剪贴板**，再在输入框执行 ``Ctrl+V`` 粘贴。
本模块封装三类写入能力：

- :func:`set_text`  —— 纯文本（大段文字、链接）
- :func:`set_files` —— 一个或多个本地文件（CF_HDROP，等价于资源管理器复制文件）
- :func:`set_image` —— 图片（截图 / 本地图片，写入 CF_DIB 位图）

除 :func:`set_text` 外，其余能力依赖 Windows 原生剪贴板格式，仅在 Windows 可用。
"""

from __future__ import annotations

import os
import time
from typing import Iterable, List, Sequence

from .exceptions import ClipboardError

try:  # pyperclip 为跨平台纯文本方案，缺失时降级到 win32clipboard
    import pyperclip  # type: ignore
except Exception:  # pragma: no cover - 环境缺失时的兜底
    pyperclip = None


def _require_win32():
    """按需导入 win32 相关模块，缺失时给出清晰报错。"""
    try:
        import win32clipboard  # type: ignore
        import win32con  # type: ignore

        return win32clipboard, win32con
    except Exception as exc:  # pragma: no cover - 仅 Windows 具备
        raise ClipboardError(
            "写入文件 / 图片到剪贴板需要 pywin32（win32clipboard），"
            "请在 Windows 上执行 `pip install pywin32`。"
        ) from exc


def set_text(text: str) -> None:
    """把纯文本写入剪贴板。

    支持换行、特殊符号、空格与 emoji（取决于剪贴板 Unicode 支持）。
    """
    if pyperclip is not None:
        pyperclip.copy(text)
        return

    # 兜底：直接使用 win32clipboard 写入 Unicode 文本
    win32clipboard, win32con = _require_win32()
    win32clipboard.OpenClipboard()
    try:
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32con.CF_UNICODETEXT, text)
    finally:
        win32clipboard.CloseClipboard()


def get_text() -> str:
    """读取剪贴板纯文本内容。"""
    if pyperclip is not None:
        return pyperclip.paste()

    win32clipboard, win32con = _require_win32()
    win32clipboard.OpenClipboard()
    try:
        if win32clipboard.IsClipboardFormatAvailable(win32con.CF_UNICODETEXT):
            return win32clipboard.GetClipboardData(win32con.CF_UNICODETEXT)
        return ""
    finally:
        win32clipboard.CloseClipboard()


def _normalize_paths(paths: Sequence[str]) -> List[str]:
    """校验并规范化文件路径列表，全部转为绝对路径。"""
    normalized: List[str] = []
    for p in paths:
        abs_path = os.path.abspath(os.path.expanduser(p))
        if not os.path.exists(abs_path):
            raise ClipboardError(f"文件不存在，无法复制到剪贴板：{abs_path}")
        normalized.append(abs_path)
    if not normalized:
        raise ClipboardError("文件列表为空。")
    return normalized


def set_files(paths: Iterable[str]) -> List[str]:
    """把一个或多个本地文件写入剪贴板（CF_HDROP 格式）。

    效果等价于在资源管理器中选中文件并 ``Ctrl+C``，随后即可在微信输入框
    ``Ctrl+V`` 粘贴发送（文档、压缩包、Excel、PDF、图片皆可）。

    Args:
        paths: 文件路径集合（相对 / 绝对 / 含 ``~`` 均可）。

    Returns:
        规范化后的绝对路径列表。
    """
    win32clipboard, win32con = _require_win32()
    file_list = _normalize_paths(list(paths))

    import struct

    # DROPFILES 结构：pFiles 偏移(20) + x,y + fNC + fWide(1 表示宽字符)
    offset = 20
    dropfiles = struct.pack("Iiiii", offset, 0, 0, 0, 1)
    # 以 \0 分隔、以 \0\0 结尾的宽字符文件名列表
    files_joined = ("\0".join(file_list) + "\0\0").encode("utf-16-le")
    data = dropfiles + files_joined

    win32clipboard.OpenClipboard()
    try:
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32con.CF_HDROP, data)
    finally:
        win32clipboard.CloseClipboard()
    return file_list


def set_image(image_path: str) -> None:
    """把本地图片写入剪贴板（CF_DIB），随后可在输入框粘贴发送。

    Args:
        image_path: 本地图片路径（png / jpg / bmp 等 Pillow 支持的格式）。
    """
    try:
        from PIL import Image  # type: ignore
    except Exception as exc:  # pragma: no cover
        raise ClipboardError(
            "写入图片到剪贴板需要 Pillow，请执行 `pip install Pillow`。"
        ) from exc

    win32clipboard, win32con = _require_win32()
    abs_path = os.path.abspath(os.path.expanduser(image_path))
    if not os.path.exists(abs_path):
        raise ClipboardError(f"图片不存在：{abs_path}")

    image = Image.open(abs_path).convert("RGB")
    import io

    output = io.BytesIO()
    image.save(output, "BMP")
    # BMP 文件头 14 字节，剪贴板 DIB 需去掉文件头
    dib_data = output.getvalue()[14:]
    output.close()

    win32clipboard.OpenClipboard()
    try:
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32con.CF_DIB, dib_data)
    finally:
        win32clipboard.CloseClipboard()


def clear() -> None:
    """清空剪贴板内容。"""
    win32clipboard, _ = _require_win32()
    win32clipboard.OpenClipboard()
    try:
        win32clipboard.EmptyClipboard()
    finally:
        win32clipboard.CloseClipboard()


def wait_clipboard_ready(delay: float = 0.2) -> None:
    """写入剪贴板后的短暂等待，规避粘贴过快导致内容未就绪。"""
    time.sleep(delay)
