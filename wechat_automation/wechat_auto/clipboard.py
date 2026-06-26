"""剪贴板工具。

封装三类操作：
1. 文本写入/读取（支持大段文字、链接、换行、特殊符号）。
2. 把「本地文件路径」写入剪贴板（CF_HDROP 格式），用于 Ctrl+V 粘贴发送文件/图片。
3. 把 PIL 图片写入剪贴板（CF_DIB），用于直接粘贴图片。

原理说明（对应需求「复制文件路径到剪贴板 + Ctrl+V」）：
微信输入框接收的是 Windows 资源管理器风格的文件拖放数据（CF_HDROP），
所以发送文件不是写「路径字符串」，而是写「文件列表」结构体到剪贴板。
"""

from __future__ import annotations

import os
import time
from typing import Iterable, List, Sequence

from .exceptions import ClipboardError

try:  # 这些库仅在 Windows 上可用，import 失败时给出友好提示
    import win32clipboard  # type: ignore
    import win32con  # type: ignore
    _HAS_PYWIN32 = True
except Exception:  # pragma: no cover - 非 Windows 环境
    win32clipboard = None  # type: ignore
    win32con = None  # type: ignore
    _HAS_PYWIN32 = False


def _require_pywin32() -> None:
    if not _HAS_PYWIN32:
        raise ClipboardError(
            "未检测到 pywin32，剪贴板高级操作不可用。请在 Windows 上执行 `pip install pywin32`。"
        )


def _open_clipboard_with_retry(retry: int = 5, interval: float = 0.1) -> None:
    """打开剪贴板（其他进程可能临时占用，做几次重试）。"""
    last_err: Exception | None = None
    for _ in range(retry):
        try:
            win32clipboard.OpenClipboard()
            return
        except Exception as exc:  # noqa: BLE001
            last_err = exc
            time.sleep(interval)
    raise ClipboardError(f"无法打开剪贴板: {last_err}")


def set_text(text: str) -> None:
    """把纯文本写入剪贴板。优先用 pyperclip，失败再退回 win32。"""
    try:
        import pyperclip  # 延迟导入，避免无依赖时报错

        pyperclip.copy(text)
        return
    except Exception:  # noqa: BLE001
        pass

    _require_pywin32()
    _open_clipboard_with_retry()
    try:
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32con.CF_UNICODETEXT, text)
    except Exception as exc:  # noqa: BLE001
        raise ClipboardError(f"写入文本到剪贴板失败: {exc}") from exc
    finally:
        win32clipboard.CloseClipboard()


def get_text() -> str:
    """读取剪贴板中的文本，没有文本时返回空串。"""
    try:
        import pyperclip

        return pyperclip.paste()
    except Exception:  # noqa: BLE001
        pass

    _require_pywin32()
    _open_clipboard_with_retry()
    try:
        if win32clipboard.IsClipboardFormatAvailable(win32con.CF_UNICODETEXT):
            return win32clipboard.GetClipboardData(win32con.CF_UNICODETEXT)
        return ""
    finally:
        win32clipboard.CloseClipboard()


def set_files(paths: Sequence[str]) -> List[str]:
    """把一个或多个本地文件路径写入剪贴板（CF_HDROP）。

    返回实际写入的「绝对路径」列表，便于调用方记录日志。
    不存在的路径会被跳过；全部不存在时抛 ClipboardError。
    """
    _require_pywin32()

    abs_paths: List[str] = []
    for p in paths:
        ap = os.path.abspath(os.path.expanduser(p))
        if os.path.exists(ap):
            abs_paths.append(ap)
    if not abs_paths:
        raise ClipboardError(f"没有任何有效文件可写入剪贴板: {list(paths)}")

    # 构造 DROPFILES 结构 + 以 \0 结尾、整体再加 \0 的宽字符路径列表
    import struct

    # DROPFILES: pFiles(偏移=20), pt(8字节), fNC(4字节), fWide(4字节=1表示Unicode)
    offset = 20
    dropfiles = struct.pack("Iiiii", offset, 0, 0, 0, 1)
    files_blob = ("\0".join(abs_paths) + "\0\0").encode("utf-16-le")
    data = dropfiles + files_blob

    _open_clipboard_with_retry()
    try:
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32con.CF_HDROP, data)
    except Exception as exc:  # noqa: BLE001
        raise ClipboardError(f"写入文件列表到剪贴板失败: {exc}") from exc
    finally:
        win32clipboard.CloseClipboard()
    return abs_paths


def set_image(image_path: str) -> None:
    """把本地图片以位图（CF_DIB）形式写入剪贴板，可直接 Ctrl+V 粘贴为图片。

    与 set_files 的区别：set_files 发送的是「文件」，set_image 发送的是「图片消息」。
    """
    _require_pywin32()
    try:
        from PIL import Image  # 延迟导入
    except Exception as exc:  # noqa: BLE001
        raise ClipboardError("需要 Pillow 才能把图片写入剪贴板: pip install Pillow") from exc

    abs_path = os.path.abspath(os.path.expanduser(image_path))
    if not os.path.exists(abs_path):
        raise ClipboardError(f"图片不存在: {abs_path}")

    import io

    image = Image.open(abs_path)
    output = io.BytesIO()
    image.convert("RGB").save(output, "BMP")
    # BMP 文件头 14 字节，DIB 数据从第 14 字节开始
    dib_data = output.getvalue()[14:]
    output.close()

    _open_clipboard_with_retry()
    try:
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32con.CF_DIB, dib_data)
    except Exception as exc:  # noqa: BLE001
        raise ClipboardError(f"写入图片到剪贴板失败: {exc}") from exc
    finally:
        win32clipboard.CloseClipboard()


def clear() -> None:
    """清空剪贴板。"""
    _require_pywin32()
    _open_clipboard_with_retry()
    try:
        win32clipboard.EmptyClipboard()
    finally:
        win32clipboard.CloseClipboard()
