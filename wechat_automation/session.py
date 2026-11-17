"""第三部分：会话列表管理。

- 读取左侧全部会话列表名称
- 遍历会话、自动点击切换任意聊天窗口
- 获取当前聊天窗口历史消息区域文本（UI 读取文字）
- 下拉滚动会话列表加载更多历史会话
- 区分私聊 / 群聊会话
"""

import time
from typing import Dict, List, Optional

from .config import WeChatConfig
from .exceptions import ContactNotFoundError
from .input_control import InputController
from .window import WeChatWindow


class SessionManager:
    """会话列表读取、切换与消息读取。"""

    def __init__(
        self,
        window: WeChatWindow,
        inputs: InputController,
        config: WeChatConfig,
    ):
        self.win = window
        self.inputs = inputs
        self.config = config

    # ----------------------------------------------------- 定位会话列表容器
    def _session_list(self):
        win = self.win._ensure_window()
        ctrl = self.win.find_control(
            title=self.config.session_list_title, control_type="List"
        )
        if ctrl is None:
            ctrl = self.win.find_control(control_type="List")
        return ctrl

    def get_session_names(self) -> List[str]:
        """读取左侧当前已加载的全部会话名称。"""
        lst = self._session_list()
        if lst is None:
            return []
        names: List[str] = []
        try:
            for item in lst.children(control_type="ListItem"):
                name = item.window_text()
                if name:
                    names.append(name)
        except Exception:  # noqa: BLE001
            pass
        return names

    # ----------------------------------------------------- 切换 / 遍历会话
    def switch_to(self, name: str, timeout: Optional[float] = None) -> None:
        """点击切换到指定名称的会话。"""
        lst = self._session_list()
        if lst is None:
            raise ContactNotFoundError("未找到会话列表控件。")
        timeout = self.config.default_timeout if timeout is None else timeout
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                for item in lst.children(control_type="ListItem"):
                    if item.window_text() == name:
                        item.click_input()
                        time.sleep(self.config.action_delay)
                        return
            except Exception:  # noqa: BLE001
                pass
            self.scroll_down()
        raise ContactNotFoundError(f"会话列表中未找到会话: {name}")

    def iterate_sessions(self):
        """生成器：依次切换并产出每个会话名称，便于逐个处理。"""
        for name in self.get_session_names():
            try:
                self.switch_to(name)
                yield name
            except Exception:  # noqa: BLE001
                continue

    # ----------------------------------------------------- 滚动加载更多会话
    def scroll_down(self, amount: int = 3) -> None:
        """下拉滚动会话列表，加载更多历史会话。"""
        lst = self._session_list()
        if lst is None:
            return
        try:
            rect = lst.rectangle()
            coords = (rect.mid_point().x, rect.mid_point().y)
            self.inputs.scroll(coords, wheel_dist=-amount)
        except Exception:  # noqa: BLE001
            pass
        time.sleep(self.config.poll_interval)

    def load_all_sessions(self, max_scrolls: int = 30) -> List[str]:
        """持续下拉直到不再加载新会话，返回去重后的全部会话名称。"""
        seen: List[str] = []
        stable = 0
        for _ in range(max_scrolls):
            names = self.get_session_names()
            new = [n for n in names if n not in seen]
            seen.extend(new)
            if not new:
                stable += 1
                if stable >= 2:
                    break
            else:
                stable = 0
            self.scroll_down()
        return seen

    # ----------------------------------------------------- 读取历史消息区域
    def get_current_messages(self) -> List[str]:
        """获取当前聊天窗口历史消息区域的全部文本（UI 读取）。"""
        win = self.win._ensure_window()
        msg_list = self.win.find_control(
            title=self.config.message_list_title, control_type="List"
        )
        messages: List[str] = []
        if msg_list is None:
            return messages
        try:
            for item in msg_list.children(control_type="ListItem"):
                txt = item.window_text()
                if txt:
                    messages.append(txt)
        except Exception:  # noqa: BLE001
            pass
        return messages

    def scroll_messages(self, up: bool = True, amount: int = 3) -> None:
        """滚动聊天记录区域翻页（向上看历史 / 向下看最新）。"""
        msg_list = self.win.find_control(
            title=self.config.message_list_title, control_type="List"
        )
        if msg_list is None:
            return
        try:
            rect = msg_list.rectangle()
            coords = (rect.mid_point().x, rect.mid_point().y)
            self.inputs.scroll(coords, wheel_dist=amount if up else -amount)
        except Exception:  # noqa: BLE001
            pass

    # ----------------------------------------------------- 私聊 / 群聊区分
    def is_group(self, name: str) -> bool:
        """根据名称关键字粗略判断是否群聊。

        更精确的判断可在切入会话后，检测标题栏是否带成员数量，如 "xxx (12)"。
        """
        return any(kw in name for kw in self.config.group_keywords)

    def classify_sessions(self) -> Dict[str, List[str]]:
        """把当前会话分为 private / group 两类。"""
        result: Dict[str, List[str]] = {"private": [], "group": []}
        for name in self.get_session_names():
            key = "group" if self.is_group(name) else "private"
            result[key].append(name)
        return result
