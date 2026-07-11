"""窗口与控件通用操作。

负责：

    - 连接 / 唤起微信主窗口
    - 窗口置顶、最小化、还原
    - 等待控件加载、超时判断、异常捕获
    - 打印 / 导出控件树，方便调试定位
    - 查找控件、获取控件文本、判断按钮是否存在、点击可见按钮

默认使用 UIA 后端（``backend="uia"``），对新版微信控件识别更完整。
"""

from __future__ import annotations

import time
from typing import List, Optional

from .exceptions import (
    ControlNotFoundError,
    ControlTimeoutError,
    WeChatNotFoundError,
)

try:
    from pywinauto import Application, Desktop  # type: ignore
    from pywinauto.findwindows import ElementNotFoundError  # type: ignore

    _HAS_PYWINAUTO = True
except Exception:  # pragma: no cover - 非 Windows 环境
    Application = None  # type: ignore
    Desktop = None  # type: ignore
    ElementNotFoundError = Exception  # type: ignore
    _HAS_PYWINAUTO = False


# 微信桌面端主窗口的类名 / 标题
WECHAT_PROCESS = "WeChat.exe"
WECHAT_WINDOW_CLASS = "WeChatMainWndForPC"
WECHAT_WINDOW_TITLE = "微信"


class WeChatWindow:
    """封装微信主窗口的连接与通用控件操作。"""

    def __init__(self, backend: str = "uia", timeout: float = 10.0):
        if not _HAS_PYWINAUTO:
            raise RuntimeError("窗口操作需要 pywinauto（仅 Windows 支持）")
        self.backend = backend
        self.timeout = timeout
        self.app: Optional["Application"] = None
        self.window = None
        self.connect()

    # ---- 连接 / 唤起 ----

    def connect(self) -> None:
        """连接到正在运行的微信主窗口。

        :raises WeChatNotFoundError: 未找到微信进程 / 窗口
        """
        try:
            self.app = Application(backend=self.backend).connect(
                class_name=WECHAT_WINDOW_CLASS, timeout=self.timeout
            )
            self.window = self.app.window(class_name=WECHAT_WINDOW_CLASS)
        except Exception as exc:
            raise WeChatNotFoundError(
                "未找到微信主窗口，请确认微信已登录并处于运行状态"
            ) from exc

    def activate(self) -> None:
        """唤起并激活微信窗口（置于前台）。"""
        self._ensure()
        try:
            if self.window.is_minimized():
                self.window.restore()
            self.window.set_focus()
        except Exception:
            # set_focus 偶尔失败，退回 restore + 再次尝试
            self.window.restore()
            time.sleep(0.2)
            self.window.set_focus()

    def minimize(self) -> None:
        """最小化窗口。"""
        self._ensure()
        self.window.minimize()

    def restore(self) -> None:
        """还原窗口。"""
        self._ensure()
        self.window.restore()

    def set_topmost(self, on: bool = True) -> None:
        """窗口置顶 / 取消置顶。"""
        self._ensure()
        try:
            self.window.set_focus()
            # 通过 Win32 API 设置置顶
            import win32con  # type: ignore
            import win32gui  # type: ignore

            hwnd = self.window.handle
            flag = win32con.HWND_TOPMOST if on else win32con.HWND_NOTOPMOST
            win32gui.SetWindowPos(
                hwnd,
                flag,
                0,
                0,
                0,
                0,
                win32con.SWP_NOMOVE | win32con.SWP_NOSIZE,
            )
        except Exception:
            # 非致命，忽略
            pass

    # ---- 控件等待 / 查找 ----

    def _ensure(self):
        if self.window is None:
            raise WeChatNotFoundError("尚未连接微信窗口")

    def wait_ready(self, timeout: Optional[float] = None) -> None:
        """等待主窗口就绪（存在且可见）。"""
        self._ensure()
        timeout = self.timeout if timeout is None else timeout
        try:
            self.window.wait("exists visible ready", timeout=timeout)
        except Exception as exc:
            raise ControlTimeoutError("等待微信窗口就绪超时") from exc

    def find(self, timeout: Optional[float] = None, **criteria):
        """查找并返回一个控件（包装器）。

        :param criteria: pywinauto 的查找条件，如 ``title=""``、
            ``control_type="Edit"``、``auto_id=""``
        :raises ControlNotFoundError: 未找到控件
        """
        self._ensure()
        timeout = self.timeout if timeout is None else timeout
        try:
            ctrl = self.window.child_window(**criteria)
            ctrl.wait("exists", timeout=timeout)
            return ctrl
        except Exception as exc:
            raise ControlNotFoundError(f"未找到控件: {criteria}") from exc

    def try_find(self, **criteria):
        """查找控件，找不到返回 ``None``（不抛异常）。"""
        self._ensure()
        try:
            ctrl = self.window.child_window(**criteria)
            if ctrl.exists(timeout=1.0):
                return ctrl
        except Exception:
            return None
        return None

    def exists(self, **criteria) -> bool:
        """判断控件 / 按钮是否存在。"""
        return self.try_find(**criteria) is not None

    def get_text(self, **criteria) -> str:
        """获取控件文本。"""
        ctrl = self.find(**criteria)
        try:
            return ctrl.window_text()
        except Exception:
            texts = ctrl.texts()
            return "".join(texts) if texts else ""

    def click_button(self, title: str = None, auto_id: str = None, **extra) -> None:
        """点击可见按钮（更多、表情、语音、截图等）。

        :param title: 按钮标题（如 "表情"、"发送文件"、"截图"）
        :param auto_id: 控件自动化 id
        """
        criteria = dict(extra)
        if title is not None:
            criteria["title"] = title
        if auto_id is not None:
            criteria["auto_id"] = auto_id
        criteria.setdefault("control_type", "Button")
        ctrl = self.find(**criteria)
        ctrl.click_input()

    # ---- 控件树导出（调试） ----

    def dump_tree(self, depth: int = 20, to_file: Optional[str] = None) -> str:
        """导出控件树文本，便于调试定位控件。

        :param depth: 遍历深度
        :param to_file: 若提供则同时写入文件
        :return: 控件树文本
        """
        self._ensure()
        import io
        from contextlib import redirect_stdout

        buf = io.StringIO()
        with redirect_stdout(buf):
            self.window.print_control_identifiers(depth=depth)
        text = buf.getvalue()
        if to_file:
            with open(to_file, "w", encoding="utf-8") as fh:
                fh.write(text)
        return text

    def list_buttons(self) -> List[str]:
        """列出当前窗口所有按钮的标题，便于查看可点击项。"""
        self._ensure()
        names: List[str] = []
        try:
            for btn in self.window.descendants(control_type="Button"):
                name = btn.window_text()
                if name:
                    names.append(name)
        except Exception:
            pass
        return names
