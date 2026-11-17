"""第一、二部分：文本消息与文件 / 图片 / 媒体发送。

依赖 :class:`WeChatWindow`（窗口/控件）与 :class:`InputController`（键鼠）。
"""

import time
from typing import Iterable, List, Optional, Sequence, Tuple

from . import clipboard
from .config import WeChatConfig
from .exceptions import ContactNotFoundError, SendMessageError
from .input_control import InputController
from .window import WeChatWindow


class Messenger:
    """消息 / 文件发送能力。"""

    def __init__(
        self,
        window: WeChatWindow,
        inputs: InputController,
        config: WeChatConfig,
    ):
        self.win = window
        self.inputs = inputs
        self.config = config

    # ---------------------------------------------------- 一、搜索好友并切入
    def search_and_open(self, keyword: str, timeout: Optional[float] = None) -> None:
        """根据备注 / 昵称搜索好友或群聊，并自动切入其聊天窗口。"""
        self.win.activate()
        # 全局搜索快捷键 Ctrl+F，聚焦搜索框
        self.inputs.send_keys("^f")
        time.sleep(self.config.action_delay)
        self.win.clear_search()
        # 用剪贴板粘贴关键字，兼容中文 / 特殊字符
        clipboard.copy_text(keyword)
        self.inputs.paste()
        time.sleep(self.config.action_delay)
        # 回车选中第一个搜索结果并切入聊天
        self.inputs.enter()
        time.sleep(self.config.action_delay)
        # 校验是否成功切入（输入框应存在）
        if not self.win.control_exists(
            title=self.config.input_edit_title, control_type="Edit"
        ) and not self.win.control_exists(control_type="Edit"):
            raise ContactNotFoundError(f"未能切入与「{keyword}」的聊天窗口")

    # ---------------------------------------------------- 一、发送纯文本消息
    def _focus_input(self):
        edit = self.win.find_control(
            title=self.config.input_edit_title, control_type="Edit"
        ) or self.win.find_control(control_type="Edit")
        if edit is None:
            raise SendMessageError("未找到聊天输入框，请确认已切入某个会话。")
        edit.click_input()
        time.sleep(self.config.poll_interval)
        return edit

    def type_text(self, text: str, human_like: bool = True) -> None:
        """在输入框输入文本（不发送），支持换行、空格、特殊符号。"""
        self._focus_input()
        if human_like:
            self.inputs.type_like_human(text)
        else:
            # 大段文本走剪贴板粘贴，速度更快
            clipboard.copy_text(text)
            self.inputs.paste()
            time.sleep(self.config.poll_interval)

    def send_text(
        self,
        text: str,
        human_like: bool = True,
        clear_first: bool = True,
    ) -> None:
        """输入文本并回车发送。"""
        if clear_first:
            try:
                self.win.clear_input()
            except Exception:  # noqa: BLE001
                pass
        self.type_text(text, human_like=human_like)
        time.sleep(self.config.poll_interval)
        self.inputs.enter()
        time.sleep(self.config.action_delay)

    def send_paste_text(self, text: str) -> None:
        """剪贴板粘贴发送（大段文字、链接），避免逐字输入过慢。"""
        self.send_text(text, human_like=False)

    def send_segments(
        self, segments: Sequence[str], human_like: bool = True
    ) -> None:
        """分段发送长文本，每段作为一条独立消息。"""
        for seg in segments:
            self.send_text(seg, human_like=human_like)
            time.sleep(self.config.poll_interval)

    def send_multiline(self, lines: Sequence[str]) -> None:
        """把多行拼成一条消息（行间 Shift+Enter 换行）后发送。"""
        self._focus_input()
        for i, line in enumerate(lines):
            if i > 0:
                self.inputs.newline()
            clipboard.copy_text(line)
            self.inputs.paste()
            time.sleep(self.config.poll_interval)
        self.inputs.enter()
        time.sleep(self.config.action_delay)

    # ---------------------------------------------------- 一、批量群发
    def batch_send(
        self,
        contacts: Iterable[str],
        text: str,
        human_like: bool = True,
    ) -> List[Tuple[str, bool, str]]:
        """循环给多个联系人群发同一段文本。

        返回 ``[(联系人, 是否成功, 错误信息), ...]``，单个失败不影响后续。
        """
        results: List[Tuple[str, bool, str]] = []
        for contact in contacts:
            try:
                self.search_and_open(contact)
                self.send_text(text, human_like=human_like)
                results.append((contact, True, ""))
            except Exception as exc:  # noqa: BLE001
                results.append((contact, False, str(exc)))
            time.sleep(self.config.batch_interval)
        return results

    # ---------------------------------------------------- 二、文件 / 图片发送
    def _paste_and_send(self) -> None:
        self._focus_input()
        self.inputs.paste()
        # 文件 / 图片粘贴后微信需要时间加载预览
        time.sleep(self.config.action_delay)
        self.inputs.enter()
        time.sleep(self.config.action_delay)

    def send_file(self, path: str) -> None:
        """本地文件粘贴发送（文档、压缩包、Excel、PDF 等）。

        原理：复制文件路径到剪贴板（CF_HDROP）+ Ctrl+V 粘贴到输入框后发送。
        不走微信「文件」按钮弹窗（弹窗控件难定位）。
        """
        clipboard.copy_files([path])
        self._paste_and_send()

    def send_image(self, path: str) -> None:
        """图片粘贴发送（截图、本地图片）。与文件发送同一机制。"""
        self.send_file(path)

    def send_files(self, paths: Sequence[str], one_by_one: bool = False) -> None:
        """多文件发送。

        - ``one_by_one=False``：一次性把多个文件写入剪贴板后粘贴发送。
        - ``one_by_one=True``：逐个文件粘贴发送（更稳妥）。
        """
        if one_by_one:
            for p in paths:
                self.send_file(p)
                time.sleep(self.config.poll_interval)
        else:
            clipboard.copy_files(list(paths))
            self._paste_and_send()
