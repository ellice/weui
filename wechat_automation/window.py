"""第四部分：窗口与控件通用操作。

- 自动唤起微信窗口、置顶、最小化 / 还原
- 等待控件加载、超时判断、异常捕获
- 打印 / 导出全部控件树，用于调试定位
- 点击任意可见按钮
- 获取控件文本、判断按钮是否存在
- 清空搜索框 / 输入框内容
"""

import io
import time
from typing import Callable, List, Optional

from .config import DEFAULT_CONFIG, WeChatConfig
from .exceptions import ControlNotFoundError, WeChatWindowNotFoundError

try:
    from pywinauto import Application  # type: ignore
    from pywinauto.findwindows import ElementNotFoundError  # type: ignore
    import win32gui  # type: ignore
    import win32con  # type: ignore

    _HAS_DEPS = True
except ImportError:  # pragma: no cover - 非 Windows 环境
    Application = None  # type: ignore
    ElementNotFoundError = Exception  # type: ignore
    win32gui = None  # type: ignore
    win32con = None  # type: ignore
    _HAS_DEPS = False


class WeChatWindow:
    """微信主窗口连接与通用控件操作。"""

    def __init__(self, config: Optional[WeChatConfig] = None):
        self.config = config or DEFAULT_CONFIG
        self.app = None
        self.window = None

    # ----------------------------------------------------------- 连接 / 唤起
    def connect(self, timeout: Optional[float] = None) -> "WeChatWindow":
        """连接到正在运行的微信主窗口，失败抛 :class:`WeChatWindowNotFoundError`。"""
        if not _HAS_DEPS:
            raise WeChatWindowNotFoundError(
                "缺少 pywinauto / pywin32 依赖，或当前非 Windows 环境。"
            )
        timeout = self.config.default_timeout if timeout is None else timeout
        deadline = time.time() + timeout
        last_err: Optional[Exception] = None
        while time.time() < deadline:
            try:
                self.app = Application(backend=self.config.backend).connect(
                    class_name=self.config.window_class_name
                )
                self.window = self.app.window(
                    class_name=self.config.window_class_name
                )
                self.window.wait("exists", timeout=timeout)
                return self
            except Exception as exc:  # noqa: BLE001
                last_err = exc
                time.sleep(self.config.poll_interval)
        raise WeChatWindowNotFoundError(
            f"未找到微信主窗口（请确认微信已启动并登录）: {last_err}"
        )

    def _ensure_window(self):
        if self.window is None:
            self.connect()
        return self.window

    # ----------------------------------------------------------- 窗口状态控制
    def activate(self) -> None:
        """唤起并激活微信窗口（还原 + 置前）。"""
        win = self._ensure_window()
        try:
            win.set_focus()
        except Exception:  # noqa: BLE001 - 某些状态下需先还原
            self.restore()
            win.set_focus()
        time.sleep(self.config.action_delay)

    def set_topmost(self, on: bool = True) -> None:
        """窗口置顶 / 取消置顶。"""
        win = self._ensure_window()
        handle = win.handle
        flag = win32con.HWND_TOPMOST if on else win32con.HWND_NOTOPMOST
        win32gui.SetWindowPos(
            handle,
            flag,
            0,
            0,
            0,
            0,
            win32con.SWP_NOMOVE | win32con.SWP_NOSIZE,
        )

    def minimize(self) -> None:
        self._ensure_window().minimize()

    def restore(self) -> None:
        self._ensure_window().restore()

    def maximize(self) -> None:
        self._ensure_window().maximize()

    # ----------------------------------------------------------- 控件查找 / 等待
    def wait_control(
        self,
        timeout: Optional[float] = None,
        state: str = "ready",
        **criteria,
    ):
        """按条件等待控件就绪并返回；超时抛 :class:`ControlNotFoundError`。

        criteria 透传给 pywinauto，如 ``title="发送(S)"``、``control_type="Button"``。
        """
        win = self._ensure_window()
        timeout = self.config.default_timeout if timeout is None else timeout
        try:
            ctrl = win.child_window(**criteria)
            ctrl.wait(state, timeout=timeout)
            return ctrl
        except Exception as exc:  # noqa: BLE001
            raise ControlNotFoundError(
                f"等待控件超时({timeout}s) criteria={criteria}: {exc}"
            ) from exc

    def find_control(self, **criteria):
        """立即查找控件（不等待），未找到返回 None。"""
        win = self._ensure_window()
        try:
            ctrl = win.child_window(**criteria)
            if ctrl.exists():
                return ctrl
        except Exception:  # noqa: BLE001
            return None
        return None

    def control_exists(self, **criteria) -> bool:
        """判断控件 / 按钮是否存在。"""
        return self.find_control(**criteria) is not None

    def get_control_text(self, **criteria) -> str:
        """获取控件文本（window_text）。"""
        ctrl = self.find_control(**criteria)
        if ctrl is None:
            raise ControlNotFoundError(f"控件不存在: {criteria}")
        try:
            return ctrl.window_text()
        except Exception as exc:  # noqa: BLE001
            raise ControlNotFoundError(f"读取控件文本失败: {exc}") from exc

    def click_button(self, title: str, timeout: Optional[float] = None) -> None:
        """点击任意可见按钮：更多、表情、语音、截图、发送等。"""
        ctrl = self.wait_control(
            title=title, control_type="Button", timeout=timeout
        )
        ctrl.click_input()
        time.sleep(self.config.poll_interval)

    def click_control(self, timeout: Optional[float] = None, **criteria) -> None:
        """点击任意可见控件。"""
        ctrl = self.wait_control(timeout=timeout, **criteria)
        ctrl.click_input()
        time.sleep(self.config.poll_interval)

    # ----------------------------------------------------------- 输入框 / 搜索框
    def _edit(self, title: str):
        ctrl = self.find_control(title=title, control_type="Edit")
        if ctrl is None:
            ctrl = self.find_control(control_type="Edit")
        if ctrl is None:
            raise ControlNotFoundError(f"未找到编辑框: {title}")
        return ctrl

    def clear_edit(self, title: str) -> None:
        """清空指定编辑框（搜索框 / 输入框）。"""
        edit = self._edit(title)
        edit.click_input()
        time.sleep(self.config.poll_interval)
        from pywinauto import keyboard  # type: ignore

        keyboard.send_keys("^a{BACKSPACE}")
        time.sleep(self.config.poll_interval)

    def clear_search(self) -> None:
        self.clear_edit(self.config.search_box_title)

    def clear_input(self) -> None:
        self.clear_edit(self.config.input_edit_title)

    # ----------------------------------------------------------- 调试：控件树
    def dump_control_tree(
        self, to_file: Optional[str] = None, depth: Optional[int] = None
    ) -> str:
        """导出全部控件树，用于调试定位控件标识。"""
        import contextlib

        win = self._ensure_window()
        # print_control_identifiers 默认打印到 stdout，这里重定向后返回字符串
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            win.print_control_identifiers(depth=depth)
        text = buf.getvalue()
        if to_file:
            with open(to_file, "w", encoding="utf-8") as fh:
                fh.write(text)
        return text

    def retry(
        self,
        func: Callable,
        retries: int = 3,
        delay: Optional[float] = None,
        exceptions=(Exception,),
    ):
        """带重试与异常捕获的通用执行器。"""
        delay = self.config.poll_interval if delay is None else delay
        last_err: Optional[Exception] = None
        for _ in range(max(1, retries)):
            try:
                return func()
            except exceptions as exc:  # noqa: BLE001
                last_err = exc
                time.sleep(delay)
        raise ControlNotFoundError(f"操作重试 {retries} 次仍失败: {last_err}")

    def list_buttons(self) -> List[str]:
        """列出当前窗口所有按钮标题，便于定位。"""
        win = self._ensure_window()
        names: List[str] = []
        try:
            for btn in win.descendants(control_type="Button"):
                txt = btn.window_text()
                if txt:
                    names.append(txt)
        except Exception:  # noqa: BLE001
            pass
        return names
