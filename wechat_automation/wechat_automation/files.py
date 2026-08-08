"""模块二：文件、图片、媒体发送。

核心原理：把**文件对象**复制到剪贴板（Windows ``CF_HDROP``）→ 聚焦聊天
输入框 → ``Ctrl+V`` 粘贴 → 回车发送。适用于文档、压缩包、Excel、PDF、
截图、本地图片等。可一次复制多个文件实现批量发送。

不使用微信自带的“文件”按钮弹窗（系统级弹窗控件难以稳定定位）。
"""

from __future__ import annotations

import time
from typing import Any, Iterable, List

from . import clipboard
from .controls import ControlHelper
from .input_simulator import InputSimulator


class FileSender:
    """基于剪贴板粘贴的文件/图片发送器。

    :param main: 主窗口包装对象。
    :param controls: 控件助手。
    :param sim: 键鼠模拟器。
    """

    def __init__(self, main: Any, controls: ControlHelper,
                 sim: InputSimulator) -> None:
        self.main = main
        self.controls = controls
        self.sim = sim

    def _focus_input(self, timeout: float = 5.0) -> None:
        for criteria in (
            {"title": "输入", "control_type": "Edit"},
            {"control_type": "Edit", "found_index": -1},
        ):
            try:
                ctrl = self.controls.wait_control(timeout=timeout, **criteria)
                ctrl.set_focus()
                return
            except Exception:  # noqa: BLE001
                continue

    def send_file(self, path: str, caption: str = "",
                  send_delay: float = 0.6) -> None:
        """发送单个本地文件（文档/压缩包/Excel/PDF/图片皆可）。

        :param path: 本地文件绝对或相对路径。
        :param caption: 可选，粘贴文件后追加的文字说明（同一条消息内）。
        :param send_delay: 粘贴后等待渲染再发送的时间（秒）。
        """
        self.send_files([path], caption=caption, send_delay=send_delay)

    def send_files(self, paths: Iterable[str], caption: str = "",
                   send_delay: float = 0.8) -> List[str]:
        """批量发送多个文件（一次粘贴多个文件对象）。

        :return: 实际复制到剪贴板的文件绝对路径列表。
        """
        files = clipboard.copy_files(paths)  # 非 Windows 会抛依赖异常
        self._focus_input()
        self.sim.select_all()
        self.sim.backspace(1)
        self.sim.paste()
        time.sleep(send_delay)
        if caption:
            self.sim.type_text(caption)
        self.sim.enter()
        return files

    def send_image(self, path: str, caption: str = "") -> None:
        """发送本地图片（等价于 send_file，图片同样走剪贴板粘贴）。"""
        self.send_file(path, caption=caption)

    def send_files_separately(self, paths: Iterable[str],
                              interval: float = 1.0) -> List[str]:
        """逐个单独发送多个文件（每个文件一条消息）。

        与 :meth:`send_files`（合并到一条粘贴）相对，适合需要分条发送的场景。
        """
        sent: List[str] = []
        for p in paths:
            self.send_file(p)
            sent.append(p)
            time.sleep(interval)
        return sent
