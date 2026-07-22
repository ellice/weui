"""剪贴板工具。

微信桌面端发送文件 / 图片 / 大段文本最稳妥的方式是：
把内容放到系统剪贴板，然后在输入框执行 Ctrl+V 粘贴。

* 纯文本：直接用 pyperclip 即可。
* 文件 / 图片：需要写入 ``CF_HDROP`` 剪贴板格式（文件列表），
  这样 Ctrl+V 才会被微信识别为「发送文件」，而不是粘贴一段路径文本。
"""

from __future__ import annotations

import os
import time
from typing import List, Sequence

import pyperclip


def copy_text(text: str) -> None:
    """把纯文本写入剪贴板。"""
    pyperclip.copy(text)


def paste_text() -> str:
    """读取剪贴板中的纯文本。"""
    return pyperclip.paste()


def copy_files(paths: Sequence[str]) -> None:
    """把一个或多个本地文件路径以 ``CF_HDROP`` 格式写入剪贴板。

    写入后在微信输入框 Ctrl+V，即可作为「文件/图片」发送，
    从而避免去点击难以定位的「文件」弹窗控件。

    :param paths: 本地文件的绝对路径列表
    :raises FileNotFoundError: 任一路径不存在时抛出
    :raises RuntimeError: 非 Windows 平台或缺少 pywin32 时抛出
    """
    abs_paths: List[str] = []
    for p in paths:
        ap = os.path.abspath(p)
        if not os.path.exists(ap):
            raise FileNotFoundError(f"文件不存在: {ap}")
        abs_paths.append(ap)

    try:
        import win32clipboard  # type: ignore
        import win32con  # type: ignore
    except ImportError as exc:  # pragma: no cover - 仅 Windows 可用
        raise RuntimeError(
            "复制文件到剪贴板需要 pywin32（且仅支持 Windows）。请先 pip install pywin32"
        ) from exc

    # DROPFILES 结构 + 以 \0 分隔、\0\0 结尾的宽字符路径串
    import struct

    # DROPFILES: pFiles(offset), pt(x,y), fNC, fWide
    # 结构体总长 20 字节，pFiles 指向文件名区域的偏移（即结构体大小）
    dropfiles = struct.pack("Iiiii", 20, 0, 0, 0, 1)  # fWide=1 表示 Unicode
    files_str = "".join(p + "\0" for p in abs_paths) + "\0"
    data = dropfiles + files_str.encode("utf-16-le")

    win32clipboard.OpenClipboard()
    try:
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32con.CF_HDROP, data)
    finally:
        win32clipboard.CloseClipboard()


def wait_settle(delay: float = 0.3) -> None:
    """剪贴板操作后短暂等待，确保系统写入完成。"""
    time.sleep(delay)
