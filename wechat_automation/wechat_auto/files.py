"""文件 / 图片 / 媒体发送 Mixin。

核心原理：把文件路径（CF_HDROP）或图片（CF_DIB）写入剪贴板，
再在聊天输入框 Ctrl+V 粘贴，最后回车发送。

不依赖微信「文件」按钮弹窗（该原生弹窗为系统对话框，控件难以稳定定位）。
"""

from typing import Dict, Iterable, List, Sequence

from . import clipboard
from .utils import human_sleep, logger


class FileMixin:
    """文件与图片发送能力。"""

    config = None

    def _paste_and_send(self, send: bool, settle: float = 0.6):
        """聚焦输入框 -> 粘贴 -> （可选）发送 的公共流程。"""
        self.focus_input()
        clipboard.wait_clipboard_ready()
        self.paste()
        human_sleep(settle)  # 等待缩略图 / 文件卡片渲染
        if send:
            self.press_enter()

    def send_files(
        self,
        target: str,
        paths: Sequence[str],
        send: bool = True,
        per_batch: int = 0,
    ) -> bool:
        """向目标发送一个或多个本地文件（文档、压缩包、Excel、PDF 等）。

        :param target: 目标好友 / 群名称；``None`` 表示当前会话。
        :param paths: 文件路径列表。
        :param send: 是否粘贴后回车发送。
        :param per_batch: 每批粘贴的文件数，0 表示一次性粘贴全部；
            超大批量时可设为如 9，分批粘贴更稳定。
        """
        if target:
            self.search_and_open(target)

        path_list = list(paths)
        if per_batch and per_batch > 0:
            batches: List[Sequence[str]] = [
                path_list[i : i + per_batch] for i in range(0, len(path_list), per_batch)
            ]
        else:
            batches = [path_list]

        for batch in batches:
            clipboard.copy_files(batch)
            self._paste_and_send(send=send)
            human_sleep(self.config.short_pause)
        logger.info("已发送 %d 个文件到 %s", len(path_list), target or "当前会话")
        return True

    def send_file(self, target: str, path: str, send: bool = True) -> bool:
        """发送单个文件的便捷封装。"""
        return self.send_files(target, [path], send=send)

    def send_image(self, target: str, image_path: str, send: bool = True) -> bool:
        """以「图片消息」形式发送本地图片 / 截图（带预览缩略图）。

        与 :meth:`send_file` 区别：本方法发送图片消息，``send_file``
        发送的是文件附件。
        """
        if target:
            self.search_and_open(target)
        clipboard.copy_image(image_path)
        self._paste_and_send(send=send)
        logger.info("已发送图片到 %s：%s", target or "当前会话", image_path)
        return True

    def send_images(self, target: str, image_paths: Sequence[str], send: bool = True) -> bool:
        """批量发送多张图片（逐张粘贴发送）。"""
        if target:
            self.search_and_open(target)
        for p in image_paths:
            clipboard.copy_image(p)
            self._paste_and_send(send=send)
            human_sleep(self.config.short_pause)
        logger.info("已批量发送 %d 张图片到 %s", len(image_paths), target or "当前会话")
        return True

    def broadcast_files(
        self, targets: Iterable[str], paths: Sequence[str], interval: float = 1.5
    ) -> Dict[str, bool]:
        """批量给多个联系人发送同一组文件。"""
        results: Dict[str, bool] = {}
        for name in targets:
            try:
                self.send_files(name, paths)
                results[name] = True
            except Exception as exc:  # noqa: BLE001
                logger.error("发送文件到 %s 失败：%s", name, exc)
                results[name] = False
            human_sleep(interval)
        return results
