"""文件、图片、媒体发送。

对应需求「二、文件、图片、媒体发送」：

* 本地文件粘贴发送（文档、压缩包、Excel、PDF）
* 图片粘贴发送（截图、本地图片）
* 多文件批量粘贴发送
* 原理：复制文件路径到剪贴板 + Ctrl+V 粘贴到输入框发送

说明：不使用微信「文件」按钮弹窗（原生弹窗控件难以稳定定位），
统一走「剪贴板 + Ctrl+V」方案，稳定性更高。
"""

from __future__ import annotations

import logging
import os
import time
from typing import Iterable, List, Optional

from .utils import (
    set_clipboard_files,
    set_clipboard_image,
    human_delay,
)

logger = logging.getLogger("wechat_auto")


class FileSender:
    """文件 / 图片发送能力。依赖 :class:`WeChatWindow`。"""

    def __init__(self, win):
        self.win = win

    # ------------------------------------------------------------------ #
    # 文件发送（作为附件）
    # ------------------------------------------------------------------ #
    def send_files(
        self,
        paths: Iterable[str],
        send: bool = True,
        paste_wait: float = 0.8,
    ) -> List[str]:
        """把一个或多个本地文件粘贴到当前聊天输入框并发送。

        适用于文档、压缩包、Excel、PDF、图片（作为文件附件）等。

        :param paths: 本地文件路径列表。
        :param send: 粘贴后是否回车发送。
        :param paste_wait: 粘贴后等待附件加载到输入框的秒数。
        :return: 实际发送的文件绝对路径列表。
        """
        from pywinauto.keyboard import send_keys

        abs_paths = set_clipboard_files(paths)
        edit = self.win._get_message_edit()
        edit.click_input()
        time.sleep(0.2)
        send_keys("^v")
        time.sleep(paste_wait)
        human_delay(0.2, 0.2)
        if send:
            send_keys("{ENTER}")
            human_delay(0.2, 0.3)
        logger.info("已发送 %d 个文件：%s", len(abs_paths), abs_paths)
        return abs_paths

    def send_file(self, path: str, send: bool = True) -> str:
        """发送单个文件的便捷方法。"""
        return self.send_files([path], send=send)[0]

    def send_files_batch(
        self,
        paths: Iterable[str],
        per_message: int = 1,
        send: bool = True,
        interval: float = 1.0,
    ) -> int:
        """多文件批量发送。

        :param per_message: 每条消息包含的文件数量（微信支持一次粘贴多文件）。
        :param interval: 每条消息之间的间隔秒数。
        :return: 发送的消息条数。
        """
        paths = list(paths)
        count = 0
        for i in range(0, len(paths), max(1, per_message)):
            chunk = paths[i : i + per_message]
            self.send_files(chunk, send=send)
            count += 1
            if i + per_message < len(paths):
                time.sleep(interval)
        return count

    # ------------------------------------------------------------------ #
    # 图片发送（作为图片，而非文件附件）
    # ------------------------------------------------------------------ #
    def send_image(self, image_path: str, send: bool = True,
                   paste_wait: float = 0.8) -> None:
        """把本地图片以「图片」形式粘贴发送（截图 / 本地图片）。

        与 :meth:`send_files` 的区别：这里写入的是位图数据，微信会识别为
        图片消息而不是文件附件。
        """
        from pywinauto.keyboard import send_keys

        if not os.path.exists(image_path):
            raise FileNotFoundError(f"图片不存在：{image_path}")
        set_clipboard_image(image_path)
        edit = self.win._get_message_edit()
        edit.click_input()
        time.sleep(0.2)
        send_keys("^v")
        time.sleep(paste_wait)
        if send:
            send_keys("{ENTER}")
            human_delay(0.2, 0.3)
        logger.info("已发送图片：%s", image_path)

    def send_clipboard_screenshot(self, send: bool = True,
                                  paste_wait: float = 0.5) -> None:
        """发送剪贴板中已有的截图（例如用户刚用系统截图工具截好的图）。

        直接 Ctrl+V 当前剪贴板内容，不修改剪贴板。
        """
        from pywinauto.keyboard import send_keys

        edit = self.win._get_message_edit()
        edit.click_input()
        time.sleep(0.2)
        send_keys("^v")
        time.sleep(paste_wait)
        if send:
            send_keys("{ENTER}")
            human_delay(0.2, 0.3)
