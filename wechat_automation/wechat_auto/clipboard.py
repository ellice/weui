"""剪贴板工具：文本、文件路径（CF_HDROP）写入。

微信 PC 版发送文件的核心技巧是：把文件以 ``CF_HDROP`` 格式放到剪贴板，
再在输入框 ``Ctrl+V`` 粘贴，微信会自动把文件识别为附件。纯文本 / 图片
同理通过剪贴板粘贴。
"""

from __future__ import annotations

import logging
import os
import time
from typing import List, Sequence

from .exceptions import ClipboardError, FileSendError

logger = logging.getLogger("wechat_auto")


def copy_text(text: str, retry: int = 3) -> None:
    """把纯文本写入剪贴板（优先 pyperclip，回退 win32clipboard）。"""

    last_exc: Exception | None = None
    for _ in range(retry):
        try:
            import pyperclip  # type: ignore

            pyperclip.copy(text)
            return
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            time.sleep(0.2)

    # 回退：使用 win32clipboard
    try:
        _win32_set_unicode_text(text)
    except Exception as exc:  # noqa: BLE001
        raise ClipboardError("写入文本到剪贴板失败。") from (last_exc or exc)


def paste_text() -> str:
    """读取剪贴板文本。"""

    try:
        import pyperclip  # type: ignore

        return pyperclip.paste()
    except Exception as exc:  # noqa: BLE001
        raise ClipboardError("读取剪贴板文本失败。") from exc


def _win32_set_unicode_text(text: str) -> None:
    import win32clipboard  # type: ignore
    import win32con  # type: ignore

    win32clipboard.OpenClipboard()
    try:
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32con.CF_UNICODETEXT, text)
    finally:
        win32clipboard.CloseClipboard()


def copy_files(paths: Sequence[str]) -> List[str]:
    """把一个或多个本地文件以 ``CF_HDROP`` 放入剪贴板。

    返回成功放入的绝对路径列表。任何路径不存在都会抛
    :class:`FileSendError`。
    """

    abs_paths: List[str] = []
    for p in paths:
        ap = os.path.abspath(os.path.expanduser(p))
        if not os.path.exists(ap):
            raise FileSendError(f"文件不存在：{ap}")
        abs_paths.append(ap)

    try:
        import struct

        import win32clipboard  # type: ignore
        import win32con  # type: ignore

        # 构造 DROPFILES 结构 + 以 \0 分隔、\0\0 结尾的宽字符路径列表
        files = "\0".join(abs_paths) + "\0\0"
        files_bytes = files.encode("utf-16-le")

        # DROPFILES 结构：pFiles(偏移=20), pt(x,y)=0, fNC=0, fWide=1
        dropfiles = struct.pack("<IIIII", 20, 0, 0, 0, 1)
        data = dropfiles + files_bytes

        win32clipboard.OpenClipboard()
        try:
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32con.CF_HDROP, data)
        finally:
            win32clipboard.CloseClipboard()
    except ImportError as exc:  # pragma: no cover
        raise ClipboardError(
            "复制文件需要 pywin32，请执行 `pip install pywin32`。"
        ) from exc
    except Exception as exc:  # noqa: BLE001
        raise ClipboardError("写入文件到剪贴板失败。") from exc

    logger.info("已复制 %d 个文件到剪贴板。", len(abs_paths))
    return abs_paths


def copy_image_file(path: str) -> None:
    """把本地图片以 ``CF_HDROP`` 复制到剪贴板（微信可粘贴为图片消息）。

    如需以位图格式（CF_DIB）复制，请使用 :func:`copy_image_as_bitmap`。
    """

    copy_files([path])


def copy_image_as_bitmap(path: str) -> None:
    """把图片以位图（CF_DIB）格式复制到剪贴板。

    某些场景下微信会把 CF_HDROP 的图片当作"文件"发送，而 CF_DIB 会作为
    "图片消息"发送。需要安装 Pillow。
    """

    try:
        import io

        from PIL import Image  # type: ignore
        import win32clipboard  # type: ignore
        import win32con  # type: ignore

        image = Image.open(path).convert("RGB")
        output = io.BytesIO()
        image.save(output, "BMP")
        # BMP 文件头 14 字节，DIB 数据从第 14 字节开始
        data = output.getvalue()[14:]
        output.close()

        win32clipboard.OpenClipboard()
        try:
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32con.CF_DIB, data)
        finally:
            win32clipboard.CloseClipboard()
    except ImportError as exc:  # pragma: no cover
        raise ClipboardError(
            "以位图复制图片需要 Pillow 与 pywin32。"
        ) from exc
    except Exception as exc:  # noqa: BLE001
        raise ClipboardError(f"复制图片位图失败：{path}") from exc
