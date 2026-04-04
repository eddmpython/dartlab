"""macro 엔진 공통 헬퍼."""

from __future__ import annotations

from datetime import date, datetime, timedelta


def recent_timeseries(df, months: int = 6, value_col: str = "value") -> list[dict] | None:
    """gather DataFrame에서 최근 N개월분을 slice해서 [{date, value}] 리스트로 반환.

    gather가 반환하는 Polars DataFrame(date, value 컬럼)을 소비.
    """
    if df is None or len(df) == 0:
        return None

    try:
        cutoff = datetime.now() - timedelta(days=months * 30)
        filtered = df.filter(df["date"] >= cutoff).sort("date")
        if len(filtered) == 0:
            return None

        dates = filtered.get_column("date").to_list()
        vals = filtered.get_column(value_col).to_list()

        return [
            {
                "date": str(d)[:10] if hasattr(d, "isoformat") else str(d)[:10],
                "value": float(v) if v is not None else None,
            }
            for d, v in zip(dates, vals)
            if v is not None
        ]
    except Exception:
        return None


def apply_as_of(df, as_of: str | None):
    """as_of 날짜까지만 필터링. 백테스트용."""
    if as_of is None or df is None or len(df) == 0:
        return df
    try:
        cutoff = datetime.strptime(as_of, "%Y-%m-%d").date() if isinstance(as_of, str) else as_of
        return df.filter(df["date"] <= cutoff)
    except Exception:
        return df


def apply_overrides(data: dict, overrides: dict | None) -> dict:
    """overrides dict를 data에 병합. 시나리오 시뮬레이션용."""
    if overrides:
        data.update(overrides)
    return data


def fetch_macro_series(series_id: str, *, as_of: str | None = None):
    """gather.macro() 래퍼 — as_of 필터 적용.

    Args:
        series_id: FRED/ECOS 시리즈 ID
        as_of: 백테스트 날짜 (YYYY-MM-DD). None이면 전체.

    Returns:
        Polars DataFrame 또는 None
    """
    from dartlab.gather import getDefaultGather

    g = getDefaultGather()
    df = g.macro(series_id)
    return apply_as_of(df, as_of)


def wrap_gather_as_of(as_of: str | None = None):
    """gather 객체를 반환하되, as_of가 있으면 .macro()를 자동 필터링 래퍼로 교체.

    Usage::

        g = wrap_gather_as_of(as_of)
        df = g.macro("VIXCLS")  # as_of 이전 데이터만 반환
    """
    from dartlab.gather import getDefaultGather

    g = getDefaultGather()
    if as_of is None:
        return g

    _orig_macro = g.macro

    def _filtered_macro(sid):
        return apply_as_of(_orig_macro(sid), as_of)

    # shallow copy를 만들어 원본 g.macro를 보존
    import copy

    g_copy = copy.copy(g)
    g_copy.macro = _filtered_macro  # type: ignore
    return g_copy
