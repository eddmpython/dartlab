"""DataHub 실행 진단을 위한 구조화 로그와 in-process 카운터.

공개 gap 메시지는 비밀과 내부 원인을 노출하지 않도록 축약해서 유지한다. 이 모듈은
그 축약과 별개인 side channel 이다. 축약된 code 는 소비자에게 그대로 가고, 원인
traceback 과 상관 키는 로그로만 나간다.

로거 이름은 `dartlab.dataHub.<모듈>` 이며 기본 handler 를 붙이지 않는다. 호스트가
logging 을 설정하지 않으면 아무것도 출력되지 않으므로 라이브러리 사용에 영향이 없다.
"""

from __future__ import annotations

import logging
import threading
from collections import Counter
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from time import perf_counter
from typing import Any

_LOGGER_ROOT = "dartlab.dataHub"
_lock = threading.Lock()
_counters: Counter[str] = Counter()
_durations: dict[str, list[float]] = {}


def dataHubLogger(name: str) -> logging.Logger:
    """DataHub 하위 모듈용 logger 를 반환한다.

    Capabilities:
        `dartlab.dataHub` 아래 일관된 이름 공간의 logger 를 제공한다.

    Args:
        name: 호출 모듈의 `__name__`.

    Returns:
        `dartlab.dataHub.<모듈>` logger.

    Example:
        ``_log = dataHubLogger(__name__)``.

    Guide:
        handler 를 붙이지 않는다. 출력 여부는 호스트 애플리케이션이 결정한다.

    When:
        DataHub 모듈 최상단에서 한 번 호출한다.

    How:
        모듈 경로에서 `dartlab.dataHub.` 접두어를 정규화한다.

    See Also:
        ``recordFailure`` 와 ``recordDuration``.

    Requires:
        라이브러리는 root logger 설정을 바꾸지 않는다.

    AI Context:
        로그는 공개 gap 메시지를 대체하지 않는다. 둘은 독립 채널이다.
    """

    if name.startswith(_LOGGER_ROOT):
        return logging.getLogger(name)
    return logging.getLogger(f"{_LOGGER_ROOT}.{name.rsplit('.', 1)[-1]}")


def recordFailure(
    logger: logging.Logger,
    code: str,
    *,
    context: Mapping[str, Any] | None = None,
) -> None:
    """봉인 직전 실패의 원인 traceback 과 상관 키를 side channel 에 남긴다.

    Capabilities:
        축약된 공개 code 를 유지하면서 원인 추적 정보를 보존한다.

    Args:
        logger: 호출 모듈의 logger.
        code: 소비자에게 반환할 축약 gap code.
        context: requestId, assetId, market 같은 상관 키.

    Returns:
        없음.

    Example:
        ``recordFailure(_log, "CONTINUATION_OWNER_FAILED", context={"requestId": rid})``.

    Guide:
        `except` 블록 안에서만 호출한다. traceback 은 활성 예외에서 가져온다.

    When:
        원인을 버리고 축약 code 로 바꿔 반환하기 직전에 호출한다.

    How:
        `exc_info=True` 로 traceback 을 남기고 code 별 카운터를 올린다.

    See Also:
        ``failureCounts``.

    Requires:
        공개 반환 메시지는 이 호출과 무관하게 축약 상태를 유지해야 한다.

    AI Context:
        이 채널이 없으면 `except Exception` 이 원인을 완전히 삼켜 진단이 불가능하다.
    """

    with _lock:
        _counters[code] += 1
    logger.warning(
        "dataHub failure code=%s context=%s",
        code,
        dict(context or {}),
        exc_info=True,
    )


@contextmanager
def recordDuration(name: str) -> Iterator[None]:
    """구간 소요를 in-process 히스토그램 표본으로 누적한다.

    Capabilities:
        page 실행처럼 반복되는 구간의 지연 분포를 수집한다.

    Args:
        name: 구간 이름. 예 ``"ownerPage"``.

    Yields:
        없음.

    Example:
        ``with recordDuration("ownerPage"): ...``.

    Guide:
        표본은 프로세스 수명 동안만 유지한다. 영속 저장은 하지 않는다.

    When:
        page 계산, generation build 처럼 비용이 큰 구간에 감싼다.

    How:
        `perf_counter` 차이를 이름별 리스트에 누적한다.

    See Also:
        ``durationSummary``.

    Requires:
        예외가 나도 구간 소요는 기록한다.

    AI Context:
        운영 메트릭 백엔드가 없어도 즉시 p50 과 p95 를 볼 수 있게 한다.
    """

    startedAt = perf_counter()
    try:
        yield
    finally:
        elapsed = perf_counter() - startedAt
        with _lock:
            _durations.setdefault(name, []).append(elapsed)


def failureCounts() -> dict[str, int]:
    """지금까지 기록한 gap code 별 실패 수를 반환한다."""

    with _lock:
        return dict(_counters)


def durationSummary() -> dict[str, dict[str, float]]:
    """구간별 표본 수와 p50, p95, 최대값을 반환한다."""

    with _lock:
        snapshot = {name: sorted(values) for name, values in _durations.items()}
    summary: dict[str, dict[str, float]] = {}
    for name, values in snapshot.items():
        if not values:
            continue
        summary[name] = {
            "count": float(len(values)),
            "p50": values[int(len(values) * 0.5)] if len(values) > 1 else values[0],
            "p95": values[min(len(values) - 1, int(len(values) * 0.95))],
            "max": values[-1],
        }
    return summary


def resetTelemetry() -> None:
    """카운터와 구간 표본을 비운다. 테스트와 장기 실행 재기준용이다."""

    with _lock:
        _counters.clear()
        _durations.clear()


__all__ = [
    "dataHubLogger",
    "durationSummary",
    "failureCounts",
    "recordDuration",
    "recordFailure",
    "resetTelemetry",
]
