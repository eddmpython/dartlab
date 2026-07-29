"""기간별 재무비율 시계열 계산.

단일시점 계산기를 기간별로 재사용해 공식의 두 번째 구현을 만들지 않는다.
"""

from __future__ import annotations

from dartlab.core.ratioCategories import RATIO_CATEGORIES
from dartlab.core.ratios.common import _resolveArchetype
from dartlab.core.ratios.models import RatioSeriesResult
from dartlab.core.ratios.point import calcRatios

_ABSOLUTE_SOURCES = {
    "revenue": "revenueTTM",
    "operatingProfit": "operatingIncomeTTM",
    "netProfit": "netIncomeTTM",
    "totalAssets": "totalAssets",
    "totalEquity": "totalEquity",
    "operatingCashflow": "operatingCashflowTTM",
}
_SERIES_FIELDS = tuple(fieldName for _, fieldNames in RATIO_CATEGORIES for fieldName in fieldNames)
_EXTRA_FIELDS = ("beneishMScore", "sloanAccrualRatio")


def _sliceSeries(
    series: dict[str, dict[str, list[float | None]]],
    end: int,
) -> dict[str, dict[str, list[float | None]]]:
    """end 이전 값만 가진 독립 prefix를 만든다."""
    return {
        statement: {snakeId: values[:end] for snakeId, values in accounts.items()}
        for statement, accounts in series.items()
    }


def calcRatioSeries(
    annualSeries: dict[str, dict[str, list[float | None]]],
    years: list[str],
    *,
    yoyLag: int,
    archetypeOverride: str | None = None,
) -> RatioSeriesResult:
    """재무비율 시계열을 단일 공식으로 계산한다.

    Args:
        annualSeries: 연간 또는 분기 statement series.
        years: 입력 값과 같은 순서의 기간 식별자.
        yoyLag: 전년 비교 간격. 연간은 1, 분기는 4.
        archetypeOverride: 명시적 업종 정책. None이면 계정에서 판별한다.

    Returns:
        모든 비율이 years와 같은 길이인 RatioSeriesResult.

    Raises:
        ValueError: yoyLag가 양의 정수가 아니거나 업종 정책이 잘못된 경우.
    """
    if isinstance(yoyLag, bool) or not isinstance(yoyLag, int) or yoyLag <= 0:
        raise ValueError("yoyLag must be a positive integer")

    result = RatioSeriesResult(years=list(years))
    archetype = _resolveArchetype(annualSeries, archetypeOverride)
    for index in range(len(years)):
        point = calcRatios(
            _sliceSeries(annualSeries, index + 1),
            annual=True,
            archetypeOverride=archetype,
            yoyLag=yoyLag,
        )
        for fieldName in (*_SERIES_FIELDS, *_EXTRA_FIELDS):
            sourceName = _ABSOLUTE_SOURCES.get(fieldName, fieldName)
            getattr(result, fieldName).append(getattr(point, sourceName))
    return result


def toSeriesDict(
    result: RatioSeriesResult,
) -> tuple[dict[str, dict[str, list[float | None]]], list[str]]:
    """RatioSeriesResult를 statement series 형태로 변환한다.

    Returns:
        RATIO statement mapping과 기간 목록.
    """
    ratioDict: dict[str, list[float | None]] = {}
    for fieldName in _SERIES_FIELDS:
        values = getattr(result, fieldName)
        if any(value is not None for value in values):
            ratioDict[fieldName] = values
    return {"RATIO": ratioDict}, result.years
