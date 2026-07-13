"""消息发送模块：搜索联系人、切换会话、发送文本 / 剪贴板内容、批量群发。

依赖 :class:`~wechat_auto.core.WeChatCore` 提供的窗口与控件能力。
"""

from __future__ import annotations

import logging
import time
from typing import Dict, Iterable, List, Optional, Sequence

from . import clipboard, input_utils
from .core import WeChatCore
from .exceptions import ContactNotFoundError, ControlNotFoundError

logger = logging.getLogger("wechat_auto")


class MessageSender:
    """封装与"发消息"相关的所有操作。"""

    def __init__(self, core: WeChatCore) -> None:
        self.core = core

    # ------------------------------------------------------------------
    # 搜索 / 切换会话
    # ------------------------------------------------------------------
    def search_contact(self, keyword: str, wait: float = 1.2) -> None:
        """在顶部搜索框输入关键词（备注 / 昵称 / 群名）搜索。"""

        self.core.activate()
        win = self.core.main_window

        search_box = None
        # 微信主窗口顶部搜索框，常见 title 为"搜索"
        for name in ("搜索", "Search"):
            if self.core.control_exists(title=name, control_type="Edit"):
                search_box = self.core.find_control(title=name, control_type="Edit")
                break
        if search_box is None:
            # 回退：用快捷键 Ctrl+F 聚焦搜索框
            input_utils.send_keys("^f")
            time.sleep(0.3)
            search_box = self._first_edit()

        search_box.set_focus()
        input_utils.select_all()
        input_utils.press_backspace(1)
        # 用剪贴板粘贴，兼容特殊字符与 emoji
        clipboard.copy_text(keyword)
        input_utils.paste()
        time.sleep(wait)

    def open_chat(self, keyword: str, exact: bool = True, wait: float = 1.2) -> None:
        """搜索并进入与 ``keyword`` 匹配的聊天窗口。

        搜索后按回车选中第一个结果切入聊天窗口。若搜索无结果则抛
        :class:`ContactNotFoundError`。
        """

        self.search_contact(keyword, wait=wait)

        # 检查是否有搜索结果：微信搜索结果为列表项，回车进入首个结果
        input_utils.press_enter()
        time.sleep(wait)

        if exact and not self._current_chat_matches(keyword):
            # 如果标题不匹配，可能是没有结果或匹配到别的会话
            title = self.get_current_chat_title()
            if not title:
                raise ContactNotFoundError(
                    f"未搜索到联系人 / 群聊：{keyword}"
                )
            logger.warning(
                "当前会话标题(%s)与关键词(%s)不完全一致。", title, keyword
            )

    def _current_chat_matches(self, keyword: str) -> bool:
        title = self.get_current_chat_title()
        return bool(title) and keyword in title

    def get_current_chat_title(self) -> str:
        """读取当前聊天窗口标题（联系人 / 群名）。"""

        win = self.core.main_window
        for auto_id in ("chat_name", ):
            if self.core.control_exists(auto_id=auto_id):
                return self.core.get_text(
                    self.core.find_control(auto_id=auto_id)
                )
        # 回退：聊天区顶部第一个 Text 通常是标题
        try:
            texts = self.core.find_controls(control_type="Text")
            for t in texts:
                txt = self.core.get_text(t)
                if txt and txt not in ("微信", "Weixin", "WeChat"):
                    return txt
        except Exception:
            pass
        return ""

    def _first_edit(self):
        edits = self.core.find_controls(control_type="Edit")
        if not edits:
            raise ControlNotFoundError("未找到任何输入框。")
        return edits[0]

    # ------------------------------------------------------------------
    # 输入框定位
    # ------------------------------------------------------------------
    def _message_input(self):
        """定位聊天消息输入框。

        微信输入框通常是聊天区域内的可编辑控件。这里优先按较靠下的 Edit
        控件选择；不同版本控件差异较大，必要时可用 ``dump_control_tree`` 调试。
        """

        win = self.core.main_window
        # 优先尝试通过 auto_id / title
        for kwargs in (
            {"title": "输入", "control_type": "Edit"},
            {"control_type": "Edit"},
        ):
            edits = self.core.find_controls(**kwargs)
            if edits:
                # 取纵向位置最靠下的一个作为消息输入框
                try:
                    return max(edits, key=lambda c: c.rectangle().top)
                except Exception:
                    return edits[-1]
        raise ControlNotFoundError("未能定位聊天消息输入框。")

    def clear_input(self) -> None:
        """清空当前输入框。"""

        box = self._message_input()
        box.set_focus()
        input_utils.select_all()
        input_utils.press_backspace(1)

    def clear_search(self) -> None:
        """清空搜索框。"""

        input_utils.send_keys("^f")
        time.sleep(0.2)
        input_utils.select_all()
        input_utils.press_backspace(1)
        input_utils.press_esc()

    # ------------------------------------------------------------------
    # 发送文本
    # ------------------------------------------------------------------
    def send_text(
        self,
        text: str,
        slow: bool = True,
        clear_first: bool = True,
        press_send: bool = True,
    ) -> None:
        """在当前会话发送一段文本，支持换行 / 空格 / 特殊符号。

        换行由 ``Shift+Enter`` 处理，最终由 ``Enter`` 一键发送。
        """

        box = self._message_input()
        box.set_focus()
        if clear_first:
            input_utils.select_all()
            input_utils.press_backspace(1)
        input_utils.type_text(text, slow=slow)
        if press_send:
            input_utils.press_enter()

    def send_text_via_clipboard(
        self,
        text: str,
        clear_first: bool = True,
        press_send: bool = True,
    ) -> None:
        """通过剪贴板粘贴发送（适合大段文字 / 链接，速度快且不丢字）。"""

        box = self._message_input()
        box.set_focus()
        if clear_first:
            input_utils.select_all()
            input_utils.press_backspace(1)
        clipboard.copy_text(text)
        input_utils.paste()
        time.sleep(0.2)
        if press_send:
            input_utils.press_enter()

    def send_long_text_in_chunks(
        self,
        text: str,
        chunk_size: int = 500,
        interval: float = 0.8,
        use_clipboard: bool = True,
    ) -> int:
        """把长文本按 ``chunk_size`` 分段发送，返回发送段数。"""

        chunks = [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]
        for chunk in chunks:
            if use_clipboard:
                self.send_text_via_clipboard(chunk)
            else:
                self.send_text(chunk)
            time.sleep(interval)
        return len(chunks)

    # ------------------------------------------------------------------
    # 群发
    # ------------------------------------------------------------------
    def broadcast_text(
        self,
        contacts: Sequence[str],
        text: str,
        interval: float = 1.5,
        use_clipboard: bool = True,
        stop_on_error: bool = False,
    ) -> Dict[str, bool]:
        """循环给多个联系人 / 群聊群发同一段文本。

        返回 ``{联系人: 是否成功}`` 的字典。
        """

        results: Dict[str, bool] = {}
        for name in contacts:
            try:
                self.open_chat(name, exact=False)
                if use_clipboard:
                    self.send_text_via_clipboard(text)
                else:
                    self.send_text(text)
                results[name] = True
                logger.info("已发送给：%s", name)
            except Exception as exc:  # noqa: BLE001
                logger.error("发送给 %s 失败：%s", name, exc)
                results[name] = False
                if stop_on_error:
                    break
            input_utils.human_pause(interval, interval + 0.8)
        return results

    def send_mention(self, name: str, text: str = "", press_send: bool = True) -> None:
        """在群聊中 @某人 并可附带文本后发送。"""

        box = self._message_input()
        box.set_focus()
        input_utils.mention(name)
        if text:
            input_utils.type_text(" " + text, slow=False)
        if press_send:
            input_utils.press_enter()
