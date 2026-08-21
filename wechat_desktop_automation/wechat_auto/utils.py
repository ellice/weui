"""基础工具：剪贴板、重试、等待、慢速输入等。

这些函数尽量与具体 UI 解耦，方便单独测试与复用。
剪贴板相关能力优先使用 win32clipboard；在非 Windows 环境下会抛出
明确的异常，便于在开发机上按需 mock。
"""

from __future__ import annotations

import os
import sys
import time
import functools
import logging
from typing import Callable, Iterable, List, Optional, TypeVar

from .exceptions import OperationTimeout

logger = logging.getLogger("wechat_auto")

T = TypeVar("T")

IS_WINDOWS = sys.platform.startswith("win")


# --------------------------------------------------------------------------- #
# 等待 / 重试
# --------------------------------------------------------------------------- #
def wait_until(
    predicate: Callable[[], Optional[T]],
    timeout: float = 10.0,
    interval: float = 0.4,
    message: str = "等待条件超时",
) -> T:
    """轮询 ``predicate`` 直到其返回真值或超时。

    :param predicate: 返回真值代表条件成立，返回值会被原样返回。
    :param timeout: 最长等待秒数。
    :param interval: 轮询间隔秒数。
    :raises OperationTimeout: 超时仍未成立。
    """
    deadline = time.time() + timeout
    last_exc: Optional[Exception] = None
    while time.time() < deadline:
        try:
            result = predicate()
            if result:
                return result
        except Exception as exc:  # noqa: BLE001 - 轮询期间允许临时异常
            last_exc = exc
        time.sleep(interval)
    raise OperationTimeout(f"{message}（timeout={timeout}s）") from last_exc


def retry(
    times: int = 3,
    delay: float = 0.5,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
):
    """带指数退避的重试装饰器。"""

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            _delay = delay
            last_exc: Optional[Exception] = None
            for attempt in range(1, times + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:  # noqa: BLE001
                    last_exc = exc
                    logger.warning(
                        "调用 %s 第 %d/%d 次失败：%s", func.__name__, attempt, times, exc
                    )
                    if attempt < times:
                        time.sleep(_delay)
                        _delay *= backoff
            assert last_exc is not None
            raise last_exc

        return wrapper

    return decorator


# --------------------------------------------------------------------------- #
# 慢速 / 拟人输入
# --------------------------------------------------------------------------- #
def human_delay(base: float = 0.05, jitter: float = 0.05) -> None:
    """在关键操作之间加入拟人延时，降低风控风险。"""
    import random

    time.sleep(max(0.0, base + random.uniform(0, jitter)))


def type_slowly(send_char: Callable[[str], None], text: str,
                per_char: float = 0.05, jitter: float = 0.06) -> None:
    """逐字符调用 ``send_char`` 模拟真人慢速输入。"""
    import random

    for ch in text:
        send_char(ch)
        time.sleep(max(0.0, per_char + random.uniform(0, jitter)))


# --------------------------------------------------------------------------- #
# 剪贴板
# --------------------------------------------------------------------------- #
def _require_windows() -> None:
    if not IS_WINDOWS:
        raise RuntimeError("剪贴板 / 微信自动化操作仅支持在 Windows 平台运行。")


def set_clipboard_text(text: str, retries: int = 5, delay: float = 0.1) -> None:
    """将纯文本写入剪贴板。"""
    _require_windows()
    import win32clipboard  # 延迟导入，避免非 Windows 环境导入失败

    last_exc: Optional[Exception] = None
    for _ in range(retries):
        try:
            win32clipboard.OpenClipboard()
            try:
                win32clipboard.EmptyClipboard()
                win32clipboard.SetClipboardText(text, win32clipboard.CF_UNICODETEXT)
            finally:
                win32clipboard.CloseClipboard()
            return
        except Exception as exc:  # noqa: BLE001 - 剪贴板可能被其它进程占用
            last_exc = exc
            time.sleep(delay)
    raise RuntimeError(f"写入剪贴板文本失败：{last_exc}")


def get_clipboard_text() -> str:
    """读取剪贴板纯文本。"""
    _require_windows()
    import win32clipboard

    win32clipboard.OpenClipboard()
    try:
        if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_UNICODETEXT):
            return win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT)
        return ""
    finally:
        win32clipboard.CloseClipboard()


def set_clipboard_files(paths: Iterable[str], retries: int = 5, delay: float = 0.1) -> List[str]:
    """将一个或多个本地文件写入剪贴板（CF_HDROP）。

    随后在微信输入框按下 Ctrl+V 即可粘贴为「文件 / 图片」附件。

    :return: 实际写入的（已存在的）文件绝对路径列表。
    """
    _require_windows()
    import struct
    import win32clipboard

    abs_paths: List[str] = []
    for p in paths:
        ap = os.path.abspath(p)
        if not os.path.exists(ap):
            raise FileNotFoundError(f"文件不存在，无法写入剪贴板：{ap}")
        abs_paths.append(ap)
    if not abs_paths:
        raise ValueError("未提供任何文件路径。")

    # 构造 DROPFILES 结构。文件名以 \0 分隔，末尾额外一个 \0，使用宽字符。
    files_str = "".join(p + "\0" for p in abs_paths) + "\0"
    files_bytes = files_str.encode("utf-16-le")
    # DROPFILES: pFiles(4) x(4) y(4) fNC(4) fWide(4) = 20 字节头
    dropfiles_header = struct.pack("<IiiII", 20, 0, 0, 0, 1)
    data = dropfiles_header + files_bytes

    last_exc: Optional[Exception] = None
    for _ in range(retries):
        try:
            win32clipboard.OpenClipboard()
            try:
                win32clipboard.EmptyClipboard()
                win32clipboard.SetClipboardData(win32clipboard.CF_HDROP, data)
            finally:
                win32clipboard.CloseClipboard()
            return abs_paths
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            time.sleep(delay)
    raise RuntimeError(f"写入剪贴板文件失败：{last_exc}")


def set_clipboard_image(image_path: str, retries: int = 5, delay: float = 0.1) -> None:
    """将一张本地图片以位图形式写入剪贴板（用于「粘贴为图片」而非文件）。

    若希望作为文件附件发送，请改用 :func:`set_clipboard_files`。
    """
    _require_windows()
    import io
    from PIL import Image  # type: ignore
    import win32clipboard

    image = Image.open(image_path)
    output = io.BytesIO()
    image.convert("RGB").save(output, "BMP")
    # BMP 文件头 14 字节，剪贴板 CF_DIB 需要去掉这 14 字节
    data = output.getvalue()[14:]
    output.close()

    last_exc: Optional[Exception] = None
    for _ in range(retries):
        try:
            win32clipboard.OpenClipboard()
            try:
                win32clipboard.EmptyClipboard()
                win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
            finally:
                win32clipboard.CloseClipboard()
            return
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            time.sleep(delay)
    raise RuntimeError(f"写入剪贴板图片失败：{last_exc}")
