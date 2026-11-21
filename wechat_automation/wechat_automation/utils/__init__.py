"""通用工具：剪贴板、拟人化节流等。"""

from .clipboard import (
    set_clipboard_text,
    get_clipboard_text,
    set_clipboard_files,
)
from .humanize import human_sleep, human_typing_delays

__all__ = [
    "set_clipboard_text",
    "get_clipboard_text",
    "set_clipboard_files",
    "human_sleep",
    "human_typing_delays",
]
