"""窗口与控件通用操作：按钮点击、控件文本读取、存在性判断等。

这些是对 :class:`~wechat_auto.core.WeChatCore` 的进一步业务封装，方便
点击"更多 / 表情 / 语音 / 截图"等聊天工具栏按钮。
"""

from __future__ import annotations

import logging
from typing import List, Optional

from .core import WeChatCore
from .exceptions import ControlNotFoundError

logger = logging.getLogger("wechat_auto")


class WindowController:
    """封装通用窗口 / 控件操作。"""

    def __init__(self, core: WeChatCore) -> None:
        self.core = core

    # ------------------------------------------------------------------
    # 窗口
    # ------------------------------------------------------------------
    def activate(self):
        """唤起并置于最前。"""

        return self.core.activate()

    def minimize(self):
        self.core.minimize()

    def restore(self):
        self.core.restore()

    def maximize(self):
        self.core.maximize()

    def set_topmost(self, topmost: bool = True):
        self.core.set_topmost(topmost)

    # ------------------------------------------------------------------
    # 按钮 / 控件
    # ------------------------------------------------------------------
    def click_button(self, name: str, timeout: Optional[float] = None) -> bool:
        """按名称点击可见按钮（如"更多""表情""语音""截图"）。

        成功返回 True；未找到返回 False。
        """

        try:
            btn = self.core.find_control(
                title=name, control_type="Button", timeout=timeout
            )
            btn.click_input()
            logger.info("已点击按钮：%s", name)
            return True
        except ControlNotFoundError:
            logger.warning("未找到按钮：%s", name)
            return False

    def button_exists(self, name: str, timeout: float = 0.0) -> bool:
        """判断按钮是否存在。"""

        return self.core.control_exists(
            title=name, control_type="Button", timeout=timeout
        )

    def get_control_text(self, **criteria) -> str:
        """按条件查找控件并读取其文本。"""

        ctrl = self.core.find_control(**criteria)
        return self.core.get_text(ctrl)

    def list_buttons(self) -> List[str]:
        """列出主窗口内所有按钮名称，便于调试可点击项。"""

        names: List[str] = []
        for btn in self.core.find_controls(control_type="Button"):
            txt = self.core.get_text(btn)
            if txt:
                names.append(txt)
        return names

    def dump_tree(self, depth: Optional[int] = None, to_file: Optional[str] = None) -> str:
        """导出控件树用于调试。"""

        return self.core.dump_control_tree(depth=depth, to_file=to_file)

    # ------------------------------------------------------------------
    # 常用聊天工具栏快捷方法
    # ------------------------------------------------------------------
    def open_emoji(self) -> bool:
        return self.click_button("表情")

    def open_more(self) -> bool:
        for name in ("更多", "更多功能"):
            if self.click_button(name):
                return True
        return False

    def open_screenshot(self) -> bool:
        return self.click_button("截图")
