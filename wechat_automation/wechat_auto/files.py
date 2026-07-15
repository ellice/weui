"""文件、图片、媒体发送。

对应需求"二、文件、图片、媒体发送"：

- 本地文件粘贴发送（文档、压缩包、Excel、PDF）
- 图片粘贴发送（截图、本地图片）
- 多文件批量粘贴发送

原理：把文件路径 / 图片写入剪贴板 + ``Ctrl+V`` 粘贴到输入框 + 回车发送。
不依赖微信「文件」按钮弹窗（原生文件对话框控件难以稳定定位）。
"""

from __future__ import annotations

import logging
from typing import List, Sequence

from . import clipboard
from .messaging import Messenger
from .window import WeChatWindow

logger = logging.getLogger("wechat_auto.files")


class FileSender:
    """文件 / 图片发送器。复用 :class:`Messenger` 的会话切入与发送逻辑。"""

    def __init__(self, window: WeChatWindow, messenger: Messenger):
        self.window = window
        self.messenger = messenger
        self.input = window.input

    @property
    def config(self):
        return self.window.config

    def _paste_and_send(self) -> None:
        """在已聚焦的输入框执行粘贴并回车发送。"""
        edit = self.window.focus_message_edit()
        del edit  # 仅用于确保聚焦
        self.input.paste()
        # 文件 / 图片粘贴到输入框后需要稍长的渲染时间
        self.input.sleep_medium()
        self.input.press_enter()
        self.input.sleep_medium()

    def send_files(self, keyword: str, paths: Sequence[str]) -> List[str]:
        """向指定会话发送一个或多个本地文件（批量粘贴发送）。

        Args:
            keyword: 目标联系人 / 群聊。
            paths: 文件路径列表（文档、压缩包、Excel、PDF、图片等）。

        Returns:
            实际发送的规范化绝对路径列表。
        """
        self.messenger.open_chat(keyword)
        normalized = clipboard.set_files(paths)
        clipboard.wait_clipboard_ready(self.config.medium_delay)
        self._paste_and_send()
        logger.info("已向 %s 发送 %d 个文件", keyword, len(normalized))
        return normalized

    def send_file(self, keyword: str, path: str) -> str:
        """发送单个本地文件。"""
        return self.send_files(keyword, [path])[0]

    def send_image(self, keyword: str, image_path: str) -> None:
        """发送本地图片（作为图片而非文件展示）。

        写入 CF_DIB 位图到剪贴板后粘贴，微信会识别为图片消息。
        若希望以"文件"形式发送图片，请改用 :meth:`send_file`。
        """
        self.messenger.open_chat(keyword)
        clipboard.set_image(image_path)
        clipboard.wait_clipboard_ready(self.config.medium_delay)
        self._paste_and_send()
        logger.info("已向 %s 发送图片：%s", keyword, image_path)

    def send_images(self, keyword: str, image_paths: Sequence[str]) -> List[str]:
        """批量发送多张图片。

        注意：CF_DIB 一次只能承载一张位图，因此多图逐张粘贴发送。
        若追求"多图一次批量"，建议改用 :meth:`send_files`（以文件形式）。
        """
        self.messenger.open_chat(keyword)
        sent: List[str] = []
        for p in image_paths:
            clipboard.set_image(p)
            clipboard.wait_clipboard_ready(self.config.short_delay)
            self._paste_and_send()
            sent.append(p)
        logger.info("已向 %s 发送 %d 张图片", keyword, len(sent))
        return sent
