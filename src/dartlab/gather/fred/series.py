"""FRED 시계열 조회 — 단일/복수 시리즈, 검색, 메타, 릴리즈."""

from __future__ import annotations

from datetime import date, datetime

import polars as pl

from . import cache as _cache
from .client import FredClient
from .types import FredError, SeriesMeta


def fetchSeries(
    client: FredClient,
    seriesId: str,
    *,
    start: str | None = None,
    end: str | None = None,
    freq: str | None = None,
    aggregation: str = "avg",
    enrich: bool = False,
    limit: int | None = None,
) -> pl.DataFrame:
    """FRED 시계열 → Polars DataFrame ``(date, value)``.

    Capabilities: 캐시 확인 → FRED /series/observations GET → DataFrame 변환 + 캐시 저장.
    AIContext: FRED 단일 시계열의 단일 진입점 — facade.series / 외부 caller 모두 본 함수.
    Guide: missing value (".") 은 None 으로 처리. cache hit 시 즉시 반환.
    When: 매크로 단일 시계열 분석 시 (가장 빈번한 호출 path).
    How: cache.get → client.get(/series/observations) → date/value parse → cache.put.

    Parameters
    ----------
    client : FredClient
        FRED REST API 클라이언트.
    series_id : str
        FRED 시리즈 ID (예: "GDP", "UNRATE").
    start : str | None
        시작일 (YYYY-MM-DD). None이면 전체.
    end : str | None
        종료일. None이면 최신까지.
    freq : str | None
        리샘플 주파수 (d/w/bw/m/q/sa/a). None이면 원본.
    aggregation : str
        리샘플 집계 방법 (avg/sum/eop).
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
    FredError
        FRED API HTTP 오류 또는 인증 실패.

    Example
    -------
    >>> df = fetchSeries(client, "GDP", start="2020-01-01")

    Requires
    --------
    FredClient (``FRED_API_KEY``) + cache 가용.

    See Also
    --------
    fetchMulti : 복수 시리즈 wide.
    fetchMeta : 시리즈 메타.
    facade.Fred.series : 클래스 facade.
    """
    cached = _cache.get(seriesId, start, end, freq, aggregation)
    if cached is not None:
        return cached

    params: dict = {"series_id": seriesId}
    if start:
        params["observation_start"] = start
    if end:
        params["observation_end"] = end
    if freq:
        params["frequency"] = freq
    if aggregation != "avg":
        params["aggregation_method"] = aggregation

    data = client.get("/series/observations", **params)
    if not isinstance(data, dict):
        raise FredError("FRED series 응답 schema가 객체가 아닙니다")
    if "observations" not in data:
        raise FredError("FRED series 응답에 observations가 없습니다")
    observations = data["observations"]
    if not isinstance(observations, list):
        raise FredError("FRED observations가 배열이 아닙니다")

    dates: list[date] = []
    values: list[float | None] = []
    for obs in observations:
        if not isinstance(obs, dict):
            raise FredError("FRED observation 행이 객체가 아닙니다")
        try:
            d = datetime.strptime(obs["date"], "%Y-%m-%d").date()
        except (TypeError, ValueError, KeyError) as exc:
            raise FredError(f"FRED observation date를 해석할 수 없습니다: {obs.get('date')!r}") from exc
        val_str = obs.get("value", ".")
        if val_str == "." or val_str is None:
            dates.append(d)
            values.append(None)
        else:
            try:
                dates.append(d)
                values.append(float(val_str))
            except (TypeError, ValueError) as exc:
                raise FredError(f"FRED observation value를 해석할 수 없습니다: {val_str!r}") from exc

    df = pl.DataFrame({"date": dates, "value": values}).with_columns(
        pl.col("date").cast(pl.Date),
        pl.col("value").cast(pl.Float64),
    )

    is_daily = freq == "d" or (freq is None and len(df) > 500)
    _cache.put(seriesId, start, end, freq, aggregation, df, daily=is_daily)

    if enrich:
        from dartlab.gather.transforms.macro import enrichAndCache

        df = enrichAndCache(seriesId, df, source="fred")

    if limit is not None and limit > 0:
        return df.tail(limit)
    return df


def fetchMulti(
    client: FredClient,
    seriesIds: list[str],
    *,
    start: str | None = None,
    end: str | None = None,
    freq: str | None = None,
    limit: int | None = None,
) -> pl.DataFrame:
    """복수 시계열 → wide DataFrame ``(date, GDP, UNRATE, ...)``.

    Capabilities: fetchSeries fan-out → outer join + forward_fill + 메모리 관리.
    AIContext: macro cross-series 비교 진입 — 5 질문 batch 매크로 7771MB OOM 회귀 방지 코드.
    Guide: 주파수 다르면 outer join 후 forward_fill. del frames + gc.collect 로 Rust 힙 회수.
    When: 매크로 dashboard / regime 분석 / correlation 분석 시.
    How: fetchSeries fan-out → frames list → join chain → del + gc → forward_fill 일괄.

    주파수가 다른 시리즈를 합칠 때 outer join 후 forward-fill.

    Parameters
    ----------
    client : FredClient
        FRED REST API 클라이언트.
    series_ids : list[str]
        FRED 시리즈 ID 리스트.
    start : str | None
        시작일. None이면 전체.
    end : str | None
        종료일. None이면 최신까지.
    freq : str | None
        리샘플 주파수. None이면 원본.
    limit : int | None
        반환 행수 상한 (가장 최근 N). None이면 전체.

    Returns
    -------
    pl.DataFrame
        컬럼: ``date`` (Date) — 관측일, 각 시리즈 ID (Float64) — 지표값.
        빈 리스트 입력 시 빈 DataFrame.

    Raises
    ------
    FredError
        FRED API HTTP 오류.

    Example
    -------
    >>> df = fetchMulti(client, ["GDP", "UNRATE"], start="2020-01-01")

    Requires
    --------
    FredClient + 모든 ``seriesIds`` 가 valid (실패 시 부분 결과). 메모리 ≥ 시리즈 수 × 시계열 크기.

    See Also
    --------
    fetchSeries : 본 함수의 내부 fan-out 대상.
    facade.Fred.compare : 클래스 facade.
    """
    if not seriesIds:
        return pl.DataFrame()

    # 메모리 spike 방어 (5 질문 batch 매크로 7771 MB 경험):
    # - join 누적은 immutable polars 라 어쩔 수 없지만 forward_fill 을 컬럼별 30 회
    #   immutable copy 하던 것을 with_columns 한 번으로 묶음 (이전: 30 시리즈 → 30 회
    #   새 DataFrame, 메모리 spike 직접 원인).
    # - frames 리스트는 join 누적 후 명시적 del + gc.collect 로 Polars Rust 힙 회수
    #   유도 (Python GC 만으로는 회수 불가 — CLAUDE.md "[최우선] 메모리 안전 규칙").
    frames: list[pl.DataFrame] = []
    for sid in seriesIds:
        df = fetchSeries(client, sid, start=start, end=end, freq=freq)
        df = df.rename({"value": sid})
        frames.append(df)

    result = frames[0]
    for df in frames[1:]:
        result = result.join(df, on="date", how="full", coalesce=True)

    # frames 의 개별 DataFrame 들은 join 으로 흡수됐으므로 즉시 해제
    del frames
    import gc

    gc.collect()

    # forward_fill 일괄 — 30 시리즈도 한 번의 with_columns 로 (이전 30 회 → 1 회)
    fill_cols = [c for c in result.columns if c != "date"]
    if fill_cols:
        result = result.sort("date").with_columns([pl.col(c).forward_fill() for c in fill_cols])
    else:
        result = result.sort("date")

    if limit is not None and limit > 0:
        return result.tail(limit)
    return result


def searchSeries(
    client: FredClient,
    query: str,
    *,
    limit: int = 20,
) -> pl.DataFrame:
    """키워드 검색 → DataFrame.

    Capabilities: FRED /series/search endpoint GET → 인기도 순 DataFrame.
    AIContext: 카탈로그에 없는 시리즈 fuzzy 탐색 진입 — 사용자 자유 키워드.
    Guide: 영문 키워드. order_by="popularity" desc.
    When: 카탈로그 외 시리즈 탐색 시 (특수 indicator / micro data).
    How: ``client.get('/series/search', search_text=query, limit=limit, order_by='popularity')``.

    Parameters
    ----------
    client : FredClient
        FRED REST API 클라이언트.
    query : str
        검색어 (영문).
    limit : int
        최대 결과 수.

    Returns
    -------
    pl.DataFrame
        컬럼: ``id`` (Utf8) — 시리즈 ID, ``title`` (Utf8) — 제목,
        ``frequency`` (Utf8) — 주기, ``units`` (Utf8) — 단위,
        ``seasonal_adjustment`` (Utf8) — 계절조정,
        ``popularity`` (Int64) — 인기도,
        ``observation_start`` (Utf8) — 시작일,
        ``observation_end`` (Utf8) — 종료일.

    Raises
    ------
    FredError
        FRED API HTTP 오류.

    Example
    -------
    >>> df = searchSeries(client, "unemployment", limit=10)

    Requires
    --------
    FredClient (``FRED_API_KEY``).

    See Also
    --------
    catalog : 사전정의 그룹.
    fetchMeta : 단일 시리즈 메타.
    facade.Fred.search : 클래스 facade.
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


def fetchMeta(client: FredClient, seriesId: str, *, limit: int | None = None) -> SeriesMeta:
    """시계열 메타데이터 조회.

    Capabilities: FRED /series endpoint GET → SeriesMeta named tuple.
    AIContext: fetch 전 series 의 frequency/units/last_updated 확인 진입.
    Guide: 미존재 시리즈 → SeriesNotFoundError.
    When: 시리즈 단위 분석 전 메타 검증 시.
    How: ``client.get('/series', seriesId=seriesId)`` → SeriesMeta 패킹.

    Parameters
    ----------
    client : FredClient
        FRED REST API 클라이언트.
    series_id : str
        FRED 시리즈 ID.
    limit : int | None
        단건 SeriesMeta 반환 함수라 무시된다. 인터페이스 호환 목적.

    Returns
    -------
    SeriesMeta
        id, title, frequency, units, seasonal_adjustment,
        observation_start, observation_end, last_updated, notes 포함.

    Raises
    ------
    SeriesNotFoundError
        시리즈를 찾을 수 없을 때.

    Example
    -------
    >>> m = fetchMeta(client, "GDP")

    Requires
    --------
    FredClient (``FRED_API_KEY``) + 유효 seriesId.

    See Also
    --------
    fetchSeries : 본문 시계열.
    facade.Fred.meta : 클래스 facade.
    """
    del limit
    data = client.get("/series", seriesId=seriesId)
    serieses = data.get("seriess", [])
    if not serieses:
        from .types import SeriesNotFoundError

        raise SeriesNotFoundError(f"시리즈를 찾을 수 없습니다: {seriesId}")

    s = serieses[0]
    return SeriesMeta(
        id=s.get("id", seriesId),
        title=s.get("title", ""),
        frequency=s.get("frequency", ""),
        units=s.get("units", ""),
        seasonal_adjustment=s.get("seasonal_adjustment", ""),
        observation_start=s.get("observation_start", ""),
        observation_end=s.get("observation_end", ""),
        last_updated=s.get("last_updated", ""),
        notes=s.get("notes", ""),
    )


def fetchReleases(client: FredClient, *, limit: int = 20) -> pl.DataFrame:
    """최근 데이터 릴리즈 일정.

    Capabilities: FRED /releases endpoint GET → 보도자료 우선 정렬 DataFrame.
    AIContext: 매크로 신선도 모니터링 / 발표 일정 추적 진입.
    Guide: order_by="press_release" desc, sort_order=desc.
    When: 매크로 dashboard 의 staleness 표시 / 다음 발표 예측 시.
    How: ``client.get('/releases', limit=limit, order_by='press_release', sort_order='desc')``.

    Parameters
    ----------
    client : FredClient
        FRED REST API 클라이언트.
    limit : int
        최대 결과 수.

    Returns
    -------
    pl.DataFrame
        컬럼: ``id`` (Int64) — 릴리즈 ID, ``name`` (Utf8) — 릴리즈명,
        ``press_release`` (Boolean) — 보도자료 여부, ``link`` (Utf8) — URL.

    Raises
    ------
    FredError
        FRED API HTTP 오류.

    Example
    -------
    >>> df = fetchReleases(client, limit=5)

    Requires
    --------
    FredClient (``FRED_API_KEY``).

    See Also
    --------
    fetchMeta : 단일 시리즈의 last_updated.
    facade.Fred.releases : 클래스 facade.
    """
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
