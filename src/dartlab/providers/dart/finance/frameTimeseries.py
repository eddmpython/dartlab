"""이미 검증된 DART finance frame을 분기 시계열로 변환한다."""

from __future__ import annotations

import polars as pl


def buildTimeseriesFromFrame(
    df: pl.DataFrame,
    *,
    stockCode: str | None = None,
    fsDivPref: str = "CFS",
) -> tuple[dict[str, dict[str, list[float | None]]], list[str]] | None:
    """검증된 DART finance frame을 loader 호출 없이 분기 시계열로 만든다.

    Args:
        df: 동일 회사의 DART finance 원천 행.
        stockCode: Mapping ledger에 기록할 선택적 종목코드.
        fsDivPref: 시트별 우선 재무제표 구분.

    Returns:
        분기별 statement series와 period 목록. 유효 행이 없으면 ``None``.

    Raises:
        없음. 스키마 또는 지원 재무제표가 없으면 ``None``을 반환한다.

    Example:
        ``buildTimeseriesFromFrame(frame, stockCode="005930")``.
    """

    from dartlab.providers.dart.finance.pivot import (
        _normalizeFinanceFrame,
        _pivotToSeries,
    )

    result = _normalizeFinanceFrame(df, str(fsDivPref).strip() or "CFS")
    if result is None:
        return None
    normalized, periods = result
    return _pivotToSeries(normalized, periods, stockCode=stockCode), periods
