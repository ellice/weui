"""剪贴板工具。

封装 Windows 剪贴板的文本与文件读写能力，是"复制内容 + Ctrl+V 粘贴发送"
方案的基础：

* :func:`set_text` / :func:`get_text`  —— 大段文字、链接
* :func:`set_files`                    —— 把一个或多个本地文件放入剪贴板（CF_HDROP），
  之后在微信输入框 Ctrl+V 即可粘贴文件 / 图片发送

依赖 pywin32（win32clipboard / win32con）。仅 Windows 可用。
"""

from __future__ import annotations

import os
import time
from typing import List, Sequence, Union

from .exceptions import ClipboardError
from .logger import get_logger

log = get_logger("clipboard")

try:  # 仅在 Windows 上可导入
    import win32clipboard  # type: ignore
    import win32con  # type: ignore

    _HAS_WIN32 = True
except Exception:  # pragma: no cover - 非 Windows 环境
    _HAS_WIN32 = False


def _ensure_win32() -> None:
    if not _HAS_WIN32:
        raise ClipboardError(
            "剪贴板操作依赖 pywin32（win32clipboard），且仅支持 Windows 平台。"
        )


def _open_clipboard(retries: int = 5, delay: float = 0.1):
    """打开剪贴板，带重试（剪贴板常被其它进程短暂占用）。"""
    last_err: Exception | None = None
    for _ in range(retries):
        try:
            win32clipboard.OpenClipboard()
            return
        except Exception as exc:  # noqa: BLE001
            last_err = exc
            time.sleep(delay)
    raise ClipboardError(f"无法打开剪贴板：{last_err}")


def set_text(text: str) -> None:
    """把文本写入剪贴板（Unicode）。"""
    _ensure_win32()
    _open_clipboard()
    try:
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32con.CF_UNICODETEXT, text)
        log.debug("已写入剪贴板文本，长度=%d", len(text))
    except Exception as exc:  # noqa: BLE001
        raise ClipboardError(f"写入剪贴板文本失败：{exc}") from exc
    finally:
        win32clipboard.CloseClipboard()


def get_text() -> str:
    """读取剪贴板中的文本，若没有文本则返回空字符串。"""
    _ensure_win32()
    _open_clipboard()
    try:
        if win32clipboard.IsClipboardFormatAvailable(win32con.CF_UNICODETEXT):
            return win32clipboard.GetClipboardData(win32con.CF_UNICODETEXT)
        return ""
    except Exception as exc:  # noqa: BLE001
        raise ClipboardError(f"读取剪贴板文本失败：{exc}") from exc
    finally:
        win32clipboard.CloseClipboard()


def set_files(paths: Union[str, Sequence[str]]) -> List[str]:
    """把一个或多个本地文件路径写入剪贴板（CF_HDROP 格式）。

    写入后在微信输入框按 ``Ctrl+V`` 即可粘贴文件 / 图片。

    :param paths: 单个路径字符串或路径列表。
    :return: 实际写入剪贴板的绝对路径列表。
    :raises ClipboardError: 文件不存在或写入失败。
    """
    _ensure_win32()

    if isinstance(paths, (str, bytes)):
        path_list = [paths]  # type: ignore[list-item]
    else:
        path_list = list(paths)

    abs_paths: List[str] = []
    for p in path_list:
        ap = os.path.abspath(os.path.expanduser(str(p)))
        if not os.path.exists(ap):
            raise ClipboardError(f"文件不存在：{ap}")
        abs_paths.append(ap)

    if not abs_paths:
        raise ClipboardError("没有任何有效文件路径可写入剪贴板。")

    data = _build_dropfiles(abs_paths)

    _open_clipboard()
    try:
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32con.CF_HDROP, data)
        log.debug("已写入剪贴板文件 %d 个：%s", len(abs_paths), abs_paths)
    except Exception as exc:  # noqa: BLE001
        raise ClipboardError(f"写入剪贴板文件失败：{exc}") from exc
    finally:
        win32clipboard.CloseClipboard()

    return abs_paths


def _build_dropfiles(paths: Sequence[str]) -> bytes:
    """构造 CF_HDROP 所需的 DROPFILES 结构 + 以 \\0 结尾的宽字符路径串。

    DROPFILES 结构（20 字节）：
        DWORD pFiles;   偏移到文件名列表（这里紧跟结构，故为 20）
        POINT pt;       (x, y)
        BOOL  fNC;
        BOOL  fWide;    是否宽字符，Unicode 路径必须为 1
    """
    import struct

    # 文件名列表：每个路径以 \0 结尾，整体再以额外的 \0 结尾
    files_str = "".join(p + "\0" for p in paths) + "\0"
    files_bytes = files_str.encode("utf-16-le")

    # pFiles=20, pt=(0,0), fNC=0, fWide=1
    header = struct.pack("<IiiII", 20, 0, 0, 0, 1)
    return header + files_bytes
