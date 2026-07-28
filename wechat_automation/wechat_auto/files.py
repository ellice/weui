"""文件、图片、媒体发送。

统一原理：把文件路径 / 图片位图写入剪贴板，再在输入框 ``Ctrl+V`` 粘贴后回车发送。
不使用微信自带的「文件」按钮弹窗（原生文件对话框控件难以稳定定位）。

* :meth:`FileSender.send_file` —— 发送单个本地文件（文档、压缩包、Excel、PDF 等）
* :meth:`FileSender.send_files` —— 一次粘贴多个文件批量发送
* :meth:`FileSender.send_image` —— 以图片形式发送本地图片 / 截图
"""

from __future__ import annotations

from typing import Optional, Sequence

from . import clipboard
from .exceptions import SendMessageError
from .inputs import InputController
from .utils import human_sleep, logger


class FileSender:
    """文件 / 图片发送器，依附于已连接的 :class:`WeChatAuto`。"""

    def __init__(self, wx, inputs: Optional[InputController] = None) -> None:
        self.wx = wx
        self.inputs = inputs or InputController(default_delay=wx.input_delay)

    def _prepare_chat(self, keyword: Optional[str]):
        """必要时打开目标会话并聚焦输入框。"""
        from .messaging import MessageSender

        sender = MessageSender(self.wx, self.inputs)
        if keyword:
            sender.search_and_open(keyword)
        edit = sender._focus_input_box()
        if edit is None:
            raise SendMessageError("未找到聊天输入框，请确认已打开聊天窗口")
        return edit

    def send_file(self, keyword: Optional[str], file_path: str) -> None:
        """发送单个本地文件。

        :param keyword: 目标联系人 / 群名；None 表示已在目标会话。
        :param file_path: 本地文件路径。
        """
        self.send_files(keyword, [file_path])

    def send_files(
        self,
        keyword: Optional[str],
        file_paths: Sequence[str],
        press_enter: bool = True,
    ) -> None:
        """一次性把多个文件粘贴到输入框并发送。"""
        self._prepare_chat(keyword)
        clipboard.set_files(file_paths)
        # 粘贴后等待微信把文件加载到输入框（大文件需要更久）
        self.inputs.paste()
        human_sleep(max(1.0, self.wx.input_delay * 4))
        if press_enter:
            self.inputs.press_enter()
            human_sleep(self.wx.input_delay)
        logger.info("已发送 %d 个文件到 %s", len(file_paths), keyword or "当前会话")

    def send_image(self, keyword: Optional[str], image_path: str,
                   press_enter: bool = True) -> None:
        """以“图片”形式发送本地图片 / 截图（而非文件附件）。"""
        self._prepare_chat(keyword)
        clipboard.set_image(image_path)
        self.inputs.paste()
        human_sleep(max(0.8, self.wx.input_delay * 3))
        if press_enter:
            self.inputs.press_enter()
            human_sleep(self.wx.input_delay)
        logger.info("已发送图片到 %s", keyword or "当前会话")

    def send_images(
        self,
        keyword: Optional[str],
        image_paths: Sequence[str],
        interval: float = 0.6,
    ) -> None:
        """逐张发送多张图片。"""
        if keyword:
            self._prepare_chat(keyword)
        for i, path in enumerate(image_paths, 1):
            self.send_image(None, path)
            logger.info("已发送第 %d/%d 张图片", i, len(image_paths))
            human_sleep(interval)
