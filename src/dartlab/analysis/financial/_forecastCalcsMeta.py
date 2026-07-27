"""forecastCalcs.py 의 메타/플래그/캘리브레이션 — methodology · historicalRatios · forecastFlags · calibrationReport."""

from __future__ import annotations

import logging
from typing import Any

from dartlab.analysis.financial._forecastCalcsInputs import (
    _getSeriesAndMeta,
    _runForecastRevenue,
)
from dartlab.core.memory import memoizedCalc

log = logging.getLogger(__name__)


@memoizedCalc
def calcForecastMethodology(company: Any, *, basePeriod: str | None = None) -> dict | None:
    """예측 방법론 투명성 공개.

    Returns
    -------
    dict
        method : str — 예측 방법론
        confidence : str — 신뢰도 ("high" | "medium" | "low")
        sources : list[str] — 사용된 데이터 소스
        sourceWeights : dict — 소스별 가중치
        assumptions : list[str] — 가정 목록
        warnings : list[str] — 경고 메시지
        lifecycle : str — 라이프사이클 단계

    Capabilities:
        - 예측에 사용된 method/sources/weights/assumptions 투명 공개
        - 시나리오 신뢰도 + lifecycle 명시

    Guide:
        story methodology 박스 표준 입력. 사용자에게 예측 근거를 보여주는 투명성 도구.

    When:
        AI "어떻게 예측" 답변 + 방법론 검증.

    How:
        ``_runForecastRevenue`` 결과의 method/sources/assumptions 추출.

    Requires:
        매출 전망 실행 (calcRevenueForecast) 완료.

    Raises:
        없음.

    Example:
        >>> calcForecastMethodology(company)["method"]
        'ensemble_7'

    See Also:
        - calcRevenueForecast : 본 예측
        - calcForecastFlags : 위험 플래그

    AIContext:
        "예측 방법론" 답변 시 method + sources 인용.
    """
    result = _runForecastRevenue(company)
    if not result:
        return None

    return {
        "method": result.method,
        "confidence": result.confidence,
        "sources": result.sources,
        "sourceWeights": result.sourceWeights,
        "assumptions": result.assumptions,
        "warnings": result.warnings,
        "lifecycle": result.aiContext.get("lifecycle", ""),
    }


@memoizedCalc
def calcHistoricalRatios(company: Any, *, basePeriod: str | None = None) -> dict | None:
    """Pro-Forma 기반 과거 구조 비율.

    Returns
    -------
    dict
        grossMargin : float — 매출총이익률 (%)
        sgaRatio : float — 판관비율 (%)
        effectiveTaxRate : float — 유효세율 (%)
        depreciationRatio : float — 감가상각비율 (%)
        capexToRevenue : float — CAPEX/매출 (%)
        interestRateOnDebt : float — 부채이자율 (%)
        nwcToRevenue : float — 순운전자본/매출 (%)
        dividendPayout : float — 배당성향 (%)
        yearsUsed : int — 사용 연도 수
        confidence : str — 신뢰도
        trends : dict — 비율 추세 정보
        warnings : list[str] — 경고 메시지

    Capabilities:
        - 과거 IS/BS/CF 비율 (margin/SGA/tax/depreciation/capex/NWC/dividend) 8 종 추출
        - confidence + trends 동시 평가

    Guide:
        pro-forma 예측의 입력 base. yearsUsed ≥ 5 권장.

    When:
        Pro-forma 입력 + AI "이 회사 마진 구조" 답변.

    How:
        ``extractHistoricalRatios`` 위임 → 8 비율 + 메타.

    Requires:
        IS/BS/CF 시계열 ≥ 3 년.

    Raises:
        없음.

    Example:
        >>> calcHistoricalRatios(company)["grossMargin"]
        38.5

    See Also:
        - calcProFormaHighlights : 사용처
        - calcForecastMethodology : 입력 투명성

    AIContext:
        "마진 구조" 답변 시 grossMargin + trends 인용.
    """
    series, _, _, _, _ = _getSeriesAndMeta(company)

    from dartlab.analysis.financial.proforma import extractHistoricalRatios

    try:
        ratios = extractHistoricalRatios(series)
    except (KeyError, ValueError, ZeroDivisionError, TypeError) as exc:
        log.debug("과거 비율 추출 실패: %s", exc)
        return None

    return {
        "grossMargin": ratios.gross_margin,
        "sgaRatio": ratios.sga_ratio,
        "effectiveTaxRate": ratios.effective_tax_rate,
        "depreciationRatio": ratios.depreciation_ratio,
        "capexToRevenue": ratios.capex_to_revenue,
        "interestRateOnDebt": ratios.interest_rate_on_debt,
        "nwcToRevenue": ratios.nwc_to_revenue,
        "dividendPayout": ratios.dividend_payout,
        "yearsUsed": ratios.years_used,
        "confidence": ratios.confidence,
        "trends": ratios.trends,
        "warnings": ratios.warnings,
    }


@memoizedCalc
def calcForecastFlags(company: Any, *, basePeriod: str | None = None) -> dict | None:
    """매출전망 플래그.

    Capabilities:
        - 예측 불가 / 낮은 신뢰도 / 시계열 only / 구조변화 / 시나리오 격차 / engine warnings 등 6 종 flag
        - story flag 박스 입력

    Returns:
        dict — {"flags": list[(code, message)]} 또는 None.

    Guide:
        flag 누적 = 예측 신뢰도 ↓. UNFORECASTABLE 가장 강한 경고.

    When:
        Story forecast flag + AI 예측 신뢰 답변.

    How:
        forecastable/confidence/method/structural_break/scenarios 평가 → 누적.

    Requires:
        ``_runForecastRevenue`` 결과 가용.

    Raises:
        없음 — flag 0 시 None.

    Example:
        >>> calcForecastFlags(company)["flags"]
        [('LOW_CONFIDENCE', '...')]

    See Also:
        - calcRevenueForecast : 본 예측
        - calcForecastMethodology : 투명성

    AIContext:
        "예측 위험" 답변 시 flags 인용.
    """
    result = _runForecastRevenue(company)
    if not result:
        return None

    flags: list[tuple[str, str]] = []

    if not result.forecastable:
        flags.insert(0, ("UNFORECASTABLE", f"예측 불가 -- {result.unforecastableReason}"))

    if result.confidence == "low":
        flags.append(("LOW_CONFIDENCE", "예측 신뢰도 낮음 -- 데이터 부족 또는 변동성 과다"))

    if result.method == "timeseries_only":
        from dartlab.core.messaging import missingDataHint

        flags.append(("TIMESERIES_ONLY", f"시계열만 사용 -- {missingDataHint('컨센서스')}"))

    if "structural_break" in result.aiContext:
        flags.append(("STRUCTURAL_BREAK", "매출 시계열 구조변화 감지 -- 과거 추세가 미래에 유효하지 않을 수 있음"))

    if result.scenarios:
        bull = result.scenarios.get("bull", [])
        bear = result.scenarios.get("bear", [])
        if bull and bear and bull[0] > 0 and bear[0] > 0:
            spread = (bull[0] - bear[0]) / bear[0] * 100
            if spread > 50:
                flags.append(("HIGH_UNCERTAINTY", f"Bull-Bear 격차 {spread:.0f}% -- 불확실성 높음"))

    for w in result.warnings:
        flags.append(("WARNING", w))

    if not flags:
        return None

    return {"flags": flags}


@memoizedCalc
def calcCalibrationReport(company: Any, *, basePeriod: str | None = None) -> dict | None:
    """예측 캘리브레이션 리포트 — 이 종목의 과거 예측 정확도.

    forward test 레코드가 5건 미만이면 None 반환.
    데이터가 축적되면서 점진적으로 활성화된다.

    Returns
    -------
    dict | None
        None: 평가 레코드 5건 미만.
        brierScore : float — Brier 점수 (0~1, 낮을수록 정확)
        nRecords : int — 평가 레코드 수
        bins : list[dict] — 캘리브레이션 구간별 통계

    Capabilities:
        - 종목별 과거 예측 vs 실제 비교 → Brier score + 구간별 calibration bins
        - 5+ records 누적되면 점진 활성화

    Guide:
        Brier ≤ 0.20 = 잘 캘리브레이션. 0.25 = 무작위 추정 수준.

    When:
        예측 정확도 검증 + AI "이 예측 신뢰" 답변.

    How:
        forwardTest.loadRecords → directionProbability/Actual → Brier + bins.

    Requires:
        forwardTest 누적 레코드 ≥ 5.

    Raises:
        없음 — 부족 시 None.

    Example:
        >>> calcCalibrationReport(company)["brierScore"]
        0.18

    See Also:
        - forecast.forwardTest : 레코드 기록
        - calcForecastFlags : 예측 위험

    AIContext:
        "이전 예측 정확도" 답변 시 brierScore + nRecords 인용.
    """
    from dataclasses import asdict

    from dartlab.analysis.forecast.calibrationMetrics import (
        buildCalibrationBins,
        computeBrierScore,
    )
    from dartlab.analysis.forecast.forwardTest import loadRecords

    stockCode = getattr(company, "stockCode", None)
    if not stockCode:
        return None

    records = loadRecords(stockCode)
    evaluated = [r for r in records if r.directionProbability is not None and r.directionActual is not None]
    if len(evaluated) < 5:
        return None

    predictions = [r.directionProbability for r in evaluated]
    outcomes = [1 if r.directionActual == "up" else 0 for r in evaluated]

    brier = computeBrierScore(predictions, outcomes)
    bins = buildCalibrationBins(predictions, outcomes)

    return {
        "brierScore": round(brier, 4),
        "nRecords": len(evaluated),
        "bins": [asdict(b) for b in bins],
    }
