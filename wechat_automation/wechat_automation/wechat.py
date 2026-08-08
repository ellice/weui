"""顶层门面：``WeChat``。

把窗口、控件、键鼠、搜索、消息、文件、会话各子模块组合成一个易用入口，
覆盖需求中的五大模块能力。

典型用法::

    from wechat_automation import WeChat

    wx = WeChat()
    wx.connect()                        # 连接并唤起微信
    wx.open_chat("文件传输助手")          # 搜索并进入会话
    wx.send_text("你好\\n这是第二行")      # 发送多行文本
    wx.send_file(r"D:/报表.xlsx")         # 发送文件
    print(wx.list_sessions())           # 读取会话列表
    wx.broadcast(["张三", "工作群"], "通知：明天例会")  # 批量群发
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from .controls import ControlHelper
from .exceptions import NotConnectedError
from .files import FileSender
from .input_simulator import InputSimulator
from .messaging import MessageSender
from .navigation import Navigator
from .sessions import SessionManager
from .window import WeChatWindow


class WeChat:
    """微信桌面自动化统一入口。

    :param backend: pywinauto 后端，默认 ``"uia"``。
    :param human_like: 是否启用拟人慢速输入（防风控）。
    :param min_char_delay: 拟人输入单字符最小间隔（秒）。
    :param max_char_delay: 拟人输入单字符最大间隔（秒）。
    """

    def __init__(self, backend: str = "uia", human_like: bool = True,
                 min_char_delay: float = 0.02,
                 max_char_delay: float = 0.12) -> None:
        self._backend = backend
        self.window = WeChatWindow(backend=backend)
        self.sim = InputSimulator(
            human_like=human_like,
            min_char_delay=min_char_delay,
            max_char_delay=max_char_delay,
        )
        # 以下子模块在 connect() 后初始化（依赖主窗口句柄）。
        self.controls: Optional[ControlHelper] = None
        self.nav: Optional[Navigator] = None
        self.messages: Optional[MessageSender] = None
        self.file_sender: Optional[FileSender] = None
        self.sessions: Optional[SessionManager] = None

    # ------------------------------------------------------ 连接 / 窗口
    def connect(self, timeout: float = 10.0, activate: bool = True) -> "WeChat":
        """连接微信主窗口并初始化各子模块。"""
        main = self.window.connect(timeout=timeout)
        if activate:
            self.window.activate()
        self.controls = ControlHelper(main)
        self.nav = Navigator(main, self.controls, self.sim)
        self.messages = MessageSender(main, self.controls, self.sim, self.nav)
        self.file_sender = FileSender(main, self.controls, self.sim)
        self.sessions = SessionManager(main, self.controls, self.sim)
        return self

    def _require(self, attr: str) -> Any:
        value = getattr(self, attr)
        if value is None:
            raise NotConnectedError("请先调用 WeChat.connect()。")
        return value

    def activate(self) -> None:
        """唤起并激活微信窗口。"""
        self.window.activate()

    def minimize(self) -> None:
        """最小化窗口。"""
        self.window.minimize()

    def restore(self) -> None:
        """还原窗口。"""
        self.window.restore()

    def set_topmost(self, topmost: bool = True) -> None:
        """置顶 / 取消置顶。"""
        self.window.set_topmost(topmost)

    # ------------------------------------------------------ 模块一：导航 + 文本
    def open_chat(self, keyword: str, **kwargs: Any) -> None:
        """搜索并进入会话。"""
        self._require("nav").open_chat(keyword, **kwargs)

    def clear_search(self) -> None:
        """清空搜索框。"""
        self._require("nav").clear_search()

    def send_text(self, text: str, **kwargs: Any) -> None:
        """发送文本消息（支持换行/特殊符号/空格）。"""
        self._require("messages").send_text(text, **kwargs)

    def paste_and_send(self, text: str) -> None:
        """剪贴板粘贴发送大段文字 / 链接。"""
        self._require("messages").paste_and_send(text)

    def send_long_text(self, text: str, **kwargs: Any) -> None:
        """分段发送超长文本。"""
        self._require("messages").send_long_text(text, **kwargs)

    def broadcast(self, contacts: Iterable[str], text: str,
                  **kwargs: Any) -> Dict[str, str]:
        """循环批量群发文本。"""
        return self._require("messages").broadcast(contacts, text, **kwargs)

    def mention(self, member_name: str, then_text: str = "") -> None:
        """群内 @ 成员。"""
        self._require("messages").mention(member_name, then_text)

    # ------------------------------------------------------ 模块二：文件 / 图片
    def send_file(self, path: str, **kwargs: Any) -> None:
        """发送单个文件。"""
        self._require("file_sender").send_file(path, **kwargs)

    def send_files(self, paths: Iterable[str], **kwargs: Any) -> List[str]:
        """批量发送多个文件（一次粘贴）。"""
        return self._require("file_sender").send_files(paths, **kwargs)

    def send_image(self, path: str, **kwargs: Any) -> None:
        """发送图片。"""
        self._require("file_sender").send_image(path, **kwargs)

    # ------------------------------------------------------ 模块三：会话
    def list_sessions(self) -> List[str]:
        """读取左侧会话列表名称。"""
        return self._require("sessions").list_sessions()

    def switch_session(self, name: str) -> bool:
        """点击切换到指定会话。"""
        return self._require("sessions").switch_to(name)

    def get_history_texts(self) -> List[str]:
        """读取当前聊天窗口历史消息文本。"""
        return self._require("sessions").get_history_texts()

    def load_all_sessions(self, **kwargs: Any) -> List[str]:
        """下拉加载并返回全部会话名称。"""
        return self._require("sessions").load_all_sessions(**kwargs)

    def classify_sessions(self) -> Dict[str, List[str]]:
        """区分私聊 / 群聊。"""
        return self._require("sessions").classify_sessions()

    # ------------------------------------------------------ 模块四：控件调试
    def dump_control_tree(self, depth: Optional[int] = None) -> str:
        """导出控件树用于调试定位。"""
        return self._require("controls").dump_tree(depth=depth)

    def click_button(self, **criteria: Any) -> None:
        """点击任意可见按钮（更多/表情/语音/截图等）。"""
        self._require("controls").click_button(**criteria)

    def button_exists(self, **criteria: Any) -> bool:
        """判断按钮是否存在。"""
        return self._require("controls").exists(**criteria)

    def clear_input(self) -> None:
        """清空聊天输入框内容。"""
        self.sim.select_all()
        self.sim.backspace(1)
