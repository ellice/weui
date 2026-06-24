"""会话列表管理 Mixin：读取列表、遍历切换、滚动加载、私聊/群聊区分。

依赖宿主类提供 ``self.window``、``self.config`` 与 ``self.scroll`` 等方法。
"""

from typing import Dict, List, Optional

from .exceptions import ControlNotFoundError, SessionNotFoundError
from .utils import human_sleep, logger


class SessionMixin:
    """左侧会话列表相关操作。"""

    window = None
    config = None

    def _get_session_list(self):
        """定位左侧会话列表控件。"""
        last_err = None
        for name in self.config.session_list_names:
            try:
                return self.find_control(title=name, control_type="List", timeout=3)
            except ControlNotFoundError as exc:
                last_err = exc
        raise SessionNotFoundError(f"未找到会话列表：{last_err}")

    def list_sessions(self) -> List[str]:
        """读取左侧当前已加载的全部会话名称。

        :returns: 会话名称列表（含未读计数会被微信拼接到名称里，按需自行清洗）。
        """
        session_list = self._get_session_list()
        names: List[str] = []
        try:
            for item in session_list.children(control_type="ListItem"):
                text = item.window_text()
                if text:
                    names.append(text)
        except Exception as exc:  # noqa: BLE001
            logger.warning("读取会话列表失败：%s", exc)
        return names

    def open_session(self, name: str) -> bool:
        """在会话列表中点击切换到指定会话（不经过搜索）。

        :raises SessionNotFoundError: 当前已加载列表中无此会话。
        """
        session_list = self._get_session_list()
        for item in session_list.children(control_type="ListItem"):
            if item.window_text() == name:
                item.click_input()
                human_sleep(self.config.short_pause)
                logger.info("已切换到会话：%s", name)
                return True
        raise SessionNotFoundError(f"会话列表中未找到：{name}（可先滚动加载）")

    def iter_sessions(self, max_count: Optional[int] = None):
        """生成器：遍历当前已加载会话，逐个点击进入并产出名称。

        :param max_count: 最多遍历个数，``None`` 表示全部。
        :yields: 当前进入的会话名称。
        """
        session_list = self._get_session_list()
        items = session_list.children(control_type="ListItem")
        count = 0
        for item in items:
            name = item.window_text()
            if not name:
                continue
            item.click_input()
            human_sleep(self.config.short_pause)
            yield name
            count += 1
            if max_count and count >= max_count:
                break

    def scroll_sessions(self, times: int = 3, direction: str = "down") -> List[str]:
        """下拉滚动会话列表以加载更多历史会话。

        :param times: 滚动次数。
        :param direction: ``"down"`` 向下加载更多，``"up"`` 回到顶部。
        :returns: 滚动后去重的会话名称列表。
        """
        session_list = self._get_session_list()
        collected: List[str] = []
        seen = set()
        for _ in range(times):
            for n in self.list_sessions():
                if n not in seen:
                    seen.add(n)
                    collected.append(n)
            self.scroll(control=session_list, direction=direction, amount=3)
            human_sleep(0.5)
        # 收尾再采集一次
        for n in self.list_sessions():
            if n not in seen:
                seen.add(n)
                collected.append(n)
        logger.info("滚动加载会话完成，共 %d 个", len(collected))
        return collected

    def is_group_chat(self, name: Optional[str] = None) -> bool:
        """判断当前会话（或切到指定会话后）是否为群聊。

        判定策略：群聊标题通常带成员数后缀，如「群名 (12)」；
        且群聊存在「聊天信息 / 群公告」等专属控件。此处采用标题正则启发式判断。
        """
        import re

        if name:
            try:
                self.open_session(name)
            except SessionNotFoundError:
                self.search_and_open(name)
        # 尝试读取聊天标题
        title_text = ""
        try:
            for ctrl in self.window.descendants(control_type="Text"):
                t = ctrl.window_text()
                if t and (name is None or name.split()[0] in t):
                    title_text = t
                    break
        except Exception:  # noqa: BLE001
            pass
        return bool(re.search(r"[（(]\s*\d+\s*[)）]", title_text or (name or "")))

    def classify_sessions(self) -> Dict[str, List[str]]:
        """将当前已加载会话粗分为私聊与群聊。

        :returns: ``{"group": [...], "private": [...]}``。
        基于名称中的成员数后缀启发式判断，不保证 100% 准确。
        """
        import re

        groups: List[str] = []
        privates: List[str] = []
        for name in self.list_sessions():
            if re.search(r"[（(]\s*\d+\s*[)）]", name):
                groups.append(name)
            else:
                privates.append(name)
        return {"group": groups, "private": privates}
