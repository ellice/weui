"""基础消息发送能力。

对应需求"一、基础消息发送能力"：

- 根据备注 / 昵称搜索好友、群聊，自动切入聊天窗口
- 发送纯文本消息，支持换行、特殊符号、空格
- 模拟回车一键发送，支持分段长文本
- 循环批量给多个联系人群发文本
- 快捷键输入：@、表情、换行、Tab、ESC 等组合键
- 剪贴板粘贴内容发送（大段文字、链接）
"""

from __future__ import annotations

import logging
from typing import Dict, Iterable, List, Optional, Sequence

from . import clipboard
from .config import WeChatConfig
from .exceptions import ContactNotFoundError
from .window import WeChatWindow

logger = logging.getLogger("wechat_auto.messaging")


class Messenger:
    """文本消息发送器，基于 :class:`WeChatWindow` 提供的基础设施。"""

    def __init__(self, window: WeChatWindow):
        self.window = window
        self.input = window.input

    @property
    def config(self) -> WeChatConfig:
        return self.window.config

    # ————————————————————— 搜索 / 切入会话 —————————————————————
    def open_chat(self, keyword: str) -> None:
        """按备注 / 昵称 / 群名搜索并切入对应聊天窗口。

        实现：清空搜索框 -> 输入关键字 -> 回车选中首个匹配项。

        Raises:
            ContactNotFoundError: 搜索后无匹配项。
        """
        self.window.activate()
        edit = self.window.get_search_edit()
        edit.click_input()
        self.input.sleep_short()
        self.input.clear_edit()
        self.input.sleep_short()

        # 用剪贴板粘贴关键字，兼容特殊字符与 emoji
        clipboard.set_text(keyword)
        clipboard.wait_clipboard_ready(self.config.short_delay)
        self.input.paste()
        # 等待搜索结果渲染
        self.input.sleep_medium()

        # 回车选中首个搜索结果
        self.input.press_enter()
        self.input.sleep_medium()

        # 校验是否成功进入会话：输入框应可用
        try:
            self.window.get_message_edit()
        except Exception as exc:  # noqa: BLE001
            raise ContactNotFoundError(
                f"未能切入会话，未找到匹配项：{keyword}"
            ) from exc
        logger.info("已切入会话：%s", keyword)

    # ————————————————————— 发送文本 —————————————————————
    def _send_current(self) -> None:
        """对当前输入框内容执行回车发送。"""
        self.input.press_enter()
        self.input.sleep_short()

    def send_text(
        self,
        keyword: str,
        text: str,
        slow: bool = False,
        use_clipboard: bool = True,
    ) -> None:
        """向指定联系人 / 群聊发送一段文本。

        Args:
            keyword: 联系人备注 / 昵称 / 群名。
            text: 文本内容，支持 ``\\n`` 换行、特殊符号、空格。
            slow: 是否慢速逐字输入（防风控）。仅在 ``use_clipboard=False`` 生效。
            use_clipboard: 是否用剪贴板粘贴（默认，兼容大段文字 / 链接 / emoji）。
        """
        self.open_chat(keyword)
        self.type_into_edit(text, slow=slow, use_clipboard=use_clipboard)
        self._send_current()
        logger.info("已发送文本到 %s（%d 字）", keyword, len(text))

    def type_into_edit(
        self,
        text: str,
        slow: bool = False,
        use_clipboard: bool = True,
    ) -> None:
        """把文本写入当前聊天输入框（不发送）。

        换行处理：剪贴板模式直接保留 ``\\n``；键盘模式用 Shift+Enter 换行，
        避免中途触发发送。
        """
        self.window.focus_message_edit()
        if use_clipboard:
            clipboard.set_text(text)
            clipboard.wait_clipboard_ready(self.config.short_delay)
            self.input.paste()
            self.input.sleep_short()
        elif slow:
            self.input.type_text_slow(text)
        else:
            # 逐行输入，行间用 Shift+Enter
            lines = text.split("\n")
            for idx, line in enumerate(lines):
                if line:
                    self.input.type_text_fast(line)
                if idx < len(lines) - 1:
                    self.input.press_shift_enter()

    def send_paste(self, keyword: str, content: str) -> None:
        """剪贴板粘贴内容发送（大段文字 / 链接）。等价于 use_clipboard=True。"""
        self.send_text(keyword, content, use_clipboard=True)

    # ————————————————————— 分段长文本 —————————————————————
    def send_long_text(
        self,
        keyword: str,
        text: str,
        chunk_size: int = 2000,
        separator: Optional[str] = None,
    ) -> int:
        """分段发送超长文本，规避单条消息长度限制。

        Args:
            keyword: 目标会话。
            text: 长文本。
            chunk_size: 每段最大字符数。
            separator: 若提供，则优先按该分隔符切分（如 ``"\\n\\n"``），
                再对超长段落按 ``chunk_size`` 二次切分。

        Returns:
            实际发送的段数。
        """
        self.open_chat(keyword)
        chunks = self._split_text(text, chunk_size, separator)
        for chunk in chunks:
            self.type_into_edit(chunk, use_clipboard=True)
            self._send_current()
            self.input.sleep_short()
        logger.info("已分 %d 段发送长文本到 %s", len(chunks), keyword)
        return len(chunks)

    @staticmethod
    def _split_text(
        text: str, chunk_size: int, separator: Optional[str]
    ) -> List[str]:
        raw: List[str] = []
        if separator:
            raw = [p for p in text.split(separator) if p != ""]
        else:
            raw = [text]

        chunks: List[str] = []
        for part in raw:
            for i in range(0, len(part), chunk_size):
                chunks.append(part[i : i + chunk_size])
        return chunks or [""]

    # ————————————————————— 批量群发 —————————————————————
    def broadcast(
        self,
        keywords: Sequence[str],
        text: str,
        use_clipboard: bool = True,
        per_target_delay: Optional[float] = None,
    ) -> Dict[str, bool]:
        """循环给多个联系人 / 群聊群发同一段文本。

        Args:
            keywords: 目标会话关键字列表。
            text: 群发内容。
            use_clipboard: 是否剪贴板粘贴发送。
            per_target_delay: 每个目标之间的额外延时（秒），防风控。

        Returns:
            ``{关键字: 是否成功}`` 的结果字典。
        """
        results: Dict[str, bool] = {}
        for kw in keywords:
            try:
                self.send_text(kw, text, use_clipboard=use_clipboard)
                results[kw] = True
            except Exception as exc:  # noqa: BLE001
                logger.warning("群发失败 %s：%s", kw, exc)
                results[kw] = False
            if per_target_delay:
                self.input.sleep(per_target_delay)
            else:
                self.input.sleep_medium()
        return results

    # ————————————————————— @ 与快捷键 —————————————————————
    def mention(self, member_name: str) -> None:
        """在群聊输入框中 @ 某个成员。

        实现：输入 ``@`` 触发候选 -> 输入成员名 -> 回车选中。
        应在已切入群聊后调用。
        """
        self.window.focus_message_edit()
        self.input.press_at()
        self.input.sleep_short()
        self.input.type_text_fast(member_name)
        self.input.sleep_short()
        self.input.press_enter()
        self.input.sleep_short()

    def send_with_mentions(
        self,
        keyword: str,
        members: Iterable[str],
        text: str,
    ) -> None:
        """在群聊中 @ 若干成员后再发送文本。"""
        self.open_chat(keyword)
        for m in members:
            self.mention(m)
        self.type_into_edit(text, use_clipboard=True)
        self._send_current()
