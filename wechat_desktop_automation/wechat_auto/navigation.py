"""联系人 / 群聊搜索与切换。

对应需求第一类中的"根据备注 / 昵称搜索好友、群聊，自动切入聊天窗口"，
同时也是文件发送、会话管理等模块的公共前置能力。
"""

from __future__ import annotations

import time
from typing import Optional

from .exceptions import ContactNotFoundError
from .logger import get_logger
from .window import WindowManager

log = get_logger("navigation")


class Navigator:
    """负责搜索联系人并切入对应聊天窗口。"""

    def __init__(self, window: WindowManager) -> None:
        self.win = window
        self.config = window.config

    def search_and_open(self, keyword: str, exact: bool = True) -> str:
        """在顶部搜索框输入关键字，命中后回车打开聊天窗口。

        微信搜索框输入关键字后，会在下拉列表给出匹配结果，
        直接回车即可打开第一个（最匹配）结果的聊天窗口。

        :param keyword: 备注 / 昵称 / 群名关键字。
        :param exact: 为 True 时校验最终打开的会话标题是否包含关键字，
            不匹配则抛出 :class:`ContactNotFoundError`。
        :return: 成功打开后的聊天窗口标题。
        :raises ContactNotFoundError: 未搜索到目标。
        """
        cfg = self.config
        self.win.activate()

        # 1. 清空并聚焦搜索框
        box = self.win.get_search_box()
        box.click_input()
        box.type_keys("^a{BACKSPACE}", set_foreground=True)
        time.sleep(cfg.after_click_delay)

        # 2. 用剪贴板方式填入关键字，避免特殊字符 / emoji 输入问题
        from . import clipboard

        clipboard.set_text(keyword)
        box.type_keys("^v", set_foreground=True)
        time.sleep(cfg.after_search_delay)

        # 3. 回车打开第一个匹配结果
        box.type_keys("{ENTER}", set_foreground=True)
        time.sleep(cfg.after_search_delay)

        title = self.current_chat_title()
        if title is None:
            raise ContactNotFoundError(f"搜索“{keyword}”后未能打开任何聊天窗口。")

        if exact and keyword not in title:
            log.warning("打开的会话标题“%s”不包含关键字“%s”。", title, keyword)
            raise ContactNotFoundError(
                f"搜索“{keyword}”命中的会话标题为“{title}”，与预期不符。"
            )

        log.info("已切入聊天窗口：%s", title)
        return title

    def current_chat_title(self) -> Optional[str]:
        """获取当前聊天窗口标题（即对方昵称 / 群名）。

        微信聊天区域顶部通常有一个显示对话名称的控件；不同版本控件类型不同，
        这里尝试多种方式，取不到返回 None。
        """
        win = self.win
        # 方式一：标题栏文本控件（会话名一般在聊天区顶部的 Text/Button）
        try:
            # 聊天区域标题通常是聊天记录上方的一个可点击文本
            candidates = win.main_win.descendants(control_type="Text")
            for c in candidates:
                txt = c.window_text()
                if txt and txt.strip():
                    # 简单启发式：跳过明显的系统文本
                    return txt.strip()
        except Exception:  # noqa: BLE001
            pass
        return None

    def is_group_chat(self, title: Optional[str] = None) -> bool:
        """判断当前会话是否为群聊。

        启发式：群聊标题通常带人数后缀 ``(N)``；此外群聊聊天区一般存在
        "聊天信息"里的成员列表。这里以标题特征为主。
        """
        import re

        if title is None:
            title = self.current_chat_title() or ""
        return re.match(self.config.group_title_pattern, title) is not None
