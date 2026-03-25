"""ECOS 시계열 조회 — 단일/복수 지표."""

from __future__ import annotations

import logging
from datetime import date, datetime

import polars as pl

from . import cache as _cache
from . import catalog as _catalog
from .client import EcosClient
from .types import SeriesNotFoundError

log = logging.getLogger(__name__)

# 수집 시작년도
_START_YEAR = 2000


def _formatDate(dt: str, frequency: str, *, isEnd: bool = False) -> str:
    """날짜를 ECOS 주기별 형식으로 변환."""
    dt = str(dt).replace("-", "")

    # 이미 분기 형식이면 그대로
    if "Q" in dt:
        if frequency == "Q":
            return dt
        # 분기 → 월로 변환
        year = dt[:4]
        q = int(dt[-1])
        month = q * 3 if isEnd else (q - 1) * 3 + 1
        dt = f"{year}{month:02d}{'31' if isEnd else '01'}"

    # 연도만 입력된 경우 확장
    if len(dt) == 4:
        dt = dt + ("1231" if isEnd else "0101")
    elif len(dt) == 6:
        dt = dt + ("31" if isEnd else "01")

    if frequency == "A":
        return dt[:4]
    if frequency == "Q":
        if len(dt) >= 6:
            month = int(dt[4:6])
            quarter = (month - 1) // 3 + 1
            return dt[:4] + "Q" + str(quarter)
        return dt[:4] + ("Q4" if isEnd else "Q1")
    if frequency == "M":
        return dt[:6]
    # D (일별)
    return dt[:8]


def _parseDate(timeStr: str, frequency: str) -> date | None:
    """ECOS TIME 문자열 → Python date."""
    try:
        if frequency == "A":
            return datetime.strptime(timeStr, "%Y").date()
        if frequency == "Q":
            # "2024Q1" → 2024-01-01
            year = int(timeStr[:4])
            quarter = int(timeStr[-1])
            month = (quarter - 1) * 3 + 1
            return date(year, month, 1)
        if frequency == "M":
            return datetime.strptime(timeStr, "%Y%m").date()
        # D
        return datetime.strptime(timeStr, "%Y%m%d").date()
    except (ValueError, IndexError):
        return None


def _defaultStart(frequency: str) -> str:
    """기본 시작일."""
    return _formatDate(str(_START_YEAR), frequency)


def _defaultEnd(frequency: str) -> str:
    """기본 종료일 (오늘)."""
    today = date.today()
    return _formatDate(today.strftime("%Y%m%d"), frequency, isEnd=True)


def fetchSeries(
    client: EcosClient,
    indicatorId: str,
    *,
    start: str | None = None,
    end: str | None = None,
) -> pl.DataFrame:
    """ECOS 지표 시계열 → Polars DataFrame ``(date, value)``.

    Args:
        indicatorId: 카탈로그 지표 ID (예: "GDP", "CPI", "BASE_RATE").
        start: 시작일 (YYYY, YYYYMM, YYYYMMDD). None이면 2000년부터.
        end: 종료일. None이면 최신까지.
    """
    cached = _cache.get(indicatorId, start, end)
    if cached is not None:
        return cached

    entry = _catalog.getEntry(indicatorId)
    if entry is None:
        available = ", ".join(_catalog.getAllIds()[:10]) + " ..."
        raise SeriesNotFoundError(
            f"지표 '{indicatorId}'을 찾을 수 없습니다. 사용 가능: {available}"
        )

    startDate = start if start else _defaultStart(entry.frequency)
    endDate = end if end else _defaultEnd(entry.frequency)

    # 시작/종료를 ECOS 형식으로 변환
    startDate = _formatDate(startDate, entry.frequency)
    endDate = _formatDate(endDate, entry.frequency, isEnd=True)

    rows = client.get(
        tableCode=entry.tableCode,
        frequency=entry.frequency,
        startDate=startDate,
        endDate=endDate,
        itemCode=entry.itemCode,
    )

    dates: list[date] = []
    values: list[float | None] = []
    for row in rows:
        d = _parseDate(row.get("TIME", ""), entry.frequency)
        if d is None:
            continue
        valStr = row.get("DATA_VALUE", "")
        if not valStr or valStr == "-":
            dates.append(d)
            values.append(None)
        else:
            try:
                dates.append(d)
                values.append(float(valStr.replace(",", "")))
            except ValueError:
                dates.append(d)
                values.append(None)

    df = pl.DataFrame({"date": dates, "value": values}).with_columns(
        pl.col("date").cast(pl.Date),
        pl.col("value").cast(pl.Float64),
    )

    isDailyFreq = entry.frequency == "D"
    _cache.put(indicatorId, start, end, df, daily=isDailyFreq)
    return df


def fetchMulti(
    client: EcosClient,
    indicatorIds: list[str],
    *,
    start: str | None = None,
    end: str | None = None,
) -> pl.DataFrame:
    """복수 지표 → wide DataFrame ``(date, GDP, CPI, ...)``.

    주기가 다른 지표를 합칠 때 outer join 후 forward-fill.
    """
    if not indicatorIds:
        return pl.DataFrame()

    frames: list[pl.DataFrame] = []
    for iid in indicatorIds:
        df = fetchSeries(client, iid, start=start, end=end)
        df = df.rename({"value": iid})
        frames.append(df)

    result = frames[0]
    for df in frames[1:]:
        result = result.join(df, on="date", how="full", coalesce=True)

    return result.sort("date").fill_null(strategy="forward")
