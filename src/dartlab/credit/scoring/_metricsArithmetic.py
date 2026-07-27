"""credit/scoring/metrics 작은 헬퍼 — 안전 나눗셈·변동계수·분기 fallback·TTM 합산.

credit/scoring/metrics.py 가 999 줄 god module 이라 작은 헬퍼 분리.
identity 보존을 위해 metrics.py 가 본 모듈에서 re-export 한다.

함수:
- _div(a, b, pct) — 안전 나눗셈 (None/0 가드, 절대값 분모)
- _cv(values) — 변동계수 (CV % = std / |mean| × 100)
- _isQuarterlyFallback(cols) — _annualCols 결과 Q4 fallback 여부
- _ttmSum(flowData, qCol, allPeriods) — credit 차입금 TTM 합산
- _getRatios(company) — company._finance.ratios 안전 접근
"""

from __future__ import annotations


def _div(a, b, pct: bool = False) -> float | None:
    """안전한 나눗셈 (None / 0 가드)."""
    if a is None or b is None or b == 0:
        return None
    result = a / abs(b)
    if pct:
        result *= 100
    return round(result, 2)


def _cv(values: list) -> float | None:
    """변동계수 (Coefficient of Variation) = 표준편차 / |평균| × 100.

    이익 변동성, 마진 안정성 등 시계열의 상대적 흩어짐을 측정.
    유효 값 < 3 또는 평균 0 → None.
    """
    nums = [v for v in values if v is not None]
    if len(nums) < 3:
        return None
    mean = sum(nums) / len(nums)
    if mean == 0:
        return None
    variance = sum((x - mean) ** 2 for x in nums) / len(nums)
    return round((variance**0.5) / abs(mean) * 100, 2)


def _isQuarterlyFallback(cols: list[str]) -> bool:
    """``_annualCols`` 결과가 4자리 연도가 아닌 Q4 fallback 인지 판별."""
    return bool(cols) and "Q" in cols[0]


def _ttmSum(flowData: dict, qCol: str, allPeriods: list[str]) -> float | None:
    """credit 차입금 산출용 TTM 합산 — annualSumFlow credit 모드 alias."""
    from dartlab.core.utils.flow import annualSumFlow

    return annualSumFlow(flowData, qCol, allPeriods, withFallback=False)


def _getRatios(company):
    """company._finance.ratios 안전 접근."""
    try:
        return company._finance.ratios
    except (ValueError, KeyError, AttributeError):
        return None


__all__ = [
    "_cv",
    "_div",
    "_getRatios",
    "_isQuarterlyFallback",
    "_ttmSum",
]
