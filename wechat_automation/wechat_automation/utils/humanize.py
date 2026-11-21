"""拟人化节流工具：随机停顿与逐字输入延时，降低风控风险。"""

import random
import time
from typing import Iterator


def human_sleep(base: float, jitter: float = 0.3) -> None:
    """在 ``base`` 基础上叠加随机抖动后休眠。

    ``jitter`` 为相对比例，实际休眠落在 ``[base*(1-j), base*(1+j)]`` 区间。
    """
    if base <= 0:
        return
    low = base * (1 - jitter)
    high = base * (1 + jitter)
    time.sleep(random.uniform(max(0.0, low), high))


def human_typing_delays(length: int, low: float, high: float) -> Iterator[float]:
    """生成逐字输入的随机延时序列，长度为 ``length``。"""
    for _ in range(max(0, length)):
        yield random.uniform(low, high)
