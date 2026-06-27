"""微信主窗口连接与窗口/控件通用操作。

WeChatAuto 是入口类，负责：
    - 连接 / 唤起微信主窗口
    - 置顶、最小化、还原
    - 搜索并切入好友 / 群聊
    - 提供输入框、会话列表、消息区域等关键控件的访问器
    - 控件树导出等调试能力
"""

from __future__ import annotations

import sys
import time
from typing import Optional

from . import controls as C
from . import input_utils as K
from .exceptions import (
    ContactNotFoundError,
    PlatformError,
    WeChatNotRunningError,
    WindowNotFoundError,
)

try:
    from pywinauto import Application, Desktop

    _HAS_PYWINAUTO = True
except Exception:  # pragma: no cover - 非 Windows 环境
    _HAS_PYWINAUTO = False


# 微信 PC 客户端窗口标识
WECHAT_PROCESS = "WeChat.exe"
WECHAT_WINDOW_CLASS = "WeChatMainWndForPC"
WECHAT_WINDOW_TITLE = "微信"


class WeChatAuto:
    """桌面版微信自动化主控对象。"""

    def __init__(self, auto_connect: bool = True, default_timeout: float = 10.0):
        if not _HAS_PYWINAUTO:
            raise PlatformError("pywinauto 不可用：微信自动化仅支持 Windows 平台")
        if not sys.platform.startswith("win"):
            raise PlatformError("微信自动化仅支持 Windows 平台")

        self.default_timeout = default_timeout
        self.app: Optional["Application"] = None
        self.window = None
        if auto_connect:
            self.connect()

    # ------------------------------------------------------------------ #
    # 连接 / 唤起
    # ------------------------------------------------------------------ #
    def connect(self, timeout: float = 10.0):
        """连接已运行的微信进程并取得主窗口。"""
        try:
            self.app = Application(backend="uia").connect(
                class_name=WECHAT_WINDOW_CLASS, timeout=timeout
            )
        except Exception:
            try:
                self.app = Application(backend="uia").connect(
                    title=WECHAT_WINDOW_TITLE, timeout=timeout
                )
            except Exception as exc:  # noqa: BLE001
                raise WeChatNotRunningError(
                    "未找到运行中的微信，请先登录微信 PC 客户端"
                ) from exc

        self.window = self.app.window(class_name=WECHAT_WINDOW_CLASS)
        if not C.exists(self.window):
            self.window = self.app.window(title=WECHAT_WINDOW_TITLE)
        return self.window

    def launch(self, wechat_path: str, wait: float = 8.0):
        """通过可执行文件路径启动微信（一般用于未运行时）。"""
        self.app = Application(backend="uia").start(wechat_path)
        time.sleep(wait)
        return self.connect()

    # ------------------------------------------------------------------ #
    # 窗口操作：唤起 / 置顶 / 最小化 / 还原
    # ------------------------------------------------------------------ #
    def bring_to_front(self):
        """唤起并置顶微信窗口。"""
        self._ensure_window()
        try:
            if self.window.is_minimized():
                self.window.restore()
        except Exception:  # noqa: BLE001
            pass
        self.window.set_focus()
        try:
            self.window.set_focus()
        except Exception:  # noqa: BLE001
            pass
        return self.window

    def minimize(self):
        self._ensure_window()
        self.window.minimize()

    def restore(self):
        self._ensure_window()
        self.window.restore()
        self.window.set_focus()

    def maximize(self):
        self._ensure_window()
        try:
            self.window.maximize()
        except Exception:  # noqa: BLE001
            pass

    # ------------------------------------------------------------------ #
    # 关键控件访问器
    # ------------------------------------------------------------------ #
    def search_box(self):
        """左上角搜索框（Edit，title='搜索'）。"""
        self._ensure_window()
        return self.window.child_window(title="搜索", control_type="Edit")

    def input_edit(self):
        """聊天消息输入框。

        微信输入框通常是会话标题之外、靠下的 Edit；不同版本 title 可能为空，
        这里优先按可编辑 Edit 定位，必要时调用 dump_tree 调试。
        """
        self._ensure_window()
        # 优先尝试带 title 的输入框（部分版本 title 为联系人名）
        edit = self.window.child_window(
            title="输入", control_type="Edit"
        )
        if C.exists(edit):
            return edit
        # 回退：取消息发送区域的 Edit
        return self.window.child_window(control_type="Edit", found_index=0)

    def send_button(self):
        """发送按钮（部分版本 title='发送(S)'）。"""
        self._ensure_window()
        for title in ("发送(S)", "发送", "sendBtn"):
            btn = self.window.child_window(title=title, control_type="Button")
            if C.exists(btn):
                return btn
        return None

    # ------------------------------------------------------------------ #
    # 搜索并切入会话
    # ------------------------------------------------------------------ #
    def search_and_open(self, keyword: str, wait: float = 1.0) -> bool:
        """根据备注/昵称/群名搜索并打开对应聊天窗口。

        返回 True 表示已切入聊天。失败抛 ContactNotFoundError。
        """
        self.bring_to_front()
        box = self.search_box()
        C.wait_visible(box, timeout=self.default_timeout)
        box.set_focus()

        # 清空搜索框后输入关键字（用剪贴板粘贴，兼容特殊字符/表情）
        self.clear_search()
        from . import clipboard

        clipboard.copy_text(keyword)
        K.paste()
        time.sleep(wait)

        # 回车选中第一个匹配项进入聊天
        K.press_enter()
        time.sleep(wait)

        # 校验是否进入聊天（输入框可用即视为成功）
        if C.exists(self.input_edit()):
            return True
        raise ContactNotFoundError(f"未找到联系人/群聊: {keyword}")

    def clear_search(self):
        """清空搜索框内容。"""
        box = self.search_box()
        try:
            box.set_focus()
        except Exception:  # noqa: BLE001
            pass
        C.clear_edit(box)

    def clear_input(self):
        """清空聊天输入框内容。"""
        C.clear_edit(self.input_edit())

    # ------------------------------------------------------------------ #
    # 调试
    # ------------------------------------------------------------------ #
    def dump_tree(self, max_depth: int = 8) -> str:
        """导出主窗口控件树字符串，便于调试定位控件。"""
        self._ensure_window()
        return C.dump_control_tree(self.window, max_depth=max_depth)

    def print_tree(self):
        """直接打印 pywinauto 原生控件标识。"""
        self._ensure_window()
        self.window.print_control_identifiers()

    # ------------------------------------------------------------------ #
    # 内部
    # ------------------------------------------------------------------ #
    def _ensure_window(self):
        if self.window is None:
            self.connect()
        if self.window is None or not C.exists(self.window):
            raise WindowNotFoundError("微信主窗口不可用，请确认微信已登录")
        return self.window
