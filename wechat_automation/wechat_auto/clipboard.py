"""剪贴板工具：支持文本与文件（CF_HDROP）。

- 文本：优先用 ``pyperclip``，回退到 ``win32clipboard``。
- 文件：把文件路径写入剪贴板的 ``CF_HDROP`` 格式，从而可在微信输入框
  用 ``Ctrl+V`` 粘贴为"文件 / 图片"发送（这是微信桌面版发送文件的
  核心原理——弹窗控件难以定位，改用剪贴板粘贴）。
"""

from __future__ import annotations

import os
import struct
import time
from typing import Iterable, List

from .exceptions import ClipboardError

try:  # pragma: no cover - 仅 Windows
    import win32clipboard  # type: ignore
    import win32con  # type: ignore
except Exception:  # noqa: BLE001
    win32clipboard = None
    win32con = None

try:
    import pyperclip  # type: ignore
except Exception:  # noqa: BLE001
    pyperclip = None


def copy_text(text: str) -> None:
    """把纯文本复制到剪贴板。"""
    if pyperclip is not None:
        try:
            pyperclip.copy(text)
            return
        except Exception as exc:  # noqa: BLE001
            last_error = exc
    else:
        last_error = None

    if win32clipboard is None:
        raise ClipboardError(f"无法访问剪贴板（缺少 pyperclip / pywin32）：{last_error}")

    try:
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32con.CF_UNICODETEXT, text)
    except Exception as exc:  # noqa: BLE001
        raise ClipboardError(f"写入剪贴板文本失败：{exc}") from exc
    finally:
        _safe_close_clipboard()


def get_text() -> str:
    """读取剪贴板中的纯文本。"""
    if pyperclip is not None:
        try:
            return pyperclip.paste()
        except Exception:  # noqa: BLE001
            pass

    if win32clipboard is None:
        raise ClipboardError("无法访问剪贴板（缺少 pyperclip / pywin32）")

    try:
        win32clipboard.OpenClipboard()
        if win32clipboard.IsClipboardFormatAvailable(win32con.CF_UNICODETEXT):
            return win32clipboard.GetClipboardData(win32con.CF_UNICODETEXT)
        return ""
    except Exception as exc:  # noqa: BLE001
        raise ClipboardError(f"读取剪贴板文本失败：{exc}") from exc
    finally:
        _safe_close_clipboard()


def copy_files(paths: Iterable[str]) -> List[str]:
    """把一个或多个本地文件路径写入剪贴板（CF_HDROP 格式）。

    返回成功写入的绝对路径列表。随后在微信输入框执行 ``Ctrl+V`` 即可
    把这些文件 / 图片粘贴进去，再回车发送。
    """
    if win32clipboard is None or win32con is None:
        raise ClipboardError("复制文件到剪贴板需要 pywin32（仅支持 Windows）")

    abs_paths: List[str] = []
    for p in paths:
        ap = os.path.abspath(p)
        if not os.path.exists(ap):
            raise ClipboardError(f"文件不存在：{ap}")
        abs_paths.append(ap)

    if not abs_paths:
        raise ClipboardError("未提供任何文件路径")

    data = _build_dropfiles(abs_paths)

    try:
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32con.CF_HDROP, data)
    except Exception as exc:  # noqa: BLE001
        raise ClipboardError(f"写入剪贴板文件失败：{exc}") from exc
    finally:
        _safe_close_clipboard()

    # 给系统一点时间让剪贴板生效
    time.sleep(0.2)
    return abs_paths


def _build_dropfiles(paths: List[str]) -> bytes:
    """构造 ``DROPFILES`` 结构 + 以 \0 分隔、\0\0 结尾的宽字符路径串。

    DROPFILES 结构（20 字节，见 Win32 API）::

        typedef struct _DROPFILES {
            DWORD pFiles;  // 文件列表相对结构起始的偏移
            POINT pt;      // 拖放点（此处无意义，填 0）
            BOOL  fNC;
            BOOL  fWide;   // 1 表示宽字符（Unicode）
        } DROPFILES;
    """
    # 20 字节头：pFiles(4) + pt.x(4) + pt.y(4) + fNC(4) + fWide(4)
    header = struct.pack("<Iiiii", 20, 0, 0, 0, 1)
    files_str = "\0".join(paths) + "\0\0"
    return header + files_str.encode("utf-16-le")


def _safe_close_clipboard() -> None:
    if win32clipboard is None:
        return
    try:
        win32clipboard.CloseClipboard()
    except Exception:  # noqa: BLE001
        pass
