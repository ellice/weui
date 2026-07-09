"""会话列表管理（对应需求第三类）。

* 读取左侧全部会话列表名称
* 遍历会话、自动点击切换任意聊天窗口
* 获取当前聊天窗口历史消息区域文本（UI 读取文字）
* 下拉滚动会话列表加载更多历史会话
* 区分私聊、群聊会话
"""

from __future__ import annotations

import time
from typing import Dict, List, Optional

from .exceptions import ControlNotFoundError
from .inputs import InputSimulator
from .logger import get_logger
from .navigation import Navigator
from .window import WindowManager

log = get_logger("sessions")


class SessionManager:
    """左侧会话列表与聊天记录读取。"""

    def __init__(
        self,
        window: WindowManager,
        navigator: Navigator,
        inputs: InputSimulator,
    ) -> None:
        self.win = window
        self.nav = navigator
        self.inputs = inputs
        self.config = window.config

    # ------------------------------------------------------------------ #
    # 会话列表控件
    # ------------------------------------------------------------------ #
    def _get_session_list(self):
        """定位左侧会话列表控件（List 类型）。"""
        cfg = self.config
        ctrl = self.win.try_find_control(
            title=cfg.session_list_title, control_type="List"
        )
        if ctrl is None:
            # 回退：主窗口内第一个 List
            ctrl = self.win.try_find_control(control_type="List")
        if ctrl is None:
            raise ControlNotFoundError("未找到左侧会话列表控件。")
        return ctrl

    def list_sessions(self) -> List[str]:
        """读取当前左侧会话列表中所有可见会话的名称。

        注意：微信采用虚拟列表，只有滚动到可见区域的会话才会渲染出控件，
        因此本方法返回的是"当前可见"的会话；如需更多请配合 :meth:`scroll_sessions`。
        """
        lst = self._get_session_list()
        names: List[str] = []
        try:
            items = lst.children(control_type="ListItem")
        except Exception:  # noqa: BLE001
            items = lst.children()

        for item in items:
            name = item.window_text().strip()
            if name and name not in self.config.non_session_names:
                names.append(name)
        log.debug("读取到 %d 个可见会话。", len(names))
        return names

    def list_all_sessions(self, max_scroll: int = 20) -> List[str]:
        """滚动加载并去重读取尽可能多的会话名称。

        :param max_scroll: 最大滚动次数，防止无限循环。
        :return: 去重后的会话名称列表（按出现顺序）。
        """
        seen: Dict[str, None] = {}
        stable_rounds = 0
        for _ in range(max_scroll):
            before = len(seen)
            for name in self.list_sessions():
                if name not in seen:
                    seen[name] = None
            self.scroll_sessions(down=True)
            time.sleep(self.config.after_click_delay)
            # 连续两轮没有新增，认为到底了
            if len(seen) == before:
                stable_rounds += 1
                if stable_rounds >= 2:
                    break
            else:
                stable_rounds = 0
        log.info("累计读取到 %d 个会话。", len(seen))
        return list(seen.keys())

    def scroll_sessions(self, down: bool = True, amount: int = 3) -> None:
        """下拉 / 上拉滚动会话列表以加载更多历史会话。

        :param down: True 向下滚动（更多历史会话），False 向上。
        :param amount: 滚轮步进量。
        """
        lst = self._get_session_list()
        rect = lst.rectangle()
        center = (int(rect.mid_point().x), int(rect.mid_point().y))
        # wheel_dist 负数向下
        self.inputs.scroll(center, wheel_dist=-amount if down else amount)
        time.sleep(0.2)

    # ------------------------------------------------------------------ #
    # 切换会话
    # ------------------------------------------------------------------ #
    def switch_to(self, name: str) -> bool:
        """在会话列表中点击切换到指定会话。

        若当前可见列表中没有该会话，会尝试滚动查找；仍找不到时回退到搜索框搜索。

        :return: 是否成功切换。
        """
        # 先在可见项中找
        if self._click_session_if_visible(name):
            return True

        # 滚动查找
        for _ in range(20):
            self.scroll_sessions(down=True)
            time.sleep(self.config.after_click_delay)
            if self._click_session_if_visible(name):
                return True

        # 回退：直接搜索打开
        try:
            self.nav.search_and_open(name)
            return True
        except Exception as exc:  # noqa: BLE001
            log.error("切换到会话「%s」失败：%s", name, exc)
            return False

    def _click_session_if_visible(self, name: str) -> bool:
        lst = self._get_session_list()
        try:
            items = lst.children(control_type="ListItem")
        except Exception:  # noqa: BLE001
            items = lst.children()
        for item in items:
            if item.window_text().strip() == name:
                item.click_input()
                time.sleep(self.config.after_click_delay)
                log.debug("已切换到会话：%s", name)
                return True
        return False

    def iterate_sessions(self, max_scroll: int = 20):
        """生成器：依次切换到每个会话并 yield 会话名。

        用法::

            for name in session_mgr.iterate_sessions():
                text = session_mgr.get_chat_history_text()
                ...
        """
        for name in self.list_all_sessions(max_scroll=max_scroll):
            if self.switch_to(name):
                yield name

    # ------------------------------------------------------------------ #
    # 聊天记录读取
    # ------------------------------------------------------------------ #
    def get_chat_history_text(self) -> List[str]:
        """读取当前聊天窗口消息区域的文本（按消息项逐条返回）。

        同样受虚拟列表影响，只能读取当前渲染出的消息；
        需要更早的历史请配合 :meth:`scroll_chat_history` 向上滚动。
        """
        cfg = self.config
        msg_list = self.win.try_find_control(
            title=cfg.message_list_title, control_type="List"
        )
        if msg_list is None:
            # 回退：取聊天区域内的 List（通常是最后一个 List）
            lists = []
            try:
                lists = self.win.main_win.descendants(control_type="List")
            except Exception:  # noqa: BLE001
                pass
            msg_list = lists[-1] if lists else None
        if msg_list is None:
            raise ControlNotFoundError("未找到聊天记录列表控件。")

        texts: List[str] = []
        try:
            items = msg_list.children(control_type="ListItem")
        except Exception:  # noqa: BLE001
            items = msg_list.children()
        for item in items:
            txt = item.window_text().strip()
            if txt:
                texts.append(txt)
        return texts

    def scroll_chat_history(self, up: bool = True, amount: int = 3) -> None:
        """滚动聊天记录区域，向上加载更早的历史消息。"""
        cfg = self.config
        msg_list = self.win.try_find_control(
            title=cfg.message_list_title, control_type="List"
        )
        if msg_list is None:
            lists = self.win.main_win.descendants(control_type="List")
            msg_list = lists[-1] if lists else None
        if msg_list is None:
            raise ControlNotFoundError("未找到聊天记录列表控件。")
        rect = msg_list.rectangle()
        center = (int(rect.mid_point().x), int(rect.mid_point().y))
        self.inputs.scroll(center, wheel_dist=amount if up else -amount)
        time.sleep(0.3)

    # ------------------------------------------------------------------ #
    # 私聊 / 群聊区分
    # ------------------------------------------------------------------ #
    def is_group_chat(self, name: Optional[str] = None) -> bool:
        """判断当前会话（或按标题）是否为群聊。"""
        return self.nav.is_group_chat(name)

    def classify_current(self) -> str:
        """返回当前会话类型：``"group"`` 或 ``"private"``。"""
        return "group" if self.is_group_chat() else "private"
