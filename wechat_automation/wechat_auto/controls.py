"""控件通用操作：等待、查找、判断存在、取文本、点击、导出控件树、清空输入。"""

from __future__ import annotations

import contextlib
import io
import time
from typing import List, Optional

from .config import WeChatConfig
from .exceptions import ControlNotFoundError


class ControlHelper:
    """围绕微信主窗口的通用控件操作封装。

    这里的方法尽量做到"版本无关"：优先按 title + control_type 查找，
    失败时回退到候选标题列表，并统一提供等待 / 超时 / 异常处理。
    """

    def __init__(self, window, config: Optional[WeChatConfig] = None) -> None:
        self.window = window
        self.config = config or WeChatConfig()

    # ------------------------------------------------------------------ #
    # 查找 / 等待
    # ------------------------------------------------------------------ #
    def find(self, **criteria):
        """按条件查找子控件，返回 WindowSpecification（不保证存在）。"""
        return self.window.child_window(**criteria)

    def wait_control(
        self,
        timeout: Optional[float] = None,
        ready_state: str = "exists enabled visible",
        **criteria,
    ):
        """等待控件就绪并返回。

        :param ready_state: pywinauto 的等待状态，如 "exists"、"visible"、
            "enabled ready" 等空格分隔组合。
        :raises ControlNotFoundError: 超时未就绪。
        """
        timeout = self.config.default_timeout if timeout is None else timeout
        ctrl = self.window.child_window(**criteria)
        try:
            ctrl.wait(ready_state, timeout=timeout, retry_interval=self.config.poll_interval)
            return ctrl
        except Exception as exc:  # noqa: BLE001
            raise ControlNotFoundError(
                f"等待控件超时（{criteria}，state={ready_state}）：{exc}"
            ) from exc

    def exists(self, **criteria) -> bool:
        """判断控件是否存在（不抛异常）。"""
        try:
            return bool(self.window.child_window(**criteria).exists())
        except Exception:  # noqa: BLE001
            return False

    def find_first(self, candidates: List[dict], timeout: Optional[float] = None):
        """依次尝试多组查找条件，返回第一个存在的控件。

        用于兼容不同微信版本控件标题差异。
        """
        timeout = self.config.default_timeout if timeout is None else timeout
        deadline = time.time() + timeout
        last_error: Optional[Exception] = None
        while time.time() < deadline:
            for criteria in candidates:
                try:
                    ctrl = self.window.child_window(**criteria)
                    if ctrl.exists():
                        return ctrl
                except Exception as exc:  # noqa: BLE001
                    last_error = exc
            time.sleep(self.config.poll_interval)
        raise ControlNotFoundError(
            f"依次尝试 {candidates} 均未找到控件：{last_error}"
        )

    # ------------------------------------------------------------------ #
    # 读取 / 判断
    # ------------------------------------------------------------------ #
    def get_text(self, **criteria) -> str:
        """获取控件文本（优先 window_text，其次 legacy value）。"""
        ctrl = self.wait_control(**criteria)
        try:
            text = ctrl.window_text()
            if text:
                return text
        except Exception:  # noqa: BLE001
            pass
        try:
            return ctrl.legacy_properties().get("Value", "") or ""
        except Exception:  # noqa: BLE001
            return ""

    def button_exists(self, title: str) -> bool:
        """判断某个按钮是否存在。"""
        return self.exists(title=title, control_type="Button")

    # ------------------------------------------------------------------ #
    # 点击
    # ------------------------------------------------------------------ #
    def click_button(self, title: str, timeout: Optional[float] = None):
        """点击指定标题的按钮（更多、表情、语音、截图等）。"""
        ctrl = self.wait_control(
            title=title, control_type="Button", timeout=timeout
        )
        self._invoke_or_click(ctrl)
        time.sleep(self.config.action_delay)
        return ctrl

    def click_control(self, timeout: Optional[float] = None, **criteria):
        """点击任意匹配的可见控件。"""
        ctrl = self.wait_control(timeout=timeout, **criteria)
        self._invoke_or_click(ctrl)
        time.sleep(self.config.action_delay)
        return ctrl

    @staticmethod
    def _invoke_or_click(ctrl) -> None:
        """优先用 UIA invoke 模式点击，回退到坐标点击。"""
        try:
            ctrl.invoke()
            return
        except Exception:  # noqa: BLE001
            pass
        try:
            ctrl.click_input()
        except Exception:  # noqa: BLE001
            ctrl.click()

    # ------------------------------------------------------------------ #
    # 输入框 / 搜索框清空
    # ------------------------------------------------------------------ #
    def clear_edit(self, **criteria) -> None:
        """清空指定 Edit 控件内容（全选 + 删除）。"""
        ctrl = self.wait_control(**criteria)
        ctrl.set_focus()
        try:
            ctrl.type_keys("^a{BACKSPACE}", set_foreground=True)
        except Exception:  # noqa: BLE001
            # 回退：直接 set 空文本
            try:
                ctrl.set_edit_text("")
            except Exception:  # noqa: BLE001
                pass
        time.sleep(self.config.action_delay)

    # ------------------------------------------------------------------ #
    # 调试：导出控件树
    # ------------------------------------------------------------------ #
    def dump_control_tree(
        self, depth: Optional[int] = None, filename: Optional[str] = None
    ) -> str:
        """导出主窗口全部控件标识，用于调试定位。

        :param depth: 遍历深度，None 表示全部。
        :param filename: 若指定，则同时把控件树写入该文件。
        :returns: 控件树字符串（``print_control_identifiers`` 的内容）。
        """
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            self.window.print_control_identifiers(depth=depth)
        tree = buffer.getvalue()
        if filename:
            with open(filename, "w", encoding="utf-8") as fh:
                fh.write(tree)
        return tree
