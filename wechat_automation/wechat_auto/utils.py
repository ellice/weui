"""通用工具：日志、等待 / 超时、异常安全包装。"""

from __future__ import annotations

import logging
import time
from typing import Callable, Optional, TypeVar

from .exceptions import OperationTimeoutError

T = TypeVar("T")

logger = logging.getLogger("wechat_auto")


def setup_logger(level: int = logging.INFO) -> logging.Logger:
    """初始化并返回库使用的日志对象。

    重复调用不会重复添加 handler。
    """
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(level)
    return logger


def wait_until(
    condition: Callable[[], Optional[T]],
    timeout: float = 10.0,
    interval: float = 0.5,
    error_message: str = "等待条件成立超时",
) -> T:
    """轮询 ``condition``，直到它返回“真值”或超时。

    :param condition: 无参可调用对象，返回真值代表条件满足。
    :param timeout: 最大等待秒数。
    :param interval: 每次轮询之间的间隔秒数。
    :param error_message: 超时时抛出的异常信息。
    :raises OperationTimeoutError: 超时仍未满足条件。
    :return: ``condition`` 返回的真值。
    """
    deadline = time.time() + timeout
    last_exc: Optional[Exception] = None
    while time.time() < deadline:
        try:
            result = condition()
            if result:
                return result
        except Exception as exc:  # noqa: BLE001 - 轮询期间的异常先吞掉
            last_exc = exc
        time.sleep(interval)
    raise OperationTimeoutError(f"{error_message}（timeout={timeout}s）") from last_exc


def retry(
    func: Callable[[], T],
    attempts: int = 3,
    delay: float = 0.5,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
) -> T:
    """对可能瞬时失败的操作做指数退避重试。"""
    current_delay = delay
    last_exc: Optional[Exception] = None
    for i in range(1, attempts + 1):
        try:
            return func()
        except exceptions as exc:  # noqa: PERF203
            last_exc = exc
            logger.warning("第 %d/%d 次尝试失败：%s", i, attempts, exc)
            if i < attempts:
                time.sleep(current_delay)
                current_delay *= backoff
    assert last_exc is not None
    raise last_exc


def human_sleep(seconds: float) -> None:
    """轻量的 sleep 包装，方便统一控制“拟人”节奏。"""
    if seconds > 0:
        time.sleep(seconds)
