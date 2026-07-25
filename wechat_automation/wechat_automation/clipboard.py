"""剪贴板工具。

提供文本与文件（CF_HDROP）两种剪贴板写入能力：

* 文本剪贴板：用于「大段文字 / 链接」粘贴发送，跨版本兼容性好。
* 文件剪贴板：将本地文件路径写入剪贴板的 CF_HDROP 格式，等价于在
  资源管理器里「复制文件」，随后在微信输入框执行 Ctrl+V 即可粘贴
  文件 / 图片进行发送。

文件剪贴板依赖 Win32 API（pywin32），仅在 Windows 上可用。文本剪贴板
在缺少 pywin32 时会回退到 pyperclip。
"""

from __future__ import annotations

import time
from typing import List, Sequence

from .exceptions import ClipboardError

try:  # pywin32，仅 Windows 可用
    import win32clipboard  # type: ignore
    import win32con  # type: ignore

    _HAS_WIN32 = True
except Exception:  # pragma: no cover - 非 Windows 环境
    _HAS_WIN32 = False

try:
    import pyperclip  # type: ignore

    _HAS_PYPERCLIP = True
except Exception:  # pragma: no cover
    _HAS_PYPERCLIP = False


def copy_text(text: str, retry: int = 5, retry_delay: float = 0.1) -> None:
    """将纯文本写入系统剪贴板。

    优先使用 pywin32，失败时回退到 pyperclip。剪贴板偶发被其他进程占用，
    因此加入有限次重试。
    """
    last_err: Exception | None = None
    for _ in range(max(1, retry)):
        try:
            if _HAS_WIN32:
                win32clipboard.OpenClipboard()
                try:
                    win32clipboard.EmptyClipboard()
                    win32clipboard.SetClipboardData(
                        win32con.CF_UNICODETEXT, text
                    )
                finally:
                    win32clipboard.CloseClipboard()
                return
            if _HAS_PYPERCLIP:
                pyperclip.copy(text)
                return
            raise ClipboardError(
                "未安装 pywin32 或 pyperclip，无法写入剪贴板文本。"
            )
        except ClipboardError:
            raise
        except Exception as exc:  # 剪贴板占用等瞬时错误
            last_err = exc
            time.sleep(retry_delay)
    raise ClipboardError(f"写入剪贴板文本失败：{last_err}")


def get_text() -> str:
    """读取剪贴板中的纯文本内容。"""
    try:
        if _HAS_WIN32:
            win32clipboard.OpenClipboard()
            try:
                if win32clipboard.IsClipboardFormatAvailable(
                    win32con.CF_UNICODETEXT
                ):
                    return win32clipboard.GetClipboardData(
                        win32con.CF_UNICODETEXT
                    )
                return ""
            finally:
                win32clipboard.CloseClipboard()
        if _HAS_PYPERCLIP:
            return pyperclip.paste()
    except Exception as exc:  # pragma: no cover
        raise ClipboardError(f"读取剪贴板文本失败：{exc}")
    return ""


def copy_files(
    paths: Sequence[str], retry: int = 5, retry_delay: float = 0.1
) -> None:
    """将一个或多个本地文件路径以 CF_HDROP 格式写入剪贴板。

    写入后可在微信输入框直接 Ctrl+V 粘贴文件 / 图片。等价于在资源
    管理器中选中文件后按 Ctrl+C。

    Args:
        paths: 本地文件的绝对路径列表。
    """
    if not _HAS_WIN32:
        raise ClipboardError(
            "文件剪贴板依赖 pywin32（仅 Windows 可用），当前环境不支持。"
        )
    import os

    abs_paths: List[str] = []
    for p in paths:
        ap = os.path.abspath(p)
        if not os.path.exists(ap):
            raise ClipboardError(f"文件不存在：{ap}")
        abs_paths.append(ap)
    if not abs_paths:
        raise ClipboardError("未提供任何待复制的文件路径。")

    # 构造 DROPFILES 结构体 + 以 \0 分隔、\0\0 结尾的宽字符路径列表。
    import struct

    # DROPFILES: pFiles(offset), pt(x,y), fNC, fWide
    offset = 20  # sizeof(DROPFILES)
    dropfiles = struct.pack("Iiiii", offset, 0, 0, 0, 1)  # fWide=1 -> Unicode
    files_str = "".join(p + "\0" for p in abs_paths) + "\0"
    data = dropfiles + files_str.encode("utf-16-le")

    last_err: Exception | None = None
    for _ in range(max(1, retry)):
        try:
            win32clipboard.OpenClipboard()
            try:
                win32clipboard.EmptyClipboard()
                win32clipboard.SetClipboardData(win32con.CF_HDROP, data)
            finally:
                win32clipboard.CloseClipboard()
            return
        except Exception as exc:
            last_err = exc
            time.sleep(retry_delay)
    raise ClipboardError(f"写入剪贴板文件失败：{last_err}")
