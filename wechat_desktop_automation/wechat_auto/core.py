"""窗口与控件通用操作。

对应需求「四、窗口与控件通用操作」：

* 自动唤起微信窗口、置顶、最小化 / 还原
* 等待控件加载、超时判断、异常捕获
* 打印导出全部控件树，用于调试定位
* 点击任意可见按钮
* 获取控件文本、判断按钮是否存在
* 清空搜索框、清空输入框内容

本模块封装 pywinauto 的连接与主窗口，作为其它模块的基础。
"""

from __future__ import annotations

import logging
import time
from typing import List, Optional

from .exceptions import WeChatNotFoundError, ControlNotFoundError
from .utils import wait_until, IS_WINDOWS

logger = logging.getLogger("wechat_auto")

# 微信 PC 客户端常见进程名与窗口类名
WECHAT_PROCESS = "WeChat.exe"
WECHAT_WINDOW_CLASS = "WeChatMainWndForPC"
WECHAT_WINDOW_TITLE = "微信"


class WeChatWindow:
    """封装微信主窗口的连接与通用窗口 / 控件操作。"""

    def __init__(self, backend: str = "uia", connect_timeout: float = 15.0):
        """连接到正在运行的微信窗口。

        :param backend: pywinauto 后端，微信必须使用 ``uia``。
        :param connect_timeout: 连接主窗口的最长等待秒数。
        """
        self.backend = backend
        self._app = None
        self._win = None
        self.connect(connect_timeout)

    # ------------------------------------------------------------------ #
    # 连接 / 唤起
    # ------------------------------------------------------------------ #
    def connect(self, timeout: float = 15.0) -> "WeChatWindow":
        """连接（或重连）微信主窗口。"""
        if not IS_WINDOWS:
            raise RuntimeError("微信自动化仅支持 Windows 平台运行。")
        from pywinauto import Application  # 延迟导入
        from pywinauto.findwindows import ElementNotFoundError

        def _try_connect():
            try:
                app = Application(backend=self.backend).connect(
                    class_name=WECHAT_WINDOW_CLASS, timeout=1
                )
            except (ElementNotFoundError, Exception):  # noqa: BLE001
                try:
                    app = Application(backend=self.backend).connect(
                        title=WECHAT_WINDOW_TITLE, timeout=1
                    )
                except Exception:  # noqa: BLE001
                    return None
            self._app = app
            self._win = app.window(class_name=WECHAT_WINDOW_CLASS)
            if not self._win.exists():
                self._win = app.window(title=WECHAT_WINDOW_TITLE)
            return self._win if self._win.exists() else None

        try:
            wait_until(_try_connect, timeout=timeout, message="连接微信主窗口失败")
        except Exception as exc:  # noqa: BLE001
            raise WeChatNotFoundError(
                "未找到运行中的微信窗口，请确认微信 PC 客户端已启动并登录。"
            ) from exc
        logger.info("已连接微信主窗口。")
        return self

    @property
    def window(self):
        """返回底层 pywinauto 主窗口包装对象。"""
        if self._win is None:
            raise WeChatNotFoundError("尚未连接微信窗口。")
        return self._win

    # ------------------------------------------------------------------ #
    # 窗口显示状态
    # ------------------------------------------------------------------ #
    def wake(self) -> "WeChatWindow":
        """唤起并激活微信窗口（从最小化/后台恢复到前台）。"""
        win = self.window
        try:
            if win.is_minimized():
                win.restore()
        except Exception:  # noqa: BLE001
            pass
        win.set_focus()
        time.sleep(0.2)
        return self

    def bring_to_top(self) -> "WeChatWindow":
        """将窗口置顶到前台。"""
        self.wake()
        try:
            self.window.set_focus()
        except Exception:  # noqa: BLE001
            pass
        return self

    def minimize(self) -> "WeChatWindow":
        """最小化窗口。"""
        self.window.minimize()
        return self

    def restore(self) -> "WeChatWindow":
        """还原窗口。"""
        self.window.restore()
        return self

    def maximize(self) -> "WeChatWindow":
        """最大化窗口。"""
        self.window.maximize()
        return self

    def is_minimized(self) -> bool:
        try:
            return bool(self.window.is_minimized())
        except Exception:  # noqa: BLE001
            return False

    # ------------------------------------------------------------------ #
    # 控件查找 / 等待
    # ------------------------------------------------------------------ #
    def child(self, **kwargs):
        """获取主窗口下的子控件包装对象（等价 window.child_window）。"""
        return self.window.child_window(**kwargs)

    def wait_control(self, timeout: float = 10.0, **kwargs):
        """等待某个控件出现并返回，超时抛出 :class:`ControlNotFoundError`。

        用法::

            wx.wait_control(title="发送(S)", control_type="Button")
        """
        def _find():
            ctrl = self.window.child_window(**kwargs)
            return ctrl if ctrl.exists() else None

        try:
            return wait_until(_find, timeout=timeout, message="等待控件超时")
        except Exception as exc:  # noqa: BLE001
            raise ControlNotFoundError(f"未找到控件：{kwargs}") from exc

    def control_exists(self, **kwargs) -> bool:
        """判断控件（按钮等）是否存在。"""
        try:
            return bool(self.window.child_window(**kwargs).exists())
        except Exception:  # noqa: BLE001
            return False

    def get_control_text(self, **kwargs) -> str:
        """获取指定控件的文本。"""
        ctrl = self.window.child_window(**kwargs)
        if not ctrl.exists():
            raise ControlNotFoundError(f"未找到控件：{kwargs}")
        try:
            return ctrl.window_text()
        except Exception:  # noqa: BLE001
            texts = ctrl.texts()
            return texts[0] if texts else ""

    # ------------------------------------------------------------------ #
    # 通用点击
    # ------------------------------------------------------------------ #
    def click_button(self, title: str, timeout: float = 8.0, double: bool = False):
        """按标题点击任意可见按钮（更多 / 表情 / 语音 / 截图等）。"""
        btn = self.wait_control(title=title, control_type="Button", timeout=timeout)
        if double:
            btn.double_click_input()
        else:
            btn.click_input()
        return btn

    def click_control(self, timeout: float = 8.0, double: bool = False, **kwargs):
        """按任意条件等待并点击控件。"""
        ctrl = self.wait_control(timeout=timeout, **kwargs)
        if double:
            ctrl.double_click_input()
        else:
            ctrl.click_input()
        return ctrl

    # ------------------------------------------------------------------ #
    # 控件树导出（调试）
    # ------------------------------------------------------------------ #
    def dump_control_tree(self, depth: Optional[int] = None,
                          to_file: Optional[str] = None) -> str:
        """导出全部控件树字符串，用于调试定位控件。

        :param depth: 递归深度，None 表示全部。
        :param to_file: 若提供则同时写入该文件。
        """
        import io
        from contextlib import redirect_stdout

        buf = io.StringIO()
        with redirect_stdout(buf):
            if depth is None:
                self.window.print_control_identifiers()
            else:
                self.window.print_control_identifiers(depth=depth)
        tree = buf.getvalue()
        if to_file:
            with open(to_file, "w", encoding="utf-8") as fh:
                fh.write(tree)
            logger.info("控件树已导出到 %s", to_file)
        return tree

    def list_buttons(self) -> List[str]:
        """列出主窗口当前可见的全部按钮标题，便于快速定位。"""
        names: List[str] = []
        try:
            for ctrl in self.window.descendants(control_type="Button"):
                text = ctrl.window_text()
                if text:
                    names.append(text)
        except Exception as exc:  # noqa: BLE001
            logger.warning("列举按钮失败：%s", exc)
        return names

    # ------------------------------------------------------------------ #
    # 输入框 / 搜索框清空
    # ------------------------------------------------------------------ #
    def _clear_edit(self, ctrl) -> None:
        """清空一个可编辑控件的内容（全选 + 删除）。"""
        try:
            ctrl.click_input()
        except Exception:  # noqa: BLE001
            pass
        from pywinauto.keyboard import send_keys

        send_keys("^a")
        time.sleep(0.05)
        send_keys("{BACKSPACE}")

    def clear_search_box(self) -> None:
        """清空左上角搜索框。"""
        search = self.window.child_window(title="搜索", control_type="Edit")
        if not search.exists():
            search = self.window.child_window(control_type="Edit", found_index=0)
        self._clear_edit(search)

    def clear_input_box(self) -> None:
        """清空当前聊天窗口的消息输入框。"""
        edit = self._get_message_edit()
        self._clear_edit(edit)

    def _get_message_edit(self):
        """定位当前聊天窗口底部的消息输入框。

        微信输入框通常是最后一个 Edit 控件；不同版本略有差异，
        这里做多重回退查找。
        """
        candidates = self.window.descendants(control_type="Edit")
        if not candidates:
            raise ControlNotFoundError("未找到消息输入框（Edit 控件）。")
        # 一般输入框在窗口下方，取纵坐标最大的可见 Edit
        visible = [c for c in candidates if _safe_visible(c)]
        pool = visible or candidates
        try:
            return max(pool, key=lambda c: c.rectangle().top)
        except Exception:  # noqa: BLE001
            return pool[-1]


def _safe_visible(ctrl) -> bool:
    try:
        return bool(ctrl.is_visible())
    except Exception:  # noqa: BLE001
        return True
