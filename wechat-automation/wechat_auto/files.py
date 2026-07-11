"""文件、图片、媒体发送。

原理：复制文件路径到剪贴板（文件列表格式）+ Ctrl+V 粘贴到输入框 + 回车发送。

    - 本地文件粘贴发送（文档、压缩包、Excel、PDF）
    - 图片粘贴发送（截图、本地图片）
    - 多文件批量粘贴发送

说明：不使用微信「文件」按钮弹出的系统文件选择弹窗（该弹窗控件难定位、
不稳定），统一走剪贴板方案，稳定且兼容各种文件类型。
"""

from __future__ import annotations

import os
import time
from typing import List, Sequence, Union

from . import clipboard, inputs
from .exceptions import ControlNotFoundError
from .messaging import Messaging


PathLike = Union[str, "os.PathLike[str]"]


class FileSender:
    """文件 / 图片发送能力，复用 :class:`Messaging` 的输入框定位。"""

    def __init__(self, messaging: Messaging):
        self.messaging = messaging
        self.win = messaging.win

    def _focus_input(self):
        edit = self.messaging._get_edit()
        edit.click_input()
        time.sleep(0.1)
        return edit

    def send_file(self, path: PathLike, send: bool = True, wait: float = 0.6) -> None:
        """发送单个本地文件（文档、压缩包、Excel、PDF 等）。

        :param path: 本地文件路径
        :param send: 粘贴后是否直接回车发送
        :param wait: 粘贴后等待文件加载到输入框的时间
        """
        clipboard.set_files(path)
        self._focus_input()
        inputs.paste()
        time.sleep(wait)
        if send:
            inputs.enter()

    def send_files(
        self,
        paths: Sequence[PathLike],
        send: bool = True,
        wait: float = 0.8,
        one_by_one: bool = False,
    ) -> None:
        """批量发送多个文件。

        :param paths: 文件路径列表
        :param send: 粘贴后是否直接回车发送
        :param one_by_one: True 时逐个粘贴发送；False 时一次性粘贴全部文件
        """
        if one_by_one:
            for p in paths:
                self.send_file(p, send=send, wait=wait)
                time.sleep(0.4)
            return

        clipboard.set_files(list(paths))
        self._focus_input()
        inputs.paste()
        time.sleep(wait)
        if send:
            inputs.enter()

    def send_image(
        self,
        path: PathLike,
        as_image: bool = False,
        send: bool = True,
        wait: float = 0.6,
    ) -> None:
        """发送图片（截图、本地图片）。

        :param as_image: True 时以位图形式写入剪贴板（作为图片消息），
            False 时以文件形式粘贴（微信会自动识别图片并作为图片发送）
        """
        if as_image:
            clipboard.set_image(path)
        else:
            clipboard.set_files(path)
        self._focus_input()
        inputs.paste()
        time.sleep(wait)
        if send:
            inputs.enter()

    def send_to(self, contact: str, path: PathLike, **kwargs) -> None:
        """搜索联系人并发送文件（一步到位）。"""
        self.messaging.search_and_open(contact)
        self.send_file(path, **kwargs)
