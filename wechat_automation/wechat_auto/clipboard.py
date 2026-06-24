"""剪贴板工具：文本、文件路径（CF_HDROP）、图片（CF_DIB）写入。

发送文件 / 图片的核心原理：把文件路径或图片以 Windows 标准剪贴板格式写入，
再在微信输入框执行 Ctrl+V 粘贴，最后回车发送。
"""

import os
import time
from typing import List, Sequence

from .utils import logger

try:  # pyperclip 在所有平台可用，作为纯文本兜底
    import pyperclip
except ImportError:  # pragma: no cover
    pyperclip = None


def copy_text(text: str) -> None:
    """将纯文本写入剪贴板。"""
    if pyperclip is None:
        raise RuntimeError("缺少 pyperclip 依赖，无法写入文本剪贴板")
    pyperclip.copy(text)


def paste_text() -> str:
    """读取剪贴板中的纯文本。"""
    if pyperclip is None:
        raise RuntimeError("缺少 pyperclip 依赖，无法读取文本剪贴板")
    return pyperclip.paste()


def _require_pywin32():
    try:
        import win32clipboard  # type: ignore
        import win32con  # type: ignore
    except ImportError as exc:  # pragma: no cover - Windows 才有
        raise RuntimeError(
            "复制文件 / 图片到剪贴板需要 pywin32，请先 `pip install pywin32`"
        ) from exc
    return win32clipboard, win32con


def copy_files(paths: Sequence[str]) -> None:
    """将一个或多个本地文件路径以 CF_HDROP 格式写入剪贴板。

    粘贴到微信输入框后即等同于「拖入文件」，回车即可发送文档、压缩包、
    Excel、PDF 等任意类型文件。

    :param paths: 文件绝对路径列表，会自动校验存在性。
    """
    win32clipboard, win32con = _require_pywin32()

    abs_paths: List[str] = []
    for p in paths:
        ap = os.path.abspath(p)
        if not os.path.exists(ap):
            raise FileNotFoundError(f"文件不存在：{ap}")
        abs_paths.append(ap)

    if not abs_paths:
        raise ValueError("文件列表为空")

    # 构造 DROPFILES 结构：20 字节头 + 以 \0 分隔、\0\0 结尾的宽字符路径
    import struct

    files_str = "\0".join(abs_paths) + "\0\0"
    files_bytes = files_str.encode("utf-16-le")
    # DROPFILES: pFiles(偏移=20), pt(8字节,0), fNC(0), fWide(1)
    dropfiles_header = struct.pack("<IIIII", 20, 0, 0, 0, 1)
    data = dropfiles_header + files_bytes

    win32clipboard.OpenClipboard()
    try:
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32con.CF_HDROP, data)
    finally:
        win32clipboard.CloseClipboard()
    logger.debug("已复制 %d 个文件到剪贴板", len(abs_paths))


def copy_image(image_path: str) -> None:
    """将本地图片以位图（CF_DIB）格式写入剪贴板，用于「图片粘贴发送」。

    与 :func:`copy_files` 的区别：本函数发送的是图片消息（缩略图预览），
    而 ``copy_files`` 发送的是文件形式。

    :param image_path: 本地图片路径（png/jpg/bmp 等 Pillow 支持的格式）。
    """
    win32clipboard, win32con = _require_pywin32()
    try:
        from PIL import Image  # type: ignore
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("图片转剪贴板需要 Pillow，请先 `pip install pillow`") from exc

    image_path = os.path.abspath(image_path)
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"图片不存在：{image_path}")

    image = Image.open(image_path).convert("RGB")
    import io

    output = io.BytesIO()
    image.save(output, "BMP")
    # BMP 文件头为 14 字节，CF_DIB 需要去掉文件头
    data = output.getvalue()[14:]
    output.close()

    win32clipboard.OpenClipboard()
    try:
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32con.CF_DIB, data)
    finally:
        win32clipboard.CloseClipboard()
    logger.debug("已复制图片到剪贴板：%s", image_path)


def clear() -> None:
    """清空剪贴板。"""
    try:
        win32clipboard, _ = _require_pywin32()
        win32clipboard.OpenClipboard()
        try:
            win32clipboard.EmptyClipboard()
        finally:
            win32clipboard.CloseClipboard()
    except RuntimeError:
        # 无 pywin32 时退化为写入空文本
        copy_text("")


def wait_clipboard_ready(delay: float = 0.2) -> None:
    """剪贴板写入后给系统一点同步时间，避免粘贴到空内容。"""
    time.sleep(delay)
