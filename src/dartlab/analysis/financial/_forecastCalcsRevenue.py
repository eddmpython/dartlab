"""forecastCalcs.py 의 매출/세그먼트 전망 — calcRevenueForecast · calcSegmentForecast."""

from __future__ import annotations

from typing import Any

from dartlab.analysis.financial._forecastCalcsInputs import _runForecastRevenue
from dartlab.core.memory import memoizedCalc


@memoizedCalc
def calcRevenueForecast(company: Any, *, basePeriod: str | None = None) -> dict | None:
    """7-소스 앙상블 3-시나리오 매출 전망.

    Returns
    -------
    dict
        isEstimate : bool — 추정치 여부
        method : str — 예측 방법론
        confidence : str — 신뢰도 ("high" | "medium" | "low")
        currency : str — 통화 코드
        historical : list[float] — 과거 매출 시계열 (원)
        projected : list[float] — 전망 매출 시계열 (원)
        growthRates : list[float] — 전망 성장률 (%)
        horizon : int — 전망 기간 (년)
        scenarios : dict — 시나리오별 projected/growthRates/probability
        lifecycle : str — 라이프사이클 단계
        forecastable : bool — 예측 가능 여부
        unforecastableReason : str — 예측 불가 사유 (forecastable=False 시)
        disclaimer : str — 면책 문구

    Capabilities:
        - 7 소스 앙상블 (CAGR/회귀/세그먼트/매크로/Damodaran 등) → 3 시나리오 매출 전망
        - lifecycle + confidence + scenarios 종합

    Guide:
        매출 전망 표준 진입. forecastable=False = 예측 불가 (라이프사이클 위반 등).

    When:
        Story forecast 박스 + AI 매출 전망 답변.

    How:
        ``_runForecastRevenue`` → projected/scenarios/lifecycle 출력 dict.

    Requires:
        IS 시계열 ≥ 5 년.

    Raises:
        없음 — projected None 시 None.

    Example:
        >>> calcRevenueForecast(company)["confidence"]
        'medium'

    See Also:
        - calcSegmentForecast : 세그먼트별
        - calcProFormaHighlights : pro forma

    AIContext:
        "이 종목 매출 전망" 답변 시 projected + scenarios + confidence 인용.
    """
    result = _runForecastRevenue(company)
    if not result or not result.projected:
        return None

    currency = getattr(company, "currency", "KRW") or "KRW"

    out: dict = {
        "isEstimate": True,
        "method": result.method,
        "confidence": result.confidence,
        "currency": currency,
        "historical": result.historical,
        "projected": result.projected,
        "growthRates": result.growthRates,
        "horizon": result.horizon,
    }

    if result.scenarios:
        out["scenarios"] = {}
        for label in ("base", "bull", "bear"):
            sc = result.scenarios.get(label, [])
            sg = result.scenarioGrowthRates.get(label, [])
            prob = result.scenarioProbabilities.get(label, 0)
            if sc:
                out["scenarios"][label] = {
                    "projected": sc,
                    "growthRates": sg,
                    "probability": prob,
                }

    lifecycle = result.aiContext.get("lifecycle", "")
    if lifecycle:
        out["lifecycle"] = lifecycle

    out["disclaimer"] = result.DISCLAIMER

    out["forecastable"] = result.forecastable
    if not result.forecastable:
        out["unforecastableReason"] = result.unforecastableReason

    return out


@memoizedCalc
def calcSegmentForecast(company: Any, *, basePeriod: str | None = None) -> dict | None:
    """세그먼트별 개별 매출 성장 전망.

    Capabilities:
        - 사업 부문 segment 별 독립 매출 예측 + 비중 + 라이프사이클
        - segments 합산 = 전체 매출 전망 (calcRevenueForecast)

    Returns:
        dict | None — None=세그먼트 데이터 없음. segments list 와 currency.

    Guide:
        segment 별 다른 성장률 가능 — 부문별 lifecycle 인용으로 인사이트 풍부.

    When:
        Story segment 박스 + AI "어느 사업부가 성장" 답변.

    How:
        ``_runForecastRevenue`` → segmentForecasts 추출.

    Requires:
        segment 데이터 (notes 또는 segment 매핑) 가용.

    Raises:
        없음 — 부재 시 None.

    Example:
        >>> calcSegmentForecast(company)["segments"][0]["name"]
        '반도체'

    See Also:
        - calcRevenueForecast : 전체 매출 전망
        - calcProFormaHighlights : pro forma

    AIContext:
        "어느 사업부가 성장 끄는가" 답변 시 segments 의 growthRates 인용.
    """
    result = _runForecastRevenue(company)
    if not result or not result.segmentForecasts:
        return None

    currency = getattr(company, "currency", "KRW") or "KRW"

    segments = []
    for seg in result.segmentForecasts:
        segments.append(
            {
                "name": seg.name,
                "projected": seg.projected,
                "growthRates": seg.growthRates,
                "method": seg.method,
                "shareOfRevenue": seg.shareOfRevenue,
                "lifecycle": seg.lifecycle,
            }
        )

    return {
        "isEstimate": True,
        "currency": currency,
        "segments": segments,
    }
