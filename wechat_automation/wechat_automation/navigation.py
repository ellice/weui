"""模块一（导航部分）：搜索好友/群聊并切入聊天窗口。

原理：点击顶部搜索框 → 清空 → 输入备注/昵称 → 等待联想 → 回车进入会话。
"""

from __future__ import annotations

import time
from typing import Any

from .controls import ControlHelper
from .exceptions import ContactNotFoundError
from .input_simulator import InputSimulator


class Navigator:
    """搜索并切入聊天窗口。

    :param main: 主窗口包装对象。
    :param controls: 控件助手。
    :param sim: 键鼠模拟器。
    """

    def __init__(self, main: Any, controls: ControlHelper,
                 sim: InputSimulator) -> None:
        self.main = main
        self.controls = controls
        self.sim = sim

    def _focus_search_box(self, timeout: float = 5.0) -> Any:
        """定位并聚焦顶部搜索框。

        微信不同版本搜索框的 ``title`` 可能是“搜索”，这里做多重兜底。
        """
        for criteria in (
            {"title": "搜索", "control_type": "Edit"},
            {"title": "搜索", "control_type": "Button"},
            {"control_type": "Edit", "found_index": 0},
        ):
            try:
                ctrl = self.controls.wait_control(timeout=timeout, **criteria)
                try:
                    ctrl.click_input()
                except Exception:  # noqa: BLE001
                    ctrl.invoke()
                return ctrl
            except Exception:  # noqa: BLE001
                continue
        # 兜底：Ctrl+F 唤起搜索
        self.sim.hotkey("ctrl", "f")
        return None

    def search(self, keyword: str, wait: float = 1.2) -> None:
        """在搜索框输入关键词（备注/昵称/群名），等待联想结果。"""
        self._focus_search_box()
        # 清空后输入
        self.sim.select_all()
        self.sim.backspace(1)
        self.sim.type_text(keyword)
        time.sleep(wait)

    def open_chat(self, keyword: str, wait: float = 1.2,
                  enter_after: bool = True) -> None:
        """搜索并进入指定会话。

        :param keyword: 好友备注/昵称或群聊名称。
        :param enter_after: 命中后是否直接回车进入第一个结果。
        :raises ContactNotFoundError: 无联想结果时抛出。
        """
        self.search(keyword, wait=wait)
        # 简单校验：若搜索结果列表为空，抛出未找到。
        if not self._has_search_result():
            # 清理搜索框，避免污染下一次
            self.sim.esc()
            raise ContactNotFoundError(f"搜索不到联系人/群聊：{keyword}")
        if enter_after:
            self.sim.enter()
            time.sleep(0.4)

    def _has_search_result(self) -> bool:
        """粗略判断是否存在搜索联想结果。"""
        try:
            # 微信搜索结果通常在一个列表里，这里检测是否有可点击项。
            items = self.main.descendants(control_type="ListItem")
            return len(items) > 0
        except Exception:  # noqa: BLE001 - 拿不到就交给回车后再判断
            return True

    def clear_search(self) -> None:
        """清空搜索框内容。"""
        self._focus_search_box()
        self.sim.select_all()
        self.sim.backspace(1)
        self.sim.esc()
