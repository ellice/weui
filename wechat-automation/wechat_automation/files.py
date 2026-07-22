"""文件、图片、媒体发送。

原理：把本地文件路径以 ``CF_HDROP`` 格式复制到剪贴板，然后在聊天输入框
执行 Ctrl+V 粘贴，再回车发送。此方式无需点击微信「文件」弹窗（其控件
难以定位），兼容文档、压缩包、Excel、PDF、图片（截图/本地图片）等。
"""

from __future__ import annotations

import time
from typing import Sequence

from . import clipboard, input_utils


class FileMixin:
    """文件 / 图片发送混入类。"""

    config: "object"

    def _paste_and_send(self, wait_before_send: float = 1.0):
        cfg = self.config
        self._focus_input_box()
        input_utils.paste()
        # 文件/图片粘贴到输入框后需要一点时间生成预览
        time.sleep(wait_before_send)
        input_utils.press_enter()

    def send_file(self, path: str, wait_before_send: float = 1.0):
        """发送单个本地文件（文档、压缩包、Excel、PDF 等）。

        :param path: 本地文件绝对路径
        :raises FileNotFoundError: 路径不存在
        """
        clipboard.copy_files([path])
        clipboard.wait_settle(self.config.clipboard_settle_delay)
        self._paste_and_send(wait_before_send)
        return self

    def send_image(self, path: str, wait_before_send: float = 1.0):
        """发送单张图片（截图或本地图片）。

        图片与普通文件的发送原理一致，都是剪贴板 + Ctrl+V。
        """
        return self.send_file(path, wait_before_send)

    def send_files(
        self,
        paths: Sequence[str],
        one_by_one: bool = False,
        wait_before_send: float = 1.0,
        interval: float = 0.8,
    ):
        """批量发送多个文件 / 图片。

        :param paths: 文件路径列表
        :param one_by_one: True 时逐个发送；False 时一次性多选粘贴发送
        :param interval: 逐个发送时的间隔（秒）
        """
        if one_by_one:
            for p in paths:
                self.send_file(p, wait_before_send)
                time.sleep(interval)
            return self

        # 一次性多文件粘贴
        clipboard.copy_files(list(paths))
        clipboard.wait_settle(self.config.clipboard_settle_delay)
        self._paste_and_send(wait_before_send)
        return self
