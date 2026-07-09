"""文件、图片、媒体发送（对应需求第二类）。

核心原理：把本地文件路径写入剪贴板（CF_HDROP）+ 在输入框 ``Ctrl+V`` 粘贴，
再回车发送。适用于文档、压缩包、Excel、PDF、图片、截图等一切本地文件。

说明：本库不尝试调用微信「文件」按钮弹出的系统"打开文件"对话框——
该弹窗为原生对话框，控件定位困难且易随系统 / 版本变化，稳定性差；
剪贴板粘贴方式更稳健，因此作为唯一推荐实现。
"""

from __future__ import annotations

import os
import time
from typing import List, Optional, Sequence

from . import clipboard
from .exceptions import SendMessageError
from .inputs import InputSimulator
from .logger import get_logger
from .navigation import Navigator
from .window import WindowManager

log = get_logger("files")


class FileSender:
    """基于剪贴板粘贴的文件 / 图片发送器。"""

    def __init__(
        self,
        window: WindowManager,
        navigator: Navigator,
        inputs: InputSimulator,
    ) -> None:
        self.win = window
        self.nav = navigator
        self.inputs = inputs
        self.config = window.config

    def _focus_edit(self):
        box = self.win.get_edit_box()
        box.click_input()
        time.sleep(self.config.after_click_delay)
        return box

    def send_files(
        self,
        paths: Sequence[str] | str,
        to: Optional[str] = None,
        send_together: bool = True,
    ) -> List[str]:
        """粘贴发送一个或多个本地文件 / 图片。

        :param paths: 单个路径或路径列表（文档、压缩包、Excel、PDF、图片均可）。
        :param to: 目标联系人 / 群，为 None 时发送到当前会话。
        :param send_together: True 时多个文件一次性粘贴并作为一批发送；
            False 时逐个文件分别粘贴发送。
        :return: 实际发送的文件绝对路径列表。
        :raises SendMessageError: 发送失败。
        """
        if isinstance(paths, (str, bytes)):
            path_list = [str(paths)]
        else:
            path_list = [str(p) for p in paths]

        try:
            if to is not None:
                self.nav.search_and_open(to)

            if send_together:
                sent = self._paste_and_send(path_list)
            else:
                sent = []
                for p in path_list:
                    sent.extend(self._paste_and_send([p]))
                    time.sleep(self.config.send_interval)

            log.info("已发送 %d 个文件到「%s」。", len(sent), to or "当前会话")
            return sent
        except SendMessageError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise SendMessageError(f"发送文件失败：{exc}") from exc

    def send_image(self, path: str, to: Optional[str] = None) -> List[str]:
        """发送单张图片（本地图片 / 截图文件），等价于 send_files 单文件。"""
        return self.send_files([path], to=to)

    def send_images(self, paths: Sequence[str], to: Optional[str] = None) -> List[str]:
        """批量发送多张图片，一次性粘贴发送。"""
        return self.send_files(paths, to=to, send_together=True)

    # ------------------------------------------------------------------ #
    # 内部
    # ------------------------------------------------------------------ #
    def _paste_and_send(self, paths: Sequence[str]) -> List[str]:
        """把文件写入剪贴板 -> 聚焦输入框 -> Ctrl+V -> 等待 -> 回车发送。"""
        abs_paths = clipboard.set_files(paths)
        self._focus_edit()
        # 粘贴文件到输入框
        self.inputs.paste()
        # 文件较大时微信需要时间加载缩略图 / 附件预览
        time.sleep(max(self.config.after_search_delay, 1.0))
        self.inputs.enter()
        time.sleep(self.config.after_click_delay)
        return abs_paths
