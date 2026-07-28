"""基础消息发送能力。

* 按备注 / 昵称搜索好友、群聊并切入聊天窗口
* 发送纯文本（支持换行、特殊符号、空格）
* 回车一键发送、分段长文本
* 循环批量群发
* 剪贴板粘贴发送大段文字 / 链接
"""

from __future__ import annotations

from typing import Dict, List, Optional, Sequence

from . import clipboard
from .exceptions import ContactNotFoundError, SendMessageError
from .inputs import InputController
from .utils import human_sleep, logger, wait_until


class MessageSender:
    """消息发送器，依附于一个已连接的 :class:`WeChatAuto`。"""

    def __init__(self, wx, inputs: Optional[InputController] = None) -> None:
        self.wx = wx
        self.inputs = inputs or InputController(default_delay=wx.input_delay)

    # ------------------------------------------------------------------ #
    # 搜索 / 切换会话
    # ------------------------------------------------------------------ #
    def search_and_open(self, keyword: str, timeout: Optional[float] = None) -> None:
        """按备注 / 昵称 / 群名搜索并打开对应聊天窗口。

        实现：点击顶部搜索框 -> 清空 -> 输入关键字 -> 回车打开第一个结果。

        :raises ContactNotFoundError: 未找到匹配的联系人 / 群聊。
        """
        self.wx.activate()
        try:
            search_box = self.wx.find_control(
                title="搜索", control_type="Edit", timeout=timeout
            )
        except Exception:  # noqa: BLE001 - 部分版本搜索框无标题，退回快捷键
            search_box = None

        if search_box is not None:
            search_box.click_input()
        else:
            # Ctrl+F 聚焦搜索框（微信支持）
            self.inputs.send_keys("^f")

        human_sleep(self.wx.input_delay)
        self.inputs.clear_input()
        clipboard.set_text(keyword)
        self.inputs.paste()
        # 等待搜索结果加载
        human_sleep(max(0.8, self.wx.input_delay * 3))
        self.inputs.press_enter()
        human_sleep(self.wx.input_delay)

        if not self._verify_chat_opened(keyword, timeout=timeout):
            raise ContactNotFoundError(f"未能打开与「{keyword}」的聊天窗口")
        logger.info("已打开聊天窗口：%s", keyword)

    def _verify_chat_opened(
        self, keyword: str, timeout: Optional[float] = None
    ) -> bool:
        """尽力校验聊天窗口标题是否包含关键字（校验失败不视为致命）。"""
        timeout = timeout or 3.0
        try:
            def _check():
                # 聊天区通常有一个显示对方名称的控件
                title = self.get_current_chat_title()
                return keyword in title if title else False

            return bool(wait_until(_check, timeout=timeout, interval=0.3,
                                   error_message="等待聊天窗口打开"))
        except Exception:  # noqa: BLE001
            # 无法校验时保守返回 True，交给上层根据发送结果判断
            return True

    def get_current_chat_title(self) -> str:
        """获取当前聊天窗口对方（好友 / 群）的名称。"""
        for auto_id in ("会话", "ChatContactName"):
            try:
                ctrl = self.wx.main_window.child_window(auto_id=auto_id)
                if ctrl.exists():
                    return ctrl.window_text()
            except Exception:  # noqa: BLE001
                continue
        return ""

    # ------------------------------------------------------------------ #
    # 发送文本
    # ------------------------------------------------------------------ #
    def _focus_input_box(self):
        """聚焦聊天输入框并返回控件（找不到时返回 None，退回坐标点击）。"""
        try:
            edit = self.wx.main_window.child_window(
                title="输入", control_type="Edit"
            )
            if edit.exists():
                edit.click_input()
                return edit
        except Exception:  # noqa: BLE001
            pass
        # 退回：点击窗口下方输入区域
        try:
            edits = self.wx.main_window.descendants(control_type="Edit")
            if edits:
                edits[-1].click_input()
                return edits[-1]
        except Exception:  # noqa: BLE001
            pass
        return None

    def send_text(
        self,
        keyword: Optional[str],
        text: str,
        use_clipboard: bool = True,
        press_enter: bool = True,
    ) -> None:
        """向指定联系人 / 群发送一条纯文本消息。

        :param keyword: 联系人备注 / 昵称 / 群名；为 None 时表示已在目标聊天窗口。
        :param text: 文本内容，支持 ``\\n`` 换行、特殊符号与空格。
        :param use_clipboard: True 用剪贴板粘贴（推荐，兼容特殊符号 / 大段文本）；
                              False 用逐字模拟输入（更“拟人”）。
        :param press_enter: 是否发送后按回车（一键发送）。
        """
        if keyword:
            self.search_and_open(keyword)

        edit = self._focus_input_box()
        if edit is None:
            raise SendMessageError("未找到聊天输入框，请确认已打开聊天窗口")

        self.inputs.clear_input()

        if use_clipboard:
            clipboard.set_text(text)
            self.inputs.paste()
        else:
            self.inputs.type_text(text)

        human_sleep(self.wx.input_delay)
        if press_enter:
            self.inputs.press_enter()
            human_sleep(self.wx.input_delay)
        logger.info("已发送文本（%d 字）到 %s", len(text), keyword or "当前会话")

    def send_multiline(self, keyword: Optional[str], lines: Sequence[str]) -> None:
        """把多行组合成一条消息发送（行间用换行，不逐行发送）。"""
        self.send_text(keyword, "\n".join(lines), use_clipboard=True)

    def send_segments(
        self,
        keyword: Optional[str],
        segments: Sequence[str],
        interval: float = 0.6,
    ) -> None:
        """分段发送长文本：把 segments 逐条作为独立消息发送。

        适合把超长文本切成多条，避免单条过长。
        """
        if keyword:
            self.search_and_open(keyword)
        for i, seg in enumerate(segments, 1):
            self.send_text(None, seg, use_clipboard=True, press_enter=True)
            logger.info("已发送第 %d/%d 段", i, len(segments))
            human_sleep(interval)

    # ------------------------------------------------------------------ #
    # 批量群发
    # ------------------------------------------------------------------ #
    def broadcast(
        self,
        keywords: Sequence[str],
        text: str,
        interval: float = 1.0,
        stop_on_error: bool = False,
    ) -> Dict[str, bool]:
        """循环给多个联系人 / 群群发同一段文本。

        :param keywords: 联系人 / 群名列表。
        :param text: 要群发的文本。
        :param interval: 每个联系人之间的间隔秒数（防风控）。
        :param stop_on_error: 遇到失败时是否立即中止。
        :return: ``{联系人: 是否成功}`` 的结果字典。
        """
        results: Dict[str, bool] = {}
        for kw in keywords:
            try:
                self.send_text(kw, text)
                results[kw] = True
            except Exception as exc:  # noqa: BLE001
                logger.error("给「%s」发送失败：%s", kw, exc)
                results[kw] = False
                if stop_on_error:
                    break
            human_sleep(interval)
        ok = sum(1 for v in results.values() if v)
        logger.info("群发完成：成功 %d / 共 %d", ok, len(keywords))
        return results
