"""文件、图片、媒体发送。

核心原理：复制文件路径(CF_HDROP) 或图片(DIB) 到剪贴板 + Ctrl+V 粘贴到输入框 + 回车。
不依赖微信「文件」按钮的系统弹窗（弹窗控件难以稳定定位）。
"""

from __future__ import annotations

import time
from typing import Dict, Iterable, List, Sequence

from . import clipboard
from . import controls as C
from . import input_utils as K
from .core import WeChatAuto


class FileSender:
    """文件/图片/媒体发送能力封装。"""

    def __init__(self, wechat: WeChatAuto):
        self.wx = wechat

    def _paste_and_send(self, send_delay: float = 0.6) -> None:
        edit = self.wx.input_edit()
        C.wait_visible(edit, timeout=self.wx.default_timeout)
        edit.set_focus()
        time.sleep(0.2)
        K.paste()
        # 文件较大时微信需要时间生成预览，适当等待
        time.sleep(send_delay)
        K.press_enter()

    # ------------------------------------------------------------------ #
    # 文件（文档、压缩包、Excel、PDF 等）
    # ------------------------------------------------------------------ #
    def send_file(self, path: str, send_delay: float = 0.8) -> None:
        """以「文件」形式发送单个本地文件。"""
        clipboard.copy_files(path)
        self._paste_and_send(send_delay)

    def send_files(self, paths: Sequence[str], send_delay: float = 1.0) -> None:
        """一次性多文件批量发送（一次粘贴多个文件）。"""
        clipboard.copy_files(list(paths))
        self._paste_and_send(send_delay)

    def send_files_one_by_one(
        self, paths: Sequence[str], interval: float = 1.2
    ) -> None:
        """逐个文件分别发送（更稳妥，避免单次粘贴过多失败）。"""
        for p in paths:
            self.send_file(p)
            time.sleep(interval)

    # ------------------------------------------------------------------ #
    # 图片（截图、本地图片）
    # ------------------------------------------------------------------ #
    def send_image(self, image_path: str, send_delay: float = 0.8) -> None:
        """以「图片」形式发送本地图片（DIB 粘贴，而非文件附件）。"""
        clipboard.copy_image(image_path)
        self._paste_and_send(send_delay)

    def send_image_as_file(self, image_path: str, send_delay: float = 0.8) -> None:
        """以「文件」形式发送图片（保留原图，不压缩）。"""
        self.send_file(image_path, send_delay)

    # ------------------------------------------------------------------ #
    # 批量发送到多个联系人
    # ------------------------------------------------------------------ #
    def broadcast_file(
        self,
        contacts: Iterable[str],
        path: str,
        interval: float = 2.0,
    ) -> Dict[str, bool]:
        """把同一个文件群发给多个联系人。"""
        results: Dict[str, bool] = {}
        for name in contacts:
            try:
                self.wx.search_and_open(name)
                self.send_file(path)
                results[name] = True
            except Exception:  # noqa: BLE001
                results[name] = False
            K.random_sleep(interval, interval + 1.0)
        return results
