"""基础消息发送能力（对应需求第一类）。

* 发送纯文本，支持换行、特殊符号、空格兼容
* 模拟回车一键发送，支持分段长文本
* 循环批量群发文本给多个联系人
* 快捷键输入：@、表情、换行、Tab、ESC 等组合按键
* 剪贴板粘贴内容发送（大段文字、链接）
"""

from __future__ import annotations

import time
from typing import Dict, Iterable, List, Optional, Sequence

from . import clipboard
from .exceptions import SendMessageError
from .inputs import InputSimulator
from .logger import get_logger
from .navigation import Navigator
from .window import WindowManager

log = get_logger("messaging")


class Messenger:
    """文本消息发送器。"""

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

    # ------------------------------------------------------------------ #
    # 输入
    # ------------------------------------------------------------------ #
    def _focus_edit(self):
        box = self.win.get_edit_box()
        box.click_input()
        time.sleep(self.config.after_click_delay)
        return box

    def input_text(self, text: str, human_like: bool = True) -> None:
        """把文本键入到输入框（不发送）。

        支持换行：文本中的 ``\\n`` 会转换为 Shift+Enter，从而在同一条消息中换行。
        """
        self._focus_edit()
        segments = text.split("\n")
        for i, seg in enumerate(segments):
            if seg:
                self.inputs.type_text(seg, human_like=human_like)
            if i < len(segments) - 1:
                self.inputs.new_line()  # Shift+Enter 换行，不发送

    def input_text_by_paste(self, text: str) -> None:
        """通过剪贴板粘贴方式把（大段 / 含链接）文本填入输入框。

        对于长文本、含 emoji / 特殊字符的内容，粘贴比逐字符输入更快更稳。
        文本中的换行会随剪贴板一并粘贴。
        """
        self._focus_edit()
        clipboard.set_text(text)
        self.inputs.paste()
        time.sleep(self.config.after_click_delay)

    # ------------------------------------------------------------------ #
    # 发送
    # ------------------------------------------------------------------ #
    def send_text(
        self,
        text: str,
        to: Optional[str] = None,
        use_paste: bool = True,
        human_like: bool = False,
    ) -> None:
        """发送一条纯文本消息。

        :param text: 消息内容，支持 ``\\n`` 换行、特殊符号、空格。
        :param to: 目标联系人 / 群（备注、昵称、群名）。为 None 时发送到当前会话。
        :param use_paste: True 用剪贴板粘贴（推荐，兼容特殊字符）；False 用键盘输入。
        :param human_like: 键盘输入模式下是否逐字符慢速输入。
        :raises SendMessageError: 发送失败。
        """
        try:
            if to is not None:
                self.nav.search_and_open(to)

            if use_paste:
                self.input_text_by_paste(text)
            else:
                self.input_text(text, human_like=human_like)

            time.sleep(self.config.after_click_delay)
            # 模拟回车一键发送
            self.inputs.enter()
            log.info("已发送文本到「%s」：%.30s", to or "当前会话", text.replace("\n", " "))
        except Exception as exc:  # noqa: BLE001
            raise SendMessageError(f"发送文本失败：{exc}") from exc

    def send_long_text(
        self,
        text: str,
        to: Optional[str] = None,
        max_len: int = 2000,
        interval: Optional[float] = None,
    ) -> int:
        """分段发送长文本。

        微信单条消息有长度上限，超长文本会被切分为多段依次发送（按换行边界优先）。

        :param max_len: 每段最大字符数。
        :param interval: 段间间隔秒数，默认取配置 ``send_interval``。
        :return: 实际发送的段数。
        """
        if to is not None:
            self.nav.search_and_open(to)

        interval = self.config.send_interval if interval is None else interval
        chunks = self._split_text(text, max_len)
        for i, chunk in enumerate(chunks):
            self.send_text(chunk, to=None, use_paste=True)
            if i < len(chunks) - 1:
                time.sleep(interval)
        log.info("长文本共分 %d 段发送完成。", len(chunks))
        return len(chunks)

    def broadcast_text(
        self,
        text: str,
        contacts: Sequence[str],
        interval: Optional[float] = None,
        use_paste: bool = True,
    ) -> Dict[str, bool]:
        """循环批量给多个联系人 / 群发送同一段文本。

        :param contacts: 联系人 / 群名列表。
        :param interval: 每个联系人之间的间隔秒数。
        :return: ``{联系人: 是否成功}`` 的结果字典。
        """
        interval = self.config.send_interval if interval is None else interval
        results: Dict[str, bool] = {}
        for i, name in enumerate(contacts):
            try:
                self.send_text(text, to=name, use_paste=use_paste)
                results[name] = True
            except Exception as exc:  # noqa: BLE001
                log.error("向「%s」群发失败：%s", name, exc)
                results[name] = False
            if i < len(contacts) - 1:
                time.sleep(interval)
        ok = sum(1 for v in results.values() if v)
        log.info("群发完成：成功 %d / 共 %d。", ok, len(contacts))
        return results

    # ------------------------------------------------------------------ #
    # 快捷键 / @ 成员
    # ------------------------------------------------------------------ #
    def mention(self, member: str, to: Optional[str] = None) -> None:
        """在群聊中 @ 某位成员。

        输入 ``@`` 后微信会弹出成员列表，继续输入成员名，回车选中。
        """
        if to is not None:
            self.nav.search_and_open(to)
        self._focus_edit()
        self.inputs.at()
        time.sleep(self.config.after_click_delay)
        self.inputs.type_text(member, human_like=False)
        time.sleep(self.config.after_click_delay)
        self.inputs.enter()  # 选中 @ 列表中的成员
        log.debug("已 @ 成员：%s", member)

    def press_hotkey(self, *keys: str) -> None:
        """在输入框内发送任意组合键（如表情面板、截图等）。"""
        self._focus_edit()
        self.inputs.hotkey(*keys)

    # ------------------------------------------------------------------ #
    # 工具
    # ------------------------------------------------------------------ #
    @staticmethod
    def _split_text(text: str, max_len: int) -> List[str]:
        """按行边界优先，把文本切分为不超过 max_len 的多段。"""
        if len(text) <= max_len:
            return [text]

        chunks: List[str] = []
        current = ""
        for line in text.splitlines(keepends=True):
            # 单行本身就超长，硬切
            while len(line) > max_len:
                if current:
                    chunks.append(current)
                    current = ""
                chunks.append(line[:max_len])
                line = line[max_len:]
            if len(current) + len(line) > max_len:
                chunks.append(current)
                current = line
            else:
                current += line
        if current:
            chunks.append(current)
        return chunks
