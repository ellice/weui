"""模块一（消息部分）：文本消息发送。

- 纯文本，支持换行、特殊符号、空格；
- 回车一键发送、分段长文本；
- 循环批量群发；
- 剪贴板粘贴大段文字 / 链接发送。
"""

from __future__ import annotations

import time
from typing import Any, Dict, Iterable, List, Optional

from . import clipboard
from .controls import ControlHelper
from .input_simulator import InputSimulator


class MessageSender:
    """聊天输入框文本发送器。

    :param main: 主窗口包装对象。
    :param controls: 控件助手。
    :param sim: 键鼠模拟器。
    :param navigator: 会话导航器（批量群发时用于切会话）。
    """

    def __init__(self, main: Any, controls: ControlHelper,
                 sim: InputSimulator, navigator: Any = None) -> None:
        self.main = main
        self.controls = controls
        self.sim = sim
        self.navigator = navigator

    # ------------------------------------------------------ 输入框定位
    def _focus_input(self, timeout: float = 5.0) -> Optional[Any]:
        """聚焦聊天输入框。

        微信输入框通常是一个可编辑区域；不同版本 name 不稳定，做多重兜底，
        实在拿不到就靠“点击窗口下方 + 直接发键”兜底。
        """
        for criteria in (
            {"title": "输入", "control_type": "Edit"},
            {"control_type": "Edit", "found_index": -1},
        ):
            try:
                ctrl = self.controls.wait_control(timeout=timeout, **criteria)
                ctrl.set_focus()
                return ctrl
            except Exception:  # noqa: BLE001
                continue
        return None

    # ------------------------------------------------------ 发送文本
    def send_text(self, text: str, clear_first: bool = True,
                  use_clipboard: bool = False) -> None:
        """向当前会话发送一段文本（支持换行、特殊符号、空格）。

        :param clear_first: 发送前是否先清空输入框。
        :param use_clipboard: True 时用剪贴板粘贴（适合大段文字/链接，速度快、
            不受输入法影响）；False 时逐字模拟输入（可拟人防风控）。

        换行说明：文本内的 ``\\n`` 在逐字输入模式下会被转成
        ``Shift+Enter`` 语义之外的 ``{ENTER}``——但由于微信默认回车即发送，
        为保证“换行不误发”，多行文本一律走 :meth:`_type_multiline`。
        """
        self._focus_input()
        if clear_first:
            self.sim.select_all()
            self.sim.backspace(1)

        if use_clipboard:
            clipboard.copy_text(text)
            self.sim.paste()
        else:
            self._type_multiline(text)
        time.sleep(0.1)
        self.send()

    def _type_multiline(self, text: str) -> None:
        """逐行输入，行间用 ``Shift+Enter`` 换行（避免中途误触发送）。"""
        lines = text.split("\n")
        for idx, line in enumerate(lines):
            if line:
                self.sim.type_text(line)
            if idx < len(lines) - 1:
                # Shift+Enter：软换行，不发送。
                self.sim.send_keys("+{ENTER}")

    def send(self) -> None:
        """模拟回车一键发送。"""
        self.sim.enter()

    def paste_and_send(self, text: str) -> None:
        """把大段文字/链接放入剪贴板后粘贴并发送。"""
        self.send_text(text, use_clipboard=True)

    def send_long_text(self, text: str, chunk_size: int = 2000,
                       interval: float = 0.8) -> None:
        """分段发送超长文本，避免单条过长被截断。

        :param chunk_size: 单条最大字符数。
        :param interval: 段与段之间的间隔（秒），兼顾稳定与防风控。
        """
        for i in range(0, len(text), chunk_size):
            chunk = text[i:i + chunk_size]
            self.send_text(chunk, use_clipboard=True)
            time.sleep(interval)

    # ------------------------------------------------------ 批量群发
    def broadcast(self, contacts: Iterable[str], text: str,
                  interval: float = 1.5,
                  use_clipboard: bool = True) -> Dict[str, str]:
        """循环给多个联系人/群聊发送同一段文本。

        :param contacts: 备注/昵称/群名列表。
        :param interval: 每个联系人之间的间隔（秒），防风控。
        :return: ``{联系人: "ok" | 错误信息}`` 的结果字典。
        :raises RuntimeError: 未提供 navigator 时无法切换会话。
        """
        if self.navigator is None:
            raise RuntimeError("批量群发需要 navigator 以切换会话。")
        results: Dict[str, str] = {}
        for name in contacts:
            try:
                self.navigator.open_chat(name)
                self.send_text(text, use_clipboard=use_clipboard)
                results[name] = "ok"
            except Exception as exc:  # noqa: BLE001 - 单个失败不影响整体
                results[name] = f"error: {exc}"
            time.sleep(interval)
        return results

    # ------------------------------------------------------ @ 成员
    def mention(self, member_name: str, then_text: str = "") -> None:
        """在群里 @ 某位成员，可继续追加文本。

        输入 ``@`` 唤起成员面板，键入名字后回车选中，再输入正文。
        """
        self._focus_input()
        self.sim.at()
        self.sim.type_text(member_name)
        time.sleep(0.6)
        self.sim.enter()  # 选中候选成员
        if then_text:
            self.sim.type_text(then_text)
        self.send()
