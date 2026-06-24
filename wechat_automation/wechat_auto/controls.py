"""通用控件操作 Mixin：查找、点击、取文本、判断存在、导出控件树。

依赖宿主类提供：

* ``self.window``：当前微信主窗口 ``WindowSpecification``。
* ``self.config``：:class:`~wechat_auto.config.WeChatConfig`。
"""

from typing import List, Optional

from .exceptions import ControlNotFoundError
from .utils import logger, wait_until


class ControlMixin:
    """围绕 pywinauto 控件的通用封装。"""

    window = None  # 由 core 注入
    config = None

    # ------------------------------------------------------------------ 查找
    def find_control(
        self,
        timeout: Optional[float] = None,
        retry_interval: float = 0.3,
        **criteria,
    ):
        """按条件查找单个控件并等待其出现。

        :param timeout: 等待超时，默认取配置值。
        :param criteria: 透传给 pywinauto 的 ``child_window`` 条件，例如
            ``title="发送"``、``control_type="Button"``、``auto_id=...``。
        :returns: 已就绪的 ``WindowSpecification``。
        :raises ControlNotFoundError: 超时仍未找到。
        """
        timeout = self.config.default_timeout if timeout is None else timeout

        def _try():
            ctrl = self.window.child_window(**criteria)
            if ctrl.exists() and ctrl.is_visible():
                return ctrl
            return None

        try:
            return wait_until(
                _try,
                timeout=timeout,
                interval=retry_interval,
                message=f"未找到控件 {criteria}",
            )
        except Exception as exc:  # noqa: BLE001
            raise ControlNotFoundError(str(exc)) from exc

    def control_exists(self, timeout: float = 0.0, **criteria) -> bool:
        """判断控件是否存在（可见）。

        :param timeout: 等待时间，0 表示立即判断。
        """
        try:
            self.find_control(timeout=timeout, **criteria)
            return True
        except ControlNotFoundError:
            return False

    # ------------------------------------------------------------------ 操作
    def click_control(self, double: bool = False, right: bool = False, **criteria):
        """点击匹配到的控件（更多 / 表情 / 语音 / 截图等按钮）。

        :param double: 是否双击。
        :param right: 是否右键单击。
        """
        ctrl = self.find_control(**criteria)
        if right:
            ctrl.right_click_input()
        elif double:
            ctrl.double_click_input()
        else:
            ctrl.click_input()
        logger.debug("已点击控件：%s", criteria)
        return ctrl

    def click_button(self, name: str, double: bool = False, right: bool = False):
        """按名称点击按钮的便捷封装。"""
        return self.click_control(
            title=name, control_type="Button", double=double, right=right
        )

    def get_control_text(self, **criteria) -> str:
        """获取控件文本（window_text）。"""
        ctrl = self.find_control(**criteria)
        return ctrl.window_text()

    def button_exists(self, name: str, timeout: float = 0.0) -> bool:
        """判断指定名称的按钮是否存在。"""
        return self.control_exists(
            title=name, control_type="Button", timeout=timeout
        )

    # ------------------------------------------------------------------ 调试
    def dump_control_tree(self, depth: int = 8, to_file: Optional[str] = None) -> str:
        """打印 / 导出当前窗口完整控件树，便于调试定位。

        :param depth: 递归深度。
        :param to_file: 若指定路径，则同时写入文件。
        :returns: 控件树文本。
        """
        import io
        from contextlib import redirect_stdout

        buf = io.StringIO()
        with redirect_stdout(buf):
            self.window.print_control_identifiers(depth=depth)
        tree = buf.getvalue()
        if to_file:
            with open(to_file, "w", encoding="utf-8") as fh:
                fh.write(tree)
            logger.info("控件树已导出到：%s", to_file)
        else:
            print(tree)
        return tree

    def list_buttons(self) -> List[str]:
        """列出当前窗口所有可见按钮的名称，辅助定位。"""
        names: List[str] = []
        try:
            for ctrl in self.window.descendants(control_type="Button"):
                text = ctrl.window_text()
                if text:
                    names.append(text)
        except Exception as exc:  # noqa: BLE001
            logger.warning("枚举按钮失败：%s", exc)
        return names
