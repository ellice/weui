"""核心模块：负责连接微信主窗口、控件查找、等待与控件树导出。

设计说明
--------
微信 PC 版（3.x）主要控件基于 UI Automation（UIA）暴露，因此本库统一使用
``pywinauto`` 的 ``uia`` 后端。核心思路是先拿到主窗口 ``WindowSpecification``，
再基于该窗口按 ``title`` / ``control_type`` / ``auto_id`` 等条件递归查找子控件。

本模块只提供"地基"能力（连接、查找、等待、异常包装、控件树打印），
具体业务（发消息、发文件、会话管理等）由其他模块基于这里的能力实现。
"""

from __future__ import annotations

import logging
import time
from typing import Any, Callable, List, Optional

from .exceptions import (
    ControlNotFoundError,
    ControlTimeoutError,
    WeChatNotRunningError,
    WindowNotFoundError,
)

logger = logging.getLogger("wechat_auto")

# 微信主窗口在 UIA 下的类名与标题。不同版本可能存在差异，
# 这里给出常见默认值，允许在 WeChatCore 初始化时覆盖。
DEFAULT_WINDOW_TITLE = "微信"
DEFAULT_WINDOW_CLASS = "WeChatMainWndForPC"


def _lazy_import_pywinauto():
    """延迟导入 pywinauto。

    pywinauto 仅在 Windows 上可用，放在函数内导入可以让本模块在非 Windows
    环境（例如 CI / Linux）下也能被导入用于静态检查与文档生成。
    """

    try:
        from pywinauto import Application, Desktop  # type: ignore
        from pywinauto import timings  # type: ignore

        return Application, Desktop, timings
    except ImportError as exc:  # pragma: no cover - 依赖平台
        raise WeChatAutomationImportError(
            "未能导入 pywinauto，请在 Windows 环境下执行 `pip install pywinauto`。"
        ) from exc


class WeChatAutomationImportError(ImportError):
    """pywinauto 导入失败（通常是非 Windows 平台或未安装依赖）。"""


class WeChatCore:
    """微信自动化核心控制器。

    Parameters
    ----------
    window_title:
        主窗口标题，默认 ``微信``。
    window_class:
        主窗口类名，默认 ``WeChatMainWndForPC``。
    default_timeout:
        查找控件 / 等待窗口的默认超时时间（秒）。
    poll_interval:
        轮询等待时的间隔（秒）。
    """

    def __init__(
        self,
        window_title: str = DEFAULT_WINDOW_TITLE,
        window_class: str = DEFAULT_WINDOW_CLASS,
        default_timeout: float = 10.0,
        poll_interval: float = 0.3,
    ) -> None:
        self.window_title = window_title
        self.window_class = window_class
        self.default_timeout = default_timeout
        self.poll_interval = poll_interval

        self._Application, self._Desktop, self._timings = _lazy_import_pywinauto()
        self.app = None  # type: ignore[assignment]
        self._main_window = None  # type: ignore[assignment]

    # ------------------------------------------------------------------
    # 连接 / 主窗口
    # ------------------------------------------------------------------
    def connect(self, timeout: Optional[float] = None) -> "WeChatCore":
        """连接到已经启动的微信进程。

        若微信未运行则抛出 :class:`WeChatNotRunningError`。
        """

        timeout = self.default_timeout if timeout is None else timeout
        try:
            # 优先通过类名连接，兼容多语言标题。
            self.app = self._Application(backend="uia").connect(
                class_name=self.window_class, timeout=timeout
            )
        except Exception:
            try:
                self.app = self._Application(backend="uia").connect(
                    title=self.window_title, timeout=timeout
                )
            except Exception as exc:
                raise WeChatNotRunningError(
                    "未检测到运行中的微信，请先手动登录微信 PC 版。"
                ) from exc
        logger.info("已连接到微信进程。")
        self._main_window = None  # 重置缓存
        return self

    def launch(self, exe_path: str, wait_login_timeout: float = 60.0) -> "WeChatCore":
        """启动微信可执行文件并等待主窗口出现（需要用户扫码登录）。

        Parameters
        ----------
        exe_path:
            ``WeChat.exe`` 的完整路径。
        wait_login_timeout:
            等待主窗口出现（即登录完成）的最长时间。
        """

        self.app = self._Application(backend="uia").start(exe_path)
        logger.info("已启动微信：%s", exe_path)
        self.wait_main_window(timeout=wait_login_timeout)
        return self

    @property
    def main_window(self):
        """返回主窗口 ``WindowSpecification``（带缓存）。"""

        if self._main_window is None:
            self._main_window = self._resolve_main_window()
        return self._main_window

    def _resolve_main_window(self):
        if self.app is None:
            self.connect()
        try:
            win = self.app.window(class_name=self.window_class)
            if not win.exists(timeout=self.default_timeout):
                win = self.app.window(title=self.window_title)
            win.wait("exists", timeout=self.default_timeout)
            return win
        except Exception as exc:
            raise WindowNotFoundError("未能定位微信主窗口。") from exc

    def wait_main_window(self, timeout: Optional[float] = None):
        """阻塞等待主窗口出现并就绪。"""

        timeout = timeout if timeout is not None else self.default_timeout
        deadline = time.time() + timeout
        last_exc: Optional[Exception] = None
        while time.time() < deadline:
            try:
                win = self._resolve_main_window()
                win.wait("exists ready", timeout=self.poll_interval)
                self._main_window = win
                return win
            except Exception as exc:  # noqa: BLE001 - 需要循环重试
                last_exc = exc
                time.sleep(self.poll_interval)
        raise WindowNotFoundError(
            f"等待微信主窗口超时（{timeout}s）。"
        ) from last_exc

    # ------------------------------------------------------------------
    # 控件查找与等待
    # ------------------------------------------------------------------
    def find_control(
        self,
        parent=None,
        timeout: Optional[float] = None,
        **criteria: Any,
    ):
        """在 ``parent``（默认主窗口）下按条件查找单个控件。

        ``criteria`` 直接透传给 pywinauto，例如
        ``title="发送"``、``control_type="Button"``、``auto_id="..."``。

        若超时未找到，抛出 :class:`ControlNotFoundError`。
        """

        timeout = timeout if timeout is not None else self.default_timeout
        parent = parent if parent is not None else self.main_window
        ctrl = parent.child_window(**criteria)
        try:
            ctrl.wait("exists", timeout=timeout, retry_interval=self.poll_interval)
        except Exception as exc:
            raise ControlNotFoundError(
                f"未找到控件：{criteria}"
            ) from exc
        return ctrl

    def find_controls(self, parent=None, **criteria: Any) -> List[Any]:
        """返回满足条件的全部控件列表（可能为空）。"""

        parent = parent if parent is not None else self.main_window
        try:
            return parent.children(**criteria) if criteria else parent.children()
        except Exception:
            # 回退到 descendants 深度查找
            try:
                return parent.descendants(**criteria)
            except Exception:
                return []

    def control_exists(self, parent=None, timeout: float = 0.0, **criteria: Any) -> bool:
        """判断控件是否存在，不抛异常。"""

        parent = parent if parent is not None else self.main_window
        try:
            return parent.child_window(**criteria).exists(timeout=timeout)
        except Exception:
            return False

    def wait_control_ready(
        self,
        ctrl,
        timeout: Optional[float] = None,
        state: str = "exists enabled visible ready",
    ):
        """等待控件进入指定状态，超时抛 :class:`ControlTimeoutError`。"""

        timeout = timeout if timeout is not None else self.default_timeout
        try:
            ctrl.wait(state, timeout=timeout, retry_interval=self.poll_interval)
        except Exception as exc:
            raise ControlTimeoutError(
                f"等待控件就绪超时：{state}"
            ) from exc
        return ctrl

    def wait_until(
        self,
        predicate: Callable[[], bool],
        timeout: Optional[float] = None,
        message: str = "条件等待超时",
    ) -> bool:
        """轮询等待任意布尔条件满足。"""

        timeout = timeout if timeout is not None else self.default_timeout
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                if predicate():
                    return True
            except Exception:  # noqa: BLE001 - predicate 可能抛错，继续重试
                pass
            time.sleep(self.poll_interval)
        raise ControlTimeoutError(message)

    def get_text(self, ctrl) -> str:
        """安全地读取控件文本，失败返回空串。"""

        for getter in ("window_text", "get_value", "texts"):
            try:
                value = getattr(ctrl, getter)()
                if isinstance(value, (list, tuple)):
                    return "".join(str(x) for x in value)
                if value:
                    return str(value)
            except Exception:
                continue
        return ""

    # ------------------------------------------------------------------
    # 调试：控件树导出
    # ------------------------------------------------------------------
    def dump_control_tree(
        self,
        ctrl=None,
        depth: Optional[int] = None,
        to_file: Optional[str] = None,
    ) -> str:
        """打印 / 导出控件树，用于调试定位控件。

        Parameters
        ----------
        ctrl:
            起始控件，默认主窗口。
        depth:
            最大遍历深度，``None`` 表示不限制。
        to_file:
            若提供路径，则同时写入文件（UTF-8）。
        """

        import io
        from contextlib import redirect_stdout

        ctrl = ctrl if ctrl is not None else self.main_window
        buffer = io.StringIO()
        try:
            with redirect_stdout(buffer):
                # pywinauto 的 print_control_identifiers 直接打印到 stdout
                ctrl.print_control_identifiers(depth=depth)
        except Exception as exc:  # pragma: no cover - 依赖运行时
            buffer.write(f"[dump 失败] {exc}\n")
        text = buffer.getvalue()
        if to_file:
            with open(to_file, "w", encoding="utf-8") as fh:
                fh.write(text)
            logger.info("控件树已导出到：%s", to_file)
        return text

    # ------------------------------------------------------------------
    # 窗口操作
    # ------------------------------------------------------------------
    def activate(self):
        """唤起（置于最前）微信主窗口。"""

        win = self.main_window
        try:
            win.set_focus()
        except Exception:
            # 部分环境 set_focus 会失败，退化为 restore + click
            try:
                win.restore()
            except Exception:
                pass
        return win

    def minimize(self):
        """最小化主窗口。"""

        self.main_window.minimize()

    def restore(self):
        """还原主窗口。"""

        self.main_window.restore()

    def maximize(self):
        """最大化主窗口。"""

        self.main_window.maximize()

    def set_topmost(self, topmost: bool = True):
        """置顶 / 取消置顶主窗口（基于 Win32 API）。"""

        try:
            import win32con  # type: ignore
            import win32gui  # type: ignore

            hwnd = self.main_window.handle
            flag = win32con.HWND_TOPMOST if topmost else win32con.HWND_NOTOPMOST
            win32gui.SetWindowPos(
                hwnd,
                flag,
                0,
                0,
                0,
                0,
                win32con.SWP_NOMOVE | win32con.SWP_NOSIZE,
            )
        except ImportError:  # pragma: no cover
            logger.warning("未安装 pywin32，无法设置窗口置顶。")
