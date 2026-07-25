"""基础消息发送能力。

提供：

* 按备注 / 昵称搜索并切入好友或群聊会话
* 发送纯文本（支持换行、特殊符号、空格）
* 剪贴板粘贴发送大段文本 / 链接
* 分段发送长文本
* 循环批量群发
* 定位并聚焦聊天输入框

发送优先采用「剪贴板 + Ctrl+V」策略以获得最佳的换行 / 特殊字符兼容性，
同时保留逐字符慢速输入模式用于模拟真人、规避风控。
"""

from __future__ import annotations

import time
from typing import Iterable, List, Optional, Sequence

from . import clipboard, input_sim
from .config import WeChatConfig, DEFAULT_CONFIG
from .exceptions import ContactNotFoundError, SendMessageError
from .window import WindowManager


class Messenger:
    """封装文本消息相关操作，依赖已连接的 :class:`WindowManager`。"""

    def __init__(
        self,
        window: WindowManager,
        config: Optional[WeChatConfig] = None,
    ):
        self.win = window
        self.config = config or window.config or DEFAULT_CONFIG

    # ------------------------------------------------------------------
    # 搜索与切入会话
    # ------------------------------------------------------------------
    def search_and_open(self, keyword: str, timeout: Optional[float] = None) -> None:
        """在搜索框输入关键字（备注 / 昵称）并回车切入首个匹配会话。

        Args:
            keyword: 好友备注、昵称或群聊名称。
        """
        cfg = self.config
        self.win.bring_to_front()
        try:
            search = self.win.find_control(
                title=cfg.search_edit_name,
                control_type="Edit",
                timeout=timeout,
            )
        except Exception:
            # 部分版本搜索框无标题，退化为第一个 Edit 控件。
            search = self.win.find_control(control_type="Edit", timeout=timeout)

        search.click_input()
        time.sleep(cfg.action_delay)
        # 先清空旧内容再输入。
        input_sim.clear_edit()
        clipboard.copy_text(keyword)
        input_sim.paste()
        time.sleep(0.6)  # 等待搜索结果浮出
        input_sim.press_enter()
        time.sleep(cfg.action_delay + 0.3)

    def open_chat(self, keyword: str) -> None:
        """搜索并进入指定联系人 / 群聊的聊天窗口（search_and_open 的别名）。"""
        self.search_and_open(keyword)

    # ------------------------------------------------------------------
    # 输入框定位
    # ------------------------------------------------------------------
    def _focus_input(self):
        """定位并聚焦聊天输入框。

        微信输入框在不同版本可能表现为 Edit 或 Document 控件，这里做多重回退。
        """
        cfg = self.config
        candidates = [
            {"title": cfg.input_edit_name, "control_type": "Edit"},
            {"control_type": "Edit"},
            {"control_type": "Document"},
        ]
        last_err: Optional[Exception] = None
        for crit in candidates:
            try:
                edit = self.win.find_control(timeout=3, **crit)
                if edit.exists():
                    edit.click_input()
                    time.sleep(0.1)
                    return edit
            except Exception as exc:
                last_err = exc
                continue
        raise SendMessageError(f"未能定位聊天输入框：{last_err}")

    # ------------------------------------------------------------------
    # 发送文本
    # ------------------------------------------------------------------
    def send_text(
        self,
        text: str,
        use_clipboard: bool = True,
        human_like: bool = False,
    ) -> None:
        """向当前会话发送一条文本消息。

        Args:
            text: 消息内容，支持 ``\\n`` 换行、特殊符号、空格。
            use_clipboard: 是否用剪贴板粘贴（推荐，兼容性最好）。
            human_like: 为 True 时逐字符慢速输入以模拟真人（会忽略
                use_clipboard）。
        """
        cfg = self.config
        self._focus_input()

        if human_like:
            input_sim.type_text(
                text,
                interval_min=cfg.type_interval_min,
                interval_max=cfg.type_interval_max,
            )
        elif use_clipboard:
            clipboard.copy_text(text)
            input_sim.paste()
        else:
            # 直接 send_keys：换行转 Shift+Enter，其他字符转义。
            for line_idx, line in enumerate(text.split("\n")):
                if line_idx > 0:
                    input_sim.press_shift_enter()
                if line:
                    input_sim.send_keys(input_sim.escape_keys(line))

        time.sleep(cfg.action_delay)
        input_sim.press_enter()
        time.sleep(cfg.send_delay)

    def send_multiline(self, lines: Sequence[str], use_clipboard: bool = True) -> None:
        """将多行合并为一条消息发送（行间使用软换行）。"""
        self.send_text("\n".join(lines), use_clipboard=use_clipboard)

    def send_long_text_in_chunks(
        self, text: str, chunk_size: int = 1500, delay: Optional[float] = None
    ) -> int:
        """分段发送长文本，规避单条消息长度限制。

        Args:
            text: 长文本。
            chunk_size: 每段最大字符数。
            delay: 每段之间的间隔秒数，默认取 ``send_delay``。

        Returns:
            实际发送的段数。
        """
        delay = self.config.send_delay if delay is None else delay
        chunks = [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]
        for chunk in chunks:
            self.send_text(chunk)
            time.sleep(delay)
        return len(chunks)

    def paste_and_send(self, content: str) -> None:
        """将大段文字 / 链接写入剪贴板后粘贴并发送。"""
        self.send_text(content, use_clipboard=True)

    # ------------------------------------------------------------------
    # 批量群发
    # ------------------------------------------------------------------
    def batch_send(
        self,
        contacts: Iterable[str],
        text: str,
        interval: Optional[float] = None,
        human_like: bool = False,
        stop_on_error: bool = False,
    ) -> dict:
        """循环给多个联系人 / 群聊群发同一段文本。

        Args:
            contacts: 联系人备注 / 昵称 / 群名称的可迭代对象。
            text: 要群发的文本。
            interval: 每个联系人之间的间隔秒数，默认取 ``batch_interval``。
            human_like: 是否逐字符慢速输入。
            stop_on_error: 出错时是否立即中断。

        Returns:
            形如 ``{"success": [...], "failed": {name: err}}`` 的结果字典。
        """
        interval = self.config.batch_interval if interval is None else interval
        result = {"success": [], "failed": {}}
        for name in contacts:
            try:
                self.search_and_open(name)
                self.send_text(text, human_like=human_like)
                result["success"].append(name)
            except Exception as exc:
                result["failed"][name] = str(exc)
                if stop_on_error:
                    raise SendMessageError(
                        f"群发在联系人 '{name}' 处中断：{exc}"
                    )
            time.sleep(interval)
        return result

    # ------------------------------------------------------------------
    # 快捷键组合
    # ------------------------------------------------------------------
    def mention(self, nickname: str) -> None:
        """在群聊中 @ 某位成员：输入 @ + 昵称后回车选中候选项。"""
        self._focus_input()
        input_sim.press_at()
        time.sleep(0.3)
        input_sim.type_text(
            nickname,
            interval_min=self.config.type_interval_min,
            interval_max=self.config.type_interval_max,
        )
        time.sleep(0.4)
        input_sim.press_enter()  # 选中候选成员
        time.sleep(0.2)

    def clear_input(self) -> None:
        """清空聊天输入框内容。"""
        self._focus_input()
        input_sim.clear_edit()

    def clear_search(self) -> None:
        """清空搜索框内容。"""
        cfg = self.config
        try:
            search = self.win.find_control(
                title=cfg.search_edit_name, control_type="Edit"
            )
        except Exception:
            search = self.win.find_control(control_type="Edit")
        search.click_input()
        input_sim.clear_edit()
