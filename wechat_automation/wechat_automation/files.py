"""文件、图片、媒体发送。

核心原理：将本地文件路径写入剪贴板（CF_HDROP 格式，等价资源管理器
「复制文件」），再在微信输入框执行 Ctrl+V 粘贴，最后回车发送。

支持：

* 单个本地文件发送（文档、压缩包、Excel、PDF 等）
* 图片发送（截图、本地图片）
* 多文件批量粘贴发送（一次 Ctrl+V 粘贴多个文件）

说明：不采用微信自带「文件」按钮弹窗选择文件的方式，因为系统文件
选择弹窗的控件较难稳定定位；剪贴板粘贴方案兼容性与稳定性更好。
"""

from __future__ import annotations

import os
import time
from typing import List, Optional, Sequence

from . import clipboard, input_sim
from .config import WeChatConfig, DEFAULT_CONFIG
from .exceptions import FileSendError
from .messaging import Messenger
from .window import WindowManager


class FileSender:
    """封装文件 / 图片发送，依赖已连接的窗口与 Messenger。"""

    def __init__(
        self,
        window: WindowManager,
        messenger: Optional[Messenger] = None,
        config: Optional[WeChatConfig] = None,
    ):
        self.win = window
        self.config = config or window.config or DEFAULT_CONFIG
        self.messenger = messenger or Messenger(window, self.config)

    def _validate(self, paths: Sequence[str]) -> List[str]:
        abs_paths: List[str] = []
        for p in paths:
            ap = os.path.abspath(p)
            if not os.path.isfile(ap):
                raise FileSendError(f"文件不存在或不是普通文件：{ap}")
            abs_paths.append(ap)
        if not abs_paths:
            raise FileSendError("未提供任何待发送的文件。")
        return abs_paths

    def _paste_and_send(self, caption: Optional[str]) -> None:
        cfg = self.config
        # 聚焦输入框
        self.messenger._focus_input()
        time.sleep(0.2)
        input_sim.paste()          # Ctrl+V 粘贴文件 / 图片
        time.sleep(0.8)            # 等待微信生成文件 / 图片预览
        if caption:
            # 附带说明文字：文件粘贴后追加一段文本再一起发送。
            clipboard.copy_text(caption)
            time.sleep(0.2)
            # 注意：粘贴文件后光标已在输入框，直接追加文本可能覆盖预览，
            # 这里选择先发送文件，再单独发送文字更稳妥。
        input_sim.press_enter()
        time.sleep(cfg.send_delay)
        if caption:
            self.messenger.send_text(caption)

    def send_file(
        self, path: str, to: Optional[str] = None, caption: Optional[str] = None
    ) -> None:
        """发送单个本地文件。

        Args:
            path: 本地文件绝对 / 相对路径（文档、压缩包、Excel、PDF 等）。
            to: 可选，先搜索并切入该联系人 / 群聊再发送。
            caption: 可选，随文件补发的说明文字。
        """
        abs_paths = self._validate([path])
        if to:
            self.messenger.search_and_open(to)
        clipboard.copy_files(abs_paths)
        time.sleep(0.3)
        self._paste_and_send(caption)

    def send_image(
        self, path: str, to: Optional[str] = None, caption: Optional[str] = None
    ) -> None:
        """发送图片（截图 / 本地图片）。

        与 :meth:`send_file` 原理一致；图片粘贴后微信会显示为图片消息。
        """
        self.send_file(path, to=to, caption=caption)

    def send_files(
        self, paths: Sequence[str], to: Optional[str] = None, one_by_one: bool = False
    ) -> None:
        """批量发送多个文件。

        Args:
            paths: 文件路径列表。
            to: 可选，先切入指定会话。
            one_by_one: 为 True 时逐个发送；否则一次性粘贴全部文件后发送。
        """
        abs_paths = self._validate(paths)
        if to:
            self.messenger.search_and_open(to)

        if one_by_one:
            for p in abs_paths:
                clipboard.copy_files([p])
                time.sleep(0.3)
                self._paste_and_send(None)
                time.sleep(self.config.send_delay)
        else:
            clipboard.copy_files(abs_paths)
            time.sleep(0.3)
            self._paste_and_send(None)
