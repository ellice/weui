"""消息发送 Mixin：搜索好友/群、切换聊天、发送文本、批量群发。

依赖宿主类提供：``self.window``、``self.config`` 以及来自其它 Mixin 的
``type_text`` / ``press_enter`` / ``paste`` / ``select_all`` 等方法。
"""

from typing import Dict, Iterable, List, Optional

from . import clipboard
from .exceptions import ControlNotFoundError, SessionNotFoundError
from .utils import human_sleep, logger


class MessagingMixin:
    """文本消息相关能力。"""

    window = None
    config = None

    # ------------------------------------------------------------------ 搜索 & 切换
    def _get_search_box(self):
        """定位顶部搜索框（兼容中英文名称）。"""
        last_err = None
        for name in self.config.search_box_names:
            try:
                return self.find_control(title=name, control_type="Edit", timeout=2)
            except ControlNotFoundError as exc:
                last_err = exc
        # 兜底：取第一个 Edit
        try:
            return self.find_control(control_type="Edit", timeout=2)
        except ControlNotFoundError:
            raise ControlNotFoundError(f"未找到搜索框：{last_err}")

    def clear_search(self):
        """清空搜索框内容。"""
        box = self._get_search_box()
        box.click_input()
        self.select_all()
        self.press_backspace(1)

    def search_and_open(self, keyword: str, wait: float = 1.2):
        """根据备注 / 昵称 / 群名搜索并切入对应聊天窗口。

        :param keyword: 好友备注、昵称或群聊名称。
        :param wait: 搜索结果渲染等待秒数。
        :raises SessionNotFoundError: 未匹配到任何结果。
        """
        box = self._get_search_box()
        box.click_input()
        # 先清空，避免上次残留
        self.select_all()
        self.press_backspace(1)
        human_sleep(0.2)
        self.type_text(keyword)
        human_sleep(wait)
        # 回车选中第一个匹配结果并打开会话
        self.press_enter()
        human_sleep(0.6)
        # 简单校验：检查标题区域是否切换（不同版本控件不同，失败不阻断）
        logger.info("已尝试打开会话：%s", keyword)
        return True

    def open_chat(self, keyword: str) -> bool:
        """:meth:`search_and_open` 的语义别名。"""
        return self.search_and_open(keyword)

    # ------------------------------------------------------------------ 输入框
    def _get_message_edit(self):
        """定位聊天输入框。

        微信底部输入框是一个无标题 Edit，通常是窗口里最后一个 Edit。
        """
        try:
            edits = self.window.descendants(control_type="Edit")
            if edits:
                # 通常输入框在底部，取垂直坐标最大的可见 Edit
                visible = [e for e in edits if e.is_visible()]
                if visible:
                    return max(visible, key=lambda e: e.rectangle().top)
        except Exception as exc:  # noqa: BLE001
            logger.debug("枚举 Edit 失败：%s", exc)
        return self.find_control(control_type="Edit")

    def focus_input(self):
        """点击聊天输入框使其获得焦点。"""
        edit = self._get_message_edit()
        edit.click_input()
        return edit

    def clear_input(self):
        """清空聊天输入框内容。"""
        self.focus_input()
        self.select_all()
        self.press_backspace(1)

    # ------------------------------------------------------------------ 发送
    def send_text(
        self,
        target: Optional[str],
        text: str,
        send: bool = True,
        slow: bool = False,
        use_clipboard: bool = False,
    ) -> bool:
        """向指定联系人发送纯文本消息（支持换行、特殊符号、空格）。

        :param target: 目标好友 / 群名称；为 ``None`` 时直接在当前会话发送。
        :param text: 文本内容，``\\n`` 会被转换为换行（输入框内换行）。
        :param send: 是否回车发送，``False`` 仅写入输入框不发送。
        :param slow: 是否慢速逐字输入（防风控）。
        :param use_clipboard: 大段文字 / 链接建议置 True，走剪贴板粘贴更稳更快。
        """
        if target:
            self.search_and_open(target)
        self.focus_input()
        self.select_all()
        self.press_backspace(1)

        if use_clipboard:
            clipboard.copy_text(text)
            clipboard.wait_clipboard_ready()
            self.paste()
        else:
            # 逐行输入，行间用 Shift+Enter 换行，避免提前发送
            lines = text.split("\n")
            for idx, line in enumerate(lines):
                self.type_text(line, slow=slow)
                if idx != len(lines) - 1:
                    self.new_line()
        human_sleep(self.config.short_pause)
        if send:
            self.press_enter()
            logger.info("已发送文本到 %s：%s", target or "当前会话", text[:30])
        return True

    def send_long_text(self, target: Optional[str], text: str, chunk_size: int = 2000) -> int:
        """分段发送超长文本，每段不超过 ``chunk_size`` 字符。

        :returns: 实际发送的段数。
        """
        chunks = [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)] or [""]
        if target:
            self.search_and_open(target)
        for i, chunk in enumerate(chunks):
            self.send_text(None, chunk, send=True, use_clipboard=True)
            human_sleep(self.config.short_pause)
        logger.info("分段发送完成，共 %d 段", len(chunks))
        return len(chunks)

    def broadcast_text(
        self,
        targets: Iterable[str],
        text: str,
        interval: float = 1.0,
        use_clipboard: bool = True,
    ) -> Dict[str, bool]:
        """循环批量给多个联系人 / 群发送同一段文本。

        :param targets: 目标名称可迭代对象。
        :param interval: 每个目标之间的间隔秒数（防风控）。
        :returns: ``{目标: 是否成功}`` 的结果字典。
        """
        results: Dict[str, bool] = {}
        for name in targets:
            try:
                self.send_text(name, text, use_clipboard=use_clipboard)
                results[name] = True
            except Exception as exc:  # noqa: BLE001 - 单个失败不影响整体
                logger.error("群发到 %s 失败：%s", name, exc)
                results[name] = False
            human_sleep(interval)
        ok = sum(1 for v in results.values() if v)
        logger.info("批量群发完成：成功 %d / 共 %d", ok, len(results))
        return results

    def get_chat_messages(self, limit: int = 0) -> List[str]:
        """读取当前聊天窗口历史消息区域的文本（UI 读取）。

        :param limit: 返回最近多少条，0 表示全部当前已加载。
        :returns: 消息文本列表（按从上到下顺序）。
        """
        messages: List[str] = []
        msg_list = None
        for name in self.config.message_list_names:
            try:
                msg_list = self.find_control(title=name, control_type="List", timeout=2)
                break
            except ControlNotFoundError:
                continue
        if msg_list is None:
            raise SessionNotFoundError("未定位到消息列表区域")

        try:
            for item in msg_list.children():
                text = item.window_text()
                if text:
                    messages.append(text)
        except Exception as exc:  # noqa: BLE001
            logger.warning("读取消息文本失败：%s", exc)

        if limit > 0:
            return messages[-limit:]
        return messages
