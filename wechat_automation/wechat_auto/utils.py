"""通用辅助函数：等待、超时判断、日志、防风控延时。"""

import logging
import random
import time
from typing import Callable, Optional, TypeVar

from .exceptions import OperationTimeoutError

logger = logging.getLogger("wechat_auto")

T = TypeVar("T")


def setup_logger(level: int = logging.INFO) -> logging.Logger:
    """初始化并返回包级日志器（仅在未配置 handler 时添加）。"""
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
        )
        logger.addHandler(handler)
    logger.setLevel(level)
    return logger


def wait_until(
    predicate: Callable[[], Optional[T]],
    timeout: float = 10.0,
    interval: float = 0.3,
    message: str = "等待条件超时",
) -> T:
    """轮询执行 ``predicate``，直到返回真值或超时。

    :param predicate: 无参可调用对象，返回真值表示条件满足。
    :param timeout: 最长等待秒数。
    :param interval: 轮询间隔秒数。
    :param message: 超时异常文案。
    :returns: ``predicate`` 第一次返回的真值结果。
    :raises OperationTimeoutError: 超时仍未满足条件。
    """
    deadline = time.time() + timeout
    last_exc: Optional[Exception] = None
    while time.time() < deadline:
        try:
            result = predicate()
            if result:
                return result
        except Exception as exc:  # noqa: BLE001 - 轮询期间忽略瞬时异常
            last_exc = exc
        time.sleep(interval)
    raise OperationTimeoutError(
        f"{message}（超时 {timeout}s）" + (f"，最近一次异常：{last_exc}" if last_exc else "")
    )


def human_sleep(base: float, jitter: float = 0.4) -> None:
    """带随机抖动的休眠，模拟真人操作节奏，降低被风控概率。

    :param base: 基础休眠秒数。
    :param jitter: 抖动比例（0~1），实际休眠在 ``base * (1 ± jitter)`` 之间。
    """
    if base <= 0:
        return
    low = base * (1 - jitter)
    high = base * (1 + jitter)
    time.sleep(random.uniform(max(0.0, low), high))
