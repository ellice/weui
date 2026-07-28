"""剪贴板工具。

微信桌面版没有稳定可定位的“文件选择”弹窗控件，最可靠的做法是：
把内容（文本 / 文件路径 / 图片位图）写入系统剪贴板，再在输入框里 ``Ctrl+V``。

本模块封装三类剪贴板写入能力：

* :func:`set_text` —— 纯文本
* :func:`set_files` —— 一个或多个本地文件（CF_HDROP，等价于在资源管理器里复制文件）
* :func:`set_image` —— 本地图片以位图（CF_DIB）形式放入剪贴板

除 :func:`set_text` 外，其余能力依赖 ``pywin32``，仅在 Windows 下可用。
"""

from __future__ import annotations

import os
import time
from typing import List, Sequence

from .exceptions import ClipboardError
from .utils import logger


def set_text(text: str) -> None:
    """把纯文本写入剪贴板。"""
    try:
        import pyperclip

        pyperclip.copy(text)
    except Exception as exc:  # noqa: BLE001
        raise ClipboardError(f"写入文本到剪贴板失败：{exc}") from exc


def get_text() -> str:
    """读取剪贴板中的纯文本。"""
    try:
        import pyperclip

        return pyperclip.paste()
    except Exception as exc:  # noqa: BLE001
        raise ClipboardError(f"读取剪贴板文本失败：{exc}") from exc


def _open_clipboard_with_retry(attempts: int = 5, delay: float = 0.1):
    """打开剪贴板，剪贴板经常被其它进程占用，这里做重试。"""
    import win32clipboard  # type: ignore

    last_exc = None
    for _ in range(attempts):
        try:
            win32clipboard.OpenClipboard()
            return win32clipboard
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            time.sleep(delay)
    raise ClipboardError(f"无法打开系统剪贴板：{last_exc}")


def set_files(paths: Sequence[str]) -> None:
    """把一个或多个本地文件放入剪贴板（相当于在资源管理器里“复制”文件）。

    随后在微信输入框中 ``Ctrl+V`` 即可作为“文件”发送。

    :param paths: 文件路径列表，必须是已存在的本地文件。
    """
    normalized: List[str] = []
    for p in paths:
        abspath = os.path.abspath(os.path.expanduser(p))
        if not os.path.exists(abspath):
            raise ClipboardError(f"文件不存在：{abspath}")
        normalized.append(abspath)

    if not normalized:
        raise ClipboardError("未提供任何有效文件路径")

    try:
        import win32clipboard  # type: ignore
        import win32con  # type: ignore
        from ctypes import (
            Structure,
            c_uint,
            c_int,
            sizeof,
            memmove,
            addressof,
            create_unicode_buffer,
        )
    except Exception as exc:  # noqa: BLE001
        raise ClipboardError(
            "复制文件到剪贴板需要 pywin32，且仅支持 Windows 平台"
        ) from exc

    class POINT(Structure):
        _fields_ = [("x", c_int), ("y", c_int)]

    class DROPFILES(Structure):
        # 参考 Win32 DROPFILES 结构
        _fields_ = [
            ("pFiles", c_uint),
            ("pt", POINT),
            ("fNC", c_int),
            ("fWide", c_int),
        ]

    # 以 \0 分隔、\0\0 结尾的宽字符文件列表
    file_block = "".join(f"{path}\0" for path in normalized) + "\0"
    buf = create_unicode_buffer(file_block)
    files_bytes = bytes(buf)

    df = DROPFILES()
    df.pFiles = sizeof(DROPFILES)
    df.pt = POINT(0, 0)
    df.fNC = 0
    df.fWide = 1  # 使用 Unicode

    payload = bytearray(sizeof(DROPFILES) + len(files_bytes))
    memmove(
        (c_uint * 1).from_buffer(payload),
        addressof(df),
        sizeof(DROPFILES),
    )
    payload[sizeof(DROPFILES):] = files_bytes

    clip = _open_clipboard_with_retry()
    try:
        clip.EmptyClipboard()
        win32clipboard.SetClipboardData(win32con.CF_HDROP, bytes(payload))
        logger.info("已将 %d 个文件写入剪贴板", len(normalized))
    except Exception as exc:  # noqa: BLE001
        raise ClipboardError(f"写入文件到剪贴板失败：{exc}") from exc
    finally:
        clip.CloseClipboard()


def set_image(image_path: str) -> None:
    """把一张本地图片以位图（CF_DIB）形式写入剪贴板。

    这样在微信里 ``Ctrl+V`` 会作为“图片”而非“文件”发送。
    """
    abspath = os.path.abspath(os.path.expanduser(image_path))
    if not os.path.exists(abspath):
        raise ClipboardError(f"图片不存在：{abspath}")

    try:
        import io

        from PIL import Image  # type: ignore
        import win32clipboard  # type: ignore
        import win32con  # type: ignore
    except Exception as exc:  # noqa: BLE001
        raise ClipboardError(
            "复制图片到剪贴板需要 Pillow + pywin32，且仅支持 Windows 平台"
        ) from exc

    image = Image.open(abspath).convert("RGB")
    output = io.BytesIO()
    image.save(output, "BMP")
    # BMP 文件头 14 字节，DIB 数据从第 14 字节开始
    dib_data = output.getvalue()[14:]
    output.close()

    clip = _open_clipboard_with_retry()
    try:
        clip.EmptyClipboard()
        win32clipboard.SetClipboardData(win32con.CF_DIB, dib_data)
        logger.info("已将图片写入剪贴板：%s", abspath)
    except Exception as exc:  # noqa: BLE001
        raise ClipboardError(f"写入图片到剪贴板失败：{exc}") from exc
    finally:
        clip.CloseClipboard()
