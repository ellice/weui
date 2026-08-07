"""文件、图片、媒体发送（第二类）。

核心原理：把本地文件路径写入剪贴板（CF_HDROP）→ 在输入框 ``Ctrl+V``
粘贴 → 回车发送。适用于文档、压缩包、Excel、PDF、图片、截图等。

说明：不直接调用微信「文件」按钮弹窗选择文件——该弹窗为系统原生
控件，难以稳定定位，改用剪贴板粘贴更可靠。
"""

from __future__ import annotations

import os
import time
from typing import Iterable, List, Optional

from . import clipboard
from .config import WeChatConfig
from .controls import ControlHelper
from .exceptions import SendMessageError
from .inputs import InputController

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}


class FileSender:
    """通过剪贴板粘贴发送文件 / 图片 / 多文件。"""

    def __init__(
        self,
        window,
        controls: ControlHelper,
        inputs: InputController,
        config: WeChatConfig,
    ) -> None:
        self.window = window
        self.controls = controls
        self.inputs = inputs
        self.config = config

    # ------------------------------------------------------------------ #
    # 发送文件 / 图片
    # ------------------------------------------------------------------ #
    def send_file(self, path: str, caption: Optional[str] = None) -> None:
        """发送单个本地文件（文档 / 压缩包 / Excel / PDF 等）。

        :param caption: 可选的附带文字说明（先发文字再发文件）。
        """
        self.send_files([path], caption=caption)

    def send_image(self, path: str, caption: Optional[str] = None) -> None:
        """发送单张图片（截图或本地图片）。原理同 send_file。"""
        self.send_files([path], caption=caption)

    def send_files(
        self, paths: Iterable[str], caption: Optional[str] = None
    ) -> List[str]:
        """批量发送多个文件 / 图片（一次性粘贴）。

        :returns: 实际发送的绝对路径列表。
        :raises SendMessageError: 粘贴或发送失败。
        """
        paths = list(paths)
        abs_paths = clipboard.copy_files(paths)

        edit = self._get_input_edit()
        edit.set_focus()

        if caption:
            self.inputs.type_text_slowly(caption)
            self.inputs.new_line()

        # 粘贴文件到输入框
        self.inputs.hotkey_paste()
        # 粘贴文件后微信需要一点时间生成预览
        time.sleep(max(self.config.action_delay, 1.0))

        try:
            self.inputs.press_enter()
            time.sleep(self.config.action_delay)
        except Exception as exc:  # noqa: BLE001
            raise SendMessageError(f"发送文件失败：{exc}") from exc

        return abs_paths

    def send_files_one_by_one(
        self, paths: Iterable[str], interval: Optional[float] = None
    ) -> List[str]:
        """逐个发送多个文件（每个文件单独一条消息）。

        某些版本一次粘贴多文件会合并成"聊天记录"，需要逐个发送时使用。
        """
        interval = self.config.batch_interval if interval is None else interval
        sent: List[str] = []
        paths = list(paths)
        for i, p in enumerate(paths):
            self.send_files([p])
            sent.append(os.path.abspath(p))
            if i < len(paths) - 1:
                time.sleep(interval)
        return sent

    # ------------------------------------------------------------------ #
    # 内部
    # ------------------------------------------------------------------ #
    def _get_input_edit(self):
        return self.controls.find_first(
            [
                {"title": t, "control_type": "Edit"}
                for t in self.config.input_edit_fallback_titles
            ],
            timeout=self.config.default_timeout,
        )

    @staticmethod
    def is_image(path: str) -> bool:
        return os.path.splitext(path)[1].lower() in IMAGE_EXTENSIONS
