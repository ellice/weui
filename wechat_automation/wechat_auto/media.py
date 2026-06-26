"""文件、图片、媒体发送（需求类别二）。

核心原理：复制文件路径到剪贴板（CF_HDROP）+ Ctrl+V 粘贴到输入框 + 回车发送。
不依赖微信「文件」按钮弹窗（弹窗为系统对话框，控件难定位、稳定性差）。

支持：
- 本地文件发送（文档、压缩包、Excel、PDF 等）
- 图片发送（截图/本地图片，走 CF_DIB 直接粘贴为图片）
- 多文件批量发送（一次性写入文件列表）
"""

from __future__ import annotations

import os
from typing import List, Sequence

from . import clipboard
from .base import WeChatBase
from .exceptions import SendMessageError
from .input_sim import InputSimulator
from .message import MessageSender
from .utils import human_sleep, logger


class MediaSender:
    def __init__(
        self, base: WeChatBase, inp: InputSimulator, msg: MessageSender
    ) -> None:
        self.base = base
        self.inp = inp
        self.msg = msg

    def _paste_and_send(self, send: bool, wait: float = 1.0) -> None:
        self.inp.paste()
        human_sleep(wait, 0.5)  # 等待微信加载文件/图片预览
        if send:
            self.inp.press_enter()
            human_sleep(0.5, 0.3)

    def send_file(self, file_path: str, send: bool = True) -> str:
        """发送单个本地文件（作为「文件」消息）。返回绝对路径。"""
        abs_paths = clipboard.set_files([file_path])
        self.msg._focus_input()
        self._paste_and_send(send)
        logger.info("已发送文件: %s", abs_paths[0])
        return abs_paths[0]

    def send_files(self, file_paths: Sequence[str], send: bool = True) -> List[str]:
        """批量发送多个文件：一次性写入剪贴板文件列表后粘贴。"""
        abs_paths = clipboard.set_files(file_paths)
        self.msg._focus_input()
        self._paste_and_send(send, wait=1.5)
        logger.info("已批量发送 %d 个文件", len(abs_paths))
        return abs_paths

    def send_files_one_by_one(
        self, file_paths: Sequence[str], send: bool = True, delay: float = 1.0
    ) -> List[str]:
        """逐个发送文件（更稳，适合大文件或网络较慢时）。"""
        sent: List[str] = []
        for p in file_paths:
            try:
                sent.append(self.send_file(p, send=send))
            except Exception as exc:  # noqa: BLE001
                logger.error("发送文件 %s 失败: %s", p, exc)
            human_sleep(delay, 0.4)
        return sent

    def send_image(self, image_path: str, send: bool = True, as_file: bool = False) -> str:
        """发送本地图片。

        - as_file=False：作为「图片」消息发送（CF_DIB 粘贴，对方看到的是图片）。
        - as_file=True：作为「文件」发送（保留原图质量，走文件列表）。
        """
        abs_path = os.path.abspath(os.path.expanduser(image_path))
        if not os.path.exists(abs_path):
            raise SendMessageError(f"图片不存在: {abs_path}")

        if as_file:
            return self.send_file(abs_path, send=send)

        clipboard.set_image(abs_path)
        self.msg._focus_input()
        self._paste_and_send(send)
        logger.info("已发送图片: %s", abs_path)
        return abs_path

    def send_images(self, image_paths: Sequence[str], send: bool = True) -> List[str]:
        """批量发送多张图片（逐张粘贴，保证顺序）。"""
        sent: List[str] = []
        for p in image_paths:
            try:
                sent.append(self.send_image(p, send=send))
            except Exception as exc:  # noqa: BLE001
                logger.error("发送图片 %s 失败: %s", p, exc)
            human_sleep(0.8, 0.4)
        return sent
