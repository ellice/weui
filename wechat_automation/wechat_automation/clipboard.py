"""剪贴板工具。

支持三类写入：
- 纯文本：用于「剪贴板粘贴发送大段文字 / 链接」。
- 文件列表（CF_HDROP）：用于「复制文件路径 + Ctrl+V 粘贴发送文件 / 图片」。
- 图片位图（CF_DIB）：用于「截图 / 本地图片直接粘贴发送」。
"""

from __future__ import annotations

import os
import time
from typing import Iterable, List

from ._compat import IS_WINDOWS, load_win32
from .exceptions import ClipboardError


def set_text(text: str) -> None:
    """把纯文本写入剪贴板。"""
    win32 = load_win32()
    cb = win32.clipboard
    try:
        cb.OpenClipboard()
        cb.EmptyClipboard()
        cb.SetClipboardText(text, win32.con.CF_UNICODETEXT)
    except Exception as exc:  # pragma: no cover - 依赖系统剪贴板
        raise ClipboardError(f"写入文本到剪贴板失败: {exc}") from exc
    finally:
        try:
            cb.CloseClipboard()
        except Exception:  # pragma: no cover
            pass


def get_text() -> str:
    """读取剪贴板中的纯文本，没有则返回空串。"""
    win32 = load_win32()
    cb = win32.clipboard
    try:
        cb.OpenClipboard()
        if cb.IsClipboardFormatAvailable(win32.con.CF_UNICODETEXT):
            return cb.GetClipboardData(win32.con.CF_UNICODETEXT)
        return ""
    except Exception as exc:  # pragma: no cover
        raise ClipboardError(f"读取剪贴板文本失败: {exc}") from exc
    finally:
        try:
            cb.CloseClipboard()
        except Exception:  # pragma: no cover
            pass


def set_files(paths: Iterable[str]) -> List[str]:
    """把一个或多个本地文件以 CF_HDROP 形式写入剪贴板。

    随后在微信输入框 Ctrl+V，即可触发「发送文件 / 图片」。

    返回成功写入的绝对路径列表。
    """
    abs_paths: List[str] = []
    for p in paths:
        ap = os.path.abspath(os.path.expanduser(p))
        if not os.path.exists(ap):
            raise ClipboardError(f"文件不存在: {ap}")
        abs_paths.append(ap)
    if not abs_paths:
        raise ClipboardError("未提供任何有效的文件路径")

    win32 = load_win32()
    cb = win32.clipboard
    con = win32.con

    # 构造 DROPFILES 结构 + 以两个 \0 结尾的宽字符路径列表。
    import struct

    # DROPFILES: pFiles(offset, DWORD)=20, pt(8 bytes)=0, fNC(DWORD)=0, fWide(DWORD)=1
    dropfiles = struct.pack("Iiiii", 20, 0, 0, 0, 1)
    file_blob = ("\0".join(abs_paths) + "\0\0").encode("utf-16-le")
    data = dropfiles + file_blob

    try:
        cb.OpenClipboard()
        cb.EmptyClipboard()
        cb.SetClipboardData(con.CF_HDROP, data)
    except Exception as exc:  # pragma: no cover
        raise ClipboardError(f"写入文件列表到剪贴板失败: {exc}") from exc
    finally:
        try:
            cb.CloseClipboard()
        except Exception:  # pragma: no cover
            pass
    return abs_paths


def set_image(image_path: str) -> str:
    """把一张本地图片以位图（CF_DIB）形式写入剪贴板。

    适合「截图后直接粘贴」的语义；若只是想作为文件发送可改用 :func:`set_files`。
    需要安装 Pillow。
    """
    ap = os.path.abspath(os.path.expanduser(image_path))
    if not os.path.exists(ap):
        raise ClipboardError(f"图片不存在: {ap}")
    try:
        from PIL import Image  # type: ignore
    except ImportError as exc:  # pragma: no cover
        raise ClipboardError("写入图片需要 Pillow，请执行: pip install Pillow") from exc

    import io

    win32 = load_win32()
    cb = win32.clipboard
    con = win32.con
    try:
        image = Image.open(ap).convert("RGB")
        output = io.BytesIO()
        image.save(output, "BMP")
        # BMP 文件头 14 字节，DIB 数据从第 14 字节开始。
        dib = output.getvalue()[14:]
        output.close()
        cb.OpenClipboard()
        cb.EmptyClipboard()
        cb.SetClipboardData(con.CF_DIB, dib)
    except Exception as exc:  # pragma: no cover
        raise ClipboardError(f"写入图片到剪贴板失败: {exc}") from exc
    finally:
        try:
            cb.CloseClipboard()
        except Exception:  # pragma: no cover
            pass
    return ap


def wait_clipboard_ready(delay: float = 0.2) -> None:
    """剪贴板写入后给系统一点时间落地，避免随后立即 Ctrl+V 取到旧内容。"""
    if not IS_WINDOWS:
        return
    time.sleep(max(0.0, delay))
