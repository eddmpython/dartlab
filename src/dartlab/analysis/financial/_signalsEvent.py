"""calcEventImpact + helpers — 이벤트 충격 분석 (공시 급변/지배구조 변화 시점).

calcEventImpact + _calcGrowthRates + _calcMargins + _buildEvent + _findPeriodIdx 5 함수.
predictionSignals.py 의 calc 4c 분리.

과거 공시 텍스트 급변 또는 지배구조 변화 시점을 식별하고 전후 매출/마진 변화 패턴 추출.
"""

from __future__ import annotations

import logging

from dartlab.analysis.financial._predictionProbability import _DIRECTION_SCORES
from dartlab.core.memory import memoizedCalc
from dartlab.core.utils.calc import safeDiv as _safe
from dartlab.core.utils.helpers import annualColsFromPeriods, toDictBySnakeId
from dartlab.core.utils.safe import get as _get

log = logging.getLogger(__name__)

_getF = _get


def _getStockCode(company) -> str | None:
    return getattr(company, "stockCode", None)


# ══════════════════════════════════════
# calc 4c: 이벤트 충격 분석
# ══════════════════════════════════════


@memoizedCalc
def calcEventImpact(company, *, basePeriod: str | None = None) -> dict | None:
    """이벤트 충격 분석 — 공시 급변/지배구조 변화 시점 전후 재무 패턴.

    과거에 공시 텍스트가 급변하거나 지배구조가 변한 시점을 식별하고,
    해당 시점 전후 매출/마진 변화 패턴을 추출한다.

    Capabilities:
        - 이벤트 시점 전후 매출·마진 충격과 회복기간 측정.

    Returns
    -------
    dict
        events : list[dict] — 감지된 이벤트 목록
            period : str — 이벤트 발생 기간
            type : str — 유형 ("disclosureShock" | "structuralBreak" | "revenueShock")
            magnitude : float — 변화 크기
            preRevGrowth : float | None — 이벤트 전 매출 성장률 (%)
            postRevGrowth : float | None — 이벤트 후 매출 성장률 (%)
            preMargin : float | None — 이벤트 전 영업마진 (%)
            postMargin : float | None — 이벤트 후 영업마진 (%)
            recoveryYears : int | None — 회복까지 걸린 기간 (일수)
        averageImpact : dict[str, float] — 이벤트 유형별 평균 충격 (%p)
        resilience : str — 충격 회복력 ("high" | "medium" | "low")
        avgRecoveryYears : float | None — 평균 회복 기간

    Guide:
        평균 회복 ≤ 1 년이면 high 회복력, 3 년 이상이면 low.

    When:
        구조적 사건 (지배구조·공시 급변) 후 회복력 평가 시점.

    How:
        IS 시계열 + 공시 diff 결합 → 이벤트 식별 → 전후 매출/마진 비교.

    Requires:
        IS 다년 시계열, 공시 텍스트 diff 또는 구조변화 신호.

    Raises:
        없음 — 데이터 부재 시 None.

    Example:
        >>> calcEventImpact(company)
        {'resilience': 'medium', 'avgRecoveryYears': 1.5}

    See Also:
        - calcStructuralBreak : 구조 변화 검출.

    AIContext:
        이벤트 라벨링은 통계 신호 — 의도/사유 단정 금지.
    """
    isResult = company.select("IS", ["매출액", "영업이익"])
    isParsed = toDictBySnakeId(isResult)
    if isParsed is None:
        return None
    isData, isPeriods = isParsed
    revRow = isData.get("매출액", {})
    oiRow = isData.get("영업이익", {})

    cols = annualColsFromPeriods(isPeriods, basePeriod=basePeriod)
    if len(cols) < 4:
        return None

    revValues = [_get(revRow, c) or None for c in cols]
    oiValues = [_get(oiRow, c) or None for c in cols]

    # 매출 성장률 + 마진 계산
    revGrowth = _calcGrowthRates(revValues)
    margins = _calcMargins(revValues, oiValues)

    events: list[dict] = []

    # 1. 공시 텍스트 급변 감지 (disclosureDelta 활용)
    try:
        from dartlab.analysis.financial.predictionSignals import calcDisclosureDelta  # noqa: PLC0415

        discDelta = calcDisclosureDelta(company, basePeriod=basePeriod)
        if discDelta and discDelta.get("changeIntensity"):
            intensity = discDelta["changeIntensity"]
            if intensity.get("totalChangeBytes", 0) > 50000:
                eventIdx = 0  # 최신 기간
                events.append(
                    _buildEvent(
                        period=cols[eventIdx] if eventIdx < len(cols) else "unknown",
                        eventType="disclosureShock",
                        magnitude=intensity.get("totalChangeBytes", 0) / 10000,
                        revGrowth=revGrowth,
                        margins=margins,
                        eventIdx=eventIdx,
                    )
                )
    except (AttributeError, TypeError, KeyError):
        pass

    # 2. 구조변화점 감지 (structuralBreak 재활용)
    try:
        from dartlab.analysis.financial.predictionSignals import calcStructuralBreak  # noqa: PLC0415

        breakResult = calcStructuralBreak(company, basePeriod=basePeriod)
        if breakResult:
            for metric, detail in breakResult.get("metrics", {}).items():
                if detail.get("breakDetected"):
                    breakYear = detail.get("breakYear")
                    if breakYear:
                        eventIdx = _findPeriodIdx(cols, breakYear)
                        if eventIdx is not None:
                            events.append(
                                _buildEvent(
                                    period=cols[eventIdx] if eventIdx < len(cols) else str(breakYear),
                                    eventType="structuralBreak",
                                    magnitude=abs(detail.get("postBreakGrowth", 0) - detail.get("preBreakGrowth", 0)),
                                    revGrowth=revGrowth,
                                    margins=margins,
                                    eventIdx=eventIdx,
                                )
                            )
    except (AttributeError, TypeError, KeyError):
        pass

    # 3. 매출 급변 감지 (|성장률| > 30% = 충격)
    for i, g in enumerate(revGrowth):
        if g is not None and abs(g) > 30:
            events.append(
                _buildEvent(
                    period=cols[i] if i < len(cols) else "unknown",
                    eventType="revenueShock",
                    magnitude=abs(g),
                    revGrowth=revGrowth,
                    margins=margins,
                    eventIdx=i,
                )
            )

    if not events:
        return {
            "events": [],
            "averageImpact": {},
            "resilience": "high",
            "summary": "최근 5년간 유의미한 충격 이벤트 없음",
        }

    # 회복력 판단
    recoveries = [e.get("recoveryYears") for e in events if e.get("recoveryYears") is not None]
    avgRecovery = sum(recoveries) / len(recoveries) if recoveries else None
    resilience = (
        "high"
        if avgRecovery is not None and avgRecovery <= 1
        else ("low" if avgRecovery and avgRecovery >= 3 else "medium")
    )

    # 유형별 평균 충격
    typeImpacts: dict[str, list[float]] = {}
    for e in events:
        t = e["type"]
        impact = (e.get("postRevGrowth") or 0) - (e.get("preRevGrowth") or 0)
        typeImpacts.setdefault(t, []).append(impact)

    averageImpact = {t: round(sum(v) / len(v), 2) for t, v in typeImpacts.items()}

    return {
        "events": events,
        "averageImpact": averageImpact,
        "resilience": resilience,
        "avgRecoveryYears": round(avgRecovery, 1) if avgRecovery else None,
    }


def _calcGrowthRates(values: list[float | None]) -> list[float | None]:
    """연간 성장률 계산."""
    rates = []
    for i in range(len(values) - 1):
        cur, prev = values[i], values[i + 1]
        if cur is not None and prev is not None and prev != 0:
            rates.append((cur - prev) / abs(prev) * 100)
        else:
            rates.append(None)
    return rates


def _calcMargins(revValues: list, oiValues: list | None) -> list[float | None]:
    """영업마진 시계열."""
    if oiValues is None:
        return [None] * len(revValues)
    margins = []
    for r, o in zip(revValues, oiValues):
        if r is not None and o is not None and r != 0:
            margins.append(o / r * 100)
        else:
            margins.append(None)
    return margins


def _buildEvent(
    *,
    period: str,
    eventType: str,
    magnitude: float,
    revGrowth: list[float | None],
    margins: list[float | None],
    eventIdx: int,
) -> dict:
    """이벤트 전후 재무 패턴 추출."""
    preRevGrowth = revGrowth[eventIdx + 1] if eventIdx + 1 < len(revGrowth) else None
    postRevGrowth = revGrowth[eventIdx] if eventIdx < len(revGrowth) else None
    preMargin = margins[eventIdx + 1] if eventIdx + 1 < len(margins) else None
    postMargin = margins[eventIdx] if eventIdx < len(margins) else None

    # 회복 시간: 이벤트 후 성장률이 양으로 돌아오는 기간
    recoveryYears = None
    if postRevGrowth is not None and postRevGrowth < 0:
        for j in range(eventIdx - 1, -1, -1):
            if j < len(revGrowth) and revGrowth[j] is not None and revGrowth[j] > 0:
                recoveryYears = eventIdx - j
                break

    return {
        "period": period,
        "type": eventType,
        "magnitude": round(magnitude, 2),
        "preRevGrowth": round(preRevGrowth, 2) if preRevGrowth is not None else None,
        "postRevGrowth": round(postRevGrowth, 2) if postRevGrowth is not None else None,
        "preMargin": round(preMargin, 1) if preMargin is not None else None,
        "postMargin": round(postMargin, 1) if postMargin is not None else None,
        "recoveryYears": recoveryYears,
    }


def _findPeriodIdx(cols: list[str], year: int) -> int | None:
    """연도로 기간 인덱스 찾기."""
    yearStr = str(year)
    for i, col in enumerate(cols):
        if col.startswith(yearStr):
            return i
    return None


__all__ = ["calcEventImpact"]
