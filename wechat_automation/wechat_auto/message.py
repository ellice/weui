"""基础消息发送能力（需求类别一）。

依赖 base（控件）、input_sim（键鼠）、clipboard（剪贴板）。
能力：
- 根据备注/昵称搜索好友、群聊并切入聊天窗口
- 发送纯文本（支持换行、特殊符号、空格）
- 模拟回车发送，支持分段长文本
- 循环批量群发
- 快捷键输入：@、换行、Tab、ESC 等
- 剪贴板粘贴大段文字/链接发送
"""

from __future__ import annotations

from typing import Dict, Iterable, List, Optional, Sequence

from . import clipboard
from .base import WeChatBase
from .exceptions import ContactNotFoundError, SendMessageError
from .input_sim import InputSimulator
from .utils import human_sleep, logger


class MessageSender:
    def __init__(self, base: WeChatBase, inp: InputSimulator) -> None:
        self.base = base
        self.inp = inp

    # ---------------- 搜索 / 切入聊天 ----------------
    def _search_box(self):
        # 微信搜索框：Edit 控件，名称为「搜索」
        return self.base.find(title="搜索", control_type="Edit", timeout=self.base.timeout)

    def search_and_open(self, keyword: str, exact: bool = True) -> bool:
        """搜索备注/昵称/群名并打开对应聊天窗口。

        exact=True 时回车直达第一个匹配项；适合较精确的关键词。
        返回是否成功切入。
        """
        search = self._search_box()
        search.click_input()
        human_sleep(0.3, 0.2)
        # 清空搜索框已有内容
        self.inp.clear_field()
        human_sleep(0.2, 0.1)
        # 用剪贴板粘贴关键词，兼容特殊字符/emoji
        clipboard.set_text(keyword)
        self.inp.paste()
        human_sleep(0.8, 0.4)  # 等待搜索结果加载

        # 回车选择第一个搜索结果，进入聊天窗口
        self.inp.press_enter()
        human_sleep(0.6, 0.3)

        if not self._is_chat_opened(keyword):
            # 兜底：尝试点击搜索结果列表第一项
            opened = self._click_first_search_result(keyword)
            if not opened:
                raise ContactNotFoundError(f"搜索不到联系人/群聊: {keyword}")
        logger.info("已切入聊天: %s", keyword)
        return True

    def _click_first_search_result(self, keyword: str) -> bool:
        result = self.base.find_optional(title=keyword, control_type="ListItem", timeout=2.0)
        if result is not None:
            result.click_input()
            human_sleep(0.5, 0.3)
            return True
        return False

    def _is_chat_opened(self, keyword: str) -> bool:
        """粗略判断是否已进入目标聊天：聊天区标题包含关键词。"""
        title_ctrl = self.base.find_optional(
            title=keyword, control_type="Text", timeout=1.5
        )
        return title_ctrl is not None

    # ---------------- 输入框 ----------------
    def _edit_box(self):
        """聊天消息输入框（Edit 控件）。不同版本无固定名称，取最后一个可编辑 Edit。"""
        # 优先尝试常见输入框：很多版本输入框名称即当前聊天对象名
        edits = self.base.window.descendants(control_type="Edit")
        if not edits:
            raise SendMessageError("未找到聊天输入框，请确认已进入聊天窗口。")
        # 搜索框通常在最上方，输入框在底部，取靠下的那个
        edits_sorted = sorted(edits, key=lambda e: e.rectangle().top)
        return edits_sorted[-1]

    def _focus_input(self) -> None:
        edit = self._edit_box()
        edit.click_input()
        human_sleep(0.2, 0.1)

    # ---------------- 发送文本 ----------------
    def send_text(
        self,
        text: str,
        clear_first: bool = True,
        send: bool = True,
        slow: bool = False,
    ) -> None:
        """向当前聊天发送纯文本。

        - 支持换行：\n 在输入框内表现为软换行（Shift+Enter）。
        - 支持特殊符号、空格。
        - send=True 时按回车发送。
        - slow=True 时逐字慢速输入（防风控）。
        """
        self._focus_input()
        if clear_first:
            self.inp.clear_field()
            human_sleep(0.1, 0.1)

        if slow:
            self.inp.type_text_slowly(text)
        else:
            self._type_multiline(text)

        if send:
            human_sleep(0.2, 0.2)
            self.inp.press_enter()
            human_sleep(0.3, 0.2)

    def _type_multiline(self, text: str) -> None:
        """逐行输入，行间用 Shift+Enter 换行，避免中途触发发送。"""
        lines = text.split("\n")
        for i, line in enumerate(lines):
            if line:
                self.inp.type_text(line)
            if i < len(lines) - 1:
                self.inp.newline()

    def send_text_via_clipboard(self, text: str, send: bool = True) -> None:
        """大段文字/链接：直接走剪贴板粘贴，速度快且不丢字符。"""
        self._focus_input()
        self.inp.clear_field()
        clipboard.set_text(text)
        self.inp.paste()
        human_sleep(0.3, 0.2)
        if send:
            self.inp.press_enter()
            human_sleep(0.3, 0.2)

    def send_long_text_in_chunks(
        self, text: str, chunk_size: int = 1000, send: bool = True
    ) -> int:
        """分段发送超长文本，返回发送的段数。"""
        chunks = [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]
        for chunk in chunks:
            self.send_text_via_clipboard(chunk, send=send)
            human_sleep(0.6, 0.4)
        return len(chunks)

    # ---------------- 批量群发 ----------------
    def broadcast(
        self,
        contacts: Sequence[str],
        text: str,
        per_contact_delay: float = 1.2,
        via_clipboard: bool = True,
    ) -> Dict[str, bool]:
        """循环给多个联系人/群发送同一段文本。

        返回 {联系人: 是否成功}。单个失败不影响其余。
        """
        results: Dict[str, bool] = {}
        for name in contacts:
            try:
                self.search_and_open(name)
                if via_clipboard:
                    self.send_text_via_clipboard(text)
                else:
                    self.send_text(text)
                results[name] = True
                logger.info("已发送给: %s", name)
            except Exception as exc:  # noqa: BLE001
                results[name] = False
                logger.error("发送给 %s 失败: %s", name, exc)
            human_sleep(per_contact_delay, 0.5)
        return results

    # ---------------- 快捷输入 ----------------
    def at_member(self, name: str = "", text: str = "", send: bool = False) -> None:
        """群聊 @ 某人，可附带后续文本。"""
        self._focus_input()
        self.inp.at_someone(name)
        if text:
            human_sleep(0.2, 0.1)
            self.inp.type_text(" " + text)
        if send:
            self.inp.press_enter()

    def clear_input(self) -> None:
        """清空当前输入框内容。"""
        self._focus_input()
        self.inp.clear_field()

    def clear_search(self) -> None:
        """清空搜索框内容。"""
        try:
            search = self._search_box()
            search.click_input()
            self.inp.clear_field()
        except Exception as exc:  # noqa: BLE001
            logger.warning("清空搜索框失败: %s", exc)
