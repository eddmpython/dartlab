"""FRED 시계열 조회 — 단일/복수 시리즈, 검색, 메타, 릴리즈."""

from __future__ import annotations

from datetime import date, datetime

import polars as pl

from . import cache as _cache
from .client import FredClient
from .types import SeriesMeta


def fetch_series(
    client: FredClient,
    series_id: str,
    *,
    start: str | None = None,
    end: str | None = None,
    frequency: str | None = None,
    aggregation: str = "avg",
) -> pl.DataFrame:
    """FRED 시계열 → Polars DataFrame ``(date, value)``.

    Args:
        series_id: FRED 시리즈 ID (예: "GDP", "UNRATE").
        start: 시작일 (YYYY-MM-DD). None이면 전체.
        end: 종료일. None이면 최신까지.
        frequency: 리샘플 주파수 (d/w/bw/m/q/sa/a). None이면 원본.
        aggregation: 리샘플 집계 방법 (avg/sum/eop).
    """
    cached = _cache.get(series_id, start, end, frequency, aggregation)
    if cached is not None:
        return cached

    params: dict = {"series_id": series_id}
    if start:
        params["observation_start"] = start
    if end:
        params["observation_end"] = end
    if frequency:
        params["frequency"] = frequency
    if aggregation != "avg":
        params["aggregation_method"] = aggregation

    data = client.get("/series/observations", **params)
    observations = data.get("observations", [])

    dates: list[date] = []
    values: list[float | None] = []
    for obs in observations:
        try:
            d = datetime.strptime(obs["date"], "%Y-%m-%d").date()
        except (ValueError, KeyError):
            continue
        val_str = obs.get("value", ".")
        if val_str == "." or val_str is None:
            dates.append(d)
            values.append(None)
        else:
            try:
                dates.append(d)
                values.append(float(val_str))
            except ValueError:
                dates.append(d)
                values.append(None)

    df = pl.DataFrame({"date": dates, "value": values}).with_columns(
        pl.col("date").cast(pl.Date),
        pl.col("value").cast(pl.Float64),
    )

    is_daily = frequency == "d" or (frequency is None and len(df) > 500)
    _cache.put(series_id, start, end, frequency, aggregation, df, daily=is_daily)
    return df


def fetch_multi(
    client: FredClient,
    series_ids: list[str],
    *,
    start: str | None = None,
    end: str | None = None,
    frequency: str | None = None,
) -> pl.DataFrame:
    """복수 시계열 → wide DataFrame ``(date, GDP, UNRATE, ...)``.

    주파수가 다른 시리즈를 합칠 때 outer join 후 forward-fill.
    """
    if not series_ids:
        return pl.DataFrame()

    frames: list[pl.DataFrame] = []
    for sid in series_ids:
        df = fetch_series(client, sid, start=start, end=end, frequency=frequency)
        df = df.rename({"value": sid})
        frames.append(df)

    result = frames[0]
    for df in frames[1:]:
        result = result.join(df, on="date", how="full", coalesce=True)

    result = result.sort("date")
    # forward-fill로 주파수 차이 보정
    for col in result.columns:
        if col != "date":
            result = result.with_columns(pl.col(col).forward_fill())

    return result


def search_series(
    client: FredClient,
    query: str,
    *,
    limit: int = 20,
) -> pl.DataFrame:
    """키워드 검색 → DataFrame ``(id, title, frequency, units, popularity)``.

    Args:
        query: 검색어 (영문).
        limit: 최대 결과 수.
    """
    data = client.get(
        "/series/search",
        search_text=query,
        limit=limit,
        order_by="popularity",
        sort_order="desc",
    )
    serieses = data.get("seriess", [])

    rows = []
    for s in serieses:
        rows.append(
            {
                "id": s.get("id", ""),
                "title": s.get("title", ""),
                "frequency": s.get("frequency", ""),
                "units": s.get("units", ""),
                "seasonal_adjustment": s.get("seasonal_adjustment_short", ""),
                "popularity": s.get("popularity", 0),
                "observation_start": s.get("observation_start", ""),
                "observation_end": s.get("observation_end", ""),
            }
        )

    return (
        pl.DataFrame(rows)
        if rows
        else pl.DataFrame(
            schema={
                "id": pl.Utf8,
                "title": pl.Utf8,
                "frequency": pl.Utf8,
                "units": pl.Utf8,
                "seasonal_adjustment": pl.Utf8,
                "popularity": pl.Int64,
                "observation_start": pl.Utf8,
                "observation_end": pl.Utf8,
            }
        )
    )


def fetch_meta(client: FredClient, series_id: str) -> SeriesMeta:
    """시계열 메타데이터 조회."""
    data = client.get("/series", series_id=series_id)
    serieses = data.get("seriess", [])
    if not serieses:
        from .types import SeriesNotFoundError

        raise SeriesNotFoundError(f"시리즈를 찾을 수 없습니다: {series_id}")

    s = serieses[0]
    return SeriesMeta(
        id=s.get("id", series_id),
        title=s.get("title", ""),
        frequency=s.get("frequency", ""),
        units=s.get("units", ""),
        seasonal_adjustment=s.get("seasonal_adjustment", ""),
        observation_start=s.get("observation_start", ""),
        observation_end=s.get("observation_end", ""),
        last_updated=s.get("last_updated", ""),
        notes=s.get("notes", ""),
    )


def fetch_releases(client: FredClient, *, limit: int = 20) -> pl.DataFrame:
    """최근 데이터 릴리즈 일정."""
    data = client.get("/releases", limit=limit, order_by="press_release", sort_order="desc")
    releases = data.get("releases", [])

    rows = []
    for r in releases:
        rows.append(
            {
                "id": r.get("id", 0),
                "name": r.get("name", ""),
                "press_release": r.get("press_release", "false") == "true",
                "link": r.get("link", ""),
            }
        )

    return (
        pl.DataFrame(rows)
        if rows
        else pl.DataFrame(schema={"id": pl.Int64, "name": pl.Utf8, "press_release": pl.Boolean, "link": pl.Utf8})
    )
