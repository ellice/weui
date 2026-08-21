"""控件通用工具。

对需求「四」中控件相关能力做进一步的独立封装，便于在调试脚本里
直接查找、遍历、判断控件，而不必关心业务模块。
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

from .exceptions import ControlNotFoundError
from .utils import wait_until

logger = logging.getLogger("wechat_auto")


class ControlHelper:
    """针对微信主窗口的通用控件操作。依赖 :class:`WeChatWindow`。"""

    def __init__(self, win):
        self.win = win

    def find(self, timeout: float = 8.0, **kwargs):
        """等待并返回控件，超时抛出 :class:`ControlNotFoundError`。"""
        def _find():
            ctrl = self.win.window.child_window(**kwargs)
            return ctrl if ctrl.exists() else None

        try:
            return wait_until(_find, timeout=timeout, message="等待控件超时")
        except Exception as exc:  # noqa: BLE001
            raise ControlNotFoundError(f"未找到控件：{kwargs}") from exc

    def exists(self, **kwargs) -> bool:
        return self.win.control_exists(**kwargs)

    def text(self, **kwargs) -> str:
        return self.win.get_control_text(**kwargs)

    def click(self, timeout: float = 8.0, double: bool = False, right: bool = False,
              **kwargs):
        ctrl = self.find(timeout=timeout, **kwargs)
        if right:
            ctrl.right_click_input()
        elif double:
            ctrl.double_click_input()
        else:
            ctrl.click_input()
        return ctrl

    def list_all(self, control_type: Optional[str] = None) -> List[Dict]:
        """列出主窗口下全部（或指定类型）控件的名称与类型，便于定位。"""
        kwargs = {"control_type": control_type} if control_type else {}
        result: List[Dict] = []
        try:
            for ctrl in self.win.window.descendants(**kwargs):
                try:
                    result.append(
                        {
                            "text": ctrl.window_text(),
                            "type": ctrl.element_info.control_type,
                            "rect": tuple(ctrl.rectangle()),
                        }
                    )
                except Exception:  # noqa: BLE001
                    continue
        except Exception as exc:  # noqa: BLE001
            logger.warning("列举控件失败：%s", exc)
        return result

    def dump_tree(self, depth: Optional[int] = None,
                  to_file: Optional[str] = None) -> str:
        """导出控件树（转发到 WeChatWindow）。"""
        return self.win.dump_control_tree(depth=depth, to_file=to_file)
