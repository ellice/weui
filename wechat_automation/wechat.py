"""顶层门面类 :class:`WeChat`，聚合窗口、键鼠、消息与会话能力。

使用示例::

    from wechat_automation import WeChat

    wx = WeChat()
    wx.connect()                       # 连接已登录的微信 PC 版
    wx.search_and_open("文件传输助手")   # 搜索并切入会话
    wx.send_text("你好，世界！")         # 发送文本
    wx.send_file(r"D:\\report.pdf")     # 发送文件
    print(wx.get_session_names())       # 读取会话列表
"""

from typing import Iterable, List, Optional, Sequence, Tuple

from .config import DEFAULT_CONFIG, WeChatConfig
from .input_control import InputController
from .messaging import Messenger
from .session import SessionManager
from .window import WeChatWindow


class WeChat:
    """微信 PC 版自动化统一入口。"""

    def __init__(self, config: Optional[WeChatConfig] = None):
        self.config = config or DEFAULT_CONFIG
        self.window = WeChatWindow(self.config)
        self.inputs = InputController(self.config)
        self.messenger = Messenger(self.window, self.inputs, self.config)
        self.sessions = SessionManager(self.window, self.inputs, self.config)

    # --------------------------------------------------------------- 连接
    def connect(self, timeout: Optional[float] = None) -> "WeChat":
        self.window.connect(timeout=timeout)
        return self

    # --------------------------------------------- 窗口控制（四）代理方法
    def activate(self) -> None:
        self.window.activate()

    def set_topmost(self, on: bool = True) -> None:
        self.window.set_topmost(on)

    def minimize(self) -> None:
        self.window.minimize()

    def restore(self) -> None:
        self.window.restore()

    def dump_control_tree(self, to_file: Optional[str] = None) -> str:
        return self.window.dump_control_tree(to_file=to_file)

    def click_button(self, title: str) -> None:
        self.window.click_button(title)

    def button_exists(self, title: str) -> bool:
        return self.window.control_exists(title=title, control_type="Button")

    def clear_search(self) -> None:
        self.window.clear_search()

    def clear_input(self) -> None:
        self.window.clear_input()

    # --------------------------------------------- 消息发送（一、二）代理方法
    def search_and_open(self, keyword: str) -> None:
        self.messenger.search_and_open(keyword)

    def send_text(self, text: str, human_like: bool = True) -> None:
        self.messenger.send_text(text, human_like=human_like)

    def send_paste_text(self, text: str) -> None:
        self.messenger.send_paste_text(text)

    def send_segments(self, segments: Sequence[str]) -> None:
        self.messenger.send_segments(segments)

    def send_multiline(self, lines: Sequence[str]) -> None:
        self.messenger.send_multiline(lines)

    def batch_send(
        self, contacts: Iterable[str], text: str, human_like: bool = True
    ) -> List[Tuple[str, bool, str]]:
        return self.messenger.batch_send(contacts, text, human_like=human_like)

    def send_file(self, path: str) -> None:
        self.messenger.send_file(path)

    def send_image(self, path: str) -> None:
        self.messenger.send_image(path)

    def send_files(self, paths: Sequence[str], one_by_one: bool = False) -> None:
        self.messenger.send_files(paths, one_by_one=one_by_one)

    # --------------------------------------------- 会话管理（三）代理方法
    def get_session_names(self) -> List[str]:
        return self.sessions.get_session_names()

    def switch_session(self, name: str) -> None:
        self.sessions.switch_to(name)

    def iterate_sessions(self):
        return self.sessions.iterate_sessions()

    def load_all_sessions(self, max_scrolls: int = 30) -> List[str]:
        return self.sessions.load_all_sessions(max_scrolls=max_scrolls)

    def get_current_messages(self) -> List[str]:
        return self.sessions.get_current_messages()

    def classify_sessions(self):
        return self.sessions.classify_sessions()
