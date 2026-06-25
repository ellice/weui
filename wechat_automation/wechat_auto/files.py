# -*- coding: utf-8 -*-
"""文件、图片、媒体发送 Mixin。

原理：把本地文件路径以 CF_HDROP 写入剪贴板 + 在输入框 ``Ctrl+V`` 粘贴后回车发送。
不依赖微信「文件」按钮弹窗（弹窗为系统对话框、控件难以稳定定位）。
"""

from __future__ import annotations

import time
from typing import Optional, Sequence, Union

from . import clipboard, inputs
from .exceptions import FileSendError


class FileMixin:
    """文件 / 图片 / 多文件发送能力。"""

    def send_file(self, path: str, *, to: Optional[str] = None,
                  enter_to_send: bool = True, wait: float = 0.8) -> None:
        """发送单个本地文件（文档、压缩包、Excel、PDF 等）。

        :param path: 本地文件绝对 / 相对路径。
        :param to: 若提供则先切入对应会话。
        :param wait: 粘贴后等待微信加载附件的时间。
        """
        self.send_files([path], to=to, enter_to_send=enter_to_send, wait=wait)

    # 图片与文件走同一通道（微信会自动识别图片格式）
    send_image = send_file

    def send_files(self, paths: Sequence[str], *, to: Optional[str] = None,
                   enter_to_send: bool = True, wait: float = 1.0) -> None:
        """多文件批量粘贴发送。

        :param paths: 文件路径列表，可混合图片与文档。
        :raises FileSendError: 路径不存在或剪贴板写入失败。
        """
        if not paths:
            raise FileSendError("待发送文件列表为空")

        if to:
            self.search_contact(to)  # type: ignore[attr-defined]

        # 写入剪贴板（会校验路径存在性）
        clipboard.copy_files(list(paths))

        self.focus_input()  # type: ignore[attr-defined]
        time.sleep(0.2)
        inputs.paste()
        time.sleep(wait)  # 等待附件预览加载完成

        if enter_to_send:
            inputs.press_enter()

    def send_files_separately(self, paths: Sequence[str], *,
                              to: Optional[str] = None,
                              interval: float = 0.8) -> None:
        """逐个发送多个文件（每个文件单独一条消息）。"""
        if to:
            self.search_contact(to)  # type: ignore[attr-defined]
        for i, p in enumerate(paths):
            self.send_file(p, enter_to_send=True)
            if i != len(paths) - 1:
                inputs.sleep_jitter(interval, 0.3)
