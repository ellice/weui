"""数据模型。"""

from dataclasses import dataclass
from enum import Enum


class SessionType(Enum):
    """会话类型。"""

    PRIVATE = "private"  # 私聊
    GROUP = "group"      # 群聊
    OFFICIAL = "official"  # 公众号 / 服务号
    UNKNOWN = "unknown"


@dataclass
class SessionItem:
    """左侧会话列表中的一个会话条目。"""

    name: str
    session_type: SessionType = SessionType.UNKNOWN
    # 会话摘要（最后一条消息预览），部分版本可读
    preview: str = ""
    # 未读数量，读取不到时为 0
    unread: int = 0

    def __str__(self) -> str:  # pragma: no cover - 便于打印
        flag = {
            SessionType.PRIVATE: "私聊",
            SessionType.GROUP: "群聊",
            SessionType.OFFICIAL: "公众号",
            SessionType.UNKNOWN: "未知",
        }[self.session_type]
        unread = f" (未读{self.unread})" if self.unread else ""
        return f"[{flag}] {self.name}{unread}"
