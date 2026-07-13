"""文件 / 图片 / 媒体发送模块。

实现原理
--------
微信 PC 版的"文件"按钮会弹出系统文件选择对话框，其控件较难稳定定位，
因此本库采用更可靠的 **剪贴板粘贴** 方案：

1. 把本地文件路径以 ``CF_HDROP`` 写入剪贴板；
2. 聚焦聊天输入框后 ``Ctrl+V`` 粘贴；
3. 微信自动把文件识别为附件，回车发送。

该方案同样适用于文档、压缩包、Excel、PDF、图片，以及多文件批量发送。
"""

from __future__ import annotations

import logging
import time
from typing import Sequence

from . import clipboard, input_utils
from .core import WeChatCore
from .exceptions import FileSendError
from .message import MessageSender

logger = logging.getLogger("wechat_auto")


class FileSender:
    """封装文件 / 图片发送。"""

    def __init__(self, core: WeChatCore, message_sender: MessageSender | None = None) -> None:
        self.core = core
        self.messages = message_sender or MessageSender(core)

    def _focus_input(self):
        box = self.messages._message_input()  # noqa: SLF001 - 内部复用
        box.set_focus()
        return box

    def send_file(
        self,
        path: str,
        press_send: bool = True,
        wait_paste: float = 0.8,
    ) -> None:
        """发送单个本地文件（文档 / 压缩包 / Excel / PDF 等）。"""

        self.send_files([path], press_send=press_send, wait_paste=wait_paste)

    def send_files(
        self,
        paths: Sequence[str],
        press_send: bool = True,
        wait_paste: float = 0.8,
    ) -> None:
        """批量发送多个本地文件（一次性粘贴，作为多个附件发送）。"""

        if not paths:
            raise FileSendError("待发送文件列表为空。")

        clipboard.copy_files(paths)
        self._focus_input()
        input_utils.paste()
        time.sleep(wait_paste)
        if press_send:
            input_utils.press_enter()
        logger.info("已发送 %d 个文件。", len(paths))

    def send_image(
        self,
        path: str,
        as_image: bool = True,
        press_send: bool = True,
        wait_paste: float = 0.8,
    ) -> None:
        """发送本地图片。

        ``as_image=True`` 时优先尝试以位图（CF_DIB）粘贴，让微信作为
        "图片消息"发送；失败则回退为 CF_HDROP 文件方式。
        """

        self._focus_input()
        pasted = False
        if as_image:
            try:
                clipboard.copy_image_as_bitmap(path)
                input_utils.paste()
                pasted = True
            except Exception as exc:  # noqa: BLE001
                logger.warning("位图粘贴失败，回退为文件方式：%s", exc)

        if not pasted:
            clipboard.copy_files([path])
            input_utils.paste()

        time.sleep(wait_paste)
        if press_send:
            input_utils.press_enter()
        logger.info("已发送图片：%s", path)

    def send_images(
        self,
        paths: Sequence[str],
        press_send: bool = True,
        wait_paste: float = 0.8,
    ) -> None:
        """批量发送多张图片（以文件方式一次性粘贴）。"""

        self.send_files(paths, press_send=press_send, wait_paste=wait_paste)
