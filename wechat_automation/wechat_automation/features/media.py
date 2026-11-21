"""文件、图片、媒体发送能力（第二类能力）。

原理：将本地文件路径以 ``CF_HDROP`` 写入剪贴板，再在微信输入框 ``Ctrl+V``
粘贴，微信会自动识别为文件 / 图片附件，最后回车发送。

说明：不走微信「文件」按钮弹出的系统选择框——该弹窗为原生对话框，
控件难以稳定定位，剪贴板方案更可靠。
"""

from typing import Iterable, List, Optional

from ..config import WeChatConfig
from ..core.input_device import InputDevice
from ..core.window import WindowController
from ..exceptions import ContactNotFoundError
from ..utils.clipboard import set_clipboard_files
from ..utils.humanize import human_sleep


class MediaSender:
    def __init__(
        self,
        window: WindowController,
        device: InputDevice,
        config: Optional[WeChatConfig] = None,
    ):
        self.window = window
        self.device = device
        self.config = config or window.config

    def _input_edit(self):
        if self.window.exists(
            title=self.config.input_edit_title, control_type="Edit"
        ):
            return self.window.find(
                title=self.config.input_edit_title, control_type="Edit"
            )
        edits = self.window.main.descendants(control_type="Edit")
        if not edits:
            raise ContactNotFoundError("未找到消息输入框，请确认已进入聊天窗口。")
        return edits[-1]

    def send_files(self, paths: Iterable[str], send: bool = True) -> List[str]:
        """发送一个或多个本地文件 / 图片（文档、压缩包、Excel、PDF、截图等）。

        ``send=True`` 时粘贴后自动回车发送；设为 ``False`` 可先预览再手动发送。
        返回实际写入剪贴板并粘贴的绝对路径列表。
        """
        abs_paths = set_clipboard_files(paths)

        edit = self._input_edit()
        edit.click_input()
        self.device.send_keys("^v")
        # 文件较多 / 较大时，微信生成附件缩略图需要时间。
        human_sleep(self.config.action_pause * 3)

        if send:
            self.device.send_keys("{ENTER}")
            human_sleep(self.config.action_pause)
        return abs_paths

    def send_file(self, path: str, send: bool = True) -> List[str]:
        """发送单个文件的便捷封装。"""
        return self.send_files([path], send=send)

    def send_images(self, paths: Iterable[str], send: bool = True) -> List[str]:
        """发送图片（语义化封装，与 ``send_files`` 行为一致）。"""
        return self.send_files(paths, send=send)
