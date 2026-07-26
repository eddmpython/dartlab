"""외부 API 호출 재시도. dart, edgar, edinet 공통.

원래 `_common/__init__.py` 본문에 있었다. `__init__` 은 재export 파사드여야 하고 로직은
형제 모듈이 소유한다는 규칙에 맞춰 내렸다. 공개 경로 `dartlab.providers._common.httpRetry`
는 그대로다.
"""

from __future__ import annotations

import time
from typing import Callable, TypeVar

T = TypeVar("T")


def httpRetry(
    fn: Callable[[], T],
    *,
    maxRetries: int = 3,
    backoffSec: float = 1.0,
    backoffMultiplier: float = 2.0,
) -> T:
    """외부 API 호출 재시도. 지수 backoff.

    Capabilities:
        DART, EDGAR, EDINET, FRED 같은 외부 API 의 일시 실패(네트워크, rate limit, 5xx)를
        자동 재시도한다. dart/openapi 와 edgar/openapi 에 흩어져 있던 중복 로직을 모았다.

    AIContext:
        재시도는 transient 실패 전제다. 계약 위반이나 인증 실패처럼 다시 해도 같은
        결과인 오류에는 쓰지 않는다.

    Guide:
        마지막 시도까지 실패하면 그 예외를 그대로 올린다. 삼키지 않는다.

    When:
        원천이 외부 네트워크일 때. 로컬 파일 읽기에는 쓰지 않는다.

    How:
        `maxRetries` 회까지 다시 부르고 backoff 를 `backoffMultiplier` 배로 늘린다.

    Args:
        fn: 인자 없는 callable.
        maxRetries: 최대 재시도 횟수.
        backoffSec: 첫 backoff 초.
        backoffMultiplier: 매 재시도 배수.

    Returns:
        `fn()` 결과.

    Raises:
        마지막 시도의 예외.

    Example:
        >>> from dartlab.providers._common import httpRetry
        >>> result = httpRetry(lambda: fetchSomething())

    See Also:
        `dartlab.core.hfRetry.retryHfCall`.
    """

    lastException: Exception | None = None
    currentBackoff = backoffSec
    for attempt in range(maxRetries + 1):
        try:
            return fn()
        except Exception as e:  # noqa: BLE001
            lastException = e
            if attempt >= maxRetries:
                break
            time.sleep(currentBackoff)
            currentBackoff *= backoffMultiplier
    raise lastException if lastException else RuntimeError("httpRetry: 알 수 없는 실패")
