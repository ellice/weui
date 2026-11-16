"""控件通用操作。

提供等待、查找、点击、读取文本、判断存在性、导出控件树等调试/操作能力，
其它业务模块（消息、会话、文件）都构建在它之上。
"""

from __future__ import annotations

import time
from typing import Any, List, Optional

from .exceptions import ControlNotFoundError, TimeoutError


class ControlHelper:
    """围绕 pywinauto 控件的工具方法集合。"""

    def __init__(self, root: Any) -> None:
        """
        :param root: 作为查找起点的根控件（通常是微信主窗口）。
        """
        self.root = root

    # ----- 等待 -----
    def wait_until(self, predicate, timeout: float = 10.0,
                   interval: float = 0.3, message: str = "") -> Any:
        """轮询直到 ``predicate()`` 返回真值或超时。

        返回 predicate 的真值结果，便于「等待并取得控件」一步到位。
        """
        deadline = time.time() + timeout
        last_exc: Optional[Exception] = None
        while time.time() < deadline:
            try:
                result = predicate()
                if result:
                    return result
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
            time.sleep(interval)
        raise TimeoutError(
            message or f"等待超时（{timeout}s）。最后异常: {last_exc}"
        )

    def wait_control(self, timeout: float = 10.0, **criteria) -> Any:
        """按条件等待某个控件出现并返回。"""
        def _find():
            ctrl = self.root.child_window(**criteria)
            return ctrl if ctrl.exists() else None

        return self.wait_until(
            _find, timeout=timeout,
            message=f"等待控件超时: {criteria}",
        )

    # ----- 查找 -----
    def find(self, **criteria) -> Any:
        """查找单个控件，不存在则抛异常。"""
        ctrl = self.root.child_window(**criteria)
        if not ctrl.exists():
            raise ControlNotFoundError(f"未找到控件: {criteria}")
        return ctrl

    def find_optional(self, **criteria) -> Optional[Any]:
        """查找单个控件，不存在返回 None。"""
        try:
            ctrl = self.root.child_window(**criteria)
            return ctrl if ctrl.exists() else None
        except Exception:  # noqa: BLE001
            return None

    def exists(self, **criteria) -> bool:
        """判断控件是否存在。"""
        return self.find_optional(**criteria) is not None

    # ----- 操作 -----
    def click(self, **criteria) -> Any:
        """查找并点击控件（使用 invoke / click_input 自适配）。"""
        ctrl = self.find(**criteria)
        self.click_control(ctrl)
        return ctrl

    @staticmethod
    def click_control(ctrl: Any) -> None:
        """点击给定控件，优先用 invoke，失败回退到 click_input。"""
        try:
            ctrl.click_input()
        except Exception:  # noqa: BLE001  # pragma: no cover
            ctrl.invoke()

    @staticmethod
    def get_text(ctrl: Any) -> str:
        """读取控件文本（兼容 window_text / texts）。"""
        try:
            text = ctrl.window_text()
            if text:
                return text
        except Exception:  # noqa: BLE001
            pass
        try:
            texts = ctrl.texts()
            return "\n".join(t for t in texts if t)
        except Exception:  # noqa: BLE001
            return ""

    # ----- 调试 -----
    def dump_tree(self, depth: Optional[int] = None) -> None:
        """打印控件树（pywinauto 的 print_control_identifiers）。"""
        if depth is None:
            self.root.print_control_identifiers()
        else:
            self.root.print_control_identifiers(depth=depth)

    def collect_texts(self, control_type: str = "Button") -> List[str]:
        """收集指定类型可见控件的文本，便于定位按钮等。"""
        results: List[str] = []
        try:
            for ctrl in self.root.descendants(control_type=control_type):
                txt = self.get_text(ctrl)
                if txt:
                    results.append(txt)
        except Exception:  # noqa: BLE001  # pragma: no cover
            pass
        return results
