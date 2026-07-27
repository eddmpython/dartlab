"""macroCycle 헬퍼 — 정규분포 CDF · 시계열 트리거 매핑.

macro/cycles/macroCycle.py 가 1055 줄이라 isolate 헬퍼 분리.
identity 보존을 위해 macroCycle.py 가 본 모듈에서 re-export 한다.

상수:
- _SIGNAL_SERIES_MAP — 신호→시계열 매핑 (14 종)

함수:
- _normCdf — 표준정규 CDF 근사 (Abramowitz & Stegun 26.2.17)
- _findFirstTriggerDates — 발현 신호의 최초 트리거 날짜 역추적
"""

from __future__ import annotations

import math

_SIGNAL_SERIES_MAP: dict[str, tuple[str, str, float]] = {
    "hy_spread_declining": ("hy_spread_3m_change", "lt", -30),
    "hy_spread_widening": ("hy_spread_3m_change", "gt", 50),
    "hy_spread_stable": ("hy_spread_3m_change", "abs_lt", 30),
    "gold_declining": ("gold_yoy", "lt", -3),
    "gold_surging": ("gold_yoy", "gt", 15),
    "long_rate_rising": ("long_rate_change", "gt", 0.2),
    "vix_stable": ("vix", "lt", 18),
    "vix_rising": ("vix", "gt", 22),
    "vix_spiking": ("vix", "gt", 30),
    "term_spread_normalizing": ("term_spread", "gt", 0.5),
    "term_spread_flattening": ("term_spread", "gt", 0),
    "term_spread_inverted": ("term_spread", "lt", 0),
    "bei_rising": ("bei_10y", "gt", 2.3),
    "bei_overheating": ("bei_10y", "gt", 2.8),
}


def _normCdf(z: float) -> float:
    """표준정규분포 CDF.

    예전에는 Abramowitz & Stegun 26.2.17 근사를 손으로 적어 두고 오차가 7.5e-8 이라고
    문서에 밝혔는데, 지수항의 1/sqrt(2*pi) 계수가 빠져 있어 실제 최대 오차가 0.037 이었다.
    문서가 주장한 것보다 50 만 배 크다. Φ(1) 이 0.8703 으로 나와 참값 0.8413 과 3 퍼센트
    포인트 가까이 어긋났고, 그 값이 백분위와 국면 판정에 그대로 들어갔다.

    표준 라이브러리의 `math.erf` 로 정확히 계산한다. 같은 저장소의 다른 구현
    (`quant/strategy/_metricsOverfitting`)이 이미 이 방식을 쓴다.
    """

    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def _findFirstTriggerDates(
    sequence: tuple[str, ...],
    signalChecks: dict[str, bool],
    history: dict[str, list[tuple[str, float]]],
) -> dict[str, str]:
    """발현된 신호의 최초 트리거 날짜를 시계열에서 역추적."""
    result: dict[str, str] = {}
    for signal_name in sequence:
        if not signalChecks.get(signal_name, False):
            continue
        mapping = _SIGNAL_SERIES_MAP.get(signal_name)
        if mapping is None:
            continue
        series_key, comparison, threshold = mapping
        ts_data = history.get(series_key)
        if not ts_data:
            continue
        for dateStr, value in ts_data:
            if comparison == "lt" and value < threshold:
                result[signal_name] = dateStr
                break
            elif comparison == "gt" and value > threshold:
                result[signal_name] = dateStr
                break
            elif comparison == "abs_lt" and abs(value) < threshold:
                result[signal_name] = dateStr
                break
    return result


__all__ = ["_SIGNAL_SERIES_MAP", "_findFirstTriggerDates", "_normCdf"]
