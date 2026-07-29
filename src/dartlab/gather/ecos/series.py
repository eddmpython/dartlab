"""ECOS 시계열 조회 — 단일/복수 지표."""

from __future__ import annotations

import logging
from datetime import date, datetime

import polars as pl

from . import cache as _cache
from . import catalog as _catalog
from .client import EcosClient
from .types import EcosError, SeriesNotFoundError

log = logging.getLogger(__name__)

# 수집 시작년도
_START_YEAR = 2000


def _formatDate(dt: str, freq: str, *, isEnd: bool = False) -> str:
    """날짜를 ECOS 주기별 형식으로 변환.

    Parameters
    ----------
    dt : str
        날짜 문자열 (YYYY, YYYYMM, YYYYMMDD, 또는 YYYYQn).
    freq : str
        ECOS 주기 코드. "A"(연), "Q"(분기), "M"(월), "D"(일).
    isEnd : bool
        True 면 기간 종료일 방향으로 확장 (12월/Q4/31일).

    Returns
    -------
    str
        ECOS API 형식 날짜 문자열.
        A → "YYYY", Q → "YYYYQ1", M → "YYYYMM", D → "YYYYMMDD".
    """
    dt = str(dt).replace("-", "")

    # 이미 분기 형식이면 그대로
    if "Q" in dt:
        if freq == "Q":
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

    if freq == "A":
        return dt[:4]
    if freq == "Q":
        if len(dt) >= 6:
            month = int(dt[4:6])
            quarter = (month - 1) // 3 + 1
            return dt[:4] + "Q" + str(quarter)
        return dt[:4] + ("Q4" if isEnd else "Q1")
    if freq == "M":
        return dt[:6]
    # D (일별)
    return dt[:8]


def _parseDate(timeStr: str, freq: str) -> date | None:
    """ECOS TIME 문자열 → Python date.

    Parameters
    ----------
    timeStr : str
        ECOS 응답의 TIME 필드 (예: "2024", "2024Q1", "202401", "20240101").
    freq : str
        ECOS 주기 코드. "A"/"Q"/"M"/"D".

    Returns
    -------
    date | None
        변환된 날짜. 파싱 실패 시 None.
    """
    try:
        if freq == "A":
            return datetime.strptime(timeStr, "%Y").date()
        if freq == "Q":
            # "2024Q1" → 2024-01-01
            year = int(timeStr[:4])
            quarter = int(timeStr[-1])
            month = (quarter - 1) * 3 + 1
            return date(year, month, 1)
        if freq == "M":
            return datetime.strptime(timeStr, "%Y%m").date()
        # D
        return datetime.strptime(timeStr, "%Y%m%d").date()
    except (ValueError, IndexError):
        return None


def _defaultStart(freq: str) -> str:
    """기본 시작일 — 2000년을 주기 형식으로 반환.

    Parameters
    ----------
    freq : str
        ECOS 주기 코드. "A"/"Q"/"M"/"D".

    Returns
    -------
    str
        주기별 형식의 시작일 (예: A → "2000", M → "200001").
    """
    return _formatDate(str(_START_YEAR), freq)


def _defaultEnd(freq: str) -> str:
    """기본 종료일 — 오늘 날짜를 주기 형식으로 반환.

    Parameters
    ----------
    freq : str
        ECOS 주기 코드. "A"/"Q"/"M"/"D".

    Returns
    -------
    str
        주기별 형식의 종료일 (예: A → "2026", Q → "2026Q2").
    """
    today = date.today()
    return _formatDate(today.strftime("%Y%m%d"), freq, isEnd=True)


def fetchSeries(
    client: EcosClient,
    indicatorId: str,
    *,
    start: str | None = None,
    end: str | None = None,
    enrich: bool = False,
    limit: int | None = None,
) -> pl.DataFrame:
    """ECOS 지표 시계열 → Polars DataFrame ``(date, value)``.

    Capabilities: 캐시 확인 → catalog entry lookup → ECOS StatisticSearch GET → DataFrame.
    AIContext: ECOS 단일 시계열의 단일 진입점 — facade.Ecos.series 의 본체.
    Guide: 카탈로그 미등록 indicatorId 는 SeriesNotFoundError + 가용 list 안내.
    When: 한국 매크로 단일 시계열 분석 시 (가장 빈번한 호출 path).
    How: catalog.getEntry → freq별 default date 보강 → client.get → date/value parse.

    Parameters
    ----------
    client : EcosClient
        ECOS REST API 클라이언트.
    indicatorId : str
        카탈로그 지표 ID (예: "GDP", "CPI", "BASE_RATE").
    start : str | None
        시작일 (YYYY, YYYYMM, YYYYMMDD). None이면 2000년부터.
    end : str | None
        종료일. None이면 최신까지.
    enrich : bool
        True이면 변화율 추가 + Parquet 영구 캐시.
    limit : int | None
        반환 행수 상한 (가장 최근 N). None이면 [start, end] 전체.

    Returns
    -------
    pl.DataFrame
        컬럼: ``date`` (Date) — 관측일, ``value`` (Float64) — 지표값.
        enrich=True 시 변화율 컬럼 추가.

    Raises
    ------
    SeriesNotFoundError
        카탈로그에 없는 indicatorId.

    Requires
    --------
    EcosClient (``ECOS_API_KEY``) + indicatorId 가 카탈로그에 등록.

    Example
    -------
    >>> df = fetchSeries(client, "CPI", start="2020-01-01")

    See Also
    --------
    fetchMulti : 복수 지표 wide.
    facade.Ecos.series : 클래스 facade.
    """
    cached = _cache.get(indicatorId, start, end)
    if cached is not None:
        return cached

    entry = _catalog.getEntry(indicatorId)
    if entry is None:
        available = ", ".join(_catalog.getAllIds()[:10]) + " ..."
        raise SeriesNotFoundError(f"지표 '{indicatorId}'을 찾을 수 없습니다. 사용 가능: {available}")

    startDate = start if start else _defaultStart(entry.frequency)
    endDate = end if end else _defaultEnd(entry.frequency)

    # 시작/종료를 ECOS 형식으로 변환
    startDate = _formatDate(startDate, entry.frequency)
    endDate = _formatDate(endDate, entry.frequency, isEnd=True)

    rows = client.get(
        tableCode=entry.tableCode,
        freq=entry.frequency,
        startDate=startDate,
        endDate=endDate,
        itemCode=entry.itemCode,
    )

    dates: list[date] = []
    values: list[float | None] = []
    for row in rows:
        if not isinstance(row, dict):
            raise EcosError("ECOS observation 행이 객체가 아닙니다")
        timeValue = str(row.get("TIME") or "")
        d = _parseDate(timeValue, entry.frequency)
        if d is None:
            raise EcosError(f"ECOS TIME 값을 해석할 수 없습니다: {timeValue!r}")
        valStr = row.get("DATA_VALUE", "")
        if not valStr or valStr == "-":
            dates.append(d)
            values.append(None)
        else:
            try:
                dates.append(d)
                values.append(float(str(valStr).replace(",", "")))
            except (TypeError, ValueError) as exc:
                raise EcosError(f"ECOS DATA_VALUE를 해석할 수 없습니다: {valStr!r}") from exc

    df = pl.DataFrame({"date": dates, "value": values}).with_columns(
        pl.col("date").cast(pl.Date),
        pl.col("value").cast(pl.Float64),
    )

    isDailyFreq = entry.frequency == "D"
    _cache.put(indicatorId, start, end, df, daily=isDailyFreq)

    if enrich:
        from dartlab.gather.transforms.macro import enrichAndCache

        df = enrichAndCache(indicatorId, df, source="ecos")

    if limit is not None and limit > 0:
        return df.tail(limit)
    return df


def fetchMulti(
    client: EcosClient,
    indicatorIds: list[str],
    *,
    start: str | None = None,
    end: str | None = None,
    limit: int | None = None,
) -> pl.DataFrame:
    """복수 지표 → wide DataFrame ``(date, GDP, CPI, ...)``.

    Capabilities: fetchSeries fan-out → outer join + forward_fill.
    AIContext: 한국 매크로 cross-series 분석 진입 — facade.Ecos.compare 의 본체.
    Guide: 주기 다르면 outer join 후 forward_fill — caller dropna 권장.
    When: 한국 매크로 regime / correlation 분석 시.
    How: ``[fetchSeries(...).rename({'value': iid}) for iid in ids]`` → join chain → sort + fill.

    주기가 다른 지표를 합칠 때 outer join 후 forward-fill.

    Parameters
    ----------
    client : EcosClient
        ECOS REST API 클라이언트.
    indicatorIds : list[str]
        카탈로그 지표 ID 리스트.
    start : str | None
        시작일. None이면 2000년부터.
    end : str | None
        종료일. None이면 최신까지.
    limit : int | None
        반환 행수 상한 (가장 최근 N). None이면 전체.

    Returns
    -------
    pl.DataFrame
        컬럼: ``date`` (Date) — 관측일, 각 지표 ID (Float64) — 지표값.
        빈 리스트 입력 시 빈 DataFrame.

    Raises
    ------
    SeriesNotFoundError
        indicatorIds 중 하나라도 카탈로그에 없을 때.

    Requires
    --------
    EcosClient + 모든 indicatorIds 가 카탈로그 등록.

    Example
    -------
    >>> df = fetchMulti(client, ["CPI", "BASE_RATE"], start="2020-01-01")

    See Also
    --------
    fetchSeries : 본 함수의 내부 fan-out 대상.
    facade.Ecos.compare : 클래스 facade.
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

    out = result.sort("date").fill_null(strategy="forward")
    if limit is not None and limit > 0:
        return out.tail(limit)
    return out
