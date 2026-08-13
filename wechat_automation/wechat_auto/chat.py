"""消息与文件/图片发送（第一、二类能力）。

- 搜索好友/群聊并切入会话
- 发送纯文本（支持换行、特殊符号、空格）
- 剪贴板粘贴发送（大段文字/链接）
- 循环批量群发
- 文件/图片粘贴发送（复制路径到剪贴板 + Ctrl+V）
- 快捷键输入：@、换行、Tab、ESC 等
"""

from __future__ import annotations

import time
from typing import Iterable, List, Optional, Sequence

from . import clipboard, input_sim
from .config import WeChatConfig, DEFAULT_CONFIG
from .exceptions import ContactNotFoundError, SendMessageError
from .window import WindowManager


class ChatManager:
    """聊天消息 / 文件发送操作。"""

    def __init__(
        self,
        window: WindowManager,
        config: WeChatConfig = DEFAULT_CONFIG,
    ):
        self.window = window
        self.config = config

    # ------------------------------------------------------------------ #
    # 搜索 & 切入会话
    # ------------------------------------------------------------------ #
    def _search_box(self):
        return self.window.wait_control(
            title=self.config.controls.search_box,
            control_type="Edit",
        )

    def clear_search(self) -> None:
        """清空搜索框内容。"""
        box = self._search_box()
        box.click_input()
        input_sim.select_all()
        input_sim.press_backspace()

    def search_and_open(self, keyword: str, timeout: Optional[float] = None) -> None:
        """根据备注/昵称/群名搜索并切入第一个匹配的会话。

        :raises ContactNotFoundError: 搜索无结果时抛出。
        """
        self.window.activate()
        box = self._search_box()
        box.click_input()
        input_sim.select_all()
        input_sim.press_backspace()
        # 通过剪贴板粘贴关键词，兼容中文/特殊字符
        clipboard.copy_text(keyword)
        input_sim.paste()
        time.sleep(self.config.timing.action_pause + 0.3)

        # 搜索结果出现后，回车打开第一个匹配项
        deadline = time.time() + (
            timeout if timeout is not None else self.config.timing.control_timeout
        )
        while time.time() < deadline:
            if self._chat_input_ready_for(keyword):
                return
            input_sim.press_enter()
            time.sleep(self.config.timing.action_pause + 0.4)
            if self._chat_input_ready():
                return
        raise ContactNotFoundError(f"搜索无匹配会话: {keyword}")

    def _chat_input_ready(self) -> bool:
        """判断聊天输入框是否已就绪（说明已切入某个会话）。"""
        return self.window.control_exists(control_type="Edit", found_index=0) and (
            self.window.button_exists(self.config.controls.send_button)
            or self.window.control_exists(control_type="Edit")
        )

    def _chat_input_ready_for(self, keyword: str) -> bool:
        """粗略判断当前已切入与关键词相关的会话（标题包含关键词）。"""
        try:
            title = self.get_current_title()
            return bool(title) and (keyword in title or title in keyword)
        except Exception:
            return False

    def get_current_title(self) -> str:
        """获取当前聊天窗口顶部的对话名称。"""
        try:
            # 顶部标题通常是聊天区域内的第一个 Text/Button
            ctrl = self.window.main.child_window(
                control_type="Text", found_index=0
            )
            return ctrl.window_text()
        except Exception:
            return ""

    # ------------------------------------------------------------------ #
    # 输入框操作
    # ------------------------------------------------------------------ #
    def _message_input(self):
        """定位消息输入框。

        微信输入框通常没有稳定标题，取聊天区域内的 Edit 控件。
        """
        # 优先按配置名称，退化为第一个可编辑 Edit
        if self.window.control_exists(
            title=self.config.controls.message_input, control_type="Edit"
        ):
            return self.window.find_control(
                title=self.config.controls.message_input, control_type="Edit"
            )
        return self.window.wait_control(control_type="Edit", found_index=0)

    def focus_input(self) -> None:
        """点击并聚焦消息输入框。"""
        self._message_input().click_input()
        time.sleep(self.config.timing.action_pause)

    def clear_input(self) -> None:
        """清空输入框内容。"""
        self.focus_input()
        input_sim.select_all()
        input_sim.press_backspace()

    # ------------------------------------------------------------------ #
    # 文本发送
    # ------------------------------------------------------------------ #
    def send_text(
        self,
        text: str,
        human: bool = True,
        via_clipboard: bool = False,
        send: bool = True,
    ) -> None:
        """发送纯文本消息，支持换行、空格、特殊符号。

        :param human: 逐字模拟真人输入（含随机延时防风控）。
        :param via_clipboard: True 时改用剪贴板粘贴（大段文字/链接更快更稳）。
        :param send: True 时输入后自动回车发送。
        """
        try:
            self.focus_input()
            if via_clipboard:
                clipboard.copy_text(text)
                input_sim.paste()
                time.sleep(self.config.timing.action_pause)
            else:
                input_sim.type_text(text, timing=self.config.timing, human=human)
            if send:
                time.sleep(self.config.timing.action_pause)
                input_sim.press_enter()
                time.sleep(self.config.timing.action_pause)
        except Exception as exc:
            raise SendMessageError(f"发送文本失败: {exc}") from exc

    def send_clipboard_text(self, text: str, send: bool = True) -> None:
        """剪贴板粘贴发送（大段文字/链接），:meth:`send_text` 的便捷封装。"""
        self.send_text(text, via_clipboard=True, send=send)

    def send_long_text_segments(
        self,
        segments: Sequence[str],
        interval: float = 0.5,
        via_clipboard: bool = True,
    ) -> None:
        """分段发送长文本，每段单独发送。"""
        for seg in segments:
            self.send_text(seg, via_clipboard=via_clipboard, send=True)
            time.sleep(interval)

    def send_to_contact(
        self,
        keyword: str,
        text: str,
        via_clipboard: bool = False,
        human: bool = True,
    ) -> None:
        """搜索并切入某个联系人/群，然后发送文本。"""
        self.search_and_open(keyword)
        self.send_text(text, human=human, via_clipboard=via_clipboard)

    def batch_send(
        self,
        contacts: Iterable[str],
        text: str,
        interval: float = 1.0,
        via_clipboard: bool = True,
        stop_on_error: bool = False,
    ) -> List[str]:
        """循环批量给多个联系人/群发送同一段文本。

        :return: 发送失败的联系人列表。
        """
        failed: List[str] = []
        for name in contacts:
            try:
                self.send_to_contact(name, text, via_clipboard=via_clipboard)
            except Exception as exc:
                failed.append(name)
                if stop_on_error:
                    raise SendMessageError(f"给 {name} 发送失败: {exc}") from exc
            time.sleep(interval)
        return failed

    # ------------------------------------------------------------------ #
    # 文件 / 图片发送
    # ------------------------------------------------------------------ #
    def send_files(
        self,
        paths: Sequence[str],
        caption: Optional[str] = None,
        send: bool = True,
    ) -> None:
        """通过“复制文件到剪贴板 + Ctrl+V”发送本地文件/图片。

        支持文档、压缩包、Excel、PDF、图片等；可一次粘贴多个文件。

        :param caption: 可选，随文件一起发送的说明文字（会另起一条）。
        """
        try:
            self.focus_input()
            clipboard.copy_files(list(paths))
            input_sim.paste()
            # 等待微信读取剪贴板并把文件加载到输入框
            time.sleep(self.config.timing.paste_render_delay)
            if send:
                input_sim.press_enter()
                time.sleep(self.config.timing.paste_render_delay)
            if caption:
                self.send_text(caption, via_clipboard=True, send=True)
        except Exception as exc:
            raise SendMessageError(f"发送文件失败: {exc}") from exc

    def send_file(self, path: str, caption: Optional[str] = None) -> None:
        """发送单个文件，:meth:`send_files` 的便捷封装。"""
        self.send_files([path], caption=caption)

    def send_image(self, path: str, caption: Optional[str] = None) -> None:
        """发送单张图片（与文件同样走剪贴板粘贴）。"""
        self.send_files([path], caption=caption)

    def send_files_to_contact(
        self,
        keyword: str,
        paths: Sequence[str],
        caption: Optional[str] = None,
    ) -> None:
        """搜索并切入会话后批量发送文件。"""
        self.search_and_open(keyword)
        self.send_files(paths, caption=caption)
