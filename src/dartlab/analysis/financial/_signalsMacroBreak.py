"""_signalsMacro 의 calcStructuralBreak: Chow Test 기반 구조변화 감지."""

from __future__ import annotations

import logging

from dartlab.analysis.financial._companyLookup import _getSectorKey
from dartlab.analysis.financial._constants import (
    TREND_RSQUARED_HIGH,
    TREND_RSQUARED_MEDIUM,
)
from dartlab.analysis.financial._predictionMath import _fitOLS
from dartlab.analysis.financial._predictionProbability import _clamp
from dartlab.core.memory import memoizedCalc
from dartlab.core.utils.calc import safeDiv as _safe
from dartlab.core.utils.helpers import annualColsFromPeriods, toDictBySnakeId
from dartlab.core.utils.safe import get as _get

log = logging.getLogger(__name__)
_getF = _getF2 = _getF3 = _getF4 = _get
_MAX_YEARS = 8


def _getStockCode(company) -> str | None:
    return getattr(company, "stockCode", None)


def _getRatioValues(company, ratioName: str, maxYears: int) -> list[float | None]:
    """Lazy proxy: _signalsMacroSensitivity 의 동명 함수 호출 (cycle 회피)."""
    from dartlab.analysis.financial._signalsMacroSensitivity import (
        _getRatioValues as _f,
    )

    return _f(company, ratioName, maxYears)


def _avgGrowth(vals: list[float]) -> float | None:
    """Lazy proxy: _signalsMacroSensitivity 의 동명 함수 호출 (cycle 회피)."""
    from dartlab.analysis.financial._signalsMacroSensitivity import (
        _avgGrowth as _f,
    )

    return _f(vals)


# ══════════════════════════════════════
# calc 3: 구조변화 감지
# ══════════════════════════════════════


@memoizedCalc
def calcStructuralBreak(company, *, basePeriod: str | None = None) -> dict | None:
    """Chow Test → 매출/영업이익/마진/ROE 구조변화점 감지 + 추세 신뢰도.

    Capabilities:
        Chow Test (1960) 의 dummy variable F-test 로 4 대 지표의 break year
        를 탐색. break 전후 평균 성장률 비교로 트렌드 안정성 판정. predicition
        모델의 horizon 결정 시 신뢰도 입력 (break 이후 데이터만 사용 권장).

    Args:
        company: Company 객체. IS 시계열 ≥ 6 년 필요.
        basePeriod: 기준 기간. None 이면 최신.

    Returns:
        dict | None: 다음 키 (6 년 미만 시 ``None``):
            - ``metrics`` (list[dict]): 4 지표별:
                * ``name`` (str): revenue/operatingIncome/operatingMargin/roe
                * ``hasBreak`` (bool): break 존재 여부 (Chow F > 임계)
                * ``breakYear`` (str|None): break 시점
                * ``preBreakGrowth``/``postBreakGrowth`` (float|None): 평균 성장률
                * ``trendReliability`` (str): high/medium/low
                * ``nObservations`` (int)
            - ``overallStability`` (str): ``"stable"``/``"transitioning"``/
              ``"volatile"`` (4 지표 합산)

    Raises:
        없음.

    Example:
        >>> r = calcStructuralBreak(Company("005930"))
        >>> r["overallStability"]
        'stable'
        >>> [m["name"] for m in r["metrics"] if m["hasBreak"]]
        ['operatingMargin']  # 마진만 구조변화

    Guide:
        Chow Test 임계: F > 5 = high break. preBreakGrowth vs postBreakGrowth
        부호 반전 시 reversing trend. DCF/forecastRevenue 의 horizon 단축
        권장 (break 이후 데이터만 사용). 6 년 미만 회사는 break 탐지 불가.

    When:
        장기 추세 안정성 점검과 horizon 결정 직전.

    How:
        4 지표 시계열을 year split 별 Chow F-stat 으로 break 탐색.

    SeeAlso:
        - ``dartlab.core.utils.ols.detectStructuralBreak``: Chow Test 본체
        - ``calcMacroRegression``: 매크로 회귀에서 break 인지 분기

    Requires:
        IS 시계열 ≥ 6 년 + 매출액/영업이익 데이터.

    AIContext:
        ``overallStability="volatile"`` 회사는 모든 forecast 결과 신뢰도
        하향. break year 가 외부 충격 (코로나/금융위기) 과 일치하면
        natural break. 회사 fundamentals 변화로 해석 금지.

    LLM Specifications:
        AntiPatterns:
            - hasBreak=True 만 보고 즉시 "트렌드 깨짐" 단정 금지. preBreak
              vs postBreak 평균 비교 후 가속/감속/reversal 분류.
            - 6 년 미만 회사에 본 함수 호출 → None. 호출자 분기 필요.
        OutputSchema:
            ``{metrics: list[dict 7키], overallStability: str}``.
        Prerequisites:
            IS 시계열 ≥ 6 년 + ``ols.detectStructuralBreak`` 로드 가능.
        Freshness:
            IS 의 freshness (최신 분기).
        Dataflow:
            IS 시계열 → 4 지표 추출 → Chow Test (각 year split) → F-stat
            max → break year → pre/post 평균 → overall 합산.
        TargetMarkets: KR (DART), US (EDGAR).
    """
    from dartlab.core.utils.ols import detectStructuralBreak, ols

    isResult = company.select("IS", ["매출액", "영업이익"])
    isParsed = toDictBySnakeId(isResult)
    if isParsed is None:
        return None
    isData, isPeriods = isParsed

    revRow = isData.get("매출액", {})
    oiRow = isData.get("영업이익", {})
    yCols = annualColsFromPeriods(isPeriods, basePeriod=basePeriod, maxYears=_MAX_YEARS)
    if len(yCols) < 6:
        return None

    # ROE 시계열 (ratioSeries에서)
    roeVals = _getRatioValues(company, "roe", len(yCols))

    # 4대 지표 시계열 (오래된 → 최신 순서로 뒤집기)
    metrics = []

    revVals = [_get(revRow, c) for c in reversed(yCols)]
    oiVals = [_get(oiRow, c) for c in reversed(yCols)]
    marginVals = [
        _safe(oi, rev) * 100 if rev != 0 and _safe(oi, rev) is not None else None for rev, oi in zip(revVals, oiVals)
    ]

    for name, vals in [
        ("revenue", revVals),
        ("operatingIncome", oiVals),
        ("operatingMargin", marginVals),
        ("roe", roeVals),
    ]:
        clean = [v for v in vals if v is not None]
        if len(clean) < 6:
            metrics.append(
                {
                    "name": name,
                    "hasBreak": False,
                    "breakYear": None,
                    "preBreakGrowth": None,
                    "postBreakGrowth": None,
                    "trendReliability": "low",
                    "nObservations": len(clean),
                }
            )
            continue

        breakIdx = detectStructuralBreak(clean)

        if breakIdx is not None:
            # 변화점 기준 전/후 성장률
            pre = clean[:breakIdx]
            post = clean[breakIdx:]
            preGrowth = _avgGrowth(pre)
            postGrowth = _avgGrowth(post)

            # 연도 매핑 (reversed yCols 기준)
            reversedCols = list(reversed(yCols))
            breakYear = reversedCols[breakIdx] if breakIdx < len(reversedCols) else None

            metrics.append(
                {
                    "name": name,
                    "hasBreak": True,
                    "breakYear": breakYear,
                    "preBreakGrowth": round(preGrowth, 2) if preGrowth is not None else None,
                    "postBreakGrowth": round(postGrowth, 2) if postGrowth is not None else None,
                    "trendReliability": "low",
                    "nObservations": len(clean),
                }
            )
        else:
            # 변화점 없음. 추세 일관
            _, _, r2 = ols(list(range(len(clean))), clean)
            reliability = "high" if r2 > TREND_RSQUARED_HIGH else ("medium" if r2 > TREND_RSQUARED_MEDIUM else "low")
            metrics.append(
                {
                    "name": name,
                    "hasBreak": False,
                    "breakYear": None,
                    "preBreakGrowth": None,
                    "postBreakGrowth": None,
                    "trendReliability": reliability,
                    "nObservations": len(clean),
                }
            )

    # 전체 안정성 판단
    nBreaks = sum(1 for m in metrics if m["hasBreak"])
    if nBreaks == 0:
        overallStability = "stable"
    elif nBreaks <= 1:
        overallStability = "transitioning"
    else:
        overallStability = "volatile"

    return {
        "metrics": metrics,
        "overallStability": overallStability,
    }
