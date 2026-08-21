"""基础消息发送能力。

对应需求「一、基础消息发送能力」：

* 根据备注 / 昵称搜索好友、群聊，自动切入聊天窗口
* 发送纯文本消息，支持换行、特殊符号、空格兼容
* 模拟回车一键发送，支持分段长文本
* 循环批量给多个联系人群发文本
* 快捷键输入：@、表情、换行、Tab、ESC 等组合按键
* 剪贴板粘贴内容发送（大段文字、链接）
"""

from __future__ import annotations

import logging
import time
from typing import Dict, Iterable, List, Optional

from .exceptions import ContactNotFoundError
from .utils import (
    set_clipboard_text,
    human_delay,
    type_slowly,
)

logger = logging.getLogger("wechat_auto")


class Messaging:
    """文本消息与联系人搜索相关能力。依赖 :class:`WeChatWindow`。"""

    def __init__(self, win):
        self.win = win  # WeChatWindow 实例

    # ------------------------------------------------------------------ #
    # 搜索并切入聊天
    # ------------------------------------------------------------------ #
    def search_and_open(self, keyword: str, timeout: float = 8.0) -> None:
        """根据备注 / 昵称 / 群名搜索并进入对应聊天窗口。

        实现：点击搜索框 -> 清空 -> 用剪贴板粘贴关键字（兼容特殊字符）
        -> 回车选中第一个结果。
        """
        from pywinauto.keyboard import send_keys

        self.win.wake()
        search = self.win.window.child_window(title="搜索", control_type="Edit")
        if not search.exists():
            search = self.win.window.child_window(control_type="Edit", found_index=0)
        search.click_input()
        time.sleep(0.2)
        send_keys("^a")
        send_keys("{BACKSPACE}")
        # 用剪贴板粘贴，避免中文 / 特殊符号输入法问题
        set_clipboard_text(keyword)
        send_keys("^v")
        # 等待搜索结果加载
        time.sleep(max(0.8, timeout * 0.15))
        send_keys("{ENTER}")
        human_delay(0.3, 0.3)
        # 校验是否成功进入聊天（标题应包含关键字或聊天区可用）
        if not self._chat_opened(keyword):
            raise ContactNotFoundError(
                f"未能进入与「{keyword}」的聊天，请确认备注/昵称正确且能被搜索到。"
            )
        logger.info("已进入与「%s」的聊天窗口。", keyword)

    def _chat_opened(self, keyword: str) -> bool:
        """粗略判断是否已进入某个聊天窗口。"""
        try:
            # 存在消息输入框即认为进入了聊天
            self.win._get_message_edit()
            return True
        except Exception:  # noqa: BLE001
            return False

    # ------------------------------------------------------------------ #
    # 文本发送
    # ------------------------------------------------------------------ #
    def send_text(
        self,
        text: str,
        send: bool = True,
        use_clipboard: bool = True,
        slow: bool = False,
    ) -> None:
        """向当前已打开的聊天发送纯文本。

        :param text: 文本内容，``\\n`` 表示换行。
        :param send: 为 True 时输入完成后回车发送。
        :param use_clipboard: 为 True 时用剪贴板粘贴（推荐，兼容换行/特殊符号/空格/emoji）；
                              为 False 时用键盘逐段输入。
        :param slow: 为 True 且不使用剪贴板时，逐字符慢速输入模拟真人。
        """
        from pywinauto.keyboard import send_keys

        edit = self.win._get_message_edit()
        edit.click_input()
        time.sleep(0.15)

        if use_clipboard:
            set_clipboard_text(text)
            send_keys("^v")
        else:
            self._type_text_by_keyboard(text, slow=slow)

        human_delay(0.15, 0.2)
        if send:
            send_keys("{ENTER}")
            human_delay(0.15, 0.2)

    def _type_text_by_keyboard(self, text: str, slow: bool = False) -> None:
        """用键盘输入文本，换行以 Shift+Enter 处理，避免中途发送。"""
        from pywinauto.keyboard import send_keys

        lines = text.split("\n")
        for idx, line in enumerate(lines):
            if line:
                if slow:
                    type_slowly(lambda ch: send_keys(_escape_keys(ch), pause=0),
                                line)
                else:
                    send_keys(_escape_keys(line), pause=0.01)
            if idx < len(lines) - 1:
                # Shift+Enter = 输入框内换行而非发送
                send_keys("+{ENTER}")

    def send_long_text(
        self,
        text: str,
        max_len: int = 2000,
        send: bool = True,
        delay_between: float = 0.6,
    ) -> int:
        """分段发送超长文本（超过 ``max_len`` 按段落 / 长度切分）。

        :return: 实际发送的段数。
        """
        segments = _split_text(text, max_len)
        for i, seg in enumerate(segments):
            self.send_text(seg, send=send, use_clipboard=True)
            if i < len(segments) - 1:
                time.sleep(delay_between)
        return len(segments)

    def send_via_clipboard(self, content: str, send: bool = True) -> None:
        """剪贴板粘贴内容发送（大段文字、链接）。等价 use_clipboard=True。"""
        self.send_text(content, send=send, use_clipboard=True)

    # ------------------------------------------------------------------ #
    # 批量群发
    # ------------------------------------------------------------------ #
    def broadcast_text(
        self,
        contacts: Iterable[str],
        text: str,
        interval: float = 1.5,
        raise_on_error: bool = False,
    ) -> Dict[str, bool]:
        """循环批量给多个联系人 / 群聊发送同一段文本。

        :param contacts: 备注 / 昵称 / 群名列表。
        :param text: 要群发的文本。
        :param interval: 每个联系人之间的间隔秒数（防风控）。
        :param raise_on_error: 为 True 时遇到失败立即抛出，否则记录并继续。
        :return: {联系人: 是否成功} 的字典。
        """
        result: Dict[str, bool] = {}
        for name in contacts:
            try:
                self.search_and_open(name)
                self.send_text(text, send=True, use_clipboard=True)
                result[name] = True
                logger.info("已发送给「%s」", name)
            except Exception as exc:  # noqa: BLE001
                result[name] = False
                logger.error("发送给「%s」失败：%s", name, exc)
                if raise_on_error:
                    raise
            time.sleep(interval)
        return result

    # ------------------------------------------------------------------ #
    # 快捷键 / 组合键
    # ------------------------------------------------------------------ #
    def press_keys(self, keys: str, pause: float = 0.05) -> None:
        """在当前焦点控件发送任意 pywinauto 组合键字符串。

        例如：``press_keys('{ESC}')``、``press_keys('%s')``。
        """
        from pywinauto.keyboard import send_keys

        send_keys(keys, pause=pause)

    def mention(self, name: str, in_group: bool = True) -> None:
        """在群聊输入框 @ 某人。

        输入 ``@`` 后微信会弹出候选列表，粘贴姓名并回车选择。
        """
        from pywinauto.keyboard import send_keys

        edit = self.win._get_message_edit()
        edit.click_input()
        send_keys("@")
        time.sleep(0.4)
        set_clipboard_text(name)
        send_keys("^v")
        time.sleep(0.4)
        send_keys("{ENTER}")

    def open_emoji_panel(self) -> None:
        """点击表情按钮，打开表情面板。"""
        self.win.click_button("表情")

    def newline(self) -> None:
        """在输入框内插入换行（Shift+Enter）。"""
        self.press_keys("+{ENTER}")

    def press_tab(self) -> None:
        self.press_keys("{TAB}")

    def press_esc(self) -> None:
        self.press_keys("{ESC}")


# --------------------------------------------------------------------------- #
# 内部工具
# --------------------------------------------------------------------------- #
def _escape_keys(text: str) -> str:
    """转义 pywinauto send_keys 的特殊字符。"""
    specials = "^%+~(){}[]"
    out = []
    for ch in text:
        if ch in specials:
            out.append("{" + ch + "}")
        else:
            out.append(ch)
    return "".join(out)


def _split_text(text: str, max_len: int) -> List[str]:
    """按段落优先、长度兜底的方式切分长文本。"""
    if len(text) <= max_len:
        return [text]
    segments: List[str] = []
    buf = ""
    for para in text.split("\n"):
        candidate = para if not buf else buf + "\n" + para
        if len(candidate) <= max_len:
            buf = candidate
        else:
            if buf:
                segments.append(buf)
                buf = ""
            # 单段仍超长则按长度硬切
            while len(para) > max_len:
                segments.append(para[:max_len])
                para = para[max_len:]
            buf = para
    if buf:
        segments.append(buf)
    return segments
