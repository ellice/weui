"""文件、图片、媒体发送。

原理：把本地文件路径以 CF_HDROP 写入剪贴板，在输入框 Ctrl+V 粘贴后回车发送。
这样无需定位微信「文件」按钮的系统选择弹窗（该弹窗控件难以稳定定位）。

支持：
- 单个 / 多个本地文件（文档、压缩包、Excel、PDF）；
- 图片（截图 / 本地图片）：默认以「文件路径」方式发送原图，
  也可用 ``as_image=True`` 走位图剪贴板（粘贴为图片内容）。
"""

from __future__ import annotations

import time
from typing import Any, Iterable, List

from . import clipboard
from .controls import ControlHelper
from .exceptions import FileSendError
from .input_simulator import InputSimulator


class FileSender:
    """文件 / 图片发送器，依赖输入框焦点能力。"""

    def __init__(self, window: Any, controls: ControlHelper,
                 simulator: InputSimulator, message_sender: Any) -> None:
        self.window = window
        self.controls = controls
        self.sim = simulator
        self.messages = message_sender

    def _focus_input(self) -> None:
        self.messages.focus_input()

    def send_files(self, paths: Iterable[str], send: bool = True,
                   settle: float = 0.6) -> List[str]:
        """发送一个或多个本地文件（批量也走同一路径）。

        :param paths: 本地文件路径列表。
        :param send: 粘贴后是否回车发送。
        :param settle: 粘贴后等待微信加载预览的时间。
        :return: 实际发送的绝对路径列表。
        """
        path_list = list(paths)
        if not path_list:
            raise FileSendError("未提供任何文件")
        try:
            abs_paths = clipboard.set_files(path_list)
            clipboard.wait_clipboard_ready(0.3)
            self._focus_input()
            self.sim.paste()
            time.sleep(settle)
            if send:
                self.sim.press_enter()
            return abs_paths
        except FileSendError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise FileSendError(f"发送文件失败: {exc}") from exc

    def send_file(self, path: str, send: bool = True) -> str:
        """发送单个文件。"""
        return self.send_files([path], send=send)[0]

    def send_image(self, path: str, as_image: bool = False,
                   send: bool = True, settle: float = 0.6) -> str:
        """发送图片。

        :param as_image: False（默认）以文件方式发送（保留原图）；
                         True 以位图粘贴（相当于截图直接贴）。
        """
        try:
            if as_image:
                ap = clipboard.set_image(path)
                clipboard.wait_clipboard_ready(0.3)
                self._focus_input()
                self.sim.paste()
                time.sleep(settle)
                if send:
                    self.sim.press_enter()
                return ap
            return self.send_file(path, send=send)
        except FileSendError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise FileSendError(f"发送图片失败: {exc}") from exc

    def send_images(self, paths: Iterable[str], send: bool = True) -> List[str]:
        """批量发送多张图片（以文件方式一次性粘贴）。"""
        return self.send_files(paths, send=send)
