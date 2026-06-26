"""通用辅助：延时、重试、日志。"""

from __future__ import annotations

import logging
import random
import time
from typing import Callable, Optional, Tuple, Type, TypeVar

T = TypeVar("T")

logger = logging.getLogger("wechat_auto")
if not logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(
        logging.Formatter("[%(asctime)s] %(levelname)s %(name)s: %(message)s")
    )
    logger.addHandler(_handler)
    logger.setLevel(logging.INFO)


def human_sleep(base: float = 0.3, jitter: float = 0.2) -> None:
    """模拟真人停顿：在 base 基础上叠加随机抖动，降低风控风险。"""
    delay = max(0.0, base + random.uniform(0, jitter))
    time.sleep(delay)


def wait_until(
    predicate: Callable[[], bool],
    timeout: float = 10.0,
    interval: float = 0.3,
) -> bool:
    """轮询等待，直到 predicate 返回 True 或超时。返回是否成功。"""
    end = time.time() + timeout
    while time.time() < end:
        try:
            if predicate():
                return True
        except Exception:  # noqa: BLE001
            pass
        time.sleep(interval)
    return False


def retry(
    func: Callable[[], T],
    attempts: int = 3,
    delay: float = 0.5,
    backoff: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
) -> T:
    """带指数退避的简单重试。"""
    last_err: Optional[Exception] = None
    cur = delay
    for i in range(attempts):
        try:
            return func()
        except exceptions as exc:  # noqa: BLE001
            last_err = exc
            logger.warning("第 %d/%d 次尝试失败: %s", i + 1, attempts, exc)
            if i < attempts - 1:
                time.sleep(cur)
                cur *= backoff
    assert last_err is not None
    raise last_err
