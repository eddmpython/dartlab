"""시계열 값 추출 유틸."""

from __future__ import annotations

# 계정 alias: 기업마다 같은 개념이 다른 snakeId로 매핑되는 경우 fallback
_ACCOUNT_ALIASES: dict[str, list[str]] = {
    "total_equity": ["total_stockholders_equity", "owners_of_parent_equity"],
    "revenue": ["sales"],
    "sales": ["revenue"],
}


def _hasNonNull(vals: list | None) -> bool:
    """리스트에 non-null 값이 3개 이상 있는지."""
    if not vals:
        return False
    return sum(1 for v in vals if v is not None) >= 3


def _resolveVals(
    series: dict[str, dict[str, list[float | None]]],
    sjDiv: str,
    snakeId: str,
) -> list[float | None] | None:
    """snakeId로 값을 찾되, 유효 데이터 부족 시 alias 체인으로 fallback."""
    vals = series.get(sjDiv, {}).get(snakeId)
    if _hasNonNull(vals):
        return vals
    for alias in _ACCOUNT_ALIASES.get(snakeId, []):
        avals = series.get(sjDiv, {}).get(alias)
        if _hasNonNull(avals):
            return avals
    # 원본이라도 있으면 반환 (non-null 2개라도)
    return vals if vals else None


def getTTM(
    series: dict[str, dict[str, list[float | None]]],
    sjDiv: str,
    snakeId: str,
    *,
    strict: bool = True,
    annualize: bool = False,
    maxTrailingNones: int | None = None,
) -> float | None:
    """최근 4개 non-null 값의 합 (IS/CF용 TTM).

    Args:
        series: buildTimeseries() 결과.
        sjDiv: "IS" 또는 "CF".
        snakeId: 계정 snakeId.
        strict: True면 4/4 분기 모두 필요 (annualize=False일 때).
        annualize: True면 분기 부족 시 연환산 (2~3분기 → ×4/N).
                   strict보다 우선. FY 직후 TTM 공백 방지용.
        maxTrailingNones: 허용할 trailing None 개수.
                   None이면 제한 없이 끝의 None을 제거한다.
                   0이면 최신 period가 비어 있는 stale 시계열을 TTM으로 쓰지 않는다.

    Returns:
        TTM 합계 또는 None.
    """
    vals = _resolveVals(series, sjDiv, snakeId)
    if not vals:
        return None
    # 끝에서 trailing None 제거 후 최근 4개 선택 (미공시 기간 대응)
    trimmed = vals
    trailingNones = 0
    while trimmed and trimmed[-1] is None:
        trimmed = trimmed[:-1]
        trailingNones += 1
    if maxTrailingNones is not None and trailingNones > maxTrailingNones:
        return None
    if not trimmed:
        return None
    last4 = [v for v in trimmed[-4:] if v is not None]
    if len(last4) == 4:
        return sum(last4)
    if annualize and len(last4) >= 2:
        return sum(last4) * 4 / len(last4)
    if not strict and len(last4) == 3:
        return sum(last4) * 4 / 3
    return None


def getLatest(
    series: dict[str, dict[str, list[float | None]]],
    sjDiv: str,
    snakeId: str,
) -> float | None:
    """최신 non-null 값 (BS용).

    Args:
        series: buildTimeseries() 결과.
        sjDiv: "BS".
        snakeId: 계정 snakeId.

    Returns:
        최신 값 또는 None.
    """
    vals = _resolveVals(series, sjDiv, snakeId)
    if not vals:
        return None
    for v in reversed(vals):
        if v is not None:
            return v
    return None


def getAnnualValues(
    series: dict[str, dict[str, list[float | None]]],
    sjDiv: str,
    snakeId: str,
) -> list[float | None]:
    """해당 계정의 전체 시계열 값 리스트.

    Returns:
        값 리스트 (None 포함). 계정이 없으면 빈 리스트.
    """
    return _resolveVals(series, sjDiv, snakeId) or []


def getRevenueGrowth3Y(
    series: dict[str, dict[str, list[float | None]]],
) -> float | None:
    """매출 3년 CAGR (%).

    연간 데이터 기준: 끝에서 4번째 vs 마지막 non-null.
    """
    vals = _resolveVals(series, "IS", "sales")
    if not vals:
        return None

    valid = [(i, v) for i, v in enumerate(vals) if v is not None and v > 0]
    if len(valid) < 4:
        return None

    oldIdx, oldRev = valid[-4]
    newIdx, newRev = valid[-1]
    nYears = newIdx - oldIdx
    if nYears <= 0 or oldRev <= 0:
        return None

    return ((newRev / oldRev) ** (1 / nYears) - 1) * 100
