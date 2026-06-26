"""微信连接与窗口、控件通用操作（需求类别四）。

负责：
- 自动连接 / 唤起微信主窗口
- 置顶、最小化、还原、激活
- 等待控件、超时与异常处理
- 打印导出控件树（调试定位）
- 查找控件、读取文本、判断按钮是否存在、点击按钮
"""

from __future__ import annotations

import time
from typing import List, Optional

from .exceptions import (
    ControlNotFoundError,
    ControlTimeoutError,
    WeChatNotRunningError,
    WindowNotFoundError,
)
from .utils import logger, wait_until

try:
    from pywinauto import Application  # type: ignore
    from pywinauto.findwindows import ElementNotFoundError  # type: ignore
    _HAS_PWA = True
except Exception:  # pragma: no cover
    Application = None  # type: ignore
    ElementNotFoundError = Exception  # type: ignore
    _HAS_PWA = False


# 微信主窗口的类名（PC 微信 3.x）。新版本若不同，可通过 window_title 兜底匹配。
WECHAT_MAIN_CLASS = "WeChatMainWndForPC"
WECHAT_WINDOW_TITLE = "微信"


class WeChatBase:
    """微信连接与控件操作基类。"""

    def __init__(
        self,
        exe_path: Optional[str] = None,
        window_title: str = WECHAT_WINDOW_TITLE,
        main_class: str = WECHAT_MAIN_CLASS,
        timeout: float = 15.0,
    ) -> None:
        if not _HAS_PWA:
            raise RuntimeError("未安装 pywinauto，无法连接微信：pip install pywinauto")
        self.exe_path = exe_path
        self.window_title = window_title
        self.main_class = main_class
        self.timeout = timeout
        self.app: Optional[Application] = None
        self.win = None  # type: ignore  # 主窗口 WindowSpecification

    # ---------------- 连接 / 唤起 ----------------
    def connect(self) -> "WeChatBase":
        """连接到已运行的微信。连不上则尝试用 exe_path 启动。"""
        try:
            self.app = Application(backend="uia").connect(
                class_name=self.main_class, timeout=self.timeout
            )
        except Exception:  # noqa: BLE001
            try:
                self.app = Application(backend="uia").connect(
                    title=self.window_title, timeout=5
                )
            except Exception as exc:  # noqa: BLE001
                if self.exe_path:
                    return self._launch()
                raise WeChatNotRunningError(
                    "未找到运行中的微信窗口，请先登录微信，或传入 exe_path 以自动启动。"
                ) from exc
        self._bind_main_window()
        return self

    def _launch(self) -> "WeChatBase":
        logger.info("尝试启动微信: %s", self.exe_path)
        self.app = Application(backend="uia").start(self.exe_path)
        ok = wait_until(self._try_bind_main_window, timeout=60, interval=1.0)
        if not ok:
            raise WeChatNotRunningError("微信启动后仍未检测到主窗口（可能需要扫码登录）。")
        return self

    def _try_bind_main_window(self) -> bool:
        try:
            self._bind_main_window()
            return True
        except Exception:  # noqa: BLE001
            return False

    def _bind_main_window(self) -> None:
        assert self.app is not None
        try:
            win = self.app.window(class_name=self.main_class)
            win.wait("exists", timeout=self.timeout)
        except Exception:
            win = self.app.window(title=self.window_title)
            win.wait("exists", timeout=self.timeout)
        self.win = win

    @property
    def window(self):
        if self.win is None:
            raise WindowNotFoundError("尚未连接微信主窗口，请先调用 connect()。")
        return self.win

    # ---------------- 窗口操作 ----------------
    def activate(self) -> None:
        """唤起并激活微信主窗口到前台。"""
        self.window.set_focus()

    def bring_to_top(self) -> None:
        """置顶窗口。"""
        try:
            self.window.set_focus()
            self.window.wrapper_object().set_focus()
        except Exception as exc:  # noqa: BLE001
            logger.warning("置顶失败: %s", exc)

    def minimize(self) -> None:
        try:
            self.window.minimize()
        except Exception as exc:  # noqa: BLE001
            logger.warning("最小化失败: %s", exc)

    def restore(self) -> None:
        try:
            self.window.restore()
            self.window.set_focus()
        except Exception as exc:  # noqa: BLE001
            logger.warning("还原失败: %s", exc)

    def maximize(self) -> None:
        try:
            self.window.maximize()
        except Exception as exc:  # noqa: BLE001
            logger.warning("最大化失败: %s", exc)

    def is_running(self) -> bool:
        try:
            return bool(self.win) and self.window.exists()
        except Exception:  # noqa: BLE001
            return False

    # ---------------- 控件查找 / 等待 ----------------
    def find(
        self,
        parent=None,
        timeout: Optional[float] = None,
        **criteria,
    ):
        """查找单个控件（child_window），带等待。

        criteria 例如 title="搜索", control_type="Edit", auto_id=..., class_name=...
        """
        parent = parent if parent is not None else self.window
        ctrl = parent.child_window(**criteria)
        tmo = self.timeout if timeout is None else timeout
        try:
            ctrl.wait("exists", timeout=tmo)
        except Exception as exc:  # noqa: BLE001
            raise ControlNotFoundError(f"未找到控件 {criteria}: {exc}") from exc
        return ctrl

    def find_optional(self, parent=None, timeout: float = 1.0, **criteria):
        """查找控件，找不到返回 None（不抛异常）。"""
        try:
            return self.find(parent=parent, timeout=timeout, **criteria)
        except ControlNotFoundError:
            return None

    def wait_ready(self, ctrl, timeout: Optional[float] = None) -> None:
        """等待控件存在、可见、可用。超时抛 ControlTimeoutError。"""
        tmo = self.timeout if timeout is None else timeout
        try:
            ctrl.wait("exists enabled visible ready", timeout=tmo)
        except Exception as exc:  # noqa: BLE001
            raise ControlTimeoutError(f"等待控件就绪超时: {exc}") from exc

    def exists(self, parent=None, **criteria) -> bool:
        """判断控件/按钮是否存在。"""
        return self.find_optional(parent=parent, timeout=1.0, **criteria) is not None

    def get_text(self, ctrl) -> str:
        """读取控件文本（兼容多种属性）。"""
        for getter in ("window_text", "get_value", "texts"):
            try:
                attr = getattr(ctrl, getter)
                val = attr()
                if isinstance(val, list):
                    return "".join(str(x) for x in val)
                if val:
                    return str(val)
            except Exception:  # noqa: BLE001
                continue
        return ""

    def click_button(self, title: str, parent=None, timeout: Optional[float] = None) -> bool:
        """按名称点击按钮（更多、表情、语音、截图等）。成功返回 True。"""
        try:
            btn = self.find(parent=parent, timeout=timeout, title=title, control_type="Button")
            btn.click_input()
            return True
        except ControlNotFoundError:
            logger.warning("未找到按钮: %s", title)
            return False

    def click_control(self, ctrl) -> None:
        """点击给定控件（用真实鼠标，兼容性更好）。"""
        ctrl.click_input()

    # ---------------- 调试 ----------------
    def dump_tree(self, parent=None, depth: int = 12, to_file: Optional[str] = None) -> None:
        """打印/导出控件树，用于调试定位控件。"""
        parent = parent if parent is not None else self.window
        if to_file:
            import io
            import contextlib

            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                parent.print_control_identifiers(depth=depth)
            with open(to_file, "w", encoding="utf-8") as f:
                f.write(buf.getvalue())
            logger.info("控件树已导出到: %s", to_file)
        else:
            parent.print_control_identifiers(depth=depth)

    def list_buttons(self, parent=None) -> List[str]:
        """列出当前窗口所有按钮名称，便于发现可点击项。"""
        parent = parent if parent is not None else self.window
        names: List[str] = []
        try:
            for btn in parent.descendants(control_type="Button"):
                t = btn.window_text()
                if t:
                    names.append(t)
        except Exception as exc:  # noqa: BLE001
            logger.warning("枚举按钮失败: %s", exc)
        return names
