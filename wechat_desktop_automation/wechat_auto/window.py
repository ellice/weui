"""窗口与控件通用操作（对应需求第四类）。

:class:`WindowManager` 负责：

* 连接 / 唤起微信主窗口，置顶、最小化、还原
* 等待控件加载、超时判断、异常捕获
* 打印导出全部控件树，用于调试定位
* 点击任意可见按钮、获取控件文本、判断按钮是否存在
* 清空搜索框 / 输入框内容

它是所有业务模块的底座，向上层暴露 pywinauto 的 ``main_win`` 与一批
稳健的辅助方法（内置重试 / 超时 / 日志）。
"""

from __future__ import annotations

import io
import time
from contextlib import redirect_stdout
from typing import Callable, List, Optional, TypeVar

from .config import Config
from .exceptions import (
    ControlNotFoundError,
    TimeoutError,
    WeChatNotRunningError,
    WindowNotFoundError,
)
from .logger import get_logger

log = get_logger("window")

try:
    from pywinauto import Application  # type: ignore
    from pywinauto.findwindows import ElementNotFoundError  # type: ignore
    from pywinauto.timings import TimeoutError as PwaTimeoutError  # type: ignore

    _HAS_PYWINAUTO = True
except Exception:  # pragma: no cover
    _HAS_PYWINAUTO = False
    ElementNotFoundError = Exception  # type: ignore
    PwaTimeoutError = Exception  # type: ignore

T = TypeVar("T")


class WindowManager:
    """微信主窗口与控件的通用管理器。"""

    def __init__(self, config: Optional[Config] = None) -> None:
        if not _HAS_PYWINAUTO:
            raise RuntimeError("pywinauto 未安装或当前非 Windows 平台，无法使用。")
        self.config = config or Config()
        self.app: Optional["Application"] = None
        self.main_win = None  # type: ignore

    # ------------------------------------------------------------------ #
    # 连接 / 唤起
    # ------------------------------------------------------------------ #
    def connect(self, timeout: Optional[float] = None) -> "WindowManager":
        """连接已经在运行的微信主窗口。

        :raises WeChatNotRunningError: 未找到微信进程 / 主窗口。
        """
        cfg = self.config
        timeout = cfg.default_timeout if timeout is None else timeout
        try:
            self.app = Application(backend=cfg.backend).connect(
                class_name=cfg.main_window_class, timeout=timeout
            )
        except (ElementNotFoundError, PwaTimeoutError) as exc:
            # 退而求其次，按标题连接
            try:
                self.app = Application(backend=cfg.backend).connect(
                    title=cfg.main_window_title, timeout=timeout
                )
            except Exception:  # noqa: BLE001
                raise WeChatNotRunningError(
                    "未检测到正在运行的微信主窗口，请先登录微信 PC 版。"
                ) from exc

        self.main_win = self.app.window(class_name=cfg.main_window_class)
        if not self.main_win.exists():
            self.main_win = self.app.window(title=cfg.main_window_title)
        log.info("已连接微信主窗口。")
        return self

    def is_running(self) -> bool:
        """判断微信主窗口当前是否可用。"""
        try:
            return bool(self.main_win and self.main_win.exists())
        except Exception:  # noqa: BLE001
            return False

    # ------------------------------------------------------------------ #
    # 窗口状态
    # ------------------------------------------------------------------ #
    def activate(self) -> None:
        """唤起并激活（置于前台）微信主窗口。"""
        self._require_window()
        try:
            if self.main_win.is_minimized():
                self.main_win.restore()
        except Exception:  # noqa: BLE001
            pass
        self.main_win.set_focus()
        time.sleep(self.config.after_click_delay)
        log.debug("已激活微信主窗口。")

    def bring_to_top(self) -> None:
        """将窗口置顶到最前。"""
        self._require_window()
        try:
            self.main_win.set_focus()
            # UIA 下 set_focus 已足够；补一次 restore 保证可见
            if self.main_win.is_minimized():
                self.main_win.restore()
        except Exception as exc:  # noqa: BLE001
            log.warning("置顶窗口失败：%s", exc)

    def minimize(self) -> None:
        """最小化窗口。"""
        self._require_window()
        self.main_win.minimize()

    def restore(self) -> None:
        """从最小化 / 最大化还原窗口。"""
        self._require_window()
        self.main_win.restore()

    def maximize(self) -> None:
        """最大化窗口。"""
        self._require_window()
        self.main_win.maximize()

    # ------------------------------------------------------------------ #
    # 控件查找 / 等待
    # ------------------------------------------------------------------ #
    def find_control(self, parent=None, timeout: Optional[float] = None, **criteria):
        """在指定父控件（默认主窗口）下按条件查找控件，带超时等待。

        :param criteria: pywinauto 的定位条件，如 ``title=..``, ``control_type=..``,
            ``auto_id=..``, ``class_name=..`` 等。
        :raises ControlNotFoundError: 超时仍未找到。
        """
        self._require_window()
        parent = parent or self.main_win
        timeout = self.config.default_timeout if timeout is None else timeout
        try:
            ctrl = parent.child_window(**criteria)
            ctrl.wait("exists", timeout=timeout, retry_interval=self.config.poll_interval)
            return ctrl
        except (ElementNotFoundError, PwaTimeoutError) as exc:
            raise ControlNotFoundError(f"未找到控件：{criteria}") from exc

    def try_find_control(self, parent=None, timeout: float = 2.0, **criteria):
        """查找控件，找不到返回 None（不抛异常）。"""
        try:
            return self.find_control(parent=parent, timeout=timeout, **criteria)
        except ControlNotFoundError:
            return None

    def control_exists(self, parent=None, timeout: float = 2.0, **criteria) -> bool:
        """判断控件（按钮等）是否存在。"""
        return self.try_find_control(parent=parent, timeout=timeout, **criteria) is not None

    def wait_until(
        self,
        condition: Callable[[], bool],
        timeout: Optional[float] = None,
        interval: Optional[float] = None,
        desc: str = "条件成立",
    ) -> None:
        """轮询等待某个条件成立，超时抛出 :class:`TimeoutError`。"""
        timeout = self.config.default_timeout if timeout is None else timeout
        interval = self.config.poll_interval if interval is None else interval
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                if condition():
                    return
            except Exception:  # noqa: BLE001
                pass
            time.sleep(interval)
        raise TimeoutError(f"等待超时：{desc}（{timeout}s）")

    # ------------------------------------------------------------------ #
    # 控件操作
    # ------------------------------------------------------------------ #
    def click_button(self, title: str, parent=None, timeout: Optional[float] = None) -> None:
        """按标题点击任意可见按钮（更多 / 表情 / 语音 / 截图等）。"""
        ctrl = self.find_control(
            parent=parent, timeout=timeout, title=title, control_type="Button"
        )
        ctrl.click_input()
        time.sleep(self.config.after_click_delay)
        log.debug("已点击按钮：%s", title)

    def click_control(self, parent=None, timeout: Optional[float] = None, **criteria) -> None:
        """按任意条件点击控件。"""
        ctrl = self.find_control(parent=parent, timeout=timeout, **criteria)
        ctrl.click_input()
        time.sleep(self.config.after_click_delay)

    def get_text(self, parent=None, timeout: Optional[float] = None, **criteria) -> str:
        """获取控件文本（window_text）。"""
        ctrl = self.find_control(parent=parent, timeout=timeout, **criteria)
        return ctrl.window_text()

    def get_texts(self, parent=None, timeout: Optional[float] = None, **criteria) -> List[str]:
        """获取控件的多行文本（texts()）。"""
        ctrl = self.find_control(parent=parent, timeout=timeout, **criteria)
        return list(ctrl.texts())

    # ------------------------------------------------------------------ #
    # 搜索框 / 输入框
    # ------------------------------------------------------------------ #
    def get_search_box(self):
        """获取顶部搜索框控件。"""
        return self.find_control(title=self.config.search_box_title, control_type="Edit")

    def get_edit_box(self):
        """获取聊天输入框控件。

        不同微信版本输入框标题可能为空，这里做多重回退：
        先按配置标题找，找不到再退回主窗口内第一个可编辑的 Edit。
        """
        cfg = self.config
        ctrl = self.try_find_control(title=cfg.input_edit_title, control_type="Edit")
        if ctrl is not None:
            return ctrl
        # 回退：查找任意 Edit 控件
        edit = self.try_find_control(control_type="Edit")
        if edit is None:
            raise ControlNotFoundError("未找到聊天输入框（Edit 控件）。")
        return edit

    def clear_search_box(self) -> None:
        """清空搜索框内容。"""
        box = self.get_search_box()
        box.click_input()
        box.type_keys("^a{BACKSPACE}", set_foreground=True)
        time.sleep(self.config.after_click_delay)
        log.debug("已清空搜索框。")

    def clear_edit_box(self) -> None:
        """清空聊天输入框内容。"""
        box = self.get_edit_box()
        box.click_input()
        box.type_keys("^a{BACKSPACE}", set_foreground=True)
        time.sleep(self.config.after_click_delay)
        log.debug("已清空输入框。")

    # ------------------------------------------------------------------ #
    # 调试
    # ------------------------------------------------------------------ #
    def dump_control_tree(self, depth: Optional[int] = None, to_file: Optional[str] = None) -> str:
        """打印 / 导出主窗口的全部控件树，用于调试定位。

        :param depth: 递归深度，None 表示全部。
        :param to_file: 若提供，则把结果写入该文件。
        :return: 控件树文本。
        """
        self._require_window()
        buf = io.StringIO()
        with redirect_stdout(buf):
            if depth is None:
                self.main_win.print_control_identifiers()
            else:
                self.main_win.print_control_identifiers(depth=depth)
        text = buf.getvalue()
        if to_file:
            with open(to_file, "w", encoding="utf-8") as f:
                f.write(text)
            log.info("控件树已导出到：%s", to_file)
        return text

    # ------------------------------------------------------------------ #
    # 内部工具
    # ------------------------------------------------------------------ #
    def _require_window(self) -> None:
        if self.main_win is None:
            raise WindowNotFoundError("尚未连接微信主窗口，请先调用 connect()。")
